# Tasks — Forja

## Fase 1 — Foundation

- [x] Criar pyproject.toml com metadata, entry point `forja`, deps de dev (pytest, ruff)
- [x] Criar core/__init__.py e core/config.py (PROJECT_ROOT, paths, env vars com defaults)
- [x] Criar core/utils.py (read_file, parse_markdown_sections, ensure_dir)
- [x] Criar core/logger.py (setup_logger com formato timestamped, log por iteração)
- [x] Criar core/git_manager.py (has_changes, commit, get_recent_commits, stall_check)
- [x] Criar core/metrics.py (read_metric, compare_metrics, is_improvement)
- [x] Criar tests/test_config.py
- [x] Criar tests/test_utils.py
- [ ] Criar tests/test_git_manager.py (com tmp_path fixture e repo temporário)
- [ ] Criar tests/test_metrics.py

## Fase 2 — Ralph Loop (Build)

- [ ] Criar core/ralph/__init__.py
- [ ] Criar core/ralph/task_parser.py (parse_tasks, next_pending, mark_done, mark_blocked)
- [ ] Criar core/ralph/prompt_builder.py (build_prompt com task, constitution, contexto)
- [ ] Criar core/ralph/loop.py (run_iteration, run_loop com stall detection)
- [ ] Criar core/ralph/ralph.sh (bash entry point, banner, loop, stall abort)
- [ ] Criar tests/test_task_parser.py (pendentes, concluídas, blocked, edge cases)
- [ ] Criar tests/test_prompt_builder.py
- [ ] Criar tests/test_ralph_loop.py

## Fase 3 — CLI (Build)

- [ ] Criar core/cli.py com argparse (forja build start|status|next)
- [ ] Registrar entry point `forja` no pyproject.toml
- [ ] Criar tests/test_cli.py

## Fase 4 — Autoresearch Loop (Optimize)

- [ ] Criar core/autoresearch/__init__.py
- [ ] Criar core/autoresearch/experiment_tracker.py (log_experiment, get_history, best_result)
- [ ] Criar core/autoresearch/baseline_manager.py (capture_baseline, load_baseline, update_baseline)
- [ ] Criar core/autoresearch/loop.py (run_experiment, run_loop com stall detection)
- [ ] Criar core/autoresearch/autoresearch.sh (bash entry point, banner, loop, stall abort)
- [ ] Criar tests/test_experiment_tracker.py
- [ ] Criar tests/test_baseline_manager.py
- [ ] Criar tests/test_autoresearch_loop.py

## Fase 5 — CLI (Optimize)

- [ ] Adicionar subcommands optimize (start, status, history, baseline) ao cli.py
- [ ] Criar tests/test_cli_optimize.py

## Fase 6 — Prompts e Templates

- [ ] Criar prompts/build/Prompt.md (instrução mestre do Ralph)
- [ ] Criar prompts/optimize/program.md (instrução mestre do Autoresearch)
- [ ] Criar prompts/templates/constitution_template.md
- [ ] Criar prompts/templates/program_template.md

## Fase 7 — Adapters

- [ ] Criar adapters/claude-code/SKILL.md
- [ ] Criar adapters/claude-code/plugin.json
- [ ] Criar adapters/claude-code/hooks/ (pre-task.sh, post-task.sh)
- [ ] Criar adapters/claude-code/CLAUDE.md (template)
- [ ] Criar adapters/opencode/spec-kit-loop.ts
- [ ] Criar adapters/codex-mcp/AGENTS.md (template)
- [ ] Criar adapters/generic/AGENTS.md (template)
- [ ] Criar adapters/generic/run.sh

## Fase 8 — MCP Server

- [ ] Criar mcp/__init__.py
- [ ] Criar mcp/server.py (FastAPI + tools: build_start, build_status, optimize_start, optimize_status, etc)
- [ ] Criar mcp/mcp_schema.json
- [ ] Criar tests/test_mcp_server.py

## Fase 9 — Docs e Packaging

- [ ] Criar docs/quickstart.md
- [ ] Criar docs/architecture.md
- [ ] Criar docs/phase-1-build.md
- [ ] Criar docs/phase-2-optimize.md
- [ ] Criar docs/adapters.md
- [ ] Criar docs/faq.md
- [ ] Finalizar pyproject.toml (classifiers, URLs, readme)
- [ ] Testar instalação via `uv tool install .`
