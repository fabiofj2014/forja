"""Autoresearch Loop: run optimization experiments with stall detection."""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.autoresearch.baseline_manager import BaselineManager
from core.autoresearch.experiment_tracker import Experiment, ExperimentTracker
from core.config import (
    AGENT_CLI,
    EXPERIMENT_TIMEOUT,
    MAX_EXPERIMENTS,
    METRIC_DIRECTION,
    METRIC_KEY,
    OPTIMIZE_LOGS_DIR,
    OPTIMIZE_PROMPT_FILE,
    PROJECT_ROOT,
    STALL_LIMIT,
    STATE_DIR,
)
from core.git_manager import commit, has_changes
from core.logger import get_iteration_logger
from core.metrics import is_improvement, read_metric
from core.utils import ensure_dir


class OptimizeStatus(Enum):
    """Outcome of an Autoresearch Loop run."""

    MAX_EXPERIMENTS = "MAX_EXPERIMENTS"
    STALLED = "STALLED"


@dataclass
class ExperimentRunResult:
    """Result of running a single experiment.

    Attributes:
        experiment: The logged Experiment record.
        reverted: Whether the change was reverted (no improvement).
    """

    experiment: Experiment
    reverted: bool


def _revert_changes(project_root: Path) -> None:
    """Revert uncommitted changes in the working tree.

    Reverts tracked files and removes new untracked files, but preserves
    state/ and logs/ directories which are managed by Forja.
    """
    subprocess.run(
        ["git", "checkout", "--", "."],
        cwd=project_root,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["git", "clean", "-fd", "--exclude=state/", "--exclude=logs/"],
        cwd=project_root,
        capture_output=True,
        check=False,
    )


def run_experiment(
    experiment_num: int,
    tracker: ExperimentTracker,
    baseline_manager: BaselineManager,
    metrics_file: Path,
    project_root: Path = PROJECT_ROOT,
    prompt_file: Path = OPTIMIZE_PROMPT_FILE,
    agent_cli: str = AGENT_CLI,
    log_dir: Path = OPTIMIZE_LOGS_DIR,
    metric_key: str = METRIC_KEY,
    direction: str = METRIC_DIRECTION,
    timeout: int = EXPERIMENT_TIMEOUT,
) -> ExperimentRunResult | None:
    """Run a single optimization experiment.

    Args:
        experiment_num: Current experiment number (for logging).
        tracker: ExperimentTracker to log results.
        baseline_manager: BaselineManager for current baseline.
        metrics_file: Path to the JSON file with metric values.
        project_root: Root of the project.
        prompt_file: Path to program.md (optimize prompt).
        agent_cli: Agent CLI command.
        log_dir: Directory for experiment logs.
        metric_key: Metric key to optimize.
        direction: 'lower' or 'higher'.
        timeout: Seconds before agent is killed.

    Returns:
        ExperimentRunResult, or None if baseline cannot be loaded.
    """
    baseline = baseline_manager.load_baseline()
    if baseline is None:
        return None

    ensure_dir(log_dir)
    logger = get_iteration_logger("optimize", experiment_num, log_dir)
    logger.info("Experiment %d — baseline %s=%.4f", experiment_num, metric_key, baseline.value)

    prompt_content = (
        prompt_file.read_text(encoding="utf-8")
        if prompt_file.exists()
        else (
            f"Optimize the code to improve {metric_key} (direction: {direction}). "
            f"Current baseline: {baseline.value:.4f}."
        )
    )

    iter_log = log_dir / f"exp_{experiment_num:04d}.log"
    result = subprocess.run(
        [agent_cli, "--print", prompt_content],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    iter_log.write_text(result.stdout + result.stderr, encoding="utf-8")

    if not has_changes(project_root):
        logger.warning("Agent made no changes")
        experiment = tracker.log_experiment(
            hypothesis="(no changes made)",
            metric_before=baseline.value,
            metric_after=baseline.value,
            direction=direction,
            improved=False,
        )
        return ExperimentRunResult(experiment=experiment, reverted=False)

    try:
        new_value = read_metric(metrics_file, metric_key)
    except Exception as e:
        logger.warning("Could not read metric: %s — reverting", e)
        _revert_changes(project_root)
        experiment = tracker.log_experiment(
            hypothesis="(metric read failed)",
            metric_before=baseline.value,
            metric_after=baseline.value,
            direction=direction,
            improved=False,
        )
        return ExperimentRunResult(experiment=experiment, reverted=True)

    improved = is_improvement(baseline.value, new_value, direction)
    commit_sha: str | None = None

    if improved:
        try:
            commit_sha = commit(
                project_root,
                f"[autoresearch] exp{experiment_num:04d}: {metric_key} {baseline.value:.4f}→{new_value:.4f}",
            )
            baseline_manager.update_baseline(new_value, commit_sha or "")
            logger.info("✓ Improved: %.4f → %.4f (committed %s)", baseline.value, new_value, commit_sha)
        except Exception as e:
            logger.warning("Commit failed: %s", e)
    else:
        _revert_changes(project_root)
        logger.info("✗ No improvement: %.4f → %.4f (reverted)", baseline.value, new_value)

    experiment = tracker.log_experiment(
        hypothesis=result.stdout[:200] if result.stdout else "(no output)",
        metric_before=baseline.value,
        metric_after=new_value,
        direction=direction,
        improved=improved,
        commit_sha=commit_sha,
    )

    return ExperimentRunResult(experiment=experiment, reverted=not improved)


def run_optimize_loop(
    metrics_file: Path,
    project_root: Path = PROJECT_ROOT,
    prompt_file: Path = OPTIMIZE_PROMPT_FILE,
    agent_cli: str = AGENT_CLI,
    log_dir: Path = OPTIMIZE_LOGS_DIR,
    state_dir: Path = STATE_DIR,
    metric_key: str = METRIC_KEY,
    direction: str = METRIC_DIRECTION,
    max_experiments: int = MAX_EXPERIMENTS,
    stall_limit: int = STALL_LIMIT,
    timeout: int = EXPERIMENT_TIMEOUT,
) -> OptimizeStatus:
    """Run the Autoresearch Loop until stalled or max experiments reached.

    Args:
        metrics_file: Path to the JSON file with metric values.
        project_root: Root of the project.
        prompt_file: Path to program.md.
        agent_cli: Agent CLI command.
        log_dir: Directory for experiment logs.
        state_dir: Directory for state files.
        metric_key: Metric key to optimize.
        direction: 'lower' or 'higher'.
        max_experiments: Maximum number of experiments.
        stall_limit: Consecutive failures before declaring stall.
        timeout: Seconds per experiment.

    Returns:
        OptimizeStatus indicating why the loop stopped.
    """
    ensure_dir(state_dir)

    tracker = ExperimentTracker(state_dir / "experiments.json")
    baseline_manager = BaselineManager(state_dir / "baseline.json")

    if baseline_manager.load_baseline() is None:
        try:
            initial_value = read_metric(metrics_file, metric_key)
            baseline_manager.capture_baseline(
                value=initial_value,
                commit_sha="initial",
                metric_key=metric_key,
                direction=direction,
            )
        except Exception:
            pass

    for i in range(1, max_experiments + 1):
        result = run_experiment(
            experiment_num=i,
            tracker=tracker,
            baseline_manager=baseline_manager,
            metrics_file=metrics_file,
            project_root=project_root,
            prompt_file=prompt_file,
            agent_cli=agent_cli,
            log_dir=log_dir,
            metric_key=metric_key,
            direction=direction,
            timeout=timeout,
        )

        if result is None:
            return OptimizeStatus.STALLED

        if tracker.consecutive_no_improvement() >= stall_limit:
            return OptimizeStatus.STALLED

    return OptimizeStatus.MAX_EXPERIMENTS
