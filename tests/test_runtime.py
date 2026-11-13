import io
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import flowco
from support import FlowCoTestCase


class TestRuntime(FlowCoTestCase):
    def test_verification_obeys_disabled_execution(self):
        flowco.SANDBOX['mode'] = 'off'
        with mock.patch.object(flowco.subprocess, 'Popen') as spawn:
            self.assertIn('[VERIFICATION FAILED]', flowco.tool_verify(command='echo hi'))
            spawn.assert_not_called()

    def test_all_commands_obey_approval(self):
        flowco.CFG['confirm_commands'] = True
        for execute in [lambda: flowco.tool_verify(command='echo hi'),
                        lambda: flowco.tool_run_command('echo hi'),
                        lambda: flowco.tool_run_background('echo hi'),
                        lambda: flowco.tool_run_sandbox(command='echo hi'),
                        lambda: flowco.tool_git('status'),
                        lambda: flowco.tool_start_server(command='echo hi')]:
            with mock.patch.object(flowco.subprocess, 'Popen') as spawn, mock.patch('sys.stdin.isatty', return_value=False):
                self.assertIn('confirmation', execute())
                spawn.assert_not_called()

    def test_sandbox_script_path_escape(self):
        for name in ['../../escape.py', '/tmp/escape.py', 'x.py;echo hi', 'sub/file.py']:
            self.assertIn('Error:', flowco.tool_run_sandbox(script_code='print(42)', script_name=name))
        self.assertFalse((flowco.WORK / 'escape.py').exists())

    def test_timeout_and_nonzero_exit(self):
        self.assertEqual(flowco.execute_process('exit 42').exit_code, 42)
        self.assertEqual(flowco.execute_process('sleep 3', timeout=0.1).exit_code, 124)

    def test_free_cache_cost(self):
        self.assertEqual(flowco.calculate_cost(1000000, 0, 1000000,
                          {'price_in_per_m': 2, 'price_cache_read_per_m': 0}), 0)

    def test_responses_usage(self):
        self.assertEqual(flowco.normalize_usage({'input_tokens': 100, 'output_tokens': 30,
                          'input_tokens_details': {'cached_tokens': 80}}), (100, 30, 80, False))

    def test_output_is_capped_before_request(self):
        flowco.BUDGET.start_task('cap', 3000)
        ticket, output = flowco.BUDGET.reserve(1000, 8192, {'base_url': 'http://localhost:1/v1'})
        self.assertEqual(output, 2000)
        flowco.BUDGET.release(ticket)

    def test_dollar_cap_and_unknown_pricing(self):
        profile = {'base_url': 'https://example.com/v1', 'pricing_confirmed': True,
                   'price_in_per_m': 1, 'price_out_per_m': 10}
        flowco.CFG['task_budget_usd'] = .002
        ticket, output = flowco.BUDGET.reserve(1000, 8000, profile)
        self.assertLessEqual(output, 100)
        flowco.BUDGET.release(ticket)
        profile['pricing_confirmed'] = False
        with self.assertRaises(flowco.ConfigurationError):
            flowco.BUDGET.reserve(100, 100, profile)

    def test_cache_options_are_provider_specific(self):
        msgs = [{'role': 'system', 'content': 'stable'}]
        profile = {'base_url': 'https://openrouter.ai/api/v1', 'model': 'meta-llama/llama'}
        self.assertIsInstance(flowco.prepare_cached_messages(msgs, profile)[0]['content'], str)
        profile['model'] = 'anthropic/claude-sonnet'
        self.assertIsInstance(flowco.prepare_cached_messages(msgs, profile)[0]['content'], list)
        self.assertEqual(msgs[0]['content'], 'stable')

    def test_compaction_keeps_tool_pairs(self):
        messages = [{'role': 'system', 'content': 'static'}] + [{'role': 'user', 'content': str(i)} for i in range(10)]
        messages.extend([{'role': 'assistant', 'tool_calls': [{'id': 'a', 'function': {'name': 'read_file', 'arguments': '{}'}}]},
                         {'role': 'tool', 'tool_call_id': 'a', 'content': 'data'},
                         {'role': 'user', 'content': 'continue'}])
        flowco.compact(messages, True)
        ids = {tc['id'] for m in messages for tc in m.get('tool_calls', [])}
        self.assertTrue(all(m['tool_call_id'] in ids for m in messages if m['role'] == 'tool'))
        self.assertEqual(messages[0]['content'], 'static')

    def test_dispatch_rejects_bad_arguments(self):
        for args in ['not json', '[]', '{"path":42}', '{"path":"x","unexpected":true}']:
            self.assertEqual(flowco.dispatch_tool('read_file', args)['status'], 'error')

    def test_readonly_specialist_cannot_execute(self):
        flowco.CURRENT_CAPABILITIES = set()
        with mock.patch.object(flowco.subprocess, 'Popen') as spawn:
            self.assertIn('permission', flowco.tool_verify(command='echo hi'))
            spawn.assert_not_called()

    def test_terminal_controls_and_secrets(self):
        self.assertNotIn('\x1b', flowco.safe_text('\x1b]52;c;secret\x07\x1b[31mhi'))
        flowco.CFG['api_key'] = 'my-secret-key'
        self.assertNotIn('my-secret-key', flowco.redact('key=my-secret-key'))

    def test_unverified_edits_cannot_complete(self):
        responses = [self.response(calls=[self.call('w', 'write_file', {'path': 'x.txt', 'content': 'hello'})]), self.response('done')]
        with mock.patch.object(flowco, 'chat', side_effect=responses):
            code = flowco.run_turn([{'role': 'system', 'content': 'static'}], 'write file')
        self.assertEqual(code, 3)
        self.assertEqual(flowco.RUN_DATA['status'], 'unverified')

    def test_verified_task_and_checkpoint(self):
        responses = [self.response(calls=[self.call('w', 'write_file', {'path': 'x.txt', 'content': 'hello'})]),
                     self.response(calls=[self.call('v', 'verify', {'check_file': 'x.txt'})]), self.response('done')]
        with mock.patch.object(flowco, 'chat', side_effect=responses):
            self.assertEqual(flowco.run_turn([{'role': 'system', 'content': 'static'}], 'write file'), 0)
        messages = flowco.load_run(flowco.RUN_DATA['id'])
        self.assertEqual(len([m for m in messages if m.get('role') == 'tool']), 2)
        self.assertEqual((flowco.WORK / 'x.txt').read_text(), 'hello')

    def test_interrupted_tool_is_not_replayed(self):
        flowco.RUN_DATA.update(id='interrupted', goal='edit', status='paused', journal={'w': {'status': 'started'}}, dirty=0, verified=0, evidence=[])
        messages = [{'role': 'system', 'content': 's'}, {'role': 'assistant', 'tool_calls': [self.call('w', 'write_file', {'path': 'x', 'content': 'y'})]}]
        flowco.save_run(messages)
        flowco.load_run('interrupted')
        self.assertEqual(flowco.dispatch_tool('write_file', '{"path":"x","content":"y"}')['status'], 'error')
        self.assertFalse((flowco.WORK / 'x').exists())

    def test_sse_comments_and_multiline_data(self):
        data = [b': ping\r\n', b'data: {"a":\r\n', b'data: 1}\r\n', b'\r\n', b'data: [DONE]\n', b'\n']
        self.assertEqual(list(flowco.iter_sse(data)), [{'a': 1}, {'_done': True}])

    def test_pending_spend_is_recovered_once(self):
        flowco.RUN_DATA.update(id='pending', goal='inspect', status='executing', journal={}, dirty=0, verified=0, evidence=[])
        flowco.BUDGET.start_task('pending')
        flowco.BUDGET.reservations['ticket'] = {'tokens': 100, 'cost': .01}
        flowco.save_run([{'role': 'system', 'content': 'static'}])
        flowco.load_run('pending')
        self.assertEqual(flowco.BUDGET.task_cost, .01)
        flowco.load_run('pending')
        self.assertEqual(flowco.BUDGET.task_cost, .01)

    @staticmethod
    def call(tid, name, args):
        return {'id': tid, 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}

    @staticmethod
    def response(text='', calls=None):
        msg = {'role': 'assistant', 'content': text}
        if calls:
            msg['tool_calls'] = calls
        return {'choices': [{'message': msg, 'finish_reason': 'tool_calls' if calls else 'stop'}]}


class TestHttpProviders(FlowCoTestCase):
    def setUp(self):
        super().setUp()
        self.requests = []
        self.responses = []
        outer = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                outer.requests.append((self.path, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                status, kind, body = outer.responses.pop(0)
                self.send_response(status)
                self.send_header('Content-Type', kind)
                self.send_header('Retry-After', '0')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        flowco.CFG.update(base_url='http://127.0.0.1:%d/v1' % self.server.server_port,
                          model='test-model', max_tokens=100, max_retries=1)

    def enqueue(self, data, status=200):
        self.responses.append((status, 'application/json', json.dumps(data).encode()))

    def test_chat_completions_http(self):
        data = TestRuntime.response('hello')
        data['usage'] = {'prompt_tokens': 10, 'completion_tokens': 5}
        self.enqueue(data)
        result = flowco.chat_plain([{'role': 'user', 'content': 'hi'}], tools=[])
        self.assertEqual(result['choices'][0]['message']['content'], 'hello')
        self.assertEqual(self.requests[0][0], '/v1/chat/completions')
        self.assertEqual(flowco.BUDGET.total_task_tokens(), 15)

    def test_responses_http_and_tool_conversion(self):
        flowco.CFG['api_style'] = 'responses'
        self.enqueue({'status': 'completed', 'output': [{'type': 'function_call', 'call_id': 'c1', 'name': 'read_file', 'arguments': '{"path":"x"}'}],
                      'usage': {'input_tokens': 20, 'output_tokens': 3}})
        result = flowco.chat_plain([{'role': 'user', 'content': 'read x'}], tools=flowco.build_tools())
        self.assertEqual(result['choices'][0]['message']['tool_calls'][0]['id'], 'c1')
        self.assertEqual(self.requests[0][0], '/v1/responses')
        self.assertIn('max_output_tokens', self.requests[0][1])

    def test_stream_assembles_fragmented_calls(self):
        chunks = [{'choices': [{'delta': {'tool_calls': [{'index': 0, 'id': 'c1', 'function': {'name': 'read_', 'arguments': '{"path":'}}]}}]},
                  {'choices': [{'delta': {'tool_calls': [{'index': 0, 'function': {'name': 'file', 'arguments': '"x"}'}}]}, 'finish_reason': 'tool_calls'}]},
                  {'choices': [], 'usage': {'prompt_tokens': 10, 'completion_tokens': 6}}]
        body = ''.join('data: ' + json.dumps(c) + '\n\n' for c in chunks) + 'data: [DONE]\n\n'
        self.responses.append((200, 'text/event-stream', body.encode()))
        result = flowco.chat_stream([{'role': 'user', 'content': 'hi'}], tools=[])
        call = result['choices'][0]['message']['tool_calls'][0]
        self.assertEqual(call['function']['name'], 'read_file')
        self.assertEqual(json.loads(call['function']['arguments']), {'path': 'x'})

    def test_responses_stream_completion(self):
        flowco.CFG['api_style'] = 'responses'
        final = {'status': 'completed', 'output': [{'type': 'message', 'role': 'assistant',
                 'content': [{'type': 'output_text', 'text': 'hello'}]}], 'usage': {'input_tokens': 12, 'output_tokens': 2}}
        events = [{'type': 'response.output_text.delta', 'delta': 'hello'},
                  {'type': 'response.completed', 'response': final}]
        body = ''.join('data: ' + json.dumps(event) + '\n\n' for event in events)
        self.responses.append((200, 'text/event-stream', body.encode()))
        result = flowco.chat_stream([{'role': 'user', 'content': 'hi'}], tools=[])
        self.assertEqual(result['choices'][0]['message']['content'], 'hello')
        self.assertEqual(flowco.BUDGET.total_task_tokens(), 14)

    def test_auth_failure_is_not_retried(self):
        self.enqueue({'error': 'bad key'}, 401)
        with self.assertRaises(RuntimeError):
            flowco.chat_plain([{'role': 'user', 'content': 'hi'}], tools=[])
        self.assertEqual(len(self.requests), 1)

    def test_rate_limit_retries_are_bounded(self):
        self.enqueue({'error': 'slow'}, 429)
        self.enqueue(TestRuntime.response('ok'))
        flowco.chat_plain([{'role': 'user', 'content': 'hi'}], tools=[])
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(flowco.BUDGET.session_usage['retries'], 1)

    def test_incomplete_stream_is_not_retried(self):
        body = 'data: ' + json.dumps({'choices': [{'delta': {'content': 'partial'}}]}) + '\n\n'
        self.responses.append((200, 'text/event-stream', body.encode()))
        with self.assertRaises(flowco.PartialResponseError):
            flowco.chat_stream([{'role': 'user', 'content': 'hi'}], tools=[])
        self.assertEqual(len(self.requests), 1)
        self.assertGreater(flowco.BUDGET.total_task_tokens(), 0)


class TestCli(FlowCoTestCase):
    def command(self, *args, stdlib=False):
        executable = [sys.executable] + (['-S'] if stdlib else [])
        env = {**os.environ, 'FLOWCO_CONFIG_DIR': str(flowco.CONFIG_DIR), 'FLOWCO_TEST_MODE': '1'}
        return subprocess.run(executable + [flowco.__file__, *args], env=env, capture_output=True, text=True, timeout=15)

    def test_one_shot_jsonl(self):
        result = self.command('--workspace', str(flowco.WORK), '--provider', 'ollama', '--output', 'jsonl', 'hello')
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(events[0]['event'], 'run_started')
        self.assertEqual(events[-1]['status'], 'completed')
        self.assertTrue(list(flowco.SESSION_DIR.glob('*.json')))

    def test_no_optional_dependencies(self):
        result = self.command('--workspace', str(flowco.WORK), '--provider', 'ollama', 'hello', stdlib=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('COMPLETED', result.stdout)

    def test_invalid_budgets_and_unknown_provider(self):
        for args in [('--task-budget-usd', 'nan'), ('--task-token-budget', '-1'), ('--provider', 'missing')]:
            self.assertEqual(self.command(*args).returncode, 2)

    def test_pseudo_terminal_plain_output(self):
        import pty
        master, slave = pty.openpty()
        try:
            env = {**os.environ, 'FLOWCO_CONFIG_DIR': str(flowco.CONFIG_DIR), 'FLOWCO_TEST_MODE': '1', 'TERM': 'dumb'}
            child = subprocess.Popen([sys.executable, flowco.__file__, '--workspace', str(flowco.WORK), '--provider', 'ollama', '--no-color', 'hello'],
                                     stdin=subprocess.DEVNULL, stdout=slave, stderr=slave, env=env)
            os.close(slave)
            slave = None
            self.assertEqual(child.wait(timeout=15), 0)
            output = os.read(master, 65536).decode()
            self.assertIn('COMPLETED', output)
            self.assertNotIn('\x1b[3', output)
        finally:
            os.close(master)
            if slave is not None:
                os.close(slave)
