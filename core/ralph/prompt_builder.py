"""Build prompts for the Ralph Loop agent invocations."""

from pathlib import Path

from core.ralph.task_parser import Task
from core.utils import read_file


def build_prompt(
    task: Task,
    constitution_file: Path,
    prompt_template_file: Path,
    extra_context: str = "",
) -> str:
    """Build the agent prompt for a single task iteration.

    Combines the master Prompt.md template with the current task and
    constitution principles.

    Args:
        task: The task to implement.
        constitution_file: Path to constitution.md (inviolable principles).
        prompt_template_file: Path to the Prompt.md master template.
        extra_context: Optional additional context to append.

    Returns:
        The complete prompt string to send to the agent.

    Raises:
        FileNotFoundError: If constitution or prompt template files are missing.
    """
    constitution = read_file(constitution_file)
    template = read_file(prompt_template_file)

    sections: list[str] = [
        template,
        "",
        "## Current Task",
        "",
        f"Implement the following task:",
        f"> {task.text}",
        "",
        "## Constitution (Inviolable Principles)",
        "",
        constitution,
    ]

    if extra_context:
        sections += ["", "## Additional Context", "", extra_context]

    sections += [
        "",
        "## Completion",
        "",
        "When the task is done and tests pass, output:",
        "<promise>TASK_DONE</promise>",
    ]

    return "\n".join(sections)


def build_status_prompt(tasks_file: Path, prompt_template_file: Path) -> str:
    """Build a prompt to report current build status.

    Args:
        tasks_file: Path to tasks.md.
        prompt_template_file: Path to Prompt.md template.

    Returns:
        A prompt asking the agent to report progress.
    """
    tasks_content = read_file(tasks_file)
    template = read_file(prompt_template_file)

    return "\n".join([
        template,
        "",
        "## Status Check",
        "",
        "Review the current state of tasks.md and report:",
        "- How many tasks are done [x]",
        "- How many are pending [ ]",
        "- How many are blocked [BLOCKED]",
        "- What the next pending task is",
        "",
        "## Current tasks.md",
        "",
        tasks_content,
    ])
