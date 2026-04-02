# Constitution — Forja

## Identidade

Forja é um plugin que integra GitHub Spec-Kit + Ralph Wiggum Loop (fase build) + Autoresearch pattern (fase optimize) num pacote instalável para Claude Code, OpenCode, Codex CLI e qualquer agente que rode shell.

## Princípios Invioláveis

### 1. Zero dependências externas no core
O diretório `core/` usa exclusivamente Python stdlib (pathlib, subprocess, json, re, argparse, datetime, logging). Nenhuma biblioteca externa é permitida. Adapters podem ter dependências próprias (FastAPI, Zod, etc).

### 2. Filesystem é a interface universal
Toda comunicação entre componentes acontece via filesystem. `.specify/` para fase build, `.autoresearch/` para fase optimize. Git é o audit trail. Nenhum banco de dados, nenhum serviço externo, nenhum socket.

### 3. Agente-agnóstico por design
Os scripts `ralph.sh` e `autoresearch.sh` não sabem qual agente está rodando. A variável `AGENT_CLI` define o agente. O plugin funciona com qualquer ferramenta que aceite prompts via stdin/arquivo e rode shell.

### 4. Uma tarefa por sessão
O Ralph Loop executa exatamente uma task por sessão de agente. Testa, marca `[x]`, commita, encerra. A próxima sessão pega a próxima task. Nunca duas tasks na mesma sessão.

### 5. Stall detection é obrigatório
Ambos os loops (Ralph e Autoresearch) monitoram progresso. Após 3 iterações consecutivas sem mudança mensurável, o loop aborta automaticamente com status `STALLED`. Nunca rodar infinitamente.

### 6. Commits atômicos e convencionais
Cada unidade de trabalho gera exatamente um commit. Formato: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`. Mensagens descritivas, nunca genéricas ("fix", "update", "wip").

### 7. Testes antes de marcar done
Nenhuma task é marcada `[x]` no `tasks.md` sem que os testes relevantes passem. `uv run pytest tests/ -v` é o gate.

### 8. Não modificar templates sem instrução explícita
`Prompt.md` (build) e `program.md` (optimize) são documentos controlados. Alterações requerem instrução explícita do usuário.

## Restrições Técnicas

| Restrição | Valor |
|---|---|
| Python mínimo | 3.11 |
| Dependências core | Zero (stdlib only) |
| Gerenciador de pacotes | uv |
| Linting | ruff |
| Formatação | ruff format |
| Testes | pytest |
| Max iterações Ralph | 50 (configurável via `MAX_ITERATIONS`) |
| Max experimentos Autoresearch | 100 (configurável via `MAX_EXPERIMENTS`) |
| Stall limit | 3 iterações sem progresso |

## Fronteiras

- Forja **não é** um agente de IA — é uma orquestração que delega a agentes existentes.
- Forja **não implementa** lógica de IA, LLM, ou inferência — apenas invoca CLIs.
- Forja **não gerencia** infraestrutura, deploy, ou CI/CD — é ferramenta de desenvolvimento local.
