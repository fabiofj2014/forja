# CLAUDE.md — [PROJECT_NAME]

## Project

[Brief one-line description of what this project is.]

## Reference Files (READ BEFORE IMPLEMENTING)

- `.specify/memory/constitution.md` → Inviolable project principles
- `.specify/spec.md` → Full project requirements
- `.specify/plan.md` → Stack, technical decisions, ADRs
- `.specify/tasks.md` → Source of truth for progress (checklist)

## Stack

- **Language:** [e.g., Python 3.11+]
- **Core deps:** [e.g., Zero — stdlib only]
- **Tests:** pytest
- **Package manager:** uv
- **Linting:** ruff

## Agent Rules

### Required
1. **Read constitution.md** before any implementation
2. **One task per session** — never implement multiple tasks at once
3. **Tests must pass** before marking [x] in tasks.md
4. **Atomic commits:** `[project] Implement: <short_task_name>`
5. **If blocked** → add `[BLOCKED]` to tasks.md with reason and skip to next
6. **No external dependencies** in core/ — stdlib only

### Code Style
- Type hints on all public functions
- Docstrings on all public classes and methods
- Descriptive variable names in English
- Short functions — max ~40 lines, extract if longer
- No god objects — single responsibility
- Errors handled with typed exceptions, never silenced
- Paths always via pathlib, never string concatenation

## Useful Commands

```bash
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Check build status
forja build status

# Start Ralph Loop
AGENT_CLI=claude forja build start
```

---

> Copy this file to your project root as `CLAUDE.md` and fill in all placeholders.
> Remove this footer when done.
