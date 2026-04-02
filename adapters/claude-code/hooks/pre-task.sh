#!/usr/bin/env bash
# pre-task.sh — Hook executed before each Ralph Loop task
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

log() { echo "[forja:pre-task] $(date '+%Y-%m-%dT%H:%M:%S') $*"; }

# Ensure we're on a clean state
if ! git -C "${PROJECT_ROOT}" diff --quiet 2>/dev/null; then
    log "⚠ Working tree has uncommitted changes"
fi

# Show current task
TASKS_FILE="${PROJECT_ROOT}/.specify/tasks.md"
if [ -f "${TASKS_FILE}" ]; then
    next_task=$(grep -m1 '^\- \[ \]' "${TASKS_FILE}" 2>/dev/null | sed 's/^- \[ \] //' || true)
    if [ -n "${next_task}" ]; then
        log "Next task: ${next_task}"
    fi
fi

log "Pre-task hook complete"
