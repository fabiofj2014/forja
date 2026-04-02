"""Manage the baseline metric snapshot for the Autoresearch loop."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.config import METRIC_DIRECTION, METRIC_KEY


@dataclass
class Baseline:
    """Snapshot of the baseline metric.

    Attributes:
        metric_key: The metric identifier (e.g., 'val_bpb').
        value: The metric value at the time of capture.
        direction: 'lower' or 'higher' (which is better).
        commit_sha: Git SHA when baseline was captured.
        timestamp: ISO 8601 timestamp of capture.
    """

    metric_key: str
    value: float
    direction: str
    commit_sha: str
    timestamp: str


class BaselineManager:
    """Persist and retrieve the optimization baseline.

    Args:
        baseline_file: Path to the JSON file storing the baseline.
    """

    def __init__(self, baseline_file: Path) -> None:
        self._file = baseline_file

    def capture_baseline(
        self,
        value: float,
        commit_sha: str,
        metric_key: str = METRIC_KEY,
        direction: str = METRIC_DIRECTION,
    ) -> Baseline:
        """Save a new baseline snapshot.

        Args:
            value: The current metric value.
            commit_sha: Current git commit SHA.
            metric_key: Metric identifier.
            direction: 'lower' or 'higher'.

        Returns:
            The saved Baseline object.
        """
        baseline = Baseline(
            metric_key=metric_key,
            value=value,
            direction=direction,
            commit_sha=commit_sha,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(asdict(baseline), indent=2), encoding="utf-8")
        return baseline

    def load_baseline(self) -> Baseline | None:
        """Load the current baseline from disk.

        Returns:
            The saved Baseline, or None if no baseline exists.
        """
        if not self._file.exists():
            return None
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            return Baseline(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def update_baseline(self, value: float, commit_sha: str) -> Baseline | None:
        """Update the baseline value if a baseline already exists.

        Preserves the existing metric_key and direction.

        Args:
            value: New metric value.
            commit_sha: New git commit SHA.

        Returns:
            Updated Baseline, or None if no baseline exists to update.
        """
        existing = self.load_baseline()
        if existing is None:
            return None
        return self.capture_baseline(
            value=value,
            commit_sha=commit_sha,
            metric_key=existing.metric_key,
            direction=existing.direction,
        )
