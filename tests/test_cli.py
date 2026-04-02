"""Tests for core/cli.py — build subcommands."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.cli import _build_parser


def test_parser_build_status_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["build", "status"])
    assert args.command == "build"
    assert args.subcommand == "status"


def test_parser_build_next_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["build", "next"])
    assert args.command == "build"
    assert args.subcommand == "next"


def test_parser_build_start_defaults():
    parser = _build_parser()
    args = parser.parse_args(["build", "start"])
    assert args.command == "build"
    assert args.subcommand == "start"
    assert isinstance(args.max_iterations, int)
    assert args.max_iterations > 0
    assert isinstance(args.stall_limit, int)


def test_parser_build_start_custom_agent():
    parser = _build_parser()
    args = parser.parse_args(["build", "start", "--agent", "opencode"])
    assert args.agent == "opencode"


def test_parser_build_start_custom_iterations():
    parser = _build_parser()
    args = parser.parse_args(["build", "start", "--max-iterations", "10"])
    assert args.max_iterations == 10


def test_cmd_build_status(tmp_path: Path):
    """build status prints done/pending/blocked counts."""
    tasks_content = "- [x] Done\n- [ ] Pending\n- [BLOCKED] Stuck\n"
    tasks_file = tmp_path / ".specify" / "tasks.md"
    tasks_file.parent.mkdir(parents=True)
    tasks_file.write_text(tasks_content, encoding="utf-8")

    with patch("core.cli.TASKS_FILE", tasks_file):
        from core.cli import _cmd_build_status

        parser = _build_parser()
        args = parser.parse_args(["build", "status"])
        ret = _cmd_build_status(args)

    assert ret == 0


def test_cmd_build_status_missing_file(tmp_path: Path, capsys):
    with patch("core.cli.TASKS_FILE", tmp_path / "missing.md"):
        from core.cli import _cmd_build_status

        parser = _build_parser()
        args = parser.parse_args(["build", "status"])
        ret = _cmd_build_status(args)

    assert ret == 1


def test_cmd_build_next_with_pending(tmp_path: Path, capsys):
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text("- [ ] Next up\n", encoding="utf-8")

    with patch("core.cli.TASKS_FILE", tasks_file):
        from core.cli import _cmd_build_next

        parser = _build_parser()
        args = parser.parse_args(["build", "next"])
        ret = _cmd_build_next(args)

    assert ret == 0
    captured = capsys.readouterr()
    assert "Next up" in captured.out


def test_cmd_build_next_all_done(tmp_path: Path, capsys):
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text("- [x] Done\n", encoding="utf-8")

    with patch("core.cli.TASKS_FILE", tasks_file):
        from core.cli import _cmd_build_next

        parser = _build_parser()
        args = parser.parse_args(["build", "next"])
        ret = _cmd_build_next(args)

    assert ret == 0
    captured = capsys.readouterr()
    assert "all done" in captured.out.lower()
