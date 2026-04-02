"""Tests for core/autoresearch/experiment_tracker.py."""

from pathlib import Path

import pytest

from core.autoresearch.experiment_tracker import Experiment, ExperimentTracker


def test_log_experiment_persists(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    exp = tracker.log_experiment(
        hypothesis="Try relu instead of tanh",
        metric_before=2.0,
        metric_after=1.8,
        direction="lower",
        improved=True,
        commit_sha="abc123",
    )
    assert exp.id == 1
    assert exp.improved is True
    assert exp.commit_sha == "abc123"


def test_log_experiment_increments_id(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    e1 = tracker.log_experiment("h1", 2.0, 1.9, "lower", True)
    e2 = tracker.log_experiment("h2", 1.9, 1.85, "lower", True)
    assert e1.id == 1
    assert e2.id == 2


def test_get_history_empty(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    assert tracker.get_history() == []


def test_get_history_returns_all(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    tracker.log_experiment("h1", 2.0, 1.9, "lower", True)
    tracker.log_experiment("h2", 1.9, 1.95, "lower", False)
    history = tracker.get_history()
    assert len(history) == 2


def test_persistence_across_instances(tmp_path: Path):
    history_file = tmp_path / "experiments.json"
    t1 = ExperimentTracker(history_file)
    t1.log_experiment("h1", 2.0, 1.8, "lower", True)

    t2 = ExperimentTracker(history_file)
    assert len(t2.get_history()) == 1
    assert t2.get_history()[0].hypothesis == "h1"


def test_best_result_lower(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    tracker.log_experiment("h1", 2.0, 1.8, "lower", True)
    tracker.log_experiment("h2", 1.8, 1.6, "lower", True)
    tracker.log_experiment("h3", 1.6, 1.65, "lower", False)

    best = tracker.best_result()
    assert best is not None
    assert best.metric_after == pytest.approx(1.6)


def test_best_result_higher(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    tracker.log_experiment("h1", 0.7, 0.8, "higher", True)
    tracker.log_experiment("h2", 0.8, 0.85, "higher", True)

    best = tracker.best_result()
    assert best is not None
    assert best.metric_after == pytest.approx(0.85)


def test_best_result_none_when_no_improvements(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    tracker.log_experiment("h1", 2.0, 2.1, "lower", False)
    assert tracker.best_result() is None


def test_consecutive_no_improvement_zero(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    tracker.log_experiment("h1", 2.0, 1.8, "lower", True)
    assert tracker.consecutive_no_improvement() == 0


def test_consecutive_no_improvement_count(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    tracker.log_experiment("h1", 2.0, 1.8, "lower", True)
    tracker.log_experiment("h2", 1.8, 1.85, "lower", False)
    tracker.log_experiment("h3", 1.8, 1.82, "lower", False)
    assert tracker.consecutive_no_improvement() == 2


def test_consecutive_no_improvement_resets(tmp_path: Path):
    tracker = ExperimentTracker(tmp_path / "experiments.json")
    tracker.log_experiment("h1", 2.0, 2.1, "lower", False)
    tracker.log_experiment("h2", 2.0, 2.1, "lower", False)
    tracker.log_experiment("h3", 2.0, 1.9, "lower", True)
    assert tracker.consecutive_no_improvement() == 0
