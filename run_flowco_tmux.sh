#!/usr/bin/env bash
# run_flowco_tmux.sh - Launch FlowCo v4.5 in a dedicated tmux session
SESSION="flowco"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Attaching to existing FlowCo tmux session '$SESSION'..."
    exec tmux attach-session -t "$SESSION"
else
    echo "Starting new FlowCo v4.5 tmux session '$SESSION'..."
    tmux new-session -d -s "$SESSION" -n "FlowCo"
    # Enable dynamic pane titles and status bar integration
    tmux set-option -t "$SESSION" set-titles on
    tmux set-option -t "$SESSION" set-titles-string "#T"
    tmux set-option -t "$SESSION" pane-border-status top
    tmux set-option -t "$SESSION" pane-border-format " #[bold,fg=cyan]#{pane_title}#[default] "
    tmux send-keys -t "$SESSION:FlowCo" "cd /storage/emulated/0/agentsflowW/work && python3 flowco.py" C-m
    exec tmux attach-session -t "$SESSION"
fi
