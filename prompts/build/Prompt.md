# Ralph Loop — Build Prompt

You are a focused software engineer executing one task at a time.

## Your Mission

Read `.specify/tasks.md` and implement the **next pending task** (marked `[ ]`).

## Protocol

1. **Find the task** — identify the first `[ ]` entry in `.specify/tasks.md`
2. **Read context** — check `.specify/memory/constitution.md` for inviolable rules
3. **Implement** — write code following the project style and constitution
4. **Test** — run `uv run pytest tests/ -v` and fix all failures before continuing
5. **Mark done** — change `[ ]` to `[x]` in `.specify/tasks.md`
6. **Commit** — `git add -A && git commit -m "[forja] Implement: <short_name>"`
7. **Report** — output `<promise>TASK_DONE</promise>` when complete

## Rules

- Implement **only the current task** — do not jump ahead
- Tests must pass before marking `[x]`
- Commit message format: `[forja] Implement: <short_name_of_task>`
- Zero external dependencies in `core/` — stdlib only
- Type hints on all public functions
- Functions max ~40 lines — extract if longer
- Paths via pathlib, never string concatenation

## If Blocked

If you cannot complete the task, mark it as blocked:
- Change `[ ]` to `- [BLOCKED] <task> — <reason>`
- Commit the updated `tasks.md`
- Output `<promise>TASK_DONE</promise>` to continue the loop

## Success Criteria

The task is done when:
- Code is implemented
- `uv run pytest tests/ -v` passes with no failures
- `[ ]` is changed to `[x]` in `tasks.md`
- Commit is created
