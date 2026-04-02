# Architecture — Forja

## Overview

Forja orchestrates AI agents through two phases:

```
Spec-Kit → tasks.md
                    ↓
              Ralph Loop (Build)
              ├── task_parser reads next [ ] task
              ├── prompt_builder constructs prompt
              ├── Agent executes in clean session
              ├── Tests run
              ├── git commit if pass
              └── Repeat until ALL_TASKS_DONE

              Autoresearch Loop (Optimize)
              ├── baseline_manager captures current metric
              ├── Agent proposes + implements change
              ├── Benchmark runs → new metric
              ├── Compare: if improved → commit, else revert
              └── Repeat until STALLED or MAX_EXPERIMENTS
```

## Core Components

### `core/config.py`
Single source of truth for all paths and environment variables. All other modules import from here. No hardcoded paths anywhere.

### `core/git_manager.py`
Atomic commits, stall detection (consecutive iterations without a `[forja]` commit), working tree diff checks. Used by both loops.

### `core/ralph/` — Build Phase
| File | Role |
|---|---|
| `task_parser.py` | Parse `tasks.md`, find next `[ ]`, mark `[x]` or `[BLOCKED]` |
| `prompt_builder.py` | Combine template + task + constitution into agent prompt |
| `loop.py` | Orchestrate iterations: invoke agent, check result, commit |
| `ralph.sh` | Bash entry point with banner, stall detection, fallback |

### `core/autoresearch/` — Optimize Phase
| File | Role |
|---|---|
| `baseline_manager.py` | Save/load the current best metric snapshot |
| `experiment_tracker.py` | Persist experiment history to JSON |
| `loop.py` | Run experiments: invoke agent, measure, commit or revert |
| `autoresearch.sh` | Bash entry point with banner and stall detection |

### `core/cli.py`
Single entry point (`forja`) with two top-level subcommands:
- `forja build start|status|next`
- `forja optimize start|status|history|baseline`

### `mcp/server.py`
FastAPI server (optional dep) exposing the same operations as HTTP tools for MCP clients.

## Data Flow

### Build Phase

```
.specify/tasks.md
    │ (task_parser reads)
    ↓
IterationResult
    │ (prompt_builder builds prompt)
    ↓
Agent CLI (subprocess)
    │ (git diff check)
    ↓
commit() or BLOCKED
    │ (mark [x] in tasks.md)
    ↓
state/ralph_state.json (optional progress state)
logs/build/iter_NNNN.log
```

### Optimize Phase

```
.autoresearch/metrics.json
    │ (baseline_manager captures)
    ↓
state/baseline.json
    │
Agent CLI (subprocess)
    │ (metrics.py reads new value)
    ↓
is_improvement()?
    │ Yes → commit, update baseline
    │ No  → revert (git checkout -- .)
    ↓
state/experiments.json (experiment_tracker logs)
logs/optimize/exp_NNNN.log
```

## Stall Detection

Both loops detect stalls via `consecutive_failures` counter:
- **Ralph:** N consecutive iterations where `has_changes()` is False after agent ran
- **Autoresearch:** N consecutive experiments where `is_improvement()` is False

`STALL_LIMIT=3` by default. Configurable via env var.

## Agent Agnosticism

The loops never know which agent they're talking to. `AGENT_CLI` is just a binary that accepts a `--print <prompt>` argument and writes code to the filesystem. Adapters handle agent-specific integration (hooks, skills, TypeScript plugins).
