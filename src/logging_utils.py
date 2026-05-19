"""Logging configuration utilities."""

from __future__ import annotations

import logging
from pathlib import Path

from src.config import project_root


def setup_logging(name: str, log_dir: str | Path = "outputs/logs") -> logging.Logger:
    """Create a logger that writes to console and a script-specific log file."""
    root = project_root()
    log_path = root / log_dir
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path / f"{name}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

