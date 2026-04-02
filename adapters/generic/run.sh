#!/usr/bin/env bash
# run.sh — Generic wrapper to run Forja with any agent CLI
# Usage: AGENT_CLI=my-agent ./adapters/generic/run.sh [build|optimize]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# ── Defaults ───────────────────────────────────────────────────────────────────
AGENT_CLI="${AGENT_CLI:-claude}"
PHASE="${1:-build}"

# ── Validate ───────────────────────────────────────────────────────────────────
command -v "${AGENT_CLI}" >/dev/null 2>&1 || {
    echo "[forja] ERROR: Agent '${AGENT_CLI}' not found in PATH"
    echo "[forja] Set AGENT_CLI to your agent binary (e.g., claude, opencode, codex, amp, aider)"
    exit 1
}

case "${PHASE}" in
    build)
        echo "[forja] Starting Ralph Loop (agent=${AGENT_CLI})"
        AGENT_CLI="${AGENT_CLI}" exec "${PROJECT_ROOT}/core/ralph/ralph.sh"
        ;;
    optimize)
        echo "[forja] Starting Autoresearch Loop (agent=${AGENT_CLI})"
        AGENT_CLI="${AGENT_CLI}" exec "${PROJECT_ROOT}/core/autoresearch/autoresearch.sh"
        ;;
    status)
        "${PROJECT_ROOT}/.venv/bin/forja" build status 2>/dev/null || \
            python3 -m core.cli build status
        ;;
    *)
        echo "Usage: AGENT_CLI=<agent> $0 [build|optimize|status]"
        echo "  build    — run Ralph Loop (default)"
        echo "  optimize — run Autoresearch Loop"
        echo "  status   — show current build status"
        exit 1
        ;;
esac
