"""Secure workspace primitives (Phase 03).

Exposes :class:`Workspace` (the path jail), :class:`IgnoreMatcher`
(built-in + ``.gitignore`` rules), and the secret denylist helpers.
"""

from wecoder.workspace.ignore import BUILTIN_IGNORES, IgnoreMatcher
from wecoder.workspace.secrets import ensure_not_secret, is_secret_path
from wecoder.workspace.workspace import Workspace

__all__ = [
    "BUILTIN_IGNORES",
    "IgnoreMatcher",
    "Workspace",
    "ensure_not_secret",
    "is_secret_path",
]
