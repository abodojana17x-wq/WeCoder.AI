"""Structured logging setup for WeCoder.AI.

Logs go to stderr with a grep-able format (``timestamp LEVEL logger
message``) so stdout stays clean for command output.  Configuration secrets
are never logged here — see :meth:`wecoder.config.settings.Settings.redacted`.
"""

from __future__ import annotations

import logging
import sys

# Everything WeCoder logs under this logger name.
LOGGER_NAME = "wecoder"

# %(asctime)s  %(levelname)s  %(name)s  %(message)s
_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Configure the ``wecoder`` logger to emit structured lines to stderr.

    Safe to call more than once; each call replaces the handler set so tests
    and repeated CLI invocations in one process behave deterministically.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT))

    # Replace handlers rather than appending, so a re-run never duplicates.
    logger.handlers = [handler]
    logger.propagate = False


__all__ = ["configure_logging", "LOGGER_NAME"]
