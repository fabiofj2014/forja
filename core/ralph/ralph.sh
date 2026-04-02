#!/usr/bin/env bash
# ralph.sh — Ralph Wiggum Loop entry point for Forja (Build phase)
# Usage: AGENT_CLI=claude ./core/ralph/ralph.sh
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
AGENT_CLI="${AGENT_CLI:-claude}"
MAX_ITERATIONS="${MAX_ITERATIONS:-50}"
STALL_LIMIT="${STALL_LIMIT:-3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TASKS_FILE="${PROJECT_ROOT}/.specify/tasks.md"
LOG_DIR="${PROJECT_ROOT}/logs/build"
STATE_FILE="${PROJECT_ROOT}/state/ralph_state.json"

# ── Helpers ────────────────────────────────────────────────────────────────────
log() { echo "[ralph] $(date '+%Y-%m-%dT%H:%M:%S') $*"; }
die() { log "ERROR: $*" >&2; exit 1; }

count_tasks() {
    local status="$1"
    case "$status" in
        pending)  grep -c '^\- \[ \]' "${TASKS_FILE}" 2>/dev/null || echo 0 ;;
        done)     grep -c '^\- \[x\]' "${TASKS_FILE}" 2>/dev/null || echo 0 ;;
        blocked)  grep -c '^\- \[BLOCKED\]' "${TASKS_FILE}" 2>/dev/null || echo 0 ;;
    esac
}

next_task() {
    grep -m1 '^\- \[ \]' "${TASKS_FILE}" 2>/dev/null | sed 's/^- \[ \] //' || true
}

all_done() {
    [ "$(count_tasks pending)" -eq 0 ]
}

# ── Banner ─────────────────────────────────────────────────────────────────────
print_banner() {
    local pending done blocked
    pending=$(count_tasks pending)
    done=$(count_tasks done)
    blocked=$(count_tasks blocked)
    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║           🔨 FORJA — Ralph Loop              ║"
    echo "╠══════════════════════════════════════════════╣"
    printf  "║  Agent:    %-34s║\n" "${AGENT_CLI}"
    printf  "║  Tasks:    %-3s done  %-3s pending  %-3s blocked ║\n" "$done" "$pending" "$blocked"
    printf  "║  Max iters: %-33s║\n" "${MAX_ITERATIONS}"
    printf  "║  Stall limit: %-31s║\n" "${STALL_LIMIT}"
    echo "╚══════════════════════════════════════════════╝"
    echo ""
}

# ── Validation ─────────────────────────────────────────────────────────────────
[ -f "${TASKS_FILE}" ] || die "tasks.md not found at ${TASKS_FILE}"
command -v "${AGENT_CLI}" >/dev/null 2>&1 || die "Agent CLI '${AGENT_CLI}' not found in PATH"
mkdir -p "${LOG_DIR}" "${PROJECT_ROOT}/state"

# ── Main Loop ──────────────────────────────────────────────────────────────────
print_banner

if all_done; then
    log "✅ ALL_TASKS_DONE — nothing to do"
    exit 0
fi

consecutive_failures=0
iteration=0

while [ $iteration -lt "${MAX_ITERATIONS}" ]; do
    iteration=$((iteration + 1))
    task=$(next_task)

    if [ -z "$task" ]; then
        log "✅ ALL_TASKS_DONE after ${iteration} iterations"
        exit 0
    fi

    log "▶ Iteration ${iteration}/${MAX_ITERATIONS}: ${task}"

    # Build prompt file for this iteration
    prompt_file="${LOG_DIR}/prompt_$(printf '%04d' ${iteration}).md"
    python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}')
from core.ralph.task_parser import next_pending
from core.ralph.prompt_builder import build_prompt
from pathlib import Path

tasks_file = Path('${TASKS_FILE}')
constitution_file = Path('${PROJECT_ROOT}/.specify/memory/constitution.md')
prompt_template = Path('${PROJECT_ROOT}/prompts/build/Prompt.md')

task = next_pending(tasks_file)
if task and constitution_file.exists() and prompt_template.exists():
    prompt = build_prompt(task, constitution_file, prompt_template)
elif task:
    prompt = f'Implement this task: {task.text}\nWhen done, run tests and commit.'
else:
    print('', end='')
    sys.exit(0)

Path('${prompt_file}').write_text(prompt, encoding='utf-8')
" 2>/dev/null || true

    # Invoke agent
    iter_log="${LOG_DIR}/iter_$(printf '%04d' ${iteration}).log"
    agent_exit=0

    if [ -f "${prompt_file}" ]; then
        "${AGENT_CLI}" --print "$(cat "${prompt_file}")" \
            --cwd "${PROJECT_ROOT}" \
            > "${iter_log}" 2>&1 || agent_exit=$?
    else
        log "⚠ No prompt file, running agent with inline task"
        "${AGENT_CLI}" --print "Implement: ${task}. Run tests with: uv run pytest tests/ -v. If tests pass, mark [x] in .specify/tasks.md and commit." \
            --cwd "${PROJECT_ROOT}" \
            > "${iter_log}" 2>&1 || agent_exit=$?
    fi

    # Check if progress was made (new [x] since last iteration)
    new_done=$(count_tasks done)
    if [ "${new_done}" -gt 0 ] && git -C "${PROJECT_ROOT}" diff --quiet HEAD~1 HEAD -- .specify/tasks.md 2>/dev/null | grep -q '\[x\]' 2>/dev/null || \
       git -C "${PROJECT_ROOT}" log --oneline -1 2>/dev/null | grep -q '\[forja\]'; then
        log "✓ Progress made (agent_exit=${agent_exit})"
        consecutive_failures=0
    else
        consecutive_failures=$((consecutive_failures + 1))
        log "✗ No progress detected (${consecutive_failures}/${STALL_LIMIT})"

        if [ "${consecutive_failures}" -ge "${STALL_LIMIT}" ]; then
            log "🛑 STALLED after ${iteration} iterations (${STALL_LIMIT} consecutive failures)"
            log "   Marking current task as BLOCKED"
            python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}')
from core.ralph.task_parser import next_pending, mark_blocked
from pathlib import Path
task = next_pending(Path('${TASKS_FILE}'))
if task:
    mark_blocked(Path('${TASKS_FILE}'), task, reason='stall detected by ralph.sh')
" 2>/dev/null || true
            exit 2
        fi
    fi

    if all_done; then
        log "✅ ALL_TASKS_DONE after ${iteration} iterations"
        exit 0
    fi
done

log "⏱ MAX_ITERATIONS (${MAX_ITERATIONS}) reached"
exit 1
