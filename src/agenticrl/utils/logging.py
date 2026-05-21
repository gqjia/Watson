"""Logging utilities for AgenticRL."""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "agenticrl",
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """Set up a logger with console and optional file output.

    Args:
        name: Logger name.
        level: Logging level (default: INFO).
        log_file: Optional path to a log file.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = setup_logger("my_experiment", log_file="train.log")
        >>> logger.info("Training started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(console)

    # File handler
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    return logger
