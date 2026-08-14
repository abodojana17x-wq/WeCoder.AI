"""Secret-file denylist for the workspace (Phase 03).

This module enforces a *security boundary*, not a convenience.  A path that
matches the denylist is refused by every automatic read/write path
(``read_file``, ``write_file``, ``search_text``, and the context packer) so a
future agent cannot bypass it by simply requesting a different tool.

The denylist is intentionally name-based (cheap, no file-content scanning).
It errs on the side of refusing credential-like filenames.  ``.env.example``
is deliberately *allowed* because it is documentation, not a live secret.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

from wecoder.errors import DeniedSecretError

# Filenames / glob patterns that are always treated as secrets.
#
# These are matched against the *basename* of the path (the final
# component), which keeps the check fast and immune to deep nesting.
_SECRET_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.*",
    "*.pem",
    "*.p12",
    "*.key",
    "id_rsa",
    "id_ed25519",
    "*.ppk",
    "credentials.json",
    "service-account*.json",
)

# Directory components that, when present anywhere in a path, mark every file
# under them as denied (matching the Phase 03 contract for ``.ssh/`` and
# ``.aws/``).
_SECRET_DIR_PARTS: tuple[str, ...] = (".ssh", ".aws")

# Explicit allowlist applied *after* the secret patterns.  ``.env.example``
# is documentation rather than a live secret, so it is readable.
_ALLOWED_NAMES: frozenset[str] = frozenset({".env.example"})


def is_secret_path(path: Path) -> bool:
    """Return ``True`` if ``path`` matches the secret denylist.

    ``path`` may be absolute or relative; only the basename and directory
    components are inspected.
    """
    name = path.name
    if name in _ALLOWED_NAMES:
        return False

    # Directory-bearing secrets (e.g. ``.ssh/config``, ``.aws/credentials``).
    parts = path.parts
    for part in parts:
        if part in _SECRET_DIR_PARTS:
            return True

    return any(fnmatch.fnmatch(name, pattern) for pattern in _SECRET_PATTERNS)


def ensure_not_secret(path: Path) -> None:
    """Raise :class:`DeniedSecretError` if ``path`` is on the denylist.

    Used by tools and the context packer as the single chokepoint so the rule
    can never be bypassed by choosing a different code path.
    """
    if is_secret_path(path):
        raise DeniedSecretError(
            f"refused access to secret-like path: {path.name!r} "
            "(matched the workspace secret denylist)"
        )


__all__ = ["is_secret_path", "ensure_not_secret"]
