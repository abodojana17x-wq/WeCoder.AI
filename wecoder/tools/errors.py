"""Re-export of the tool error hierarchy for the tools package.

The canonical definitions live in :mod:`wecoder.errors`; this module keeps
imports inside ``wecoder.tools.*`` short and stable so a future phase can
depend on ``wecoder.tools.errors`` without reaching into the global error
module.
"""

from __future__ import annotations

from wecoder.errors import (
    CommandFailedError,
    CommandTimeoutError,
    DeniedSecretError,
    EditMismatchError,
    FileTooLargeError,
    PathEscapeError,
    ToolError,
)

__all__ = [
    "ToolError",
    "PathEscapeError",
    "DeniedSecretError",
    "FileTooLargeError",
    "EditMismatchError",
    "CommandTimeoutError",
    "CommandFailedError",
]
