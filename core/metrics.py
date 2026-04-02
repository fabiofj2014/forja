"""Metric reading and comparison for the Autoresearch loop."""

import json
from pathlib import Path

from core.config import METRIC_DIRECTION, METRIC_KEY


class MetricError(Exception):
    """Raised when a metric cannot be read or compared."""


def read_metric(metrics_file: Path, key: str = METRIC_KEY) -> float:
    """Read a metric value from a JSON file.

    Args:
        metrics_file: Path to a JSON file containing metric values.
        key: The metric key to read.

    Returns:
        The metric value as a float.

    Raises:
        MetricError: If the file cannot be read or the key is missing.
    """
    if not metrics_file.exists():
        raise MetricError(f"Metrics file not found: {metrics_file}")

    try:
        data = json.loads(metrics_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise MetricError(f"Invalid JSON in {metrics_file}: {e}") from e

    if key not in data:
        raise MetricError(f"Metric key '{key}' not found in {metrics_file}")

    try:
        return float(data[key])
    except (TypeError, ValueError) as e:
        raise MetricError(f"Metric '{key}' is not numeric: {data[key]}") from e


def compare_metrics(
    baseline: float, candidate: float, direction: str = METRIC_DIRECTION
) -> float:
    """Compute the improvement of candidate over baseline.

    Args:
        baseline: The reference metric value.
        candidate: The new metric value to compare.
        direction: 'lower' means lower is better, 'higher' means higher is better.

    Returns:
        Positive value = improvement, negative = regression, zero = unchanged.

    Raises:
        MetricError: If direction is not 'lower' or 'higher'.
    """
    if direction not in ("lower", "higher"):
        raise MetricError(
            f"Invalid direction '{direction}': must be 'lower' or 'higher'"
        )

    if direction == "lower":
        return baseline - candidate
    return candidate - baseline


def is_improvement(
    baseline: float, candidate: float, direction: str = METRIC_DIRECTION
) -> bool:
    """Return True if candidate is strictly better than baseline.

    Args:
        baseline: The reference metric value.
        candidate: The new metric value.
        direction: 'lower' means lower is better, 'higher' means higher is better.

    Returns:
        True if the candidate improves on the baseline.
    """
    return compare_metrics(baseline, candidate, direction) > 0
