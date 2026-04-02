"""Tests for core/autoresearch/loop.py."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.autoresearch.baseline_manager import BaselineManager
from core.autoresearch.loop import OptimizeStatus, run_optimize_loop


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=path, capture_output=True, check=True)
    (path / "init.txt").write_text("init")
    subprocess.run(["git", "add", "-A"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, capture_output=True, check=True)


def _setup(tmp_path: Path, initial_metric: float = 2.0) -> tuple:
    _init_repo(tmp_path)

    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text(json.dumps({"val_bpb": initial_metric}), encoding="utf-8")

    prompts_dir = tmp_path / "prompts" / "optimize"
    prompts_dir.mkdir(parents=True)
    prompt_file = prompts_dir / "program.md"
    prompt_file.write_text("Optimize the model.", encoding="utf-8")

    state_dir = tmp_path / "state"
    log_dir = tmp_path / "logs" / "optimize"

    subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "add metrics"], cwd=tmp_path, capture_output=True, check=True)

    return metrics_file, prompt_file, state_dir, log_dir


def _mock_agent_only(real_run, agent_response: MagicMock):
    """Return a side_effect that mocks only agent calls, passing git through."""

    def side_effect(cmd, **kwargs):
        if isinstance(cmd, list) and cmd and cmd[0] == "git":
            return real_run(cmd, **kwargs)
        return agent_response

    return side_effect


def test_run_optimize_loop_stalls(tmp_path: Path):
    metrics_file, prompt_file, state_dir, log_dir = _setup(tmp_path)

    agent_result = MagicMock()
    agent_result.returncode = 1
    agent_result.stdout = ""
    agent_result.stderr = "failed"

    real_run = subprocess.run
    with patch("core.autoresearch.loop.subprocess.run", side_effect=_mock_agent_only(real_run, agent_result)):
        status = run_optimize_loop(
            metrics_file=metrics_file,
            project_root=tmp_path,
            prompt_file=prompt_file,
            agent_cli="claude",
            log_dir=log_dir,
            state_dir=state_dir,
            metric_key="val_bpb",
            direction="lower",
            max_experiments=10,
            stall_limit=3,
            timeout=30,
        )

    assert status == OptimizeStatus.STALLED


def test_run_optimize_loop_max_experiments(tmp_path: Path):
    metrics_file, prompt_file, state_dir, log_dir = _setup(tmp_path, initial_metric=2.0)
    call_count = 0
    real_run = subprocess.run

    def smart_side_effect(cmd, **kwargs):
        nonlocal call_count
        if isinstance(cmd, list) and cmd and cmd[0] == "git":
            return real_run(cmd, **kwargs)
        call_count += 1
        current = json.loads(metrics_file.read_text())["val_bpb"]
        metrics_file.write_text(json.dumps({"val_bpb": current - 0.01}))
        (tmp_path / f"change_{call_count}.txt").write_text(f"change {call_count}")
        result = MagicMock()
        result.returncode = 0
        result.stdout = "improved"
        result.stderr = ""
        return result

    with patch("core.autoresearch.loop.subprocess.run", side_effect=smart_side_effect):
        status = run_optimize_loop(
            metrics_file=metrics_file,
            project_root=tmp_path,
            prompt_file=prompt_file,
            agent_cli="claude",
            log_dir=log_dir,
            state_dir=state_dir,
            metric_key="val_bpb",
            direction="lower",
            max_experiments=3,
            stall_limit=5,
            timeout=30,
        )

    assert status == OptimizeStatus.MAX_EXPERIMENTS


def test_baseline_captured_on_first_run(tmp_path: Path):
    metrics_file, prompt_file, state_dir, log_dir = _setup(tmp_path)

    agent_result = MagicMock()
    agent_result.returncode = 0
    agent_result.stdout = ""
    agent_result.stderr = ""

    real_run = subprocess.run
    with patch("core.autoresearch.loop.subprocess.run", side_effect=_mock_agent_only(real_run, agent_result)):
        run_optimize_loop(
            metrics_file=metrics_file,
            project_root=tmp_path,
            prompt_file=prompt_file,
            agent_cli="claude",
            log_dir=log_dir,
            state_dir=state_dir,
            metric_key="val_bpb",
            direction="lower",
            max_experiments=1,
            stall_limit=5,
            timeout=30,
        )

    bm = BaselineManager(state_dir / "baseline.json")
    baseline = bm.load_baseline()
    assert baseline is not None
    assert baseline.value == pytest.approx(2.0)
