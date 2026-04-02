"""Tests for core/ralph/task_parser.py."""

from pathlib import Path

import pytest

from core.ralph.task_parser import (
    Task,
    all_done,
    mark_blocked,
    mark_done,
    next_pending,
    parse_tasks,
)

SAMPLE_TASKS = """\
# Tasks

## Phase 1

- [ ] First task
- [x] Second task already done
- [ ] Third task
- [BLOCKED] Fourth task — some reason

## Phase 2

- [ ] Fifth task
"""


def _write_tasks(tmp_path: Path, content: str) -> Path:
    f = tmp_path / "tasks.md"
    f.write_text(content, encoding="utf-8")
    return f


def test_parse_tasks_counts(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    tasks = parse_tasks(f)
    assert len(tasks) == 5


def test_parse_tasks_statuses(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    tasks = parse_tasks(f)
    statuses = [t.status for t in tasks]
    assert statuses == ["pending", "done", "pending", "blocked", "pending"]


def test_parse_tasks_text(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    tasks = parse_tasks(f)
    assert tasks[0].text == "First task"
    assert tasks[1].text == "Second task already done"


def test_parse_tasks_empty(tmp_path: Path):
    f = _write_tasks(tmp_path, "# Tasks\n\nNo tasks here.\n")
    assert parse_tasks(f) == []


def test_next_pending_returns_first(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    task = next_pending(f)
    assert task is not None
    assert task.text == "First task"
    assert task.status == "pending"


def test_next_pending_none_when_all_done(tmp_path: Path):
    content = "- [x] Done one\n- [x] Done two\n"
    f = _write_tasks(tmp_path, content)
    assert next_pending(f) is None


def test_mark_done(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    task = next_pending(f)
    assert task is not None
    mark_done(f, task)
    content = f.read_text(encoding="utf-8")
    assert "- [x] First task" in content
    assert "- [ ] First task" not in content


def test_mark_blocked(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    task = next_pending(f)
    assert task is not None
    mark_blocked(f, task, reason="dependency missing")
    content = f.read_text(encoding="utf-8")
    assert "- [BLOCKED] First task — dependency missing" in content


def test_mark_blocked_no_reason(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    task = next_pending(f)
    assert task is not None
    mark_blocked(f, task)
    content = f.read_text(encoding="utf-8")
    assert "- [BLOCKED] First task\n" in content


def test_all_done_false(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    assert all_done(f) is False


def test_all_done_true(tmp_path: Path):
    content = "- [x] Task one\n- [x] Task two\n"
    f = _write_tasks(tmp_path, content)
    assert all_done(f) is True


def test_all_done_with_blocked_only(tmp_path: Path):
    content = "- [x] Done\n- [BLOCKED] Stuck\n"
    f = _write_tasks(tmp_path, content)
    assert all_done(f) is True


def test_parse_tasks_preserves_line_index(tmp_path: Path):
    f = _write_tasks(tmp_path, SAMPLE_TASKS)
    tasks = parse_tasks(f)
    lines = SAMPLE_TASKS.splitlines()
    for task in tasks:
        assert task.line_index < len(lines)
