"""Forja CLI entry point: forja build|optimize subcommands."""

import argparse
import sys

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


def _cmd_build_start(args: argparse.Namespace) -> int:
    """Start the Ralph Loop (build phase)."""
    from core.ralph.loop import LoopStatus, run_loop

    print(f"[forja] Starting build loop (agent={args.agent}, max_iter={args.max_iterations})")

    status = run_loop(
        tasks_file=TASKS_FILE,
        constitution_file=CONSTITUTION_FILE,
        prompt_file=BUILD_PROMPT_FILE,
        agent_cli=args.agent,
        log_dir=BUILD_LOGS_DIR,
        project_root=PROJECT_ROOT,
        max_iterations=args.max_iterations,
        stall_limit=args.stall_limit,
    )

    if status == LoopStatus.ALL_DONE:
        print("[forja] ✅ ALL_TASKS_DONE")
        return 0
    elif status == LoopStatus.STALLED:
        print("[forja] 🛑 STALLED — check logs/build/ for details")
        return 2
    else:
        print(f"[forja] ⏱ MAX_ITERATIONS ({args.max_iterations}) reached")
        return 1


def _cmd_build_status(args: argparse.Namespace) -> int:
    """Show current build status from tasks.md."""
    from core.ralph.task_parser import parse_tasks

    if not TASKS_FILE.exists():
        print(f"[forja] tasks.md not found at {TASKS_FILE}")
        return 1

    tasks = parse_tasks(TASKS_FILE)
    done = sum(1 for t in tasks if t.status == "done")
    pending = sum(1 for t in tasks if t.status == "pending")
    blocked = sum(1 for t in tasks if t.status == "blocked")
    total = len(tasks)

    print(f"[forja] Build status: {done}/{total} done, {pending} pending, {blocked} blocked")
    return 0


def _cmd_build_next(args: argparse.Namespace) -> int:
    """Show the next pending task."""
    from core.ralph.task_parser import next_pending

    if not TASKS_FILE.exists():
        print(f"[forja] tasks.md not found at {TASKS_FILE}")
        return 1

    task = next_pending(TASKS_FILE)
    if task is None:
        print("[forja] No pending tasks — all done!")
        return 0

    print(f"[forja] Next task: {task.text}")
    return 0


def _cmd_optimize_start(args: argparse.Namespace) -> int:
    """Start the Autoresearch Loop (optimize phase)."""
    from core.autoresearch.loop import OptimizeStatus, run_optimize_loop

    metrics_file = PROJECT_ROOT / args.metrics_file
    print(f"[forja] Starting optimize loop (agent={args.agent}, metric={args.metric_key})")

    status = run_optimize_loop(
        metrics_file=metrics_file,
        project_root=PROJECT_ROOT,
        prompt_file=OPTIMIZE_PROMPT_FILE,
        agent_cli=args.agent,
        log_dir=OPTIMIZE_LOGS_DIR,
        state_dir=STATE_DIR,
        metric_key=args.metric_key,
        direction=args.direction,
        max_experiments=args.max_experiments,
        stall_limit=args.stall_limit,
        timeout=args.timeout,
    )

    if status == OptimizeStatus.STALLED:
        print("[forja] 🛑 STALLED — no improvement after consecutive experiments")
        return 2
    else:
        print(f"[forja] ⏱ MAX_EXPERIMENTS ({args.max_experiments}) reached")
        return 1


def _cmd_optimize_status(args: argparse.Namespace) -> int:
    """Show current optimization status."""
    from core.autoresearch.baseline_manager import BaselineManager
    from core.autoresearch.experiment_tracker import ExperimentTracker

    tracker = ExperimentTracker(STATE_DIR / "experiments.json")
    bm = BaselineManager(STATE_DIR / "baseline.json")

    history = tracker.get_history()
    baseline = bm.load_baseline()
    best = tracker.best_result()

    total = len(history)
    improved = sum(1 for e in history if e.improved)

    print(f"[forja] Optimize status: {total} experiments, {improved} improvements")
    if baseline:
        print(f"[forja] Baseline: {baseline.metric_key}={baseline.value:.4f} ({baseline.direction})")
    if best:
        metric_key = best.metric_key if hasattr(best, "metric_key") else METRIC_KEY
        print(f"[forja] Best result: {metric_key}={best.metric_after:.4f}")
    return 0


def _cmd_optimize_history(args: argparse.Namespace) -> int:
    """Show experiment history."""
    from core.autoresearch.experiment_tracker import ExperimentTracker

    tracker = ExperimentTracker(STATE_DIR / "experiments.json")
    history = tracker.get_history()

    if not history:
        print("[forja] No experiments recorded yet")
        return 0

    n = args.last if args.last else len(history)
    for exp in history[-n:]:
        status = "✓" if exp.improved else "✗"
        print(f"  [{exp.id:03d}] {status} {exp.metric_before:.4f}→{exp.metric_after:.4f} | {exp.hypothesis[:60]}")
    return 0


def _cmd_optimize_baseline(args: argparse.Namespace) -> int:
    """Show or capture the current baseline."""
    from core.autoresearch.baseline_manager import BaselineManager
    from core.metrics import read_metric

    bm = BaselineManager(STATE_DIR / "baseline.json")

    if args.capture:
        metrics_file = PROJECT_ROOT / args.metrics_file
        try:
            value = read_metric(metrics_file, METRIC_KEY)
            baseline = bm.capture_baseline(value, "manual", METRIC_KEY, METRIC_DIRECTION)
            print(f"[forja] Baseline captured: {METRIC_KEY}={baseline.value:.4f}")
        except Exception as e:
            print(f"[forja] Error: {e}")
            return 1
    else:
        baseline = bm.load_baseline()
        if baseline is None:
            print("[forja] No baseline recorded yet")
        else:
            print(
                f"[forja] Baseline: {baseline.metric_key}={baseline.value:.4f}"
                f" ({baseline.direction}) @ {baseline.commit_sha}"
            )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forja",
        description="Forja — AI-driven build and optimize loop",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── build ──────────────────────────────────────────────────────────────────
    build_parser = subparsers.add_parser("build", help="Build phase (Ralph Loop)")
    build_sub = build_parser.add_subparsers(dest="subcommand", required=True)

    # build start
    start_parser = build_sub.add_parser("start", help="Start the Ralph Loop")
    start_parser.add_argument("--agent", default=AGENT_CLI, help="Agent CLI to use")
    start_parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    start_parser.add_argument("--stall-limit", type=int, default=STALL_LIMIT)
    start_parser.set_defaults(func=_cmd_build_start)

    # build status
    status_parser = build_sub.add_parser("status", help="Show build progress")
    status_parser.set_defaults(func=_cmd_build_status)

    # build next
    next_parser = build_sub.add_parser("next", help="Show next pending task")
    next_parser.set_defaults(func=_cmd_build_next)

    # ── optimize ───────────────────────────────────────────────────────────────
    optimize_parser = subparsers.add_parser("optimize", help="Optimize phase (Autoresearch Loop)")
    optimize_sub = optimize_parser.add_subparsers(dest="subcommand", required=True)

    # optimize start
    opt_start = optimize_sub.add_parser("start", help="Start the Autoresearch Loop")
    opt_start.add_argument("--agent", default=AGENT_CLI)
    opt_start.add_argument("--metric-key", default=METRIC_KEY)
    opt_start.add_argument("--direction", default=METRIC_DIRECTION, choices=["lower", "higher"])
    opt_start.add_argument("--max-experiments", type=int, default=MAX_EXPERIMENTS)
    opt_start.add_argument("--stall-limit", type=int, default=STALL_LIMIT)
    opt_start.add_argument("--timeout", type=int, default=EXPERIMENT_TIMEOUT)
    opt_start.add_argument("--metrics-file", default=".autoresearch/metrics.json")
    opt_start.set_defaults(func=_cmd_optimize_start)

    # optimize status
    opt_status = optimize_sub.add_parser("status", help="Show optimize progress")
    opt_status.set_defaults(func=_cmd_optimize_status)

    # optimize history
    opt_history = optimize_sub.add_parser("history", help="Show experiment history")
    opt_history.add_argument("--last", type=int, default=0, help="Show last N experiments")
    opt_history.set_defaults(func=_cmd_optimize_history)

    # optimize baseline
    opt_baseline = optimize_sub.add_parser("baseline", help="Show or capture baseline")
    opt_baseline.add_argument("--capture", action="store_true", help="Capture current metrics as new baseline")
    opt_baseline.add_argument("--metrics-file", default=".autoresearch/metrics.json")
    opt_baseline.set_defaults(func=_cmd_optimize_baseline)

    return parser


def main() -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
