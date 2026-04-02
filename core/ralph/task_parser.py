"""Parse and update tasks.md markdown checklists for the Ralph Loop."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    """A single task entry from tasks.md.

    Attributes:
        text: The task description (without checkbox).
        status: 'pending', 'done', or 'blocked'.
        line_index: Line number (0-based) in the original file.
    """

    text: str
    status: str
    line_index: int


_PENDING_RE = re.compile(r"^- \[ \] (.+)$")
_DONE_RE = re.compile(r"^- \[x\] (.+)$", re.IGNORECASE)
_BLOCKED_RE = re.compile(r"^- \[BLOCKED\] (.+)$", re.IGNORECASE)


def parse_tasks(tasks_file: Path) -> list[Task]:
    """Parse all tasks from a tasks.md file.

    Args:
        tasks_file: Path to the tasks.md file.

    Returns:
        List of Task objects in file order.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    content = tasks_file.read_text(encoding="utf-8")
    tasks: list[Task] = []

    for i, line in enumerate(content.splitlines()):
        if m := _PENDING_RE.match(line):
            tasks.append(Task(text=m.group(1), status="pending", line_index=i))
        elif m := _DONE_RE.match(line):
            tasks.append(Task(text=m.group(1), status="done", line_index=i))
        elif m := _BLOCKED_RE.match(line):
            tasks.append(Task(text=m.group(1), status="blocked", line_index=i))

    return tasks


def next_pending(tasks_file: Path) -> Task | None:
    """Return the first pending task, or None if all are done/blocked.

    Args:
        tasks_file: Path to the tasks.md file.

    Returns:
        The first Task with status 'pending', or None.
    """
    for task in parse_tasks(tasks_file):
        if task.status == "pending":
            return task
    return None


def _update_line(tasks_file: Path, line_index: int, new_line: str) -> None:
    """Replace a specific line in the tasks file."""
    lines = tasks_file.read_text(encoding="utf-8").splitlines()
    lines[line_index] = new_line
    tasks_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mark_done(tasks_file: Path, task: Task) -> None:
    """Mark a task as done ([x]) in the tasks file.

    Args:
        tasks_file: Path to the tasks.md file.
        task: The task to mark as done.
    """
    _update_line(tasks_file, task.line_index, f"- [x] {task.text}")


def mark_blocked(tasks_file: Path, task: Task, reason: str = "") -> None:
    """Mark a task as blocked in the tasks file.

    Args:
        tasks_file: Path to the tasks.md file.
        task: The task to mark as blocked.
        reason: Optional reason for the block.
    """
    suffix = f" — {reason}" if reason else ""
    _update_line(tasks_file, task.line_index, f"- [BLOCKED] {task.text}{suffix}")


def all_done(tasks_file: Path) -> bool:
    """Return True if all tasks are done or blocked (none pending).

    Args:
        tasks_file: Path to the tasks.md file.

    Returns:
        True if there are no pending tasks.
    """
    return next_pending(tasks_file) is None
