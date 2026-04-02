"""Ralph Loop core logic: run iterations and detect stalls."""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.config import (
    AGENT_CLI,
    BUILD_LOGS_DIR,
    BUILD_PROMPT_FILE,
    CONSTITUTION_FILE,
    MAX_ITERATIONS,
    STALL_LIMIT,
    TASKS_FILE,
)
from core.git_manager import commit, has_changes
from core.logger import get_iteration_logger
from core.ralph.prompt_builder import build_prompt
from core.ralph.task_parser import Task, all_done, mark_blocked, mark_done, next_pending
from core.utils import ensure_dir


class LoopStatus(Enum):
    """Outcome of a Ralph Loop run."""

    ALL_DONE = "ALL_DONE"
    STALLED = "STALLED"
    MAX_ITERATIONS = "MAX_ITERATIONS"


@dataclass
class IterationResult:
    """Result of a single Ralph Loop iteration.

    Attributes:
        iteration: Iteration number (1-based).
        task: The task that was attempted.
        success: Whether the task was completed successfully.
        agent_output: Raw output from the agent.
        commit_sha: Git commit SHA if a commit was made, else None.
    """

    iteration: int
    task: Task
    success: bool
    agent_output: str
    commit_sha: str | None


def run_iteration(
    iteration: int,
    tasks_file: Path = TASKS_FILE,
    constitution_file: Path = CONSTITUTION_FILE,
    prompt_file: Path = BUILD_PROMPT_FILE,
    agent_cli: str = AGENT_CLI,
    log_dir: Path = BUILD_LOGS_DIR,
    project_root: Path | None = None,
) -> IterationResult | None:
    """Run a single Ralph Loop iteration.

    Finds the next pending task, builds the prompt, invokes the agent,
    and commits if changes were made.

    Args:
        iteration: Current iteration number (for logging).
        tasks_file: Path to tasks.md.
        constitution_file: Path to constitution.md.
        prompt_file: Path to Prompt.md template.
        agent_cli: Agent CLI command to invoke.
        log_dir: Directory for iteration logs.
        project_root: Project root for git operations (defaults to tasks_file.parent.parent).

    Returns:
        IterationResult, or None if there are no pending tasks.
    """
    task = next_pending(tasks_file)
    if task is None:
        return None

    if project_root is None:
        project_root = tasks_file.parent.parent

    ensure_dir(log_dir)
    logger = get_iteration_logger("build", iteration, log_dir)
    logger.info("Starting iteration %d: %s", iteration, task.text)

    prompt = build_prompt(task, constitution_file, prompt_file)
    prompt_file_tmp = log_dir / f"prompt_{iteration:04d}.md"
    prompt_file_tmp.write_text(prompt, encoding="utf-8")

    result = subprocess.run(
        [agent_cli, "--print", prompt_file_tmp.read_text(encoding="utf-8")],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    agent_output = result.stdout + result.stderr
    logger.info("Agent exited with code %d", result.returncode)

    success = result.returncode == 0 and has_changes(project_root)
    commit_sha: str | None = None

    if success:
        mark_done(tasks_file, task)
        try:
            commit_sha = commit(project_root, f"[forja] Implement: {task.text[:60]}")
            logger.info("Committed: %s", commit_sha)
        except Exception as e:
            logger.warning("Commit failed: %s", e)
    else:
        logger.warning("Task did not produce changes or agent failed")

    return IterationResult(
        iteration=iteration,
        task=task,
        success=success,
        agent_output=agent_output,
        commit_sha=commit_sha,
    )


def run_loop(
    tasks_file: Path = TASKS_FILE,
    constitution_file: Path = CONSTITUTION_FILE,
    prompt_file: Path = BUILD_PROMPT_FILE,
    agent_cli: str = AGENT_CLI,
    log_dir: Path = BUILD_LOGS_DIR,
    project_root: Path | None = None,
    max_iterations: int = MAX_ITERATIONS,
    stall_limit: int = STALL_LIMIT,
) -> LoopStatus:
    """Run the Ralph Loop until all tasks are done, stalled, or max iterations reached.

    Args:
        tasks_file: Path to tasks.md.
        constitution_file: Path to constitution.md.
        prompt_file: Path to Prompt.md template.
        agent_cli: Agent CLI command to invoke.
        log_dir: Directory for iteration logs.
        project_root: Project root for git operations.
        max_iterations: Maximum number of iterations before stopping.
        stall_limit: Number of consecutive failed iterations before declaring stall.

    Returns:
        LoopStatus indicating why the loop stopped.
    """
    if project_root is None:
        project_root = tasks_file.parent.parent

    consecutive_failures = 0

    for i in range(1, max_iterations + 1):
        if all_done(tasks_file):
            return LoopStatus.ALL_DONE

        result = run_iteration(
            iteration=i,
            tasks_file=tasks_file,
            constitution_file=constitution_file,
            prompt_file=prompt_file,
            agent_cli=agent_cli,
            log_dir=log_dir,
            project_root=project_root,
        )

        if result is None:
            return LoopStatus.ALL_DONE

        if result.success:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures >= stall_limit:
                task = next_pending(tasks_file)
                if task:
                    mark_blocked(tasks_file, task, reason="stall detected")
                return LoopStatus.STALLED

    return LoopStatus.MAX_ITERATIONS
