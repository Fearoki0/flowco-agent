# ⚡ FlowCo v4.5 — Autonomous Agentic Engineering Platform

> Single-file, zero-dependency autonomous AI software engineer and execution platform built natively for **Android Termux** and **Linux**.

FlowCo is designed to turn your phone into a full-scale AI development station. It runs entirely on the **Python standard library** with zero `pip install` requirements, operating seamlessly inside **tmux** with live pane titles, streaming download engines, background task supervision, subagent swarms, and self-verifying test gates.

---

## ✨ Key Features

### 🌐 Native Internet & GitHub Downloader
- **Streaming Web Downloader (`download_file`)**: Pure stdlib chunked HTTP/HTTPS streaming with redirect resolution, anti-403 header emulation, and automatic archive extraction (`.zip`, `.tar.gz`, `.tar.bz2`).
- **Deep GitHub Integration (`github_download`)**: One-command repository shallow cloning (`--depth 1`), zero-dependency zipball fallback, raw code file streaming, and release binary / APK asset downloads.
- **Android Internal Storage Aware**: Systematically organizes downloaded files into your workplace directory (`/storage/emulated/0/AgentWork` or custom workspace) and reports direct paths for file managers.

### 🧠 Advanced Agentic Architecture
- **Subagent Swarms (`spawn_subagent`)**: Spawns isolated specialist subagents (e.g. `Researcher`, `Debugger`) that explore in clean sandboxes and return synthesized reports without consuming the parent agent's context window.
- **Structured Task Graph DAG (`task_graph`)**: Formal execution DAG with dependencies, state tracking (`PENDING`, `IN_PROGRESS`, `DONE`, `FAILED`), and visual progress ASCII boards (`/tasks`).
- **Async Background Task Supervision (`run_background`, `task_status`, `kill_task`)**: Starts heavy compiles, downloads, or preview servers in the background asynchronously without freezing the REPL.
- **Autonomous Verification Gate (`verify`)**: Executes tests and validates file invariants before declaring completion, stopping hallucinations before they reach the user.
- **Persistent Learned Skills Library (`learn_skill`, `/skills`)**: Persists lessons, troubleshooting patterns, and compiler workarounds across sessions, automatically injecting relevant rules when similar tasks arise.

### 🖥️ Native Tmux & Antigravity CLI UX
- **Interactive Input Bar & Dropdown Command Menu**: Rich `prompt_toolkit` engine with a live floating completion dropdown menu when typing `/`, displaying command descriptions and selectable with Up/Down arrow keys.
- **Real-Time Token Streaming & Benchmark (`/stream-test`)**: Live SSE text streaming directly to the terminal, complete with time-to-first-token (TTFT) and throughput telemetry.
- **Bottom Status Toolbar**: Always visible status displaying active Model, Workplace directory, Session tokens/budget, active background jobs, and keyboard shortcuts.
- **Dynamic Tmux Status & Pane Titles**: Emits terminal OSC escape sequences updating your tmux pane borders and window titles in real time (`FlowCo: [Downloading]`, `FlowCo: [Thinking]`, `FlowCo: [Ready]`).
- **Terminal Resize (`SIGWINCH`)**: Handles tmux horizontal/vertical pane splits without clipping or breaking layout.
- **Graceful Interrupts (`Ctrl+C`)**: Cancels running subprocesses or downloads without crashing the agent or closing the terminal session.
- **Persistent History & Auto-Suggestions**: Saves command history in `~/.flowco/history` with fish-style ghost auto-suggestions.

---

## 🚀 Quick Start

### 1. Run Anywhere as a Global CLI
FlowCo is installed as a global executable in your Termux environment:

```bash
# Launch interactive REPL
flowco

# Run autonomous one-shot goal
flowco "download https://github.com/octocat/Hello-World and inspect its structure"
```

### 2. Launch inside Tmux with Live Borders
Use the included launcher script:

```bash
cd work
./run_flowco_tmux.sh
```

---

## 🛠️ Slash Commands Reference

| Command | Description |
| :--- | :--- |
| `/stream-test [prompt]` | Benchmark real-time SSE token streaming, latency (TTFT), and throughput |
| `/download <url> [dest]` | Download any web file into workplace with progress bar |
| `/github <repo> [type]` | Clone repository, fetch release asset, or download file from GitHub |
| `/workspace [path]` | Inspect or switch active workplace folder on internal storage |
| `/tasks` | View the live execution task DAG and completion states |
| `/bg` | List and monitor running background jobs |
| `/skills` | Inspect the persistent library of learned rules |
| `/undo [file] [idx]` | Rollback any file edit using automatic snapshot backups |
| `/clear` | Clear terminal console screen and redraw branding banner |
| `/status` | Full system, model, token budget, and environment diagnostics |
| `/doctor` | Run automated health checks on storage, python, git, and network |

---

## 🔒 License

This software is released under the **FlowCo Community & Educational License**. You are free to run, study, inspect, modify for personal use, and teach using this code. Commercial redistribution, rebranding, and proprietary relicensing are strictly prohibited without author authorization. See [`LICENSE`](LICENSE) for full details.
