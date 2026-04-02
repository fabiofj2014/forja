# CLAUDE.md

## Projeto

**Forja** 🔥 — Plugin que integra GitHub Spec-Kit + Ralph Wiggum Loop (build) + Autoresearch pattern (optimize) num pacote instalável para Claude Code, OpenCode, Codex CLI e qualquer agente shell.

- **Repo:** https://github.com/fabiofj2014/forja
- **Autor:** Fabio FJ
- **Licença:** MIT

## Arquivos de Referência (LEIA SEMPRE antes de implementar)

- `.specify/memory/constitution.md` → Princípios invioláveis do projeto
- `.specify/spec.md` → Requisitos completos do plugin
- `.specify/plan.md` → Stack, decisões técnicas, ADRs
- `.specify/tasks.md` → Source of truth do progresso (checklist)

## Stack

- **Linguagem:** Python 3.11+ (core), Bash (scripts de loop), TypeScript (adapter OpenCode)
- **Dependências core:** Zero — apenas stdlib (pathlib, subprocess, json, re, argparse, datetime, logging)
- **Dependências adapters:** FastAPI + Uvicorn (MCP server), Zod (OpenCode tools)
- **Testes:** pytest
- **Gerenciador:** uv (pyproject.toml)
- **Linting:** ruff
- **Formatação:** ruff format
- **Git:** commits convencionais (feat:, fix:, docs:, chore:, test:, refactor:)

## Estrutura do Projeto

```
forja/
├── core/                        → Motor central
│   ├── ralph/                   → Loop de build (ralph.sh, loop.py, task_parser.py, prompt_builder.py)
│   ├── autoresearch/            → Loop de optimize (autoresearch.sh, loop.py, experiment_tracker.py, baseline_manager.py)
│   ├── config.py                → Paths, defaults, env vars
│   ├── utils.py                 → Leitura de arquivos, parsing markdown
│   ├── git_manager.py           → Commits atômicos, diff check, stall detection
│   ├── logger.py                → Logging estruturado
│   ├── metrics.py               → Leitura/comparação de métricas
│   └── cli.py                   → Entry point: forja build|optimize|status
│
├── adapters/
│   ├── claude-code/             → SKILL.md + plugin.json + hooks + CLAUDE.md template
│   ├── opencode/                → Plugin TS com hooks session.compacting
│   ├── codex-mcp/               → AGENTS.md template
│   └── generic/                 → AGENTS.md + run.sh wrapper
│
├── mcp/                         → MCP server unificado (Python)
├── prompts/                     → Prompt.md (build), program.md (optimize), templates
├── state/                       → Runtime state (JSONs de progresso, experimentos)
├── logs/                        → Logs por iteração/experimento
├── tests/                       → Testes pytest
└── docs/                        → Documentação
```

## Regras para o Agente

### Obrigatórias
1. **Ler constitution.md** antes de qualquer implementação
2. **Uma tarefa por sessão** — nunca implementar múltiplas tasks de uma vez
3. **Testes devem passar** antes de marcar [x] no tasks.md
4. **Commits atômicos:** `[forja] Implement: <nome_curto_da_tarefa>`
5. **Se bloqueado** → adicionar `[BLOCKED]` no tasks.md com motivo e pular pra próxima
6. **Zero dependências externas** no core/ — apenas stdlib Python
7. **Não modificar** Prompt.md ou program.md templates sem instrução explícita

### Estilo de Código
- Type hints em todas as funções públicas
- Docstrings em todas as classes e métodos públicos
- Nomes de variáveis descritivos em inglês
- Funções curtas — max ~40 linhas, extrair se passar
- Sem classes god object — responsabilidade única
- Erros tratados com exceções tipadas, nunca silenciados
- Paths sempre via pathlib, nunca string concatenation
- Subprocess sempre com capture_output=True e check de returncode

### Testes
- pytest em `tests/` espelhando a estrutura de `core/`
- Cada parser (task_parser, experiment_tracker) precisa de testes
- git_manager: testar com repo temporário (tmp_path fixture)
- Não precisa de mock complexo — preferir testes de integração leves
- Rodar com: `uv run pytest tests/ -v`

### Scripts Shell (ralph.sh, autoresearch.sh)
- Sempre `set -euo pipefail` no topo
- Variáveis de ambiente com defaults via `${VAR:-default}`
- Funções nomeadas para cada responsabilidade
- Banner de status no início (agente, tarefas restantes, max iterações)
- Stall detection: abortar após 3 iterações sem progresso
- Logs timestamped em `logs/build/` ou `logs/optimize/`

## Variáveis de Ambiente

| Variável | Default | Uso |
|---|---|---|
| `AGENT_CLI` | `claude` | Agente a usar (claude, opencode, codex, amp, aider) |
| `MAX_ITERATIONS` | `50` | Max voltas do Ralph |
| `MAX_EXPERIMENTS` | `100` | Max experimentos do Autoresearch |
| `EXPERIMENT_TIMEOUT` | `300` | Timeout por experimento (segundos) |
| `STALL_LIMIT` | `3` | Iterações sem progresso antes de abortar |
| `METRIC_KEY` | `val_bpb` | Métrica a otimizar (Autoresearch) |
| `METRIC_DIRECTION` | `lower` | lower = menor é melhor, higher = maior é melhor |

## Comandos Úteis

```bash
# Rodar testes
uv run pytest tests/ -v

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Ver status das tasks
forja build status

# Ver próxima tarefa
forja build next

# Iniciar Ralph Loop (Fase 1: Build)
AGENT_CLI=claude forja build start

# Iniciar Autoresearch Loop (Fase 2: Optimize)
AGENT_CLI=claude forja optimize start

# Aliases diretos via shell
AGENT_CLI=claude ./core/ralph/ralph.sh
AGENT_CLI=claude ./core/autoresearch/autoresearch.sh
```

## Fluxo de Trabalho

```
Fase 1 (Build):    Spec-Kit → Ralph Loop → projeto construído, testado, commitado
Fase 2 (Optimize): program.md → Autoresearch Loop → código otimizado + log de experimentos
```

## O que NÃO fazer

- Não usar dependências externas no core (requests, click, rich, etc)
- Não hardcodar paths — sempre relativo ao project root via config.py
- Não implementar mais de uma task por sessão
- Não pular testes
- Não fazer commits com mensagens genéricas ("fix", "update", "wip")
- Não modificar arquivos em `.specify/` exceto tasks.md (marcar [x])
- Não usar `universal-ai-dev-plugin` — o nome é **Forja**
