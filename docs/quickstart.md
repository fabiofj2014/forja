# Quickstart — Forja

Get from zero to running the Ralph Loop in under 5 minutes.

## 1. Install

```bash
pip install forja
# or with uv:
uv tool install forja
```

## 2. Set up your project

```bash
mkdir my-project && cd my-project
git init
```

Copy the templates from Forja:

```bash
# Copy constitution template
mkdir -p .specify/memory
cp $(python -c "import forja; print(forja.__file__.replace('__init__.py',''))") \
   ../prompts/templates/constitution_template.md .specify/memory/constitution.md

# Or just create .specify/memory/constitution.md manually
```

## 3. Generate your spec (with Spec-Kit or manually)

Create these 4 files in `.specify/`:

- `memory/constitution.md` — inviolable principles
- `spec.md` — what you're building
- `plan.md` — stack and technical decisions
- `tasks.md` — atomic task checklist

Example `tasks.md`:

```markdown
# Tasks

## Phase 1

- [ ] Create main.py with hello world
- [ ] Add tests in tests/test_main.py
- [ ] Configure pyproject.toml
```

## 4. Add a CLAUDE.md

Copy `adapters/claude-code/CLAUDE.md` to your project root and fill in the placeholders.

## 5. Run Ralph Loop

```bash
AGENT_CLI=claude forja build start
```

Watch tasks get implemented one by one.

## 6. Check progress

```bash
forja build status
forja build next
```

## Phase 2: Optimize (optional)

Once the project is built, create a `prompts/optimize/program.md` and run:

```bash
AGENT_CLI=claude forja optimize start
```

See [phase-2-optimize.md](phase-2-optimize.md) for details.
