"""Tests for core/ralph/prompt_builder.py."""

from pathlib import Path

import pytest

from core.ralph.prompt_builder import build_prompt, build_status_prompt
from core.ralph.task_parser import Task


def _write(tmp_path: Path, name: str, content: str) -> Path:
    f = tmp_path / name
    f.write_text(content, encoding="utf-8")
    return f


def _make_task(text: str, line_index: int = 0) -> Task:
    return Task(text=text, status="pending", line_index=line_index)


def test_build_prompt_contains_task(tmp_path: Path):
    constitution = _write(tmp_path, "constitution.md", "## Rule\nDo good work.")
    template = _write(tmp_path, "Prompt.md", "You are a helpful agent.")
    task = _make_task("Implement foo module")

    prompt = build_prompt(task, constitution, template)

    assert "Implement foo module" in prompt


def test_build_prompt_contains_constitution(tmp_path: Path):
    constitution = _write(tmp_path, "constitution.md", "## Rule\nZero deps in core.")
    template = _write(tmp_path, "Prompt.md", "Base prompt.")
    task = _make_task("Add feature")

    prompt = build_prompt(task, constitution, template)

    assert "Zero deps in core." in prompt


def test_build_prompt_contains_template(tmp_path: Path):
    constitution = _write(tmp_path, "constitution.md", "Principles here.")
    template = _write(tmp_path, "Prompt.md", "MASTER_TEMPLATE_MARKER")
    task = _make_task("Do something")

    prompt = build_prompt(task, constitution, template)

    assert "MASTER_TEMPLATE_MARKER" in prompt


def test_build_prompt_contains_completion_tag(tmp_path: Path):
    constitution = _write(tmp_path, "constitution.md", "Principles.")
    template = _write(tmp_path, "Prompt.md", "Base.")
    task = _make_task("Some task")

    prompt = build_prompt(task, constitution, template)

    assert "<promise>TASK_DONE</promise>" in prompt


def test_build_prompt_with_extra_context(tmp_path: Path):
    constitution = _write(tmp_path, "constitution.md", "Principles.")
    template = _write(tmp_path, "Prompt.md", "Base.")
    task = _make_task("Some task")

    prompt = build_prompt(
        task, constitution, template, extra_context="Important context here."
    )

    assert "Important context here." in prompt


def test_build_prompt_missing_constitution(tmp_path: Path):
    template = _write(tmp_path, "Prompt.md", "Base.")
    task = _make_task("Task")

    with pytest.raises(FileNotFoundError):
        build_prompt(task, tmp_path / "missing.md", template)


def test_build_prompt_missing_template(tmp_path: Path):
    constitution = _write(tmp_path, "constitution.md", "Principles.")
    task = _make_task("Task")

    with pytest.raises(FileNotFoundError):
        build_prompt(task, constitution, tmp_path / "missing.md")


def test_build_status_prompt(tmp_path: Path):
    tasks = _write(tmp_path, "tasks.md", "- [ ] Task one\n- [x] Task two\n")
    template = _write(tmp_path, "Prompt.md", "Base prompt.")

    prompt = build_status_prompt(tasks, template)

    assert "Task one" in prompt
    assert "Task two" in prompt
    assert "Base prompt." in prompt
