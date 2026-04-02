"""Tests for core/autoresearch/baseline_manager.py."""

from pathlib import Path

import pytest

from core.autoresearch.baseline_manager import Baseline, BaselineManager


def test_capture_baseline(tmp_path: Path):
    bm = BaselineManager(tmp_path / "baseline.json")
    baseline = bm.capture_baseline(value=2.5, commit_sha="abc123")
    assert baseline.value == pytest.approx(2.5)
    assert baseline.commit_sha == "abc123"
    assert baseline.metric_key == "val_bpb"  # default
    assert baseline.direction == "lower"  # default


def test_capture_baseline_custom_params(tmp_path: Path):
    bm = BaselineManager(tmp_path / "baseline.json")
    baseline = bm.capture_baseline(
        value=0.75,
        commit_sha="def456",
        metric_key="accuracy",
        direction="higher",
    )
    assert baseline.metric_key == "accuracy"
    assert baseline.direction == "higher"


def test_load_baseline_none_when_missing(tmp_path: Path):
    bm = BaselineManager(tmp_path / "no_baseline.json")
    assert bm.load_baseline() is None


def test_load_baseline_after_capture(tmp_path: Path):
    baseline_file = tmp_path / "baseline.json"
    bm = BaselineManager(baseline_file)
    bm.capture_baseline(1.23, "sha1")

    bm2 = BaselineManager(baseline_file)
    loaded = bm2.load_baseline()
    assert loaded is not None
    assert loaded.value == pytest.approx(1.23)
    assert loaded.commit_sha == "sha1"


def test_load_baseline_persists_all_fields(tmp_path: Path):
    bm = BaselineManager(tmp_path / "baseline.json")
    bm.capture_baseline(3.14, "sha999", metric_key="perplexity", direction="lower")

    loaded = bm.load_baseline()
    assert loaded is not None
    assert loaded.metric_key == "perplexity"
    assert loaded.direction == "lower"
    assert loaded.timestamp is not None


def test_update_baseline(tmp_path: Path):
    bm = BaselineManager(tmp_path / "baseline.json")
    bm.capture_baseline(2.0, "sha1", metric_key="loss", direction="lower")

    updated = bm.update_baseline(1.8, "sha2")
    assert updated is not None
    assert updated.value == pytest.approx(1.8)
    assert updated.commit_sha == "sha2"
    assert updated.metric_key == "loss"
    assert updated.direction == "lower"


def test_update_baseline_returns_none_when_no_baseline(tmp_path: Path):
    bm = BaselineManager(tmp_path / "baseline.json")
    result = bm.update_baseline(1.5, "sha_new")
    assert result is None


def test_update_baseline_does_not_change_direction(tmp_path: Path):
    bm = BaselineManager(tmp_path / "baseline.json")
    bm.capture_baseline(0.7, "sha1", direction="higher")

    updated = bm.update_baseline(0.8, "sha2")
    assert updated is not None
    assert updated.direction == "higher"
