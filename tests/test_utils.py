"""Tests for core/utils.py."""

from pathlib import Path

import pytest

from core.utils import ensure_dir, parse_markdown_sections, read_file


def test_read_file(tmp_path: Path):
    f = tmp_path / "hello.txt"
    f.write_text("hello world", encoding="utf-8")
    assert read_file(f) == "hello world"


def test_read_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_file(tmp_path / "nonexistent.txt")


def test_parse_markdown_sections_basic():
    content = "## Alpha\nfoo bar\n## Beta\nbaz qux"
    sections = parse_markdown_sections(content)
    assert sections["Alpha"] == "foo bar"
    assert sections["Beta"] == "baz qux"


def test_parse_markdown_sections_empty():
    assert parse_markdown_sections("") == {}


def test_parse_markdown_sections_no_headings():
    sections = parse_markdown_sections("just some text\nno headings here")
    assert sections == {}


def test_parse_markdown_sections_multiline():
    content = "## Section\nline one\nline two\nline three"
    sections = parse_markdown_sections(content)
    assert sections["Section"] == "line one\nline two\nline three"


def test_ensure_dir_creates(tmp_path: Path):
    new_dir = tmp_path / "a" / "b" / "c"
    result = ensure_dir(new_dir)
    assert new_dir.is_dir()
    assert result == new_dir


def test_ensure_dir_existing(tmp_path: Path):
    ensure_dir(tmp_path)
    ensure_dir(tmp_path)  # Should not raise
    assert tmp_path.is_dir()
