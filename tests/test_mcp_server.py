"""Tests for mcp/server.py — skipped if FastAPI not installed."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# Skip entire module if FastAPI is not installed
fastapi = pytest.importorskip("fastapi", reason="FastAPI not installed (install with pip install forja[mcp])")
from fastapi.testclient import TestClient  # noqa: E402


def _get_app():
    """Import app after FastAPI check."""
    from mcp.server import app
    return app


def test_health_endpoint():
    client = TestClient(_get_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "project_root" in data


def test_build_status_no_tasks_file(tmp_path: Path):
    with patch("mcp.server.TASKS_FILE", tmp_path / "missing.md"):
        client = TestClient(_get_app())
        resp = client.post("/tools/build_status")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data


def test_build_status_with_tasks(tmp_path: Path):
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text("- [x] Done\n- [ ] Pending\n- [BLOCKED] Stuck\n", encoding="utf-8")

    with patch("mcp.server.TASKS_FILE", tasks_file):
        client = TestClient(_get_app())
        resp = client.post("/tools/build_status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["done"] == 1
        assert data["pending"] == 1
        assert data["blocked"] == 1
        assert data["all_done"] is False


def test_build_next_with_pending(tmp_path: Path):
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text("- [ ] Next task here\n", encoding="utf-8")

    with patch("mcp.server.TASKS_FILE", tasks_file):
        client = TestClient(_get_app())
        resp = client.post("/tools/build_next")
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_task"] == "Next task here"
        assert data["all_done"] is False


def test_build_next_all_done(tmp_path: Path):
    tasks_file = tmp_path / "tasks.md"
    tasks_file.write_text("- [x] Done\n", encoding="utf-8")

    with patch("mcp.server.TASKS_FILE", tasks_file):
        client = TestClient(_get_app())
        resp = client.post("/tools/build_next")
        assert resp.status_code == 200
        data = resp.json()
        assert data["next_task"] is None
        assert data["all_done"] is True


def test_optimize_status_empty(tmp_path: Path):
    with patch("mcp.server.STATE_DIR", tmp_path / "state"):
        client = TestClient(_get_app())
        resp = client.post("/tools/optimize_status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_experiments"] == 0
        assert data["baseline_value"] is None


def test_optimize_history_empty(tmp_path: Path):
    with patch("mcp.server.STATE_DIR", tmp_path / "state"):
        client = TestClient(_get_app())
        resp = client.post("/tools/optimize_history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["experiments"] == []


def test_optimize_baseline_none(tmp_path: Path):
    with patch("mcp.server.STATE_DIR", tmp_path / "state"):
        client = TestClient(_get_app())
        resp = client.post("/tools/optimize_baseline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["baseline"] is None
