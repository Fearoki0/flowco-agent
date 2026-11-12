# ⚡ FlowCo v5.0 — Autonomous Agentic Engineering Platform

> Single-file, zero-dependency autonomous AI software engineer and execution platform built natively for **Android Termux** and **Linux**.

FlowCo is designed to turn low-resource mobile and terminal environments into a full-scale autonomous AI software development station. It runs entirely on the **Python standard library** with zero mandatory `pip install` requirements, operating seamlessly in both interactive terminals and **tmux** sessions with live pane titles, streaming download engines, background task supervision, capability-restricted subagent swarms, centralized token budgets, and self-verifying test gates.

---

## ✨ Key Features in FlowCo v5.0

### 🧠 Token Auto-Compaction & Persistent Brain Memory
- **Autonomous Compaction at 150k/250k Tokens**: Monitors active context tokens and automatically condenses older dialogue into a compact memory anchor when reaching threshold limits (configurable via `/settings set auto_compact_tokens <tokens>`).
- **Persistent Brain Memory Files**: Actively tracks and persists architectural decisions, touched files, verified facts, and execution plans to `.flowco/memory.json` and human-readable `.flowco/MEMORY.md`.
- **KV Prompt Cache Optimization**: Keeps static instructions byte-identical at the prompt prefix to maximize 80–90% token discounts on caching providers (OpenAI, DeepSeek, Anthropic, OpenRouter).
- **Read-Loop Circuit Breaker**: Detects repetitive read-only queries with zero code progress and halts context thrashing before token budgets burn out.

### 🛡️ Dedicated Isolated Local Sandbox (`.sandbox/`)
- **Safe Code & Test Execution**: Autonomous tool `run_sandbox` executes temporary code, algorithms, and tests inside `.sandbox/` with an isolated `$HOME`, sanitized `$TMPDIR`, and clean environment without polluting workspace context.
- **Dedicated Sandbox Isolation Mode**: `/sandbox isolated` switches all shell commands to run inside the workspace sandbox directory.

### 🤖 Live Model Capability Probe & Safety Warning Bar
- **Live Endpoint Querying & Capability Matrix**: Probes active model parameters (DeepSeek R1/V3, OpenAI o1/o3-mini, GPT-4o, Claude 3.5, Gemini Thinking, Qwen, Ollama, Llama).
- **Proactive Incompatibility Warning Bar**: Flags when configured settings conflict with model capabilities (e.g., custom temperature or system prompt roles on `o1`), auto-omitting unsupported parameters to prevent HTTP 400 Bad Request failures.

### 🖥️ Interactive Settings Dashboard (`/settings`) & Thinking Collapse (`Ctrl+O`)
- **Interactive Configuration Panel (`/settings`)**: Unified TUI dashboard for terminal display, sandbox isolation, token auto-compaction thresholds, command timeouts, and model parameters.
- **Thinking Process & Output Collapse (`Ctrl+O` & `/thinking`)**: Toggle verbose model chain-of-thought and multi-line task execution output into compact single-line badges with a single keystroke (`Ctrl+O`) or slash command (`/thinking toggle`).

### 🛡️ Centralized Token Budget & Spending Safety
- **Strict Separation of Accounting**: Independent tracking of **Current Task Usage**, **Session Usage**, and per-**Provider Usage**. Starting a new task refreshes task allowances without wiping session history.
- **Pre-Request Gate Checks**: Every model invocation (main loop, subagents, coder model, benchmarks, and diagnostic pings) is evaluated by the central `BudgetManager` before dispatch.
- **Fail-Safe Continuation**: When a budget is reached, model calls stop immediately and task state is preserved. Explicit continuation is supported via `/budget add <amount>`.
- **Offline Simulation Mode (`FLOWCO_TEST_MODE=1`)**: Deterministic mock dispatcher enabling zero-cost development, verification, and automated tests without API credentials or network usage.
- **Accurate Cost Calculation**: Calculates precise dollar spending from configured provider rates (`price_in_per_m`, `price_out_per_m`, `price_cache_read_per_m`).

### 🔒 Enterprise Sandbox & Workspace Protection
- **Fail-Safe Sandbox Fallback**: If PRoot isolation is unavailable in `auto` mode, execution fails safe to `mode: off` instead of silently dropping into unrestricted execution. Command execution can be explicitly toggled with `/sandbox local`.
- **Universal Command Approval (`confirm_commands`)**: Defaults to `True` for both foreground and background executions. Non-interactive sessions safely reject unapproved shell executions.
- **Symlink & Traversal Boundary Guards**: Strict path containment checks protecting Android personal storage (`DCIM`, `Download`, `Documents`, `/sdcard`) and system root from traversal, symlink escapes, or recursive wipes.
- **Atomic File Operations**: All file writes and modifications stage to temporary files and use `os.replace` with automated snapshot history and `/undo` support.

### 🧠 Advanced Agentic Architecture
- **Capability-Gated Subagents (`spawn_subagent`)**: Spawns isolated specialist subagents with role-based tool capabilities (`researcher`, `reviewer`, `debugger`, `tester`, `coder`). Dangerous tools (`wipe`, `spawn_subagent`, `shutdown`) and recursive subagent spawning are strictly prohibited.
- **Task Graph DAG (`task_graph`)**: Formal execution DAG with cycle detection, dependency management, and automatic state transitions (`PENDING` -> `READY` -> `DONE`).
- **Async Background Task Supervision (`run_background`, `task_status`, `kill_task`)**: Starts long-running compiles, downloads, or test suites asynchronously with concurrency caps and log tracking.
- **Autonomous Verification Gate (`verify`)**: Validates real process exit codes, file existence, and syntax checks before completing tasks.
- **Persistent Learned Skills Library (`learn_skill`, `/skills`)**: Persists lessons, troubleshooting patterns, and compiler workarounds across sessions.

### 🖥️ Native On-Device & Local Models Support (`/local`)
- **Seamless Local Engine Integration**: Connect natively to **Ollama** (`http://127.0.0.1:11434`), **llama.cpp server** (`http://127.0.0.1:8080`), **LM Studio** (`http://127.0.0.1:1234`), and **vLLM / LocalAI** (`http://127.0.0.1:8000`) running on Android Termux or Linux without requiring API keys.
- **One-Click Local Discovery (`/local`)**: Scans all active loopback ports with a 0.5s ping, lists running engines and active models, and provides 1-command switching (`/local use <preset> [model]`).
- **Zero-Key Local Mode**: Automatically detects loopback endpoints and enables full command execution, diagnostics (`/testapi`), and streaming benchmarks (`/stream-test`) without prompting for or requiring dummy API credentials.

### 🖥️ Native Tmux & Antigravity CLI UX
- **Interactive Input Bar & Dropdown Command Menu**: Enhanced readline and optional `prompt_toolkit` engine with a live floating completion dropdown menu when typing `/`.
- **Real-Time Token Streaming & Benchmark (`/stream-test`)**: Live SSE text streaming directly to the terminal with time-to-first-token (TTFT) and throughput telemetry.
- **Dynamic Tmux Status & Pane Titles**: Emits terminal OSC escape sequences updating your tmux pane borders and window titles in real time.
- **Self-Healing Stream Protocol**: Automatically detects and adapts to provider SSE quirks (e.g., auto-healing `stream_options`).

---

## 🚀 Quick Start

### 1. Run as a Global CLI
FlowCo is installed as a global executable:

```bash
# Launch interactive REPL
flowco

# Run autonomous one-shot goal
flowco "download https://github.com/octocat/Hello-World and inspect its structure"
```

### 2. Launch inside Tmux with Live Borders
Use the dynamic launcher script:

```bash
cd /storage/emulated/0/agentsflowW/work
./run_flowco_tmux.sh
```

### 3. Run Offline Self-Tests & Diagnostics
Verify 100% offline functionality (zero network calls, zero token consumption):

```bash
# Run comprehensive 47-test offline test suite
flowco --selftest

# Run environment and storage health checks
flowco --doctor
```

---

## 🛠️ Slash Commands Reference

| Command | Description |
| :--- | :--- |
| `/settings [set\|reset\|show]` | Interactive configuration dashboard for terminal, sandbox, compaction & model |
| `/thinking [toggle\|on\|off]` | Toggle collapse/expand of model thinking process and verbose output (`Ctrl+O`) |
| `/model [id]` | Inspect active model capabilities, probe live architecture, or switch model |
| `/local [use <preset>]` | Scan loopback ports & auto-switch to local models (Ollama, llama.cpp, etc.) |
| `/budget [add <tokens>]` | View token usage, remaining allowance, or extend task budget |
| `/cost` | Display session token ledger and dollar cost from provider rates |
| `/memory` | Inspect active execution plan, touched files, and persistent brain state |
| `/compact` | Compact conversation history into brain memory anchor |
| `/sandbox [mode]` | Inspect or switch sandbox mode (`isolated`, `local`, `proot`, `off`, `auto`) |
| `/stream-test [prompt]` | Benchmark real-time SSE token streaming, latency (TTFT), and throughput |
| `/tasks` | View the live execution task DAG and completion states |
| `/bg [kill <id>\|clear]` | List, inspect, kill, or clear background jobs |
| `/skills` | Inspect the persistent library of learned rules |
| `/undo [file] [idx]` | Rollback file edits using automated snapshot backups |
| `/workspace [path]` | Inspect or switch active workplace folder |
| `/apipro` | Manage multi-provider API profiles, endpoints, models, and rates |
| `/download <url> [dest]` | Download web files into workplace with progress bar |
| `/github <repo> [type]` | Clone repository, fetch release asset, or download file from GitHub |
| `/status` | Full system, model, token budget, and environment diagnostics |
| `/doctor` | Run automated health checks on storage, python, git, and network |
| `/wipe [workspace\|backups\|all]` | Safe guarded storage cleanup with explicit confirmation |

---

## 🔒 License

This software is released under the **FlowCo Community & Educational License**. You are free to run, study, inspect, modify for personal use, and teach using this code. Commercial redistribution, rebranding, and proprietary relicensing are strictly prohibited without author authorization. See [`LICENSE`](LICENSE) for full details.
