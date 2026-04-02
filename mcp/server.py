"""MCP server for Forja — exposes build and optimize tools via JSON-RPC over HTTP."""

from __future__ import annotations

import threading
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.config import (
    AGENT_CLI,
    BUILD_LOGS_DIR,
    BUILD_PROMPT_FILE,
    CONSTITUTION_FILE,
    EXPERIMENT_TIMEOUT,
    MAX_EXPERIMENTS,
    MAX_ITERATIONS,
    METRIC_DIRECTION,
    METRIC_KEY,
    OPTIMIZE_LOGS_DIR,
    OPTIMIZE_PROMPT_FILE,
    PROJECT_ROOT,
    STALL_LIMIT,
    STATE_DIR,
    TASKS_FILE,
)

app = FastAPI(title="Forja MCP Server", version="0.1.0")

SERVER_INFO = {"name": "forja", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"

# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "name": "build_start",
        "description": "Start the Ralph Loop (build phase). Runs asynchronously in background.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Agent CLI to use (claude, codex, opencode…)"},
                "max_iterations": {"type": "integer", "description": "Maximum loop iterations"},
                "stall_limit": {"type": "integer", "description": "Iterations without progress before aborting"},
            },
        },
    },
    {
        "name": "build_status",
        "description": "Return current build status: done/pending/blocked counts from tasks.md.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "build_next",
        "description": "Return the next pending task from tasks.md.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "optimize_start",
        "description": "Start the Autoresearch Loop (optimize phase). Runs asynchronously in background.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Agent CLI to use"},
                "metric_key": {"type": "string", "description": "Metric name to optimize"},
                "direction": {
                    "type": "string",
                    "enum": ["lower", "higher"],
                    "description": "Optimization direction",
                },
                "max_experiments": {"type": "integer", "description": "Maximum experiments"},
                "stall_limit": {
                    "type": "integer",
                    "description": "Consecutive non-improving experiments before abort",
                },
                "timeout": {"type": "integer", "description": "Per-experiment timeout in seconds"},
                "metrics_file": {"type": "string", "description": "Path to metrics JSON file"},
            },
        },
    },
    {
        "name": "optimize_status",
        "description": "Return current optimization status: experiment count, baseline, best result.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "optimize_history",
        "description": "Return the experiment history log.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "last": {
                    "type": "integer",
                    "description": "Number of most recent experiments to return (0 = all)",
                },
            },
        },
    },
    {
        "name": "optimize_baseline",
        "description": "Return the current baseline metric value, or capture a new one.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "capture": {
                    "type": "boolean",
                    "description": "If true, capture current metrics.json as new baseline",
                },
                "metrics_file": {
                    "type": "string",
                    "description": "Path to metrics JSON file (used when capture=true)",
                },
            },
        },
    },
]

# ── Tool handlers ─────────────────────────────────────────────────────────────


def _handle_build_start(args: dict[str, Any]) -> str:
    """Start the Ralph Loop in a background thread."""
    from core.ralph.loop import run_loop

    agent = args.get("agent", AGENT_CLI)
    max_iterations = int(args.get("max_iterations", MAX_ITERATIONS))
    stall_limit = int(args.get("stall_limit", STALL_LIMIT))

    def _run() -> None:
        run_loop(
            tasks_file=TASKS_FILE,
            constitution_file=CONSTITUTION_FILE,
            prompt_file=BUILD_PROMPT_FILE,
            agent_cli=agent,
            log_dir=BUILD_LOGS_DIR,
            project_root=PROJECT_ROOT,
            max_iterations=max_iterations,
            stall_limit=stall_limit,
        )

    thread = threading.Thread(target=_run, daemon=True, name="forja-ralph-loop")
    thread.start()
    return f"[forja] Ralph Loop started (agent={agent}, max_iterations={max_iterations})"


def _handle_build_status(_args: dict[str, Any]) -> str:
    """Return build status from tasks.md."""
    from core.ralph.task_parser import parse_tasks

    if not TASKS_FILE.exists():
        return f"[forja] tasks.md not found at {TASKS_FILE}"

    tasks = parse_tasks(TASKS_FILE)
    done = sum(1 for t in tasks if t.status == "done")
    pending = sum(1 for t in tasks if t.status == "pending")
    blocked = sum(1 for t in tasks if t.status == "blocked")
    total = len(tasks)
    return f"[forja] Build status: {done}/{total} done, {pending} pending, {blocked} blocked"


def _handle_build_next(_args: dict[str, Any]) -> str:
    """Return the next pending task."""
    from core.ralph.task_parser import next_pending

    if not TASKS_FILE.exists():
        return f"[forja] tasks.md not found at {TASKS_FILE}"

    task = next_pending(TASKS_FILE)
    if task is None:
        return "[forja] No pending tasks — all done!"
    return f"[forja] Next task: {task.text}"


def _handle_optimize_start(args: dict[str, Any]) -> str:
    """Start the Autoresearch Loop in a background thread."""
    from core.autoresearch.loop import run_optimize_loop

    agent = args.get("agent", AGENT_CLI)
    metric_key = args.get("metric_key", METRIC_KEY)
    direction = args.get("direction", METRIC_DIRECTION)
    max_experiments = int(args.get("max_experiments", MAX_EXPERIMENTS))
    stall_limit = int(args.get("stall_limit", STALL_LIMIT))
    timeout = int(args.get("timeout", EXPERIMENT_TIMEOUT))
    metrics_file = PROJECT_ROOT / args.get("metrics_file", ".autoresearch/metrics.json")

    def _run() -> None:
        run_optimize_loop(
            metrics_file=metrics_file,
            project_root=PROJECT_ROOT,
            prompt_file=OPTIMIZE_PROMPT_FILE,
            agent_cli=agent,
            log_dir=OPTIMIZE_LOGS_DIR,
            state_dir=STATE_DIR,
            metric_key=metric_key,
            direction=direction,
            max_experiments=max_experiments,
            stall_limit=stall_limit,
            timeout=timeout,
        )

    thread = threading.Thread(target=_run, daemon=True, name="forja-autoresearch-loop")
    thread.start()
    return f"[forja] Autoresearch Loop started (agent={agent}, metric={metric_key}, direction={direction})"


def _handle_optimize_status(_args: dict[str, Any]) -> str:
    """Return optimization status."""
    from core.autoresearch.baseline_manager import BaselineManager
    from core.autoresearch.experiment_tracker import ExperimentTracker

    tracker = ExperimentTracker(STATE_DIR / "experiments.json")
    bm = BaselineManager(STATE_DIR / "baseline.json")

    history = tracker.get_history()
    baseline = bm.load_baseline()
    best = tracker.best_result()

    total = len(history)
    improved = sum(1 for e in history if e.improved)
    lines = [f"[forja] Optimize status: {total} experiments, {improved} improvements"]
    if baseline:
        lines.append(f"Baseline: {baseline.metric_key}={baseline.value:.4f} ({baseline.direction})")
    if best:
        mk = best.metric_key if hasattr(best, "metric_key") else METRIC_KEY
        lines.append(f"Best result: {mk}={best.metric_after:.4f}")
    return "\n".join(lines)


def _handle_optimize_history(args: dict[str, Any]) -> str:
    """Return experiment history."""
    from core.autoresearch.experiment_tracker import ExperimentTracker

    tracker = ExperimentTracker(STATE_DIR / "experiments.json")
    history = tracker.get_history()

    if not history:
        return "[forja] No experiments recorded yet"

    n = int(args.get("last", 0)) or len(history)
    rows = []
    for exp in history[-n:]:
        status = "✓" if exp.improved else "✗"
        rows.append(
            f"  [{exp.id:03d}] {status} {exp.metric_before:.4f}→{exp.metric_after:.4f}"
            f" | {exp.hypothesis[:60]}"
        )
    return "\n".join(rows)


def _handle_optimize_baseline(args: dict[str, Any]) -> str:
    """Return or capture baseline."""
    from core.autoresearch.baseline_manager import BaselineManager
    from core.metrics import read_metric

    bm = BaselineManager(STATE_DIR / "baseline.json")

    if args.get("capture"):
        metrics_file = PROJECT_ROOT / args.get("metrics_file", ".autoresearch/metrics.json")
        try:
            value = read_metric(metrics_file, METRIC_KEY)
            baseline = bm.capture_baseline(value, "manual", METRIC_KEY, METRIC_DIRECTION)
            return f"[forja] Baseline captured: {METRIC_KEY}={baseline.value:.4f}"
        except Exception as exc:
            return f"[forja] Error capturing baseline: {exc}"

    baseline = bm.load_baseline()
    if baseline is None:
        return "[forja] No baseline recorded yet"
    return (
        f"[forja] Baseline: {baseline.metric_key}={baseline.value:.4f}"
        f" ({baseline.direction}) @ {baseline.commit_sha}"
    )


_TOOL_HANDLERS = {
    "build_start": _handle_build_start,
    "build_status": _handle_build_status,
    "build_next": _handle_build_next,
    "optimize_start": _handle_optimize_start,
    "optimize_status": _handle_optimize_status,
    "optimize_history": _handle_optimize_history,
    "optimize_baseline": _handle_optimize_baseline,
}

# ── JSON-RPC helpers ──────────────────────────────────────────────────────────


def _ok(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


# ── MCP endpoint ──────────────────────────────────────────────────────────────


@app.post("/")
async def mcp_endpoint(request: dict[str, Any]) -> JSONResponse:
    """Handle MCP JSON-RPC requests."""
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        return JSONResponse(
            _ok(
                req_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "serverInfo": SERVER_INFO,
                    "capabilities": {"tools": {}},
                },
            )
        )

    if method == "tools/list":
        return JSONResponse(_ok(req_id, {"tools": TOOLS}))

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        handler = _TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return JSONResponse(_err(req_id, -32601, f"Unknown tool: {tool_name}"))
        try:
            text = handler(tool_args)
            return JSONResponse(_ok(req_id, {"content": [{"type": "text", "text": text}]}))
        except Exception as exc:
            return JSONResponse(_err(req_id, -32000, str(exc)))

    if method == "notifications/initialized":
        return JSONResponse(_ok(req_id, {}))

    return JSONResponse(_err(req_id, -32601, f"Method not found: {method}"))


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "server": SERVER_INFO["name"], "version": SERVER_INFO["version"]}
