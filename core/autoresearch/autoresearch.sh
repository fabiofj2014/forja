#!/usr/bin/env bash
# autoresearch.sh — Autoresearch Loop entry point for Forja (Optimize phase)
# Usage: AGENT_CLI=claude METRIC_KEY=val_bpb ./core/autoresearch/autoresearch.sh
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
AGENT_CLI="${AGENT_CLI:-claude}"
MAX_EXPERIMENTS="${MAX_EXPERIMENTS:-100}"
STALL_LIMIT="${STALL_LIMIT:-3}"
EXPERIMENT_TIMEOUT="${EXPERIMENT_TIMEOUT:-300}"
METRIC_KEY="${METRIC_KEY:-val_bpb}"
METRIC_DIRECTION="${METRIC_DIRECTION:-lower}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROGRAM_FILE="${PROJECT_ROOT}/prompts/optimize/program.md"
METRICS_FILE="${PROJECT_ROOT}/.autoresearch/metrics.json"
STATE_DIR="${PROJECT_ROOT}/state"
LOG_DIR="${PROJECT_ROOT}/logs/optimize"

# ── Helpers ────────────────────────────────────────────────────────────────────
log() { echo "[autoresearch] $(date '+%Y-%m-%dT%H:%M:%S') $*"; }
die() { log "ERROR: $*" >&2; exit 1; }

read_metric() {
    python3 -c "
import json, sys
try:
    data = json.load(open('${METRICS_FILE}'))
    print(data.get('${METRIC_KEY}', 'N/A'))
except Exception as e:
    print('N/A')
" 2>/dev/null || echo "N/A"
}

count_experiments() {
    python3 -c "
import json, sys, pathlib
f = pathlib.Path('${STATE_DIR}/experiments.json')
if f.exists():
    data = json.loads(f.read_text())
    print(len(data))
else:
    print(0)
" 2>/dev/null || echo 0
}

consecutive_no_improvement() {
    python3 -c "
import json, pathlib
f = pathlib.Path('${STATE_DIR}/experiments.json')
if not f.exists():
    print(0)
    exit()
data = json.loads(f.read_text())
count = 0
for exp in reversed(data):
    if not exp.get('improved', False):
        count += 1
    else:
        break
print(count)
" 2>/dev/null || echo 0
}

# ── Banner ─────────────────────────────────────────────────────────────────────
print_banner() {
    local current_metric
    current_metric=$(read_metric)
    local experiments_done
    experiments_done=$(count_experiments)

    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║       🔬 FORJA — Autoresearch Loop           ║"
    echo "╠══════════════════════════════════════════════╣"
    printf  "║  Agent:     %-33s║\n" "${AGENT_CLI}"
    printf  "║  Metric:    %-33s║\n" "${METRIC_KEY} (${METRIC_DIRECTION})"
    printf  "║  Current:   %-33s║\n" "${current_metric}"
    printf  "║  Done:      %-3s / %-3s experiments           ║\n" "$experiments_done" "${MAX_EXPERIMENTS}"
    printf  "║  Stall:     %-33s║\n" "abort after ${STALL_LIMIT} no-improvement"
    echo "╚══════════════════════════════════════════════╝"
    echo ""
}

# ── Validation ─────────────────────────────────────────────────────────────────
command -v "${AGENT_CLI}" >/dev/null 2>&1 || die "Agent CLI '${AGENT_CLI}' not found in PATH"
[ -f "${PROGRAM_FILE}" ] || log "⚠ program.md not found at ${PROGRAM_FILE} — will use inline prompt"
mkdir -p "${LOG_DIR}" "${STATE_DIR}"

# ── Capture initial baseline ────────────────────────────────────────────────────
if [ -f "${METRICS_FILE}" ] && [ ! -f "${STATE_DIR}/baseline.json" ]; then
    log "Capturing initial baseline..."
    python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}')
from core.autoresearch.baseline_manager import BaselineManager
from core.metrics import read_metric
from pathlib import Path
bm = BaselineManager(Path('${STATE_DIR}/baseline.json'))
val = read_metric(Path('${METRICS_FILE}'), '${METRIC_KEY}')
bm.capture_baseline(val, 'initial', '${METRIC_KEY}', '${METRIC_DIRECTION}')
print(f'Baseline captured: {val}')
" 2>/dev/null || log "⚠ Could not capture baseline"
fi

# ── Main Loop ──────────────────────────────────────────────────────────────────
print_banner

experiment=0

while [ $experiment -lt "${MAX_EXPERIMENTS}" ]; do
    experiment=$((experiment + 1))
    current=$(read_metric)
    log "▶ Experiment ${experiment}/${MAX_EXPERIMENTS} — ${METRIC_KEY}=${current}"

    # Build prompt
    if [ -f "${PROGRAM_FILE}" ]; then
        prompt=$(cat "${PROGRAM_FILE}")
    else
        prompt="Optimize the code to improve ${METRIC_KEY} (direction: ${METRIC_DIRECTION}). Current value: ${current}. Make a targeted change, measure the result, and report whether it improved."
    fi

    # Run agent
    exp_log="${LOG_DIR}/exp_$(printf '%04d' ${experiment}).log"
    agent_exit=0
    timeout "${EXPERIMENT_TIMEOUT}" "${AGENT_CLI}" --print "${prompt}" \
        --cwd "${PROJECT_ROOT}" \
        > "${exp_log}" 2>&1 || agent_exit=$?

    # Evaluate result
    python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}')
from core.autoresearch.experiment_tracker import ExperimentTracker
from core.autoresearch.baseline_manager import BaselineManager
from core.metrics import read_metric, is_improvement
from core.git_manager import has_changes, commit
from pathlib import Path
import subprocess

project_root = Path('${PROJECT_ROOT}')
tracker = ExperimentTracker(Path('${STATE_DIR}/experiments.json'))
bm = BaselineManager(Path('${STATE_DIR}/baseline.json'))
baseline = bm.load_baseline()

if baseline is None:
    print('No baseline — skipping evaluation')
    sys.exit(0)

if not has_changes(project_root):
    tracker.log_experiment('(no changes)', baseline.value, baseline.value, '${METRIC_DIRECTION}', False)
    print('No changes made')
    sys.exit(0)

try:
    new_val = read_metric(Path('${METRICS_FILE}'), '${METRIC_KEY}')
except Exception as e:
    subprocess.run(['git', 'checkout', '--', '.'], cwd=project_root, capture_output=True)
    tracker.log_experiment('(metric read failed)', baseline.value, baseline.value, '${METRIC_DIRECTION}', False)
    print(f'Metric read failed: {e} — reverted')
    sys.exit(0)

improved = is_improvement(baseline.value, new_val, '${METRIC_DIRECTION}')
sha = None
if improved:
    sha = commit(project_root, f'[autoresearch] exp${experiment}: ${METRIC_KEY} {baseline.value:.4f}→{new_val:.4f}')
    bm.update_baseline(new_val, sha or '')
    print(f'✓ Improved: {baseline.value:.4f} → {new_val:.4f}')
else:
    subprocess.run(['git', 'checkout', '--', '.'], cwd=project_root, capture_output=True)
    subprocess.run(['git', 'clean', '-fd'], cwd=project_root, capture_output=True)
    print(f'✗ No improvement: {baseline.value:.4f} → {new_val:.4f} (reverted)')

tracker.log_experiment('agent output', baseline.value, new_val, '${METRIC_DIRECTION}', improved, sha)
" 2>/dev/null || log "⚠ Evaluation failed"

    # Stall check
    no_improve=$(consecutive_no_improvement)
    if [ "${no_improve}" -ge "${STALL_LIMIT}" ]; then
        log "🛑 STALLED — ${no_improve} consecutive experiments without improvement"
        exit 2
    fi
done

log "⏱ MAX_EXPERIMENTS (${MAX_EXPERIMENTS}) reached"
exit 1
