"""Public error hierarchy for WeCoder.AI.

Every expected failure in WeCoder.AI is represented by a subclass of
:class:`WecoderError`.  The CLI maps :class:`WecoderError` to exit code 1
and unknown exceptions to exit code 2.  Phase 03 adds the tool / workspace
error tree (``ToolError`` and its subclasses) without changing the base.
"""

from __future__ import annotations


class WecoderError(Exception):
    """Base class for all WeCoder.AI errors."""


class ConfigError(WecoderError):
    """Raised when configuration is missing, unreadable, or invalid."""


class ToolError(WecoderError):
    """Base class for expected tool / workspace failures (Phase 03+)."""


class PathEscapeError(ToolError):
    """A resolved path fell outside the workspace root."""


class DeniedSecretError(ToolError):
    """A path matched the secret denylist and was refused."""


class FileTooLargeError(ToolError):
    """A file exceeded the configured byte limit for an operation."""


class EditMismatchError(ToolError):
    """An ``edit_file`` did not find a unique occurrence of ``old_text``."""


class CommandTimeoutError(ToolError):
    """A ``run_command`` invocation exceeded its bounded timeout."""


class CommandFailedError(ToolError):
    """A ``run_command`` exited non-zero; surfaced as a result, not raised.

    Kept as a distinct type for callers that want to classify non-zero exits,
    but :class:`RunCommand` returns a ``ToolResult(ok=False)`` rather than
    raising it.
    """


__all__ = [
    "WecoderError",
    "ConfigError",
    "ToolError",
    "PathEscapeError",
    "DeniedSecretError",
    "FileTooLargeError",
    "EditMismatchError",
    "CommandTimeoutError",
    "CommandFailedError",
]
