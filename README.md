# FlowCo 6.0

A portable developer agent CLI for Linux and Android Termux. Python 3.10+; no required third-party runtime dependencies. The original license is unchanged.

## Run

```bash
python3 flowco.py --help
python3 flowco.py --selftest
python3 flowco.py
```

Install a global command with `python3 -m pip install .`; optional completion support with `python3 -m pip install '.[tui]'`. FlowCo never installs packages automatically.

Run `/setup` in the interactive CLI to configure the endpoint, model, API key environment variable, input/output/cache prices, and task dollar cap. Paid calls require confirmed prices and a cap. Environment keys are preferred; never commit secrets.

```bash
python3 flowco.py --provider ollama --workspace ./project --sandbox local "Inspect this project"
python3 flowco.py --workspace ./project --sandbox local --approval trusted "Fix the failing tests and verify"
python3 flowco.py --workspace ./project --resume RUN_ID --task-budget-usd 1
python3 flowco.py --provider ollama --workspace ./project --output jsonl "Inspect the project"
```

## Execution and recovery

Both interactive and one-shot modes initialize tools. Tool arguments are validated. Edits require a subsequent successful verification before completion. A run without verification returns an unverified result, not success.

Commands, verification, Git, scratch scripts, background jobs, and preview servers share approval checks. Commands need approval by default. `--approval trusted` explicitly enables unattended execution. The default sandbox disables commands if PRoot is unavailable; select `--sandbox local` explicitly for host execution. The `isolated` mode is a scratch directory with a clean environment, not an OS security boundary. Regex checks cannot contain arbitrary programs. Trust the project and commands before enabling host execution.

Private checkpoints live under `~/.flowco/sessions/`. `FLOWCO_CONFIG_DIR` selects another configuration directory. `/sessions` lists runs; `/resume RUN_ID` resumes. Interrupted operations with unknown outcomes require inspection before further mutations. Checkpoints contain project content and should remain private.

Exit codes: success 0; failure 1; configuration error 2; paused/unverified 3; cancelled 130.

## Providers, caching, and spending

Profiles support `api_style: "chat_completions"` and `api_style: "responses"`, custom OpenAI-compatible gateways, and keyless local servers. Native Anthropic Messages and Gemini APIs are not included.

Use `/apipro` for profiles. Advanced settings include:

```text
/settings set api_style responses
/settings set capabilities {"custom_temp":false,"max_key":"max_completion_tokens"}
/settings set routing {"coder":"cheap-coder","subagent":"cheap-researcher"}
```

Routing references existing separately priced profiles. It does not automatically choose or escalate models. Models without native tools need explicit `capabilities.text_tools: true`; this enables strict JSON tool responses.

Supported capability overrides include tools, text_tools, stream, stream_usage, custom_temp, reasoning, sys_role, system_role, ctx, max_key, and cache_control. Model-family defaults are heuristics; custom endpoints may need explicit overrides.

Each actual model attempt reserves conservative input/output allowances. The API output cap is reduced to the remaining budget. Reported usage reconciles the reservation; missing or interrupted usage is estimated conservatively. Prices are captured per request. Unknown prices are distinct from explicitly free cache reads. `/cost` shows the ledger; `/budget add N` extends tokens and `/budget add-usd N` extends the current task dollar cap. Provider invoices depend on actual metering and the accuracy of configured prices.

Static instructions and tool definitions remain stable for prefix caching. Anthropic cache metadata is automatically enabled only for Anthropic models through OpenRouter, or explicitly through capability configuration. Provider-reported cache usage is displayed; no fixed discount is promised.

## Terminal and validation

The transcript preserves scrollback, streams output, shows compact tool results, and provides a live cost/status footer on supported terminals. `/thinking` or Ctrl+O at the input prompt changes detail. Live Ctrl+O during execution is not implemented. NO_COLOR, --no-color, redirected text, and JSONL are supported.

```bash
python3 flowco.py --selftest
python3 -S flowco.py --selftest
python3 -m unittest discover -s tests
bash -n run_flowco_tmux.sh
```

See TEST_REPORT.md for tested coverage and remaining work. Historical handover and prompt documents describe older releases; this README describes this build. See LICENSE for usage terms.
