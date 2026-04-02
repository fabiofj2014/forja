"""Project-wide configuration: paths, defaults, and environment variables."""

import os
from pathlib import Path


def _find_project_root() -> Path:
    """Walk up from this file to find the project root (contains pyproject.toml)."""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent


PROJECT_ROOT: Path = _find_project_root()

# Spec-Kit directories
SPECIFY_DIR: Path = PROJECT_ROOT / ".specify"
CONSTITUTION_FILE: Path = SPECIFY_DIR / "memory" / "constitution.md"
SPEC_FILE: Path = SPECIFY_DIR / "spec.md"
PLAN_FILE: Path = SPECIFY_DIR / "plan.md"
TASKS_FILE: Path = SPECIFY_DIR / "tasks.md"

# Autoresearch directories
AUTORESEARCH_DIR: Path = PROJECT_ROOT / ".autoresearch"

# State and logs
STATE_DIR: Path = PROJECT_ROOT / "state"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
BUILD_LOGS_DIR: Path = LOGS_DIR / "build"
OPTIMIZE_LOGS_DIR: Path = LOGS_DIR / "optimize"

# Prompts
PROMPTS_DIR: Path = PROJECT_ROOT / "prompts"
BUILD_PROMPT_FILE: Path = PROMPTS_DIR / "build" / "Prompt.md"
OPTIMIZE_PROMPT_FILE: Path = PROMPTS_DIR / "optimize" / "program.md"

# Environment variable defaults
AGENT_CLI: str = os.environ.get("AGENT_CLI", "claude")
MAX_ITERATIONS: int = int(os.environ.get("MAX_ITERATIONS", "50"))
MAX_EXPERIMENTS: int = int(os.environ.get("MAX_EXPERIMENTS", "100"))
EXPERIMENT_TIMEOUT: int = int(os.environ.get("EXPERIMENT_TIMEOUT", "300"))
STALL_LIMIT: int = int(os.environ.get("STALL_LIMIT", "3"))
METRIC_KEY: str = os.environ.get("METRIC_KEY", "val_bpb")
METRIC_DIRECTION: str = os.environ.get("METRIC_DIRECTION", "lower")
