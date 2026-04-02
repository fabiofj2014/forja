# Phase 1 — Build (Ralph Loop)

## Overview

The Ralph Loop executes tasks from `tasks.md` one at a time. Each iteration:

1. Find next `[ ]` task
2. Invoke agent with a built prompt
3. Verify tests pass
4. Mark `[x]`, commit, repeat

## Setup

### 1. Prepare `.specify/`

```
.specify/
├── memory/
│   └── constitution.md    ← inviolable rules
├── spec.md
├── plan.md
└── tasks.md               ← checklist of atomic tasks
```

### 2. tasks.md format

```markdown
# Tasks

## Phase 1

- [ ] Create config.py with project paths
- [ ] Create utils.py with file helpers
- [x] Already done task
- [BLOCKED] Stuck task — waiting on dependency
```

### 3. Run

```bash
# With CLI
AGENT_CLI=claude forja build start

# With shell script directly
AGENT_CLI=claude ./core/ralph/ralph.sh

# With generic wrapper (any agent)
AGENT_CLI=opencode ./adapters/generic/run.sh build
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `AGENT_CLI` | `claude` | Agent to use |
| `MAX_ITERATIONS` | `50` | Max loop iterations |
| `STALL_LIMIT` | `3` | Iterations without progress before abort |

## Stall Detection

After `STALL_LIMIT` consecutive iterations where the agent makes no changes, the loop:
1. Marks the current task as `[BLOCKED]`
2. Exits with code 2

## Monitoring

```bash
# Check progress
forja build status

# See next task
forja build next

# View logs
ls logs/build/
tail -f logs/build/iter_0001.log
```

## Outcomes

| Exit Code | Meaning |
|---|---|
| 0 | ALL_TASKS_DONE |
| 1 | MAX_ITERATIONS reached |
| 2 | STALLED |
