"""Track Autoresearch experiments: log, retrieve history, and find best result."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class Experiment:
    """A single experiment record.

    Attributes:
        id: Unique experiment number (1-based).
        hypothesis: What change was attempted.
        metric_before: Baseline metric value.
        metric_after: Metric value after the change.
        direction: 'lower' or 'higher' (which is better).
        improved: Whether the experiment improved the metric.
        commit_sha: Git commit SHA if change was kept, else None.
        timestamp: ISO 8601 timestamp when the experiment was recorded.
    """

    id: int
    hypothesis: str
    metric_before: float
    metric_after: float
    direction: str
    improved: bool
    commit_sha: str | None
    timestamp: str


class ExperimentTracker:
    """Persists experiment history to a JSON file.

    Args:
        history_file: Path to the JSON file used for persistence.
    """

    def __init__(self, history_file: Path) -> None:
        self._file = history_file
        self._experiments: list[Experiment] = self._load()

    def _load(self) -> list[Experiment]:
        if not self._file.exists():
            return []
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            return [Experiment(**e) for e in data]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def _save(self) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps([asdict(e) for e in self._experiments], indent=2),
            encoding="utf-8",
        )

    def log_experiment(
        self,
        hypothesis: str,
        metric_before: float,
        metric_after: float,
        direction: str,
        improved: bool,
        commit_sha: str | None = None,
    ) -> Experiment:
        """Record a new experiment.

        Args:
            hypothesis: Description of the change attempted.
            metric_before: Metric value before the change.
            metric_after: Metric value after the change.
            direction: 'lower' or 'higher'.
            improved: Whether the experiment improved the metric.
            commit_sha: Commit SHA if the change was kept.

        Returns:
            The recorded Experiment object.
        """
        exp = Experiment(
            id=len(self._experiments) + 1,
            hypothesis=hypothesis,
            metric_before=metric_before,
            metric_after=metric_after,
            direction=direction,
            improved=improved,
            commit_sha=commit_sha,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._experiments.append(exp)
        self._save()
        return exp

    def get_history(self) -> list[Experiment]:
        """Return all experiments in chronological order."""
        return list(self._experiments)

    def best_result(self) -> Experiment | None:
        """Return the experiment with the best metric improvement, or None.

        For 'lower' direction: minimum metric_after among improved experiments.
        For 'higher' direction: maximum metric_after among improved experiments.

        Returns:
            The best Experiment, or None if no improvements have been recorded.
        """
        improved = [e for e in self._experiments if e.improved]
        if not improved:
            return None

        direction = improved[-1].direction
        if direction == "lower":
            return min(improved, key=lambda e: e.metric_after)
        return max(improved, key=lambda e: e.metric_after)

    def consecutive_no_improvement(self) -> int:
        """Return the count of consecutive experiments at the end with no improvement."""
        count = 0
        for exp in reversed(self._experiments):
            if not exp.improved:
                count += 1
            else:
                break
        return count
