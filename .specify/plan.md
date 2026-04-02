# Plan — Forja

## Stack

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Core | Python 3.11+ stdlib | Zero deps, disponível em qualquer ambiente |
| Scripts | Bash (set -euo pipefail) | Universal, sem runtime extra |
| Testes | pytest | Padrão Python, sem config complexa |
| Packaging | uv + pyproject.toml | Rápido, resolve deps, build nativo |
| Linting | ruff | Rápido, substitui flake8+isort+black |
| MCP Server | FastAPI + Uvicorn | Única dep externa, só no adapter |
| OpenCode adapter | TypeScript + Zod | Requisito do OpenCode |
| CI/CD | GitHub Actions | Já configurado no repo |

## Decisões Técnicas (ADRs)

### ADR-001: Filesystem como interface universal
**Decisão:** toda comunicação entre componentes via filesystem (markdown, JSON).
**Motivo:** qualquer agente pode ler/escrever arquivos. Nenhum protocolo proprietário. Git fornece versionamento grátis.
**Consequência:** estado é sempre inspecionável com `cat`/`ls`. Recovery é trivial.

### ADR-002: Shell scripts como orquestradores
**Decisão:** `ralph.sh` e `autoresearch.sh` são os entry points reais. Python faz o parsing/lógica.
**Motivo:** bash é o mínimo denominador comum. O script invoca o agente como subprocesso, o Python processa o resultado.
**Consequência:** o plugin funciona em qualquer sistema com bash + python, sem instalação de runtime adicional.

### ADR-003: Um commit por task/experimento
**Decisão:** cada task completada ou experimento bem-sucedido gera exatamente um commit.
**Motivo:** audit trail limpo. Cada commit é atômico e reversível. Histórico legível.
**Consequência:** `git log` conta a história do projeto. `git revert` desfaz uma task específica.

### ADR-004: Stall detection por diff
**Decisão:** stall é detectado por ausência de `git diff` significativo após N iterações.
**Motivo:** métrica simples e confiável. Se o agente não mudou código, não progrediu.
**Consequência:** evita loops infinitos. `STALL_LIMIT=3` como default.

### ADR-005: CLI unificado via entry point
**Decisão:** `forja` como CLI único com subcommands `build` e `optimize`.
**Motivo:** UX limpa. Um comando para tudo.
**Consequência:** registrado como entry point no pyproject.toml. Funciona após `uv tool install`.

### ADR-006: Prompts são documentos controlados
**Decisão:** `Prompt.md` e `program.md` não são modificados pelo plugin em runtime.
**Motivo:** o usuário controla o que o agente recebe. Alterações automáticas criariam comportamento imprevisível.
**Consequência:** templates fornecidos, mas o usuário é dono do conteúdo.

## Fases de Implementação

### Fase 1 — Foundation (core utils)
config.py, utils.py, logger.py, git_manager.py, metrics.py + testes

### Fase 2 — Ralph Loop (build)
task_parser.py, prompt_builder.py, loop.py, ralph.sh + testes

### Fase 3 — CLI
cli.py com subcommands build (start, status, next) + testes

### Fase 4 — Autoresearch Loop (optimize)
experiment_tracker.py, baseline_manager.py, loop.py, autoresearch.sh + testes

### Fase 5 — CLI optimize
Adicionar subcommands optimize (start, status, history, baseline) ao cli.py

### Fase 6 — Prompts e templates
Prompt.md, program.md, templates de constitution

### Fase 7 — Adapters
claude-code, opencode, codex-mcp, generic

### Fase 8 — MCP Server
Servidor unificado com FastAPI

### Fase 9 — Docs e packaging
quickstart, architecture docs, pyproject.toml finalizado

## Riscos

| Risco | Mitigação |
|---|---|
| Agentes diferentes têm CLIs incompatíveis | Adapter pattern + `AGENT_CLI` abstrai a diferença |
| Stall detection falso positivo | Threshold configurável + log detalhado pra debug |
| Tasks.md parsing frágil | Testes extensivos do task_parser com edge cases |
| Experiments destrutivos | Git revert automático em caso de regressão |
