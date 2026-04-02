"""Tests for core/cli.py — optimize subcommands."""

from pathlib import Path
from unittest.mock import patch

from core.cli import _build_parser


def test_parser_optimize_status():
    parser = _build_parser()
    args = parser.parse_args(["optimize", "status"])
    assert args.command == "optimize"
    assert args.subcommand == "status"


def test_parser_optimize_history():
    parser = _build_parser()
    args = parser.parse_args(["optimize", "history"])
    assert args.command == "optimize"
    assert args.subcommand == "history"
    assert args.last == 0


def test_parser_optimize_history_last():
    parser = _build_parser()
    args = parser.parse_args(["optimize", "history", "--last", "5"])
    assert args.last == 5


def test_parser_optimize_baseline():
    parser = _build_parser()
    args = parser.parse_args(["optimize", "baseline"])
    assert args.subcommand == "baseline"
    assert args.capture is False


def test_parser_optimize_start_defaults():
    parser = _build_parser()
    args = parser.parse_args(["optimize", "start"])
    assert args.subcommand == "start"
    assert isinstance(args.max_experiments, int)
    assert args.max_experiments > 0
    assert args.direction in ("lower", "higher")


def test_parser_optimize_start_custom():
    parser = _build_parser()
    args = parser.parse_args(
        [
            "optimize",
            "start",
            "--agent",
            "opencode",
            "--metric-key",
            "accuracy",
            "--direction",
            "higher",
            "--max-experiments",
            "20",
        ]
    )
    assert args.agent == "opencode"
    assert args.metric_key == "accuracy"
    assert args.direction == "higher"
    assert args.max_experiments == 20


def test_cmd_optimize_status_empty(tmp_path: Path, capsys):
    with patch("core.cli.STATE_DIR", tmp_path / "state"):
        from core.cli import _cmd_optimize_status

        parser = _build_parser()
        args = parser.parse_args(["optimize", "status"])
        ret = _cmd_optimize_status(args)

    assert ret == 0
    captured = capsys.readouterr()
    assert "0 experiments" in captured.out


def test_cmd_optimize_history_empty(tmp_path: Path, capsys):
    with patch("core.cli.STATE_DIR", tmp_path / "state"):
        from core.cli import _cmd_optimize_history

        parser = _build_parser()
        args = parser.parse_args(["optimize", "history"])
        ret = _cmd_optimize_history(args)

    assert ret == 0
    captured = capsys.readouterr()
    assert "No experiments" in captured.out


def test_cmd_optimize_baseline_no_baseline(tmp_path: Path, capsys):
    with patch("core.cli.STATE_DIR", tmp_path / "state"):
        from core.cli import _cmd_optimize_baseline

        parser = _build_parser()
        args = parser.parse_args(["optimize", "baseline"])
        ret = _cmd_optimize_baseline(args)

    assert ret == 0
    captured = capsys.readouterr()
    assert "No baseline" in captured.out
