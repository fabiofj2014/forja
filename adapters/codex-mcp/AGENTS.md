# AGENTS.md — [PROJECT_NAME] (Codex CLI)

## Project

[Brief one-line description of what this project is.]

## Reference Files (READ BEFORE IMPLEMENTING)

- `.specify/memory/constitution.md` → Inviolable project principles
- `.specify/spec.md` → Full project requirements
- `.specify/plan.md` → Stack, technical decisions, ADRs
- `.specify/tasks.md` → Source of truth for progress (checklist)

## Agent Protocol

You are a focused software engineer. Your job is to implement **one task at a time** from `tasks.md`.

### Each Session

1. **Read** `.specify/tasks.md` — find the next `[ ]` task
2. **Read** `.specify/memory/constitution.md` — understand the rules
3. **Implement** the task completely
4. **Test** — run `uv run pytest tests/ -v` and fix all failures
5. **Mark** the task `[x]` in `tasks.md`
6. **Commit** — `git add -A && git commit -m "[project] Implement: <short_name>"`
7. **Stop** — one task per session

### Rules

- Implement **only the current task** — do not jump ahead
- Tests must pass before marking `[x]`
- Zero external dependencies in `core/` — stdlib only
- Type hints on all public functions
- Paths via pathlib, never string concatenation

### If Blocked

If you cannot complete the task:
- Change `[ ]` to `- [BLOCKED] <task> — <reason>` in `tasks.md`
- Commit the updated `tasks.md`
- Stop

## Useful Commands

```bash
# Run tests
uv run pytest tests/ -v

# Check build status
forja build status

# See next task
forja build next
```

---

> Copy this file to your project root as `AGENTS.md` and fill in all placeholders.
> Remove this footer when done.
