# Forja 🔥

[![CI](https://github.com/fabiofj2014/forja/actions/workflows/ci.yml/badge.svg)](https://github.com/fabiofj2014/forja/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Instale uma vez. Construa e otimize qualquer projeto com qualquer agente de IA.

Forja é um plugin que orquestra o **Ralph Wiggum Loop** (build) e o **Autoresearch pattern** (optimize) num pacote instalável que funciona com Claude Code, OpenCode, Codex CLI e qualquer agente shell.

---

## Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                         FORJA PIPELINE                          │
├────────────────────┬────────────────────┬───────────────────────┤
│   Spec-Kit         │   Phase 1: Build   │  Phase 2: Optimize    │
│                    │   (Ralph Loop)     │  (Autoresearch)       │
│  constitution.md   │                   │                        │
│  spec.md      ───▶ │  tasks.md  ──┐    │  program.md ──┐       │
│  plan.md           │              ▼    │               ▼        │
│  tasks.md          │  agent runs task  │  agent proposes change │
│                    │  tests pass?      │  metric improved?      │
│                    │  ✓ mark [x]       │  ✓ commit              │
│                    │  ✗ retry/block    │  ✗ revert              │
│                    │  repeat until     │  repeat until          │
│                    │  ALL_TASKS_DONE   │  STALLED or MAX        │
└────────────────────┴────────────────────┴───────────────────────┘
```

---

## Instalação

```bash
pip install forja
# ou com uv:
uv tool install forja
```

---

## Quick Start

### Fase 1 — Build

**1. Prepare o `.specify/`** com os 4 artefatos do Spec-Kit:

```
.specify/
├── memory/constitution.md   # princípios invioláveis
├── spec.md                  # requisitos completos
├── plan.md                  # stack e decisões técnicas
└── tasks.md                 # checklist de tasks atômicas
```

Use os templates em [`prompts/templates/`](prompts/templates/) como ponto de partida.

**2. tasks.md** (formato checklist):

```markdown
## Fase 1

- [ ] Criar config.py com paths do projeto
- [ ] Criar utils.py com helpers de filesystem
- [ ] Criar tests/test_config.py
```

**3. Rode o Ralph Loop:**

```bash
AGENT_CLI=claude forja build start
```

O loop executa uma task por vez, testa, commita e repete até `ALL_TASKS_DONE`.

---

### Fase 2 — Optimize

**1. Crie `prompts/optimize/program.md`** com a métrica alvo e constraints.

**2. Configure seu benchmark** para escrever em `.autoresearch/metrics.json`:

```json
{ "val_bpb": 1.234 }
```

**3. Rode o Autoresearch Loop:**

```bash
AGENT_CLI=claude METRIC_KEY=val_bpb METRIC_DIRECTION=lower forja optimize start
```

O loop experimenta mudanças, mede o impacto, commita melhorias e reverte regressões.

---

## CLI

### Build

```bash
forja build start            # inicia o Ralph Loop
forja build status           # done/pending/blocked
forja build next             # próxima task pendente
```

### Optimize

```bash
forja optimize start         # inicia o Autoresearch Loop
forja optimize status        # resumo: experimentos, baseline, melhor resultado
forja optimize history       # histórico de experimentos
forja optimize history --last 10
forja optimize baseline      # baseline atual
forja optimize baseline --capture --metrics-file .autoresearch/metrics.json
```

---

## Variáveis de Ambiente

| Variável | Default | Descrição |
|---|---|---|
| `AGENT_CLI` | `claude` | Agente a usar (`claude`, `opencode`, `codex`, `amp`, `aider`) |
| `MAX_ITERATIONS` | `50` | Máximo de iterações do Ralph Loop |
| `MAX_EXPERIMENTS` | `100` | Máximo de experimentos do Autoresearch |
| `EXPERIMENT_TIMEOUT` | `300` | Timeout por experimento (segundos) |
| `STALL_LIMIT` | `3` | Iterações sem progresso antes de abortar |
| `METRIC_KEY` | `val_bpb` | Métrica a otimizar |
| `METRIC_DIRECTION` | `lower` | `lower` = menor é melhor, `higher` = maior é melhor |

---

## Adapters

Forja funciona com qualquer agente que aceite `--print <prompt>`. Configure via `AGENT_CLI`.

### Claude Code

```bash
AGENT_CLI=claude forja build start
```

Copie [`adapters/claude-code/CLAUDE.md`](adapters/claude-code/CLAUDE.md) para a raiz do seu projeto. O adapter inclui skill, plugin.json e hooks de ciclo de vida.

### OpenCode

```bash
AGENT_CLI=opencode forja build start
```

Plugin TypeScript em [`adapters/opencode/spec-kit-loop.ts`](adapters/opencode/spec-kit-loop.ts) com hook `session.compacting` que injeta o status do build quando o contexto é compactado.

### Codex CLI

```bash
AGENT_CLI=codex forja build start
```

Copie [`adapters/codex-mcp/AGENTS.md`](adapters/codex-mcp/AGENTS.md) para a raiz do seu projeto.

### Generic (qualquer agente)

```bash
AGENT_CLI=amp ./adapters/generic/run.sh build
AGENT_CLI=aider ./adapters/generic/run.sh optimize
```

Qualquer ferramenta que aceite `<agent> --print "<prompt>"`. Veja [`adapters/generic/`](adapters/generic/).

---

## Scripts Shell Diretos

```bash
# Sem o CLI instalado
AGENT_CLI=claude ./core/ralph/ralph.sh          # Phase 1
AGENT_CLI=claude ./core/autoresearch/autoresearch.sh  # Phase 2
```

---

## MCP Server (opcional)

```bash
pip install forja[mcp]
python -m mcp.server --host 127.0.0.1 --port 8765
```

Expõe `build_start`, `build_status`, `build_next`, `optimize_start`, `optimize_status`, `optimize_history`, `optimize_baseline` como tools HTTP. Schema em [`mcp/mcp_schema.json`](mcp/mcp_schema.json).

---

## Estrutura

```
forja/
├── core/
│   ├── ralph/          → task_parser, prompt_builder, loop, ralph.sh
│   ├── autoresearch/   → experiment_tracker, baseline_manager, loop, autoresearch.sh
│   ├── config.py       → paths e env vars
│   ├── git_manager.py  → commits atômicos e stall detection
│   ├── metrics.py      → leitura e comparação de métricas
│   └── cli.py          → entry point: forja build|optimize
├── adapters/
│   ├── claude-code/    → SKILL.md, plugin.json, hooks/, CLAUDE.md template
│   ├── opencode/       → spec-kit-loop.ts
│   ├── codex-mcp/      → AGENTS.md template
│   └── generic/        → AGENTS.md + run.sh
├── mcp/                → MCP server unificado (FastAPI)
├── prompts/
│   ├── build/Prompt.md         → instrução mestre do Ralph
│   ├── optimize/program.md     → instrução mestre do Autoresearch
│   └── templates/              → templates de constitution e program.md
├── state/              → progress JSONs, experiment history
└── logs/               → logs por iteração/experimento
```

---

## Documentação

| Doc | Conteúdo |
|---|---|
| [Quickstart](docs/quickstart.md) | Setup em 5 minutos |
| [Architecture](docs/architecture.md) | Componentes, data flow, decisões |
| [Phase 1 — Build](docs/phase-1-build.md) | Ralph Loop em detalhe |
| [Phase 2 — Optimize](docs/phase-2-optimize.md) | Autoresearch em detalhe |
| [Adapters](docs/adapters.md) | Como integrar com cada agente |
| [FAQ](docs/faq.md) | Perguntas frequentes |

---

## Licença

MIT © [Fabio FJ](https://github.com/fabiofj2014)
