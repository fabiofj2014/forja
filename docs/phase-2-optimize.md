# Phase 2 — Optimize (Autoresearch Loop)

## Overview

The Autoresearch Loop runs optimization experiments. Each iteration:

1. Read baseline metric from `state/baseline.json`
2. Invoke agent with `program.md` prompt
3. Agent proposes and implements a change
4. Measure new metric from `.autoresearch/metrics.json`
5. If improved: commit + update baseline
6. If not: revert + log
7. Repeat until stalled or max experiments

## Setup

### 1. Prepare `program.md`

Copy `prompts/templates/program_template.md` to `prompts/optimize/program.md` and fill in:

- Target metric key
- Benchmark command
- Constraints
- Promising directions

### 2. Set up metrics file

Your benchmark must write results to `.autoresearch/metrics.json`:

```json
{
  "val_bpb": 1.234,
  "train_loss": 0.567
}
```

### 3. Run

```bash
AGENT_CLI=claude METRIC_KEY=val_bpb METRIC_DIRECTION=lower forja optimize start

# Or directly
AGENT_CLI=claude ./core/autoresearch/autoresearch.sh
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `AGENT_CLI` | `claude` | Agent to use |
| `METRIC_KEY` | `val_bpb` | Metric to optimize |
| `METRIC_DIRECTION` | `lower` | `lower` = smaller is better |
| `MAX_EXPERIMENTS` | `100` | Max experiments |
| `EXPERIMENT_TIMEOUT` | `300` | Seconds per experiment |
| `STALL_LIMIT` | `3` | Consecutive failures before abort |

## Monitoring

```bash
# Status summary
forja optimize status

# Recent experiments
forja optimize history --last 10

# Current baseline
forja optimize baseline
```

## State Files

| File | Contents |
|---|---|
| `state/baseline.json` | Current best metric snapshot |
| `state/experiments.json` | Full experiment history |
| `logs/optimize/exp_NNNN.log` | Agent output per experiment |
