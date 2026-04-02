# FAQ — Forja

## General

**Q: What's the difference between Ralph Loop and Autoresearch?**

Ralph Loop (Phase 1) builds a project from a task list. It's for greenfield development. Autoresearch (Phase 2) optimizes an existing metric iteratively. Use Ralph first, then Autoresearch.

**Q: Do I need Spec-Kit to use Forja?**

No. Spec-Kit generates the `.specify/` artifacts, but you can create `constitution.md`, `spec.md`, `plan.md`, and `tasks.md` manually. Templates are in `prompts/templates/`.

**Q: Which agents does Forja support?**

Any agent with a `--print <prompt>` interface: Claude Code, OpenCode, Codex CLI, Amp, Aider. Set `AGENT_CLI` to the binary name.

## Build Phase

**Q: The loop marked a task [BLOCKED]. What happened?**

After `STALL_LIMIT` (default 3) consecutive iterations without any code changes, the loop marks the current task blocked and stops. Check `logs/build/` for details and fix the task manually.

**Q: Can I resume after a crash?**

Yes. Just run `forja build start` again. The loop reads `tasks.md` and picks up from the first `[ ]` task.

**Q: How do I skip a task?**

Change `[ ]` to `[BLOCKED] <task> — skipped manually` in `tasks.md`, then run again.

## Optimize Phase

**Q: The Autoresearch loop keeps reverting changes. Why?**

The metric isn't improving. Check `state/experiments.json` to see what's been tried. Update `program.md` with better directions or constraints.

**Q: What format should `.autoresearch/metrics.json` be?**

```json
{ "your_metric_key": 1.234 }
```

Your benchmark script must write this file after each run.

**Q: How do I set a new baseline after manually improving the code?**

```bash
forja optimize baseline --capture --metrics-file .autoresearch/metrics.json
```

## Technical

**Q: Why zero external dependencies in `core/`?**

Forja must work in any environment without a complex install. Only adapters (MCP server, OpenCode plugin) have deps.

**Q: Can I run both loops simultaneously?**

No. They share the git working tree. Run sequentially: finish build, then optimize.

**Q: Where are the logs?**

- Build: `logs/build/iter_NNNN.log`
- Optimize: `logs/optimize/exp_NNNN.log`
