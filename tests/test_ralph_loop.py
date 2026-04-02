"""Tests for core/ralph/loop.py — using patched subprocess to avoid real agent calls."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.ralph.loop import LoopStatus, run_loop
from core.ralph.task_parser import next_pending, parse_tasks


TASKS_CONTENT = """\
# Tasks

- [ ] Task one
- [ ] Task two
- [ ] Task three
"""


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=path, capture_output=True, check=True)
    (path / "init.txt").write_text("init")
    subprocess.run(["git", "add", "-A"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, capture_output=True, check=True)


def _setup(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Set up a temp repo with tasks, constitution, prompt template."""
    _init_repo(tmp_path)

    specify_dir = tmp_path / ".specify" / "memory"
    specify_dir.mkdir(parents=True)
    tasks_file = tmp_path / ".specify" / "tasks.md"
    tasks_file.write_text(TASKS_CONTENT, encoding="utf-8")

    constitution = specify_dir / "constitution.md"
    constitution.write_text("## Rules\nDo good work.", encoding="utf-8")

    prompts_dir = tmp_path / "prompts" / "build"
    prompts_dir.mkdir(parents=True)
    prompt_file = prompts_dir / "Prompt.md"
    prompt_file.write_text("You are a build agent.", encoding="utf-8")

    subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "setup"], cwd=tmp_path, capture_output=True, check=True)

    return tasks_file, constitution, prompt_file, tmp_path


def _make_successful_agent(tmp_path: Path, tasks_file: Path):
    """Return a mock that simulates a successful agent: marks the next task done."""
    def side_effect(cmd, **kwargs):
        task = next_pending(tasks_file)
        if task:
            lines = tasks_file.read_text().splitlines()
            lines[task.line_index] = f"- [x] {task.text}"
            tasks_file.write_text("\n".join(lines) + "\n")
            new_file = tmp_path / f"done_{task.line_index}.txt"
            new_file.write_text("done")
        result = MagicMock()
        result.returncode = 0
        result.stdout = "<promise>TASK_DONE</promise>"
        result.stderr = ""
        return result

    return side_effect


def test_run_loop_all_done(tmp_path: Path):
    tasks_file, constitution, prompt_file, root = _setup(tmp_path)

    with patch("core.ralph.loop.subprocess.run") as mock_run:
        mock_run.side_effect = _make_successful_agent(tmp_path, tasks_file)
        status = run_loop(
            tasks_file=tasks_file,
            constitution_file=constitution,
            prompt_file=prompt_file,
            agent_cli="claude",
            log_dir=tmp_path / "logs" / "build",
            project_root=root,
            max_iterations=10,
            stall_limit=3,
        )

    assert status == LoopStatus.ALL_DONE


def test_run_loop_stall_detection(tmp_path: Path):
    tasks_file, constitution, prompt_file, root = _setup(tmp_path)

    def no_progress(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = "Agent failed"
        return result

    with patch("core.ralph.loop.subprocess.run", side_effect=no_progress):
        status = run_loop(
            tasks_file=tasks_file,
            constitution_file=constitution,
            prompt_file=prompt_file,
            agent_cli="claude",
            log_dir=tmp_path / "logs" / "build",
            project_root=root,
            max_iterations=10,
            stall_limit=3,
        )

    assert status == LoopStatus.STALLED


def test_run_loop_max_iterations(tmp_path: Path):
    tasks_file, constitution, prompt_file, root = _setup(tmp_path)

    call_count = 0

    def slow_agent(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        task = next_pending(tasks_file)
        if task and call_count % 4 == 0:
            lines = tasks_file.read_text().splitlines()
            lines[task.line_index] = f"- [x] {task.text}"
            tasks_file.write_text("\n".join(lines) + "\n")
            (tmp_path / f"f{call_count}.txt").write_text("done")
        result = MagicMock()
        result.returncode = 0 if call_count % 4 == 0 else 1
        result.stdout = ""
        result.stderr = ""
        return result

    with patch("core.ralph.loop.subprocess.run", side_effect=slow_agent):
        status = run_loop(
            tasks_file=tasks_file,
            constitution_file=constitution,
            prompt_file=prompt_file,
            agent_cli="claude",
            log_dir=tmp_path / "logs" / "build",
            project_root=root,
            max_iterations=2,
            stall_limit=10,
        )

    assert status == LoopStatus.MAX_ITERATIONS
