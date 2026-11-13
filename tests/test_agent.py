"""
test_agent.py - Offline unit tests for FlowCo v5.0 agent architecture, DAG, and verification
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add work directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flowco
from support import FlowCoTestCase


class TestAgentArchitecture(FlowCoTestCase):
    def setUp(self):
        super().setUp()
        self.td = tempfile.TemporaryDirectory()
        self.test_root = Path(self.td.name).resolve()
        self.orig_work = flowco.WORK
        self.orig_backup = flowco.BACKUP_DIR
        flowco.WORK = (self.test_root / "workspace").resolve()
        flowco.WORK.mkdir(parents=True, exist_ok=True)
        flowco.BACKUP_DIR = (self.test_root / "backups").resolve()
        flowco.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        flowco.WORK = self.orig_work
        flowco.BACKUP_DIR = self.orig_backup
        self.td.cleanup()

    def test_task_graph_dag_and_cycles(self):
        """Verify DAG scheduling, dependency enforcement, and cycle detection."""
        flowco.tool_task_graph("init")
        flowco.tool_task_graph("add", task_id="t1", title="Research codebase")
        flowco.tool_task_graph("add", task_id="t2", title="Implement feature", depends_on="t1")

        # Cycle creation must be rejected
        cycle_res = flowco.tool_task_graph("add", task_id="t3", title="Cyclic task", depends_on="t2")
        self.assertNotIn("Error", cycle_res)
        cycle_res2 = flowco.tool_task_graph("update", task_id="t1", depends_on="t3")
        self.assertIn("Circular dependency", cycle_res2)

        # Before t1 is DONE, t2 must be PENDING/BLOCKED
        show = flowco.tool_task_graph("show")
        self.assertIn("[READY] t1", show)
        self.assertIn("[PENDING] t2", show)

        # Mark t1 DONE -> t2 becomes READY
        flowco.tool_task_graph("update", task_id="t1", status="DONE")
        show2 = flowco.tool_task_graph("show")
        self.assertIn("[DONE] t1", show2)
        self.assertIn("[READY] t2", show2)

    def test_atomic_file_write_and_undo(self):
        """Verify atomic writes leave no temp files and undo restores previous content."""
        target = flowco.safe_path("example.txt")
        res1 = flowco.tool_write_file("example.txt", "Initial content v1")
        self.assertIn("Wrote", res1)
        self.assertEqual(target.read_text(encoding="utf-8"), "Initial content v1")

        # Edit file
        res2 = flowco.tool_write_file("example.txt", "Updated content v2")
        self.assertIn("Wrote", res2)
        self.assertEqual(target.read_text(encoding="utf-8"), "Updated content v2")

        # Restore via undo
        res_undo = flowco.tool_undo("example.txt")
        self.assertIn("restored", res_undo.lower())
        self.assertEqual(target.read_text(encoding="utf-8"), "Initial content v1")

    def test_verification_gate_exit_codes(self):
        """Verify tool_verify validates real process return codes and file invariants."""
        # Check command success
        res_pass = flowco.tool_verify(command="echo OK_PASS")
        self.assertIn("[VERIFICATION PASSED]", res_pass)

        # Check command failure exit code
        res_fail = flowco.tool_verify(command="exit 42")
        self.assertIn("[VERIFICATION FAILED]", res_fail)
        self.assertIn("code 42", res_fail)

        # Check Python syntax validation
        py_bad = flowco.WORK / "bad.py"
        py_bad.write_text("def broken_syntax(:\n", encoding="utf-8")
        res_syntax = flowco.tool_verify(syntax_check="bad.py")
        self.assertIn("[VERIFICATION FAILED]", res_syntax)
        self.assertIn("syntax error", res_syntax.lower())

    def test_task_graph_delete_and_missing_deps(self):
        """Verify duplicate tasks rejected, missing dependencies mark task BLOCKED, and delete action cleans graph."""
        flowco.tool_task_graph("init")
        flowco.tool_task_graph("add", task_id="t1", title="Task 1")

        # Duplicate ID should be rejected
        dup_res = flowco.tool_task_graph("add", task_id="t1", title="Task 1 again")
        self.assertIn("already exists", dup_res)

        # Task with missing dependency must be BLOCKED
        flowco.tool_task_graph("add", task_id="t2", title="Task 2", depends_on="non_existent_dep")
        show = flowco.tool_task_graph("show")
        self.assertIn("[BLOCKED] t2", show)

        # Delete action
        del_res = flowco.tool_task_graph("delete", task_id="t1")
        self.assertIn("Deleted task 't1'", del_res)
        self.assertNotIn("t1", flowco.TASK_GRAPH["tasks"])

    def test_local_model_switch_and_sandbox(self):
        """Verify /local use and /sandbox commands configure profiles cleanly."""
        flowco.cmd_local("use ollama qwen2.5-coder")
        self.assertEqual(flowco.CFG["active_provider"], "ollama")
        self.assertIn("11434", flowco.CFG["base_url"])

        flowco.cmd_sandbox("off")
        self.assertEqual(flowco.SANDBOX["mode"], "off")

        flowco.cmd_sandbox("local")
        self.assertEqual(flowco.SANDBOX["mode"], "local")

        flowco.cmd_sandbox("isolated")
        self.assertEqual(flowco.SANDBOX["mode"], "isolated")

    def test_persistent_brain_memory_and_compaction(self):
        """Verify brain memory persistence to disk and context compaction anchor."""
        mem = flowco.update_brain_memory(
            goal="Architect FlowCo agent system",
            decision="Adopt isolated sandbox and auto-compaction",
            file_touched="engine.py",
            note="added kernel",
            verified="All unit tests pass",
            plan="1. Inspect 2. Execute 3. Verify"
        )
        self.assertEqual(mem["task_goal"], "Architect FlowCo agent system")
        self.assertIn("Adopt isolated sandbox and auto-compaction", mem["decisions"])
        self.assertIn("All unit tests pass", mem["verified_facts"])

        # Check files created on disk
        self.assertTrue(flowco.brain_memory_path().is_file())
        self.assertTrue(flowco.brain_markdown_path().is_file())
        md_text = flowco.brain_markdown_path().read_text(encoding="utf-8")
        self.assertIn("Architect FlowCo agent system", md_text)
        self.assertIn("Adopt isolated sandbox", md_text)

        # Test context compaction into brain anchor
        msgs = [{"role": "system", "content": "You are FlowCo agent."}]
        for i in range(12):
            msgs.append({"role": "user", "content": f"Turn query {i}"})
            msgs.append({"role": "assistant", "content": f"Turn response {i}"})
        self.assertEqual(len(msgs), 25)

        flowco.compact(msgs, force=True)
        # Should be system prompt + brain anchor + recent turns (max 6)
        self.assertLess(len(msgs), 10)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn("BRAIN MEMORY & CONTEXT COMPACT ANCHOR", msgs[1]["content"])

    def test_isolated_sandbox_execution(self):
        """Verify code and script execution in dedicated .sandbox/ environment."""
        res_cmd = flowco.tool_run_sandbox(command="echo 'SANDBOX_OK_123'")
        self.assertIn("SANDBOX_OK_123", res_cmd)

        script = "def multiply(a, b): return a * b\nprint('PRODUCT=' + str(multiply(6, 7)))"
        res_py = flowco.tool_run_sandbox(script_code=script, script_name="test_prod.py")
        self.assertIn("PRODUCT=42", res_py)
        self.assertTrue((flowco.WORK / ".sandbox" / "scripts" / "test_prod.py").is_file())

    def test_model_capabilities_and_quirk_omission(self):
        """Verify live capability heuristics and auto-omission of incompatible parameters."""
        caps_o1 = flowco.probe_model_capabilities("openai/o1-mini")
        self.assertTrue(caps_o1["reasoning"])
        self.assertFalse(caps_o1["custom_temp"])

        warnings = flowco.check_model_capability_warnings(caps_o1)
        # CFG temperature defaults to 0.2, so warning must be generated
        self.assertTrue(any("temperature" in w for w in warnings))

        # Test that apply_quirks strips forbidden temperature for o1
        body = {"model": "openai/o1-preview", "temperature": 0.5, "max_tokens": 4096}
        sanitized = flowco.apply_quirks(body)
        self.assertNotIn("temperature", sanitized)
        self.assertEqual(sanitized["max_tokens"], 4096)

        # Non-reasoning model strips reasoning_effort
        body_non_reasoning = {"model": "gpt-4o", "temperature": 0.2, "reasoning_effort": "high"}
        sanitized2 = flowco.apply_quirks(body_non_reasoning)
        self.assertNotIn("reasoning_effort", sanitized2)
        self.assertEqual(sanitized2["temperature"], 0.2)

    def test_settings_and_thinking_commands(self):
        """Verify /settings set/reset and /thinking toggle."""
        orig_limit = flowco.CFG.get("auto_compact_tokens", 150000)
        orig_collapse = flowco.CFG.get("collapse_thinking", False)

        flowco.cmd_settings("set auto_compact_tokens 220000")
        self.assertEqual(flowco.CFG["auto_compact_tokens"], 220000)

        flowco.cmd_settings("set collapse_thinking true")
        self.assertTrue(flowco.CFG["collapse_thinking"])

        flowco.cmd_thinking("off")
        self.assertFalse(flowco.CFG["collapse_thinking"])

        flowco.cmd_thinking("toggle")
        self.assertTrue(flowco.CFG["collapse_thinking"])

        # Reset setting
        flowco.cmd_settings("reset auto_compact_tokens")
        self.assertEqual(flowco.CFG["auto_compact_tokens"], orig_limit)

        # Restore
        flowco.CFG["collapse_thinking"] = orig_collapse

    def test_ask_user_tool(self):
        """Verify ask_user tool behavior in non-interactive / automated environments."""
        # Non-interactive mode must return fallback immediately without hanging
        res = flowco.tool_ask_user("Which database should we use?", options=["SQLite", "PostgreSQL"])
        self.assertIn("Non-Interactive Mode", res)

        # Empty question check
        res_empty = flowco.tool_ask_user("")
        self.assertIn("Error: question text is required", res_empty)

        # Argument cleaner check
        cleaned = flowco.clean_args("ask_user", {"prompt": "Confirm port?", "choices": [8080, 3000]})
        self.assertEqual(cleaned["question"], "Confirm port?")
        self.assertEqual(cleaned["options"], [8080, 3000])

    def test_claude_cognition_prompt_and_caching(self):
        """Verify Claude-style cognitive methodology prompt and prompt caching breakpoints."""
        sys_p = flowco.system_prompt()
        self.assertIn("Claude-Style Reasoning Engine", sys_p)
        self.assertIn("DEEP INTENT ANALYSIS", sys_p)
        self.assertIn("BOUNDARY DISCIPLINE", sys_p)
        self.assertIn("ask_user", sys_p)
        self.assertIn("run_sandbox", sys_p)

        # Test prompt cache breakpoint injection for Claude/OpenRouter
        orig_base = flowco.CFG.get("base_url")
        orig_model = flowco.CFG.get("model")
        try:
            flowco.CFG["base_url"] = "https://openrouter.ai/api/v1"
            flowco.CFG["model"] = "anthropic/claude-3.5-sonnet"
            msgs = [
                {"role": "system", "content": "You are FlowCo."},
                {"role": "user", "content": "🧠 [PERSISTENT BRAIN MEMORY & CONTEXT COMPACT ANCHOR]\nPrevious summary."},
                {"role": "user", "content": "Recent task prompt."},
            ]
            cached_msgs = flowco.prepare_cached_messages(msgs)
            # System prompt must have cache_control block
            self.assertIsInstance(cached_msgs[0]["content"], list)
            self.assertEqual(cached_msgs[0]["content"][0]["cache_control"]["type"], "ephemeral")
            # Compaction anchor must have cache_control block
            self.assertIsInstance(cached_msgs[1]["content"], list)
            self.assertEqual(cached_msgs[1]["content"][0]["cache_control"]["type"], "ephemeral")
            # Normal recent turns remain pure strings for token economy
            self.assertEqual(cached_msgs[2]["content"], "Recent task prompt.")
        finally:
            flowco.CFG["base_url"] = orig_base
            flowco.CFG["model"] = orig_model


if __name__ == "__main__":
    unittest.main()
