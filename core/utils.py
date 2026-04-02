"""Filesystem and markdown utilities for Forja."""

from pathlib import Path


def read_file(path: Path) -> str:
    """Read a file and return its contents as a string.

    Args:
        path: Path to the file to read.

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return path.read_text(encoding="utf-8")


def parse_markdown_sections(content: str) -> dict[str, str]:
    """Parse a markdown document into sections by heading.

    Each top-level heading (##) becomes a key, and all content
    until the next heading becomes the value.

    Args:
        content: Markdown content as a string.

    Returns:
        Dict mapping section heading text to section content.
    """
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def ensure_dir(path: Path) -> Path:
    """Create a directory (and parents) if it does not exist.

    Args:
        path: Directory path to create.

    Returns:
        The same path, for chaining.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
