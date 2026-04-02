# GitHub Actions CI/CD Design

## Summary

Two GitHub Actions workflows for the Forja project:

1. **CI** (`ci.yml`) — runs lint and tests on every push and pull request
2. **Release** (`release.yml`) — runs CI then publishes to PyPI when a version tag is pushed

## Workflow 1: CI (`ci.yml`)

**Triggers:**
- `push` to any branch
- `pull_request` targeting `main`

**Jobs:**

### `lint`
- **Runner:** `ubuntu-latest`
- **Steps:** checkout, setup uv (with cache), `uv run ruff check .`, `uv run ruff format --check .`

### `test`
- **Runner:** `ubuntu-latest`
- **Depends on:** `lint`
- **Steps:** checkout, setup uv (with cache), `uv run pytest tests/ -v`

**Python version:** 3.11 only (minimum required).

## Workflow 2: Release (`release.yml`)

**Triggers:**
- `push` of tags matching `v*` (e.g., `v0.1.0`)

**Jobs:**

### `ci`
- Same lint + test steps as `ci.yml` (inlined, not reusable workflow — keeps it simple)

### `publish`
- **Runner:** `ubuntu-latest`
- **Depends on:** `ci`
- **Environment:** `pypi` (GitHub environment for trusted publishing)
- **Permissions:** `id-token: write`, `contents: read`
- **Steps:** checkout, setup uv, `uv build`, publish to PyPI via `pypa/gh-action-pypi-publish@release/v1`

## Prerequisites

1. **PyPI Trusted Publishing:** register `fabiofj2014/forja` as a trusted publisher on pypi.org (one-time setup, no secrets needed in GitHub)
2. **GitHub Environment:** create a `pypi` environment in the repo's Settings > Environments

## Design Decisions

- **Two separate files** over one monolithic workflow: clearer separation, easier to debug
- **No matrix build:** project targets Python 3.11+ only, testing one version is sufficient
- **uv over pip:** matches the project's package manager (pyproject.toml + uv)
- **Trusted Publishing over API tokens:** more secure, no secrets to rotate
- **lint before test:** fast feedback, no point running tests if code doesn't pass lint
