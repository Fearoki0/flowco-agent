# 🤖 FlowCo v5.1 — Master AI Handover & Architecture Guide

> **To the Incoming AI Assistant:**
> This document is your complete briefing. It explains the entire architecture, design patterns, file locations, test routines, and operational constraints of **FlowCo v5.1**. Read this file first before touching any code.

---

## 📌 1. Project Overview & Mission

- **Project Name:** FlowCo (Autonomous Agentic Software Engineering Platform)
- **Primary Repository:** [https://github.com/Fearoki0/flowco-agent](https://github.com/Fearoki0/flowco-agent) (Branch: `main`)
- **Package Location in Internal Storage:** `/storage/emulated/0/FlowCo`
- **Global Executable Path:** `/data/data/com.termux/files/usr/bin/flowco`
- **Design Philosophy:** 
  - **Single-file core** (`flowco.py`) that operates on the **Python standard library** with zero mandatory external dependencies.
  - Designed natively for **Android Termux** (unrooted, low-resource mobile hardware, e.g., Realme P4X 8GB RAM) and standard Linux.
  - Full support for **remote OpenAI-compatible APIs** (OpenRouter, DeepSeek, OpenAI, Anthropic) and **zero-key local on-device models** (Ollama, llama.cpp, LM Studio, vLLM).

---

## 📂 2. File Manifest & Structure

All files are located in `/storage/emulated/0/FlowCo/`:

| File / Folder | Purpose & Contents |
| :--- | :--- |
| **`flowco.py`** | The complete 7,200+ line single-file core engine (v5.1). Contains all tools, REPL, API layers, budget supervisor, and terminal UI. |
| **`README.md`** | Comprehensive user documentation, feature highlights, and slash command reference table. |
| **`run_flowco_tmux.sh`** | Dynamic tmux launcher script with nested-session guards and live pane borders. |
| **`requirements.txt`** | Optional dependencies (e.g. `prompt_toolkit`). Zero packages are strictly mandatory. |
| **`LICENSE`** | FlowCo Community & Educational License. |
| **`.gitignore`** | Excludes cache directories, logs, temporary files, and isolated sandboxes. |
| **`tests/`** | Modular offline unit test suite (27 tests across 4 modules). |
| ├── `test_agent.py` | Tests DAG task graph, verification gate, brain memory, sandbox, model probe, and `ask_user`. |
| ├── `test_api.py` | Tests streaming parser, quirk detection, and token usage accounting. |
| ├── `test_budget.py` | Tests the centralized `BudgetManager`, pre-request budget gates, and rate calculation. |
| └── `test_security.py` | Tests path traversal prevention, symlink resolution, and atomic snapshot rollbacks. |
| **`AI_HANDOVER_GUIDE.md`** | *(This file)* The master briefing for incoming AI assistants. |
| **`FlowCo_v5.1_Targeted_Hardening_Prompt.txt`** | The authoritative v5.1 security, budget, and reliability hardening specification. |
| **`fixing.txt`** | The master v5.0 engineering overhaul brief detailing historical bugs and design requirements. |
| **`phase.txt`** | The strict execution protocol: never do blind full rewrites; preserve existing architecture. |

---

## 🗺️ 3. Code Map: The 21 Sections of `flowco.py`

When inspecting or modifying `flowco.py`, use this section index:

```text
Section 1-3   : Imports, Global State, Configuration & Centralized BudgetManager
Section 4-6   : Terminal Color Engine, Path Safety (safe_path) & Snapshot Backups
Section 7-9   : File System Tools (read, write, edit, search, info, archive)
Section 10-11 : Process Execution, Command Guard (confirm_commands), PRoot & .sandbox/
Section 12    : Background Async Process Supervision (run_background, task_status, kill_task)
Section 13    : Web Operations & Network Downloader (web_fetch, web_search, download_file, github_download)
Section 14    : Task Graph DAG (task_graph), Verification Gate (verify), ask_user, Tool Schemas (TOOL_FUNCS)
Section 15    : API Layer, Quirk Learning, Model Capability Probing (probe_model_capabilities), apply_quirks
Section 16    : Prompt Caching (prepare_cached_messages), Claude Cognition (system_prompt), Brain Memory & Compaction
Section 17-18 : Streaming Protocol (chat_stream, chat_plain), Autonomous Agent Turn Loop (run_turn)
Section 19-20 : Slash Commands (/settings, /thinking, /model, /local, /budget, /cost, /status, /doctor)
Section 21    : REPL Main Loop, prompt_toolkit TUI Engine with Ctrl+O Keybinding
```

---

## 🧠 4. Core Cognitive Engine & Features in v5.1

### A. Claude-Style Cognition Architecture
The system prompt in `system_prompt()` is designed around Claude's reasoning methodology:
1. **Deep Intent Analysis**: Analyzes what the user is *really* asking for. Robust against typos, colloquialisms, and voice-to-text slips (e.g. interprets *"quotient"* as *question*, *"cloed"* as *Claude*, *"rcli"* as *our CLI*).
2. **Firm Boundary Discipline on Impossibilities**: If a requested task violates physical, platform, or hardware limits (e.g. executing incompatible binary architectures without emulation, accessing protected Android system dirs without root), FlowCo establishes firm, polite boundaries, explains *why*, and proposes realistic alternatives.
3. **Interactive Inquiry (`ask_user`)**: When encountering major design forks, missing credentials, or genuine ambiguities, FlowCo calls `ask_user(question=..., options=[...])` to prompt the user directly in the terminal instead of guessing blindly.
4. **Direct, Zero-Slop Execution**: No corporate fluff ("Certainly!", "I'd be glad to help!"). Jumps straight to reasoning and actions.

### B. Universal Prompt Caching & Auto-Compaction
- **Prefix Caching**: The static system prompt instructions remain byte-identical across turns. DeepSeek, OpenRouter, and OpenAI automatically cache this prefix, delivering 80–90% prompt token discounts.
- **Anthropic Cache Breakpoints**: `prepare_cached_messages()` injects `"cache_control": {"type": "ephemeral"}` and `anthropic-beta: prompt-caching-2024-07-31` headers for Claude/OpenRouter models.
- **Auto-Compaction at 150k/250k Tokens**: When context reaches `auto_compact_tokens` (default: 150,000), `compact(messages, force=True)` condenses older turns into a **Context Compact Anchor**, updates `.flowco/memory.json` and `.flowco/MEMORY.md`, and drops active tokens back to ~5,000 while maintaining cache prefix validity.

### C. Dedicated Local Sandbox (`.sandbox/`)
- Tool `run_sandbox(command, script_code, script_name)` writes and executes test scripts inside `.sandbox/` with sanitized `$HOME`, clean `$TMPDIR`, and isolated `$PWD` without polluting the workspace or context history.
- `/sandbox isolated` switches all shell commands to run inside the `.sandbox/` directory.

### D. Live Model Capability Probing & Warning Bar
- Probes model families (DeepSeek R1/V3, OpenAI o1/o3-mini, GPT-4o, Claude 3.5, Gemini Thinking, Qwen, Ollama).
- If configured settings conflict with model capabilities (e.g., custom temperature or system prompt roles on `o1`), FlowCo displays a prominent **Warning Bar** in the terminal and auto-omits unsupported parameters in `apply_quirks()` to prevent HTTP 400 Bad Request errors.

### E. Settings Dashboard & Thinking Collapse (`Ctrl+O`)
- `/settings`: Full TUI dashboard to configure terminal, sandbox, compaction thresholds, and model parameters.
- `Ctrl+O` / `/thinking`: Toggles live streaming of reasoning tokens and verbose multi-line tool outputs into compact single-line badges.

---

## 🛠️ 5. How to Run & Verify

All unit tests run **100% offline** with zero token consumption and zero network usage (`FLOWCO_TEST_MODE=1`):

```bash
cd /storage/emulated/0/FlowCo

# 1. Run complete 49-test offline verification suite
python3 flowco.py --selftest

# 2. Run environment & storage diagnostic checks
python3 flowco.py --doctor

# 3. Run individual modular unit tests
python3 -m unittest discover tests
```

Expected result: **49 passed, 0 failed**.

---

## ⚠️ 6. Environmental Constraints (Realme P4X / Android Termux)

1. **Android Storage Semantics**:
   - `/storage/emulated/0/` is an Android SDCardFS / FUSE mount. It **does not support POSIX executable permissions (`chmod +x`) or symlinks directly**.
   - If a binary must have executable permissions, place it in Termux user storage (`/data/data/com.termux/files/usr/bin/` or `$HOME`).
2. **Zero Mandatory Dependencies**:
   - Do NOT introduce mandatory third-party libraries (e.g. `requests`, `rich`, `langchain`). FlowCo must run cleanly on `python3 flowco.py` with the standard library alone. `prompt_toolkit` is purely optional and lazily imported.
3. **Never Do a Blind Rewrite**:
   - As stated in `phase.txt`, make targeted, surgical edits using diffs. Preserve the verified test gates and existing features.

---

## 🚀 7. Next Potential Enhancements (Roadmap)

If you are asked to continue developing FlowCo, consider:
1. **Persona Switcher (`/settings system_prompt <persona>`)**: Load specialized prompt templates from `.flowco/personas/*.md` (e.g. *Security Auditor*, *Token Economist*, *Speed-Run Coder*).
2. **Multi-Model Parallel Swarms**: Allowing subagents spawned via `spawn_subagent` to use a different, lighter model (e.g. `llama3.2` or `qwen2.5-coder`) while the parent maintains frontier reasoning (`deepseek-r1` or `o3-mini`).
3. **Structured Export**: Expanding `/export` to emit full JSONL session replay logs compatible with external eval harnesses.

---
*Generated by Antigravity AI — FlowCo Engineering Handover Complete.*
