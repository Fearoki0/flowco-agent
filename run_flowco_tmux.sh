#!/usr/bin/env bash
# run_flowco_tmux.sh - FlowCo v5.0 Launcher for Termux & Linux
# Dynamically resolves script directory, verifies dependencies, and manages tmux session.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLOWCO_PY="$SCRIPT_DIR/flowco.py"
SESSION="flowco"

if [[ ! -f "$FLOWCO_PY" ]]; then
    # Check fallback path in user PATH
    if command -v flowco >/dev/null 2>&1; then
        FLOWCO_BIN="$(command -v flowco)"
        FLOWCO_PY="$FLOWCO_BIN"
    else
        echo "Error: flowco.py not found in '$SCRIPT_DIR' or PATH." >&2
        exit 1
    fi
fi

# If already inside tmux, launch directly to prevent nested session conflicts
if [[ -n "${TMUX:-}" ]]; then
    exec python3 "$FLOWCO_PY" "$@"
fi

# Fallback when tmux is not installed
if ! command -v tmux >/dev/null 2>&1; then
    echo "Notice: tmux is not installed. Launching FlowCo directly..."
    exec python3 "$FLOWCO_PY" "$@"
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Attaching to existing FlowCo session '$SESSION'..."
    exec tmux attach-session -t "$SESSION"
else
    echo "Starting FlowCo v5.0 tmux session '$SESSION'..."
    tmux new-session -d -s "$SESSION" -n "FlowCo"
    # Dynamic pane titles and visual borders
    tmux set-option -t "$SESSION" set-titles on 2>/dev/null || true
    tmux set-option -t "$SESSION" set-titles-string "#T" 2>/dev/null || true
    tmux set-option -t "$SESSION" pane-border-status top 2>/dev/null || true
    tmux set-option -t "$SESSION" pane-border-format " #[bold,fg=cyan]#{pane_title}#[default] " 2>/dev/null || true

    ARGS_STR=""
    if [[ $# -gt 0 ]]; then
        printf -v ARGS_STR ' %q' "$@"
    fi
    tmux send-keys -t "$SESSION:FlowCo" "cd \"$SCRIPT_DIR\" && python3 \"$FLOWCO_PY\"$ARGS_STR" C-m
    exec tmux attach-session -t "$SESSION"
fi
