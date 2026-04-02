# Spec — Forja

## Visão Geral

Plugin instalável que orquestra duas fases de desenvolvimento automatizado:

1. **Build (Ralph Loop):** lê tasks de um `tasks.md`, executa cada uma numa sessão limpa de agente, testa, commita, repete até `ALL_TASKS_DONE`.
2. **Optimize (Autoresearch Loop):** lê um `program.md` com métrica alvo, experimenta mudanças no código, mede resultado, mantém ou descarta, commita, repete.

## Componentes

### Core (`core/`)

#### Ralph Loop (`core/ralph/`)
- **ralph.sh** — Script bash principal. Lê `AGENT_CLI`, invoca o agente em loop, monitora progresso.
- **loop.py** — Lógica Python do loop: ler próxima task, construir prompt, invocar agente, verificar resultado, marcar done.
- **task_parser.py** — Parse de `tasks.md` (formato markdown checklist). Extrai tasks pendentes, em progresso, e concluídas.
- **prompt_builder.py** — Monta o prompt para o agente com: contexto do projeto, task atual, regras de constitution, arquivos relevantes.

#### Autoresearch Loop (`core/autoresearch/`)
- **autoresearch.sh** — Script bash principal. Lê `AGENT_CLI`, invoca o agente em loop de experimentação.
- **loop.py** — Lógica Python: ler baseline, propor experimento, executar, medir, comparar, decidir manter/descartar.
- **experiment_tracker.py** — Registra cada experimento (hipótese, mudanças, métrica antes/depois, decisão).
- **baseline_manager.py** — Gerencia a baseline atual (snapshot de métricas de referência).

#### Utilitários Core
- **config.py** — Paths do projeto, defaults, leitura de env vars. Tudo relativo ao project root.
- **utils.py** — Leitura de arquivos markdown, parsing de seções, helpers de filesystem.
- **git_manager.py** — Commits atômicos, diff check (houve mudança?), stall detection (N iterações sem diff).
- **logger.py** — Logging estruturado com timestamp, iteração, e contexto.
- **metrics.py** — Leitura e comparação de métricas (suporta `lower` e `higher` como direção).
- **cli.py** — Entry point: `forja build start|status|next` e `forja optimize start|status|history|baseline`.

### Adapters (`adapters/`)

#### Claude Code (`adapters/claude-code/`)
- `SKILL.md` — Skill do plugin para Claude Code
- `plugin.json` — Metadata do plugin
- `hooks/` — Hooks de ciclo de vida (pre-task, post-task, on-stall)
- `CLAUDE.md` — Template de CLAUDE.md injetado no projeto alvo

#### OpenCode (`adapters/opencode/`)
- Plugin TypeScript com hooks `session.compacting`
- Integração nativa com o sistema de hooks do OpenCode

#### Codex MCP (`adapters/codex-mcp/`)
- `AGENTS.md` — Template para Codex CLI
- Expose tools via MCP protocol

#### Generic (`adapters/generic/`)
- `AGENTS.md` — Template genérico
- `run.sh` — Wrapper que funciona com qualquer agente que aceite prompts

### MCP Server (`mcp/`)
- Servidor MCP unificado (Python + FastAPI + Uvicorn)
- Tools expostas: `build_start`, `build_status`, `build_next`, `optimize_start`, `optimize_status`, `optimize_history`, `optimize_baseline`
- Permite integração com qualquer cliente MCP

### Prompts (`prompts/`)
- `build/Prompt.md` — Instrução mestre do Ralph (o que o agente recebe a cada iteração)
- `optimize/program.md` — Instrução mestre do Autoresearch (objetivo, métrica, constraints)
- `templates/` — Templates de constitution e variantes de program.md

### State (`state/`)
- JSONs de progresso do Ralph (iteração atual, tasks done, stall count)
- JSONs de experimentos do Autoresearch (histórico, baseline, melhor resultado)

### Logs (`logs/`)
- `build/` — Log por iteração do Ralph (timestamp, task, resultado, duração)
- `optimize/` — Log por experimento do Autoresearch (hipótese, diff, métrica, decisão)

## Fluxo de Execução

### Fase 1 — Build (Ralph Loop)

```
1. Usuário prepara .specify/ (constitution, spec, plan, tasks)
2. `forja build start` ou `./core/ralph/ralph.sh`
3. Loop:
   a. task_parser lê próxima task pendente de tasks.md
   b. prompt_builder monta prompt com task + constitution + contexto
   c. Agente (via AGENT_CLI) executa numa sessão limpa
   d. Testes rodam (pytest)
   e. Se passou: marca [x], commit atômico, próxima task
   f. Se falhou: retry (max 2), depois marca [BLOCKED]
   g. Stall check: 3 iterações sem novo [x] → abort
4. ALL_TASKS_DONE ou STALLED
```

### Fase 2 — Optimize (Autoresearch Loop)

```
1. Usuário prepara program.md (métrica alvo, constraints)
2. `forja optimize start` ou `./core/autoresearch/autoresearch.sh`
3. baseline_manager captura métrica atual
4. Loop:
   a. Agente lê program.md + histórico de experimentos
   b. Propõe mudança (hipótese + diff)
   c. Executa mudança, roda benchmark
   d. Compara com baseline
   e. Se melhorou: commit, atualiza baseline
   f. Se não: revert, registra no histórico
   g. Stall check: 3 experimentos sem melhoria → abort
5. MAX_EXPERIMENTS atingido ou STALLED
```

## Variáveis de Ambiente

| Variável | Default | Descrição |
|---|---|---|
| `AGENT_CLI` | `claude` | CLI do agente (claude, opencode, codex, amp, aider) |
| `MAX_ITERATIONS` | `50` | Máximo de iterações do Ralph |
| `MAX_EXPERIMENTS` | `100` | Máximo de experimentos do Autoresearch |
| `EXPERIMENT_TIMEOUT` | `300` | Timeout por experimento em segundos |
| `STALL_LIMIT` | `3` | Iterações sem progresso antes de abortar |
| `METRIC_KEY` | `val_bpb` | Métrica a otimizar |
| `METRIC_DIRECTION` | `lower` | `lower` = menor é melhor, `higher` = maior é melhor |

## Requisitos Não-Funcionais

1. **Instalação:** `uv tool install forja` ou `pip install forja`
2. **Tempo de setup:** < 2 minutos para um projeto novo
3. **Overhead por iteração:** < 5 segundos de processamento do plugin (excluindo tempo do agente)
4. **Recuperação:** se o processo morrer, `forja build start` retoma de onde parou (state em filesystem)
5. **Observabilidade:** cada iteração/experimento gera log estruturado legível
