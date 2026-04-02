# Autoresearch Program — [PROJECT_NAME]

## Objective

Optimize the following metric:

- **Metric key:** `[METRIC_KEY]` (e.g., `val_bpb`, `accuracy`, `latency_ms`)
- **Direction:** `[lower|higher]` (lower = smaller is better, higher = larger is better)
- **Target:** [Optional: e.g., "below 1.5" or "above 0.95"]

## Benchmark Command

```bash
[COMMAND_TO_RUN_BENCHMARK]
# e.g.: uv run python train.py --eval-only
# The command must write the metric to .autoresearch/metrics.json
```

## Constraints

- [Constraint 1: e.g., "Do not change the model architecture"]
- [Constraint 2: e.g., "Batch size must remain 32"]
- [Constraint 3: e.g., "Changes must not increase runtime by more than 10%"]

## Promising Directions

> Suggestions for where to look for improvements (update as experiments complete):

- [ ] [Direction 1: e.g., "Try different learning rate schedules"]
- [ ] [Direction 2: e.g., "Experiment with gradient clipping values"]
- [ ] [Direction 3: e.g., "Try different activation functions"]

## Anti-Patterns

> Things that have been tried and don't work:

- (None yet — update as experiments fail)

---

> Copy this template to `prompts/optimize/program.md` and fill in all placeholders.
> Remove this footer line when done.
