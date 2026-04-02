#!/usr/bin/env bash
# post-task.sh — Hook executed after each Ralph Loop task
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

log() { echo "[forja:post-task] $(date '+%Y-%m-%dT%H:%M:%S') $*"; }

# Count progress
TASKS_FILE="${PROJECT_ROOT}/.specify/tasks.md"
if [ -f "${TASKS_FILE}" ]; then
    done=$(grep -c '^\- \[x\]' "${TASKS_FILE}" 2>/dev/null || echo 0)
    pending=$(grep -c '^\- \[ \]' "${TASKS_FILE}" 2>/dev/null || echo 0)
    log "Progress: ${done} done, ${pending} pending"
fi

# Run tests to verify
if command -v uv >/dev/null 2>&1; then
    log "Running tests..."
    if uv run pytest tests/ -q --tb=no 2>/dev/null; then
        log "✓ Tests pass"
    else
        log "✗ Tests FAILED — check logs"
    fi
fi

log "Post-task hook complete"
