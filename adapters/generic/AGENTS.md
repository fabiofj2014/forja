# AGENTS.md — [PROJECT_NAME] (Generic Agent)

## Project

[Brief one-line description of what this project is.]

## Reference Files (READ BEFORE IMPLEMENTING)

- `.specify/memory/constitution.md` → Inviolable project principles
- `.specify/spec.md` → Full project requirements
- `.specify/plan.md` → Stack, technical decisions, ADRs
- `.specify/tasks.md` → Source of truth for progress (checklist)

## Agent Protocol

You implement one task at a time. Each session:

1. Read `.specify/tasks.md`, find the first `[ ]` task
2. Read `.specify/memory/constitution.md` for rules
3. Implement the task
4. Run tests: `uv run pytest tests/ -v`
5. If tests pass: mark `[x]`, commit, stop
6. If tests fail: fix, re-run, repeat until pass

## Rules

- One task per session
- Tests must pass before marking done
- No external deps in core/
- Commit format: `[project] Implement: <short_name>`

## Running Forja

```bash
# Start build loop (run automatically, one task per invocation)
AGENT_CLI=your-agent-cli ./core/ralph/ralph.sh

# Start optimize loop
AGENT_CLI=your-agent-cli ./core/autoresearch/autoresearch.sh
```

---

> Copy this file to your project root as `AGENTS.md` and fill in placeholders.
> Remove this footer when done.
