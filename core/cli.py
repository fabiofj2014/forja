"""Forja CLI entry point: forja build|optimize subcommands."""

import argparse
import sys

from core.config import (
    AGENT_CLI,
    BUILD_LOGS_DIR,
    BUILD_PROMPT_FILE,
    CONSTITUTION_FILE,
    MAX_ITERATIONS,
    PROJECT_ROOT,
    STALL_LIMIT,
    TASKS_FILE,
)


def _cmd_build_start(args: argparse.Namespace) -> int:
    """Start the Ralph Loop (build phase)."""
    from core.ralph.loop import LoopStatus, run_loop

    print(
        f"[forja] Starting build loop "
        f"(agent={args.agent}, max_iter={args.max_iterations})"
    )

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

    print(
        f"[forja] Build status: {done}/{total} done, "
        f"{pending} pending, {blocked} blocked"
    )
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

    return parser


def main() -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
