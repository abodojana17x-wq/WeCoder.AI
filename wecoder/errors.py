"""Public error hierarchy for WeCoder.AI.

Every expected failure in WeCoder.AI is represented by a subclass of
:class:`WecoderError`.  The CLI maps :class:`WecoderError` to exit code 1
and unknown exceptions to exit code 2.  Later phases add more specific
subclasses (``ModelError``, ``ToolError``, ``PolicyError``, ``GitError``,
``BudgetExceeded``) without changing the base class.
"""

from __future__ import annotations


class WecoderError(Exception):
    """Base class for all WeCoder.AI errors."""


class ConfigError(WecoderError):
    """Raised when configuration is missing, unreadable, or invalid."""


__all__ = ["WecoderError", "ConfigError"]
