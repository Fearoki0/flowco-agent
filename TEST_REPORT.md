# FlowCo 6.0 verification report

Environment: Linux, Python 3.12.14. No paid API calls were made.

## Results

- Full self-test: 78 passed, 0 failed (22 embedded checks and 56 modular tests).
- Dependency-free self-test: run with `python -S flowco.py --selftest`.
- Python compilation, shell launcher syntax, and Git whitespace checks.
- Subprocess tests for one-shot CLI, JSONL events, checkpoints, invalid arguments, operation without optional packages, and pseudo-terminal output.

Local HTTP server tests exercise actual request construction and response parsing for Chat Completions and Responses, fragmented streaming tool calls, usage events, authentication failures, rate-limit retries, and incomplete-stream accounting.

Regression tests cover verification approval bypass, disabled execution, scratch-script path traversal, timeouts, nonzero exit status, dollar/token output caps, unknown pricing, free cached input, provider-specific cache options, tool-pair compaction, malformed arguments, specialist permissions, secret redaction, verified/unverified completion, and interrupted-tool recovery.

## Limits and remaining work

No hosted provider was tested with real credentials. Protocol tests do not establish compatibility with every deployment. No physical Termux device was attached. CI is configured for Python 3.10, 3.12, and 3.14; only 3.12 was run locally.

The larger plan was narrowed when the user requested a quick finish. Live detail keyboard controls during execution, automatic cheaper-model selection/escalation, extensive resize tests, full metadata discovery, and exhaustive crash/concurrent-session recovery tests remain unfinished. Specialist execution is sequential. Model routing uses explicitly configured profiles.

Native Anthropic/Gemini APIs are outside the selected scope. Local/scratch execution is not OS isolation. Spending estimates depend on prices and provider usage and cannot enforce the provider invoice.

The delivery ZIP excludes Git internals, bytecode, and caches. Existing license and historical user documents are preserved.
