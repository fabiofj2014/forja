"""Tests for core/git_manager.py using a temporary git repository."""

import subprocess
from pathlib import Path

import pytest

from core.git_manager import (
    GitError,
    commit,
    get_recent_commits,
    has_changes,
    stall_check,
)


def _init_repo(path: Path) -> None:
    """Initialize a git repo with a base commit."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True, check=True)
    (path / "init.txt").write_text("init", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "chore: init"], cwd=path, capture_output=True, check=True)


def test_has_changes_false_on_clean_repo(tmp_path: Path):
    _init_repo(tmp_path)
    assert has_changes(tmp_path) is False


def test_has_changes_true_after_modification(tmp_path: Path):
    _init_repo(tmp_path)
    (tmp_path / "new.txt").write_text("new file", encoding="utf-8")
    assert has_changes(tmp_path) is True


def test_commit_creates_commit(tmp_path: Path):
    _init_repo(tmp_path)
    (tmp_path / "feature.txt").write_text("feature", encoding="utf-8")
    sha = commit(tmp_path, "feat: add feature")
    assert len(sha) > 0
    assert not has_changes(tmp_path)


def test_commit_nothing_to_commit_raises(tmp_path: Path):
    _init_repo(tmp_path)
    with pytest.raises(GitError, match="Nothing to commit"):
        commit(tmp_path, "empty commit")


def test_get_recent_commits(tmp_path: Path):
    _init_repo(tmp_path)
    for i in range(3):
        (tmp_path / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")
        commit(tmp_path, f"feat: add file{i}")

    recent = get_recent_commits(tmp_path, n=3)
    assert len(recent) == 3
    assert "feat: add file2" in recent[0]


def test_stall_check_not_stalled(tmp_path: Path):
    _init_repo(tmp_path)
    for i in range(3):
        (tmp_path / f"task{i}.txt").write_text(f"task {i}", encoding="utf-8")
        commit(tmp_path, f"[forja] Implement: task{i}")

    assert stall_check(tmp_path, stall_limit=3, marker="[forja]") is False


def test_stall_check_stalled(tmp_path: Path):
    _init_repo(tmp_path)
    for i in range(3):
        (tmp_path / f"other{i}.txt").write_text(f"other {i}", encoding="utf-8")
        commit(tmp_path, f"chore: other{i}")

    assert stall_check(tmp_path, stall_limit=3, marker="[forja]") is True
