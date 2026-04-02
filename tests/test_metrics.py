"""Tests for core/metrics.py."""

import json
from pathlib import Path

import pytest

from core.metrics import MetricError, compare_metrics, is_improvement, read_metric


def _write_metrics(tmp_path: Path, data: dict) -> Path:
    f = tmp_path / "metrics.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


def test_read_metric_basic(tmp_path: Path):
    f = _write_metrics(tmp_path, {"val_bpb": 1.23})
    assert read_metric(f, "val_bpb") == pytest.approx(1.23)


def test_read_metric_key_missing(tmp_path: Path):
    f = _write_metrics(tmp_path, {"other": 0.5})
    with pytest.raises(MetricError, match="not found"):
        read_metric(f, "val_bpb")


def test_read_metric_file_not_found(tmp_path: Path):
    with pytest.raises(MetricError, match="not found"):
        read_metric(tmp_path / "missing.json")


def test_read_metric_invalid_json(tmp_path: Path):
    f = tmp_path / "bad.json"
    f.write_text("not json", encoding="utf-8")
    with pytest.raises(MetricError, match="Invalid JSON"):
        read_metric(f)


def test_read_metric_non_numeric(tmp_path: Path):
    f = _write_metrics(tmp_path, {"val_bpb": "not_a_number"})
    with pytest.raises(MetricError, match="not numeric"):
        read_metric(f)


def test_compare_metrics_lower_improvement():
    assert compare_metrics(2.0, 1.5, direction="lower") == pytest.approx(0.5)


def test_compare_metrics_lower_regression():
    assert compare_metrics(1.5, 2.0, direction="lower") == pytest.approx(-0.5)


def test_compare_metrics_higher_improvement():
    assert compare_metrics(0.8, 0.9, direction="higher") == pytest.approx(0.1)


def test_compare_metrics_invalid_direction():
    with pytest.raises(MetricError, match="Invalid direction"):
        compare_metrics(1.0, 2.0, direction="sideways")


def test_is_improvement_lower():
    assert is_improvement(2.0, 1.5, direction="lower") is True
    assert is_improvement(1.5, 2.0, direction="lower") is False


def test_is_improvement_higher():
    assert is_improvement(0.8, 0.9, direction="higher") is True
    assert is_improvement(0.9, 0.8, direction="higher") is False


def test_is_improvement_equal():
    assert is_improvement(1.0, 1.0, direction="lower") is False
