"""Lightweight structured logging keyed by request id."""
from __future__ import annotations

import logging
import sys

_formatter = logging.Formatter(
    '{"ts":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
