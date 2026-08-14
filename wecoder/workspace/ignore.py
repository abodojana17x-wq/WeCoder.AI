"""Workspace ignore rules (Phase 03).

Combines a small set of built-in ignore defaults with the workspace's own
``.gitignore`` (when present).  Uses ``pathspec`` so we honour gitignore
semantics without vendoring a full git engine.

Ignored files are excluded from ``list_dir``, ``search_text``, and the
context packer; they must never be silently included where a user expects
only real source to appear.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pathspec

# Built-in defaults that always apply, regardless of any .gitignore.  These
# match the Phase 03 contract.  Patterns are gitignore-style relative paths.
BUILTIN_IGNORES: tuple[str, ...] = (
    ".git/",
    ".wecoder/sessions/",
    "__pycache__/",
    ".venv/",
    "venv/",
    "node_modules/",
    "dist/",
    "build/",
    ".mypy_cache/",
    ".ruff_cache/",
    "*.pyc",
)


class IgnoreMatcher:
    """Decide whether a path inside the workspace should be ignored.

    The merged :class:`pathspec.PathSpec` is built lazily and cached, with
    mtime-based invalidation so a ``.gitignore`` written (or changed) after
    the workspace was opened is still honoured without rebuilding on every
    lookup.
    """

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._spec: pathspec.PathSpec | None = None
        self._gitignore_mtime: float | None = None

    def _gitignore_path(self) -> Path:
        return self._root / ".gitignore"

    def _build_spec(self) -> pathspec.PathSpec:
        lines: list[str] = list(BUILTIN_IGNORES)
        gitignore = self._gitignore_path()
        if gitignore.is_file():
            try:
                text = gitignore.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            lines.extend(text.splitlines())
        with warnings.catch_warnings():
            # ``gitwildmatch`` is the correct matcher for our *.pyc / dir
            # semantics; pathspec deprecates the name in favour of split
            # classes, but the replacement changes glob behaviour. Silence
            # the noisy deprecation until we migrate patterns explicitly.
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            return pathspec.PathSpec.from_lines("gitwildmatch", lines)

    def _get_spec(self) -> pathspec.PathSpec:
        """Return the cached spec, rebuilding it if ``.gitignore`` changed."""
        gi = self._gitignore_path()
        try:
            mtime = gi.stat().st_mtime if gi.is_file() else None
        except OSError:
            mtime = None
        if self._spec is None or mtime != self._gitignore_mtime:
            self._spec = self._build_spec()
            self._gitignore_mtime = mtime
        return self._spec

    def is_ignored(self, path: Path) -> bool:
        """Return ``True`` if ``path`` matches any ignore rule.

        ``path`` may be absolute (inside the workspace) or relative to the
        workspace root.  Non-existent paths are still matched against the
        rules so the matcher works for proposed writes.
        """
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(self._root)
        except ValueError:
            # Path is outside the workspace entirely; it cannot be "ignored"
            # in the workspace sense, so it is not matched here.
            return False

        if str(rel) == ".":
            return False

        spec = self._get_spec()
        posix_rel = rel.as_posix()

        # 1. Match the full relative path.
        if spec.match_file(posix_rel):
            return True
        # 2. Match the full relative path as a directory (trailing slash).
        if spec.match_file(posix_rel + "/"):
            return True

        # 3. Match each ancestor directory (and as a dir) so directory-only
        #    patterns (e.g. ``node_modules/``) ignore their contents even when
        #    the content path itself does not match the pattern directly.
        parts = rel.parts
        for i in range(1, len(parts)):
            ancestor = "/".join(parts[:i])
            if spec.match_file(ancestor) or spec.match_file(ancestor + "/"):
                return True
        return False


__all__ = ["IgnoreMatcher", "BUILTIN_IGNORES"]
