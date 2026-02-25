#!/usr/bin/env bash
# Ralph Wiggum Stop Hook — checks if autonomous tasks remain
# Exit 1 = continue (tasks remain), Exit 0 = stop (done or max iterations)

COUNTER_FILE="/tmp/ralph-wiggum-counter"
MAX_ITERATIONS="${RALPH_WIGGUM_MAX_ITERATIONS:-10}"

# Get project dir from Claude Code env or default
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TASKS_DIR="${PROJECT_DIR}/AI_Employee_Vault/Tasks"

# Read and increment counter
if [ -f "$COUNTER_FILE" ]; then
    COUNTER=$(cat "$COUNTER_FILE")
else
    COUNTER=0
fi
COUNTER=$((COUNTER + 1))
echo "$COUNTER" > "$COUNTER_FILE"

# Check max iterations
if [ "$COUNTER" -ge "$MAX_ITERATIONS" ]; then
    echo "Ralph Wiggum: Max iterations ($MAX_ITERATIONS) reached. Stopping."
    rm -f "$COUNTER_FILE"
    exit 0
fi

# Check if task files exist in Tasks/
if [ -d "$TASKS_DIR" ]; then
    TASK_COUNT=$(find "$TASKS_DIR" -name "TASK_*.md" -type f 2>/dev/null | wc -l)
    if [ "$TASK_COUNT" -gt 0 ]; then
        echo "Ralph Wiggum: $TASK_COUNT task(s) remaining (iteration $COUNTER/$MAX_ITERATIONS)"
        find "$TASKS_DIR" -name "TASK_*.md" -type f -exec basename {} \;
        exit 1  # Continue
    fi
fi

# No tasks remaining
echo "Ralph Wiggum: No tasks remaining. Stopping."
rm -f "$COUNTER_FILE"
exit 0
