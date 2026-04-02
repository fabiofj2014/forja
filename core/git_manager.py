"""Git operations for Forja: atomic commits, diff checks, stall detection."""

import subprocess
from pathlib import Path


class GitError(Exception):
    """Raised when a git operation fails."""


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result.

    Args:
        args: Command arguments (without 'git' prefix).
        cwd: Working directory for the command.

    Returns:
        CompletedProcess with stdout/stderr captured.

    Raises:
        GitError: If the command returns a non-zero exit code.
    """
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def has_changes(repo_path: Path) -> bool:
    """Check whether the working tree has uncommitted changes.

    Args:
        repo_path: Root of the git repository.

    Returns:
        True if there are staged or unstaged changes, False otherwise.
    """
    result = _run(["status", "--porcelain"], cwd=repo_path)
    return bool(result.stdout.strip())


def commit(repo_path: Path, message: str, add_all: bool = True) -> str:
    """Stage all changes and create a commit.

    Args:
        repo_path: Root of the git repository.
        message: Commit message.
        add_all: If True, run 'git add -A' before committing.

    Returns:
        The new commit SHA (short).

    Raises:
        GitError: If there is nothing to commit or the commit fails.
    """
    if add_all:
        _run(["add", "-A"], cwd=repo_path)

    if not has_changes(repo_path):
        # Check staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo_path,
            capture_output=True,
        )
        if result.returncode == 0:
            raise GitError("Nothing to commit")

    _run(["commit", "-m", message], cwd=repo_path)
    sha_result = _run(["rev-parse", "--short", "HEAD"], cwd=repo_path)
    return sha_result.stdout.strip()


def get_recent_commits(repo_path: Path, n: int = 10) -> list[str]:
    """Return the last N commit messages.

    Args:
        repo_path: Root of the git repository.
        n: Number of commits to return.

    Returns:
        List of commit messages, most recent first.
    """
    result = _run(["log", f"-{n}", "--pretty=format:%s"], cwd=repo_path)
    lines = result.stdout.strip().splitlines()
    return [line for line in lines if line]


def stall_check(repo_path: Path, stall_limit: int, marker: str) -> bool:
    """Detect whether the loop is stalled (no commits with marker in last N commits).

    Args:
        repo_path: Root of the git repository.
        stall_limit: Number of recent commits to check.
        marker: String that must appear in at least one recent commit message.

    Returns:
        True if stalled (no matching commit found), False if progressing.
    """
    recent = get_recent_commits(repo_path, n=stall_limit)
    return not any(marker in msg for msg in recent)
