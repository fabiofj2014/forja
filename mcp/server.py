"""Forja MCP Server — unified FastAPI server exposing build and optimize tools."""

from __future__ import annotations

import sys
from pathlib import Path

# FastAPI is an optional dependency (pip install forja[mcp])
try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install forja[mcp]", file=sys.stderr)
    sys.exit(1)

from core.config import (
    AGENT_CLI,
    MAX_ITERATIONS,
    METRIC_KEY,
    OPTIMIZE_PROMPT_FILE,
    PROJECT_ROOT,
    STATE_DIR,
    STALL_LIMIT,
    TASKS_FILE,
)

app = FastAPI(
    title="Forja MCP Server",
    description="MCP tools for Forja build and optimize loops",
    version="0.1.0",
)


# ── Build tools ────────────────────────────────────────────────────────────────

@app.post("/tools/build_status")
async def build_status() -> dict:
    """Return current build progress from tasks.md."""
    from core.ralph.task_parser import parse_tasks

    if not TASKS_FILE.exists():
        return {"error": f"tasks.md not found at {TASKS_FILE}"}

    tasks = parse_tasks(TASKS_FILE)
    done = sum(1 for t in tasks if t.status == "done")
    pending = sum(1 for t in tasks if t.status == "pending")
    blocked = sum(1 for t in tasks if t.status == "blocked")

    return {
        "done": done,
        "pending": pending,
        "blocked": blocked,
        "total": len(tasks),
        "all_done": pending == 0,
    }


@app.post("/tools/build_next")
async def build_next() -> dict:
    """Return the next pending task."""
    from core.ralph.task_parser import next_pending

    if not TASKS_FILE.exists():
        return {"error": f"tasks.md not found at {TASKS_FILE}"}

    task = next_pending(TASKS_FILE)
    if task is None:
        return {"next_task": None, "all_done": True}
    return {"next_task": task.text, "all_done": False}


@app.post("/tools/build_start")
async def build_start(agent: str = AGENT_CLI, max_iterations: int = MAX_ITERATIONS) -> dict:
    """Start the Ralph Loop in the background.

    Note: This is a long-running operation. For production use,
    run ralph.sh directly or use a task queue.
    """
    import subprocess
    ralph_sh = PROJECT_ROOT / "core" / "ralph" / "ralph.sh"
    if not ralph_sh.exists():
        return {"error": "ralph.sh not found"}

    proc = subprocess.Popen(
        [str(ralph_sh)],
        env={**__import__("os").environ, "AGENT_CLI": agent, "MAX_ITERATIONS": str(max_iterations)},
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {"started": True, "pid": proc.pid, "agent": agent}


# ── Optimize tools ─────────────────────────────────────────────────────────────

@app.post("/tools/optimize_status")
async def optimize_status() -> dict:
    """Return current optimization progress."""
    from core.autoresearch.baseline_manager import BaselineManager
    from core.autoresearch.experiment_tracker import ExperimentTracker

    tracker = ExperimentTracker(STATE_DIR / "experiments.json")
    bm = BaselineManager(STATE_DIR / "baseline.json")

    history = tracker.get_history()
    baseline = bm.load_baseline()
    best = tracker.best_result()

    return {
        "total_experiments": len(history),
        "improvements": sum(1 for e in history if e.improved),
        "baseline_value": baseline.value if baseline else None,
        "baseline_metric": baseline.metric_key if baseline else None,
        "best_value": best.metric_after if best else None,
        "consecutive_no_improvement": tracker.consecutive_no_improvement(),
    }


@app.post("/tools/optimize_history")
async def optimize_history(last: int = 10) -> dict:
    """Return the last N optimization experiments."""
    from core.autoresearch.experiment_tracker import ExperimentTracker

    tracker = ExperimentTracker(STATE_DIR / "experiments.json")
    history = tracker.get_history()
    n = min(last, len(history))
    recent = history[-n:] if n > 0 else []

    return {
        "experiments": [
            {
                "id": e.id,
                "hypothesis": e.hypothesis,
                "metric_before": e.metric_before,
                "metric_after": e.metric_after,
                "improved": e.improved,
                "commit_sha": e.commit_sha,
                "timestamp": e.timestamp,
            }
            for e in recent
        ]
    }


@app.post("/tools/optimize_baseline")
async def optimize_baseline() -> dict:
    """Return the current optimization baseline."""
    from core.autoresearch.baseline_manager import BaselineManager

    bm = BaselineManager(STATE_DIR / "baseline.json")
    baseline = bm.load_baseline()

    if baseline is None:
        return {"baseline": None}

    return {
        "baseline": {
            "metric_key": baseline.metric_key,
            "value": baseline.value,
            "direction": baseline.direction,
            "commit_sha": baseline.commit_sha,
            "timestamp": baseline.timestamp,
        }
    }


@app.post("/tools/optimize_start")
async def optimize_start(
    agent: str = AGENT_CLI,
    metric_key: str = METRIC_KEY,
    max_experiments: int = 100,
) -> dict:
    """Start the Autoresearch Loop in the background."""
    import subprocess
    autoresearch_sh = PROJECT_ROOT / "core" / "autoresearch" / "autoresearch.sh"
    if not autoresearch_sh.exists():
        return {"error": "autoresearch.sh not found"}

    proc = subprocess.Popen(
        [str(autoresearch_sh)],
        env={
            **__import__("os").environ,
            "AGENT_CLI": agent,
            "METRIC_KEY": metric_key,
            "MAX_EXPERIMENTS": str(max_experiments),
        },
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {"started": True, "pid": proc.pid, "agent": agent, "metric_key": metric_key}


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    """Server health check."""
    return {"status": "ok", "project_root": str(PROJECT_ROOT)}


def main() -> None:
    """Run the MCP server."""
    import argparse
    parser = argparse.ArgumentParser(description="Forja MCP Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
