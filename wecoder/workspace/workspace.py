"""The secure workspace abstraction (Phase 03).

A :class:`Workspace` binds an absolute, resolved root and resolves every
user-supplied path against it.  Any path whose *final resolved* location
falls outside the root is refused with :class:`PathEscapeError`.

This is the security boundary mandated by ADR-015: every file operation in
WeCoder goes through :meth:`Workspace.resolve`, and symlink escapes are
caught by resolving the real path before the containment check.
"""

from __future__ import annotations

import os
from pathlib import Path

from wecoder.errors import PathEscapeError
from wecoder.workspace.ignore import IgnoreMatcher
from wecoder.workspace.secrets import ensure_not_secret

# When resolving, symlink targets are followed.  A path is accepted only if
# its real, fully-resolved form is inside the root.


class Workspace:
    """A resolved workspace root with path-jail enforcement."""

    def __init__(self, root: Path) -> None:
        # ``resolve()`` follows symlinks and normalizes ``..``; the root
        # itself must be real and absolute.
        self._root: Path = root.resolve()
        self._ignore = IgnoreMatcher(self._root)

    @property
    def root(self) -> Path:
        """The absolute, resolved workspace root."""
        return self._root

    @property
    def ignore(self) -> IgnoreMatcher:
        """The ignore matcher bound to this workspace."""
        return self._ignore

    @classmethod
    def open(cls, path: str | os.PathLike[str] | Path | None = None) -> Workspace:
        """Bind a workspace.

        ``path`` defaults to the current working directory, so the workspace
        never accidentally becomes the user's entire home directory.  The
        resolved root is :meth:`Path.resolve`-d so symlinks in the root path
        itself are followed.
        """
        if path is None or path == "":
            root = Path.cwd()
        else:
            root = Path(path)
        if not root.exists():
            raise FileNotFoundError(f"workspace root does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"workspace root is not a directory: {root}")
        return cls(root)

    def resolve(self, user_path: str | os.PathLike[str] | Path) -> Path:
        """Resolve ``user_path`` against the root and enforce the jail.

        Returns the *real* resolved absolute path, with symlinks followed.

        Raises:
            PathEscapeError: if the final resolved path is outside the root.
        """
        p = Path(user_path)
        # An absolute user path is anchored at itself, not the root.  We still
        # allow it only if it resolves inside the root (e.g. a nested real
        # path); otherwise it is rejected.
        if p.is_absolute():
            candidate = p
        else:
            candidate = self._root / p

        # ``resolve()`` follows symlinks and collapses ``..``.  We pass
        # ``strict=False`` so non-existent-but-valid target paths (used by
        # ``write_file`` for new files) still resolve.
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise PathEscapeError(
                f"could not resolve path {user_path!r}: {exc}"
            ) from exc

        if not self._is_inside(resolved):
            raise PathEscapeError(
                f"path {user_path!r} resolves outside the workspace root "
                f"({resolved} is not under {self._root})"
            )
        return resolved

    def _is_inside(self, resolved: Path) -> bool:
        """Return ``True`` iff ``resolved`` is the root or beneath it."""
        root = self._root
        if resolved == root:
            return True
        try:
            resolved.relative_to(root)
        except ValueError:
            return False
        return True

    def resolve_for_read(self, user_path: str | os.PathLike[str] | Path) -> Path:
        """Resolve a path and enforce the secret denylist for reads."""
        resolved = self.resolve(user_path)
        ensure_not_secret(resolved)
        return resolved

    def resolve_for_write(self, user_path: str | os.PathLike[str] | Path) -> Path:
        """Resolve a path and enforce the secret denylist for writes."""
        resolved = self.resolve(user_path)
        ensure_not_secret(resolved)
        return resolved

    def __repr__(self) -> str:
        return f"Workspace(root={self._root!r})"


__all__ = ["Workspace"]
