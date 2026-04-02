# Adapters — Forja

Forja works with any agent that runs shell commands. Each adapter provides agent-specific integration.

## Claude Code (`adapters/claude-code/`)

| File | Purpose |
|---|---|
| `SKILL.md` | Skill definition for Claude Code |
| `plugin.json` | Plugin metadata |
| `hooks/pre-task.sh` | Runs before each task iteration |
| `hooks/post-task.sh` | Runs after each task (checks tests, reports progress) |
| `CLAUDE.md` | Template for your project's CLAUDE.md |

**Usage:**
```bash
AGENT_CLI=claude forja build start
```

## OpenCode (`adapters/opencode/`)

TypeScript plugin with `session.compacting` hook. When OpenCode compacts its context window, the hook injects current build status.

**Install:**
Copy `spec-kit-loop.ts` to your OpenCode plugins directory.

**Usage:**
```bash
AGENT_CLI=opencode forja build start
```

## Codex CLI (`adapters/codex-mcp/`)

Template `AGENTS.md` for Codex CLI projects.

**Usage:**
Copy `AGENTS.md` to your project root, then:
```bash
AGENT_CLI=codex forja build start
```

## Generic (`adapters/generic/`)

Works with any agent that accepts `--print <prompt>`:

```bash
# Wrapper script
AGENT_CLI=amp ./adapters/generic/run.sh build
AGENT_CLI=aider ./adapters/generic/run.sh optimize
```

## Adding a New Adapter

1. Create `adapters/<agent-name>/`
2. Add an `AGENTS.md` or `CLAUDE.md` template
3. If the agent has a plugin system, add the integration file
4. Test with: `AGENT_CLI=<agent> forja build start`

The only requirement: `AGENT_CLI` must be a binary that accepts:
```bash
<agent> --print "<prompt text>"
```
