"""Tests for core/config.py."""

import os
from pathlib import Path

import pytest


def test_project_root_contains_pyproject():
    from core.config import PROJECT_ROOT

    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_specify_paths_are_relative_to_root():
    from core.config import CONSTITUTION_FILE, PLAN_FILE, PROJECT_ROOT, SPEC_FILE, TASKS_FILE

    for path in (CONSTITUTION_FILE, SPEC_FILE, PLAN_FILE, TASKS_FILE):
        assert path.is_relative_to(PROJECT_ROOT)


def test_default_env_vars():
    from core.config import AGENT_CLI, MAX_EXPERIMENTS, MAX_ITERATIONS, METRIC_DIRECTION, METRIC_KEY, STALL_LIMIT

    assert AGENT_CLI == os.environ.get("AGENT_CLI", "claude")
    assert MAX_ITERATIONS == int(os.environ.get("MAX_ITERATIONS", "50"))
    assert MAX_EXPERIMENTS == int(os.environ.get("MAX_EXPERIMENTS", "100"))
    assert STALL_LIMIT == int(os.environ.get("STALL_LIMIT", "3"))
    assert METRIC_KEY == os.environ.get("METRIC_KEY", "val_bpb")
    assert METRIC_DIRECTION == os.environ.get("METRIC_DIRECTION", "lower")


def test_logs_dirs_are_relative_to_root():
    from core.config import BUILD_LOGS_DIR, LOGS_DIR, OPTIMIZE_LOGS_DIR, PROJECT_ROOT

    assert LOGS_DIR.is_relative_to(PROJECT_ROOT)
    assert BUILD_LOGS_DIR.is_relative_to(LOGS_DIR)
    assert OPTIMIZE_LOGS_DIR.is_relative_to(LOGS_DIR)
