"""Structured logging for Forja with timestamp and iteration context."""

import logging
from pathlib import Path


def setup_logger(
    name: str, log_file: Path | None = None, level: int = logging.INFO
) -> logging.Logger:
    """Create and configure a logger with timestamp format.

    Args:
        name: Logger name (usually the module, e.g. 'forja.ralph').
        log_file: Optional path to write logs to file. Parent dirs are created.
        level: Logging level (default INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_iteration_logger(phase: str, iteration: int, log_dir: Path) -> logging.Logger:
    """Get a logger scoped to a specific iteration.

    Args:
        phase: Phase name ('build' or 'optimize').
        iteration: Current iteration number.
        log_dir: Directory to write log files.

    Returns:
        Logger configured to write to a per-iteration log file.
    """
    log_file = log_dir / f"{phase}_iter_{iteration:04d}.log"
    return setup_logger(f"forja.{phase}.iter{iteration}", log_file=log_file)
