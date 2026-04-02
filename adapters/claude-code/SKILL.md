# Forja Skill — Claude Code

## Overview

Forja integrates GitHub Spec-Kit + Ralph Loop (build) + Autoresearch (optimize) for Claude Code.

## Commands

### Build Phase

```bash
# Start the Ralph Loop (build all tasks)
AGENT_CLI=claude forja build start

# Check progress
forja build status

# See next task
forja build next
```

### Optimize Phase

```bash
# Start the Autoresearch Loop
AGENT_CLI=claude forja optimize start

# Check optimization progress
forja optimize status

# View experiment history
forja optimize history --last 10

# View current baseline
forja optimize baseline
```

## Setup

1. Copy `.specify/` artifacts from `prompts/templates/` and fill in your project details
2. Review `tasks.md` before running
3. Run `AGENT_CLI=claude forja build start`

## Skill Trigger

Use this skill when:
- User says "start Ralph" or "run the build loop"
- User asks to "start optimizing" or "run autoresearch"
- User asks for `forja build status` or `forja optimize status`
