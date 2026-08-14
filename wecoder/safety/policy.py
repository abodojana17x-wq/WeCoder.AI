"""Minimal safety policy hooks (Phase 03).

Introduces a :class:`Policy` protocol and a default implementation that
enforces the workspace jail, the secret denylist, file-size limits, and the
command timeout — exactly the security primitives Phase 03 ships.

Interactive approval (Approve / Reject / Review) is explicitly deferred to
Phase 06 (ADR-016).  This module deliberately has no UI, no prompts, and no
human-in-the-loop state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from wecoder.errors import (
    CommandTimeoutError,
    DeniedSecretError,
    FileTooLargeError,
    PathEscapeError,
)
from wecoder.workspace.secrets import is_secret_path
from wecoder.workspace.workspace import Workspace


@runtime_checkable
class Policy(Protocol):
    """Allow/deny surface consulted by tools before mutating or reading.

    A future Phase 06 policy will add interactive approval behind this same
    protocol; Phase 03 ships a non-interactive default that hard-enforces
    the jail, denylist, size, and timeout boundaries.
    """

    def check_read(self, workspace: Workspace, path: Path, *, size: int | None) -> None:
        """Validate a read of ``path`` (after jail resolution)."""

    def check_write(self, workspace: Workspace, path: Path, *, size: int) -> None:
        """Validate a write of ``size`` bytes to ``path``."""

    def check_command(
        self, workspace: Workspace, *, argv: list[str], timeout: int
    ) -> None:
        """Validate a command invocation before it runs."""


@dataclass(frozen=True)
class DefaultPolicy:
    """Phase 03 default: allow all except jail, denylist, size, and timeout.

    The jail itself is enforced by :class:`Workspace.resolve`; this policy
    re-checks the secret denylist and the byte / timeout budgets so the rule
    cannot be bypassed by skipping the resolve step in a tool.
    """

    max_read_file_bytes: int = 200_000
    max_write_file_bytes: int = 200_000
    command_timeout_seconds: int = 30

    def check_read(self, workspace: Workspace, path: Path, *, size: int | None) -> None:
        # ``path`` is expected to already be a resolved path from the workspace.
        if is_secret_path(path):
            raise DeniedSecretError(
                f"refused read of secret-like path {path.name!r}"
            )
        if not _is_inside(path, workspace.root):
            raise PathEscapeError(
                f"refused read outside workspace: {path}"
            )
        if size is not None and size > self.max_read_file_bytes:
            raise FileTooLargeError(
                f"file {path.name!r} is {size} bytes; limit is "
                f"{self.max_read_file_bytes}"
            )

    def check_write(self, workspace: Workspace, path: Path, *, size: int) -> None:
        if is_secret_path(path):
            raise DeniedSecretError(
                f"refused write to secret-like path {path.name!r}"
            )
        if not _is_inside(path, workspace.root):
            raise PathEscapeError(
                f"refused write outside workspace: {path}"
            )
        if size > self.max_write_file_bytes:
            raise FileTooLargeError(
                f"write of {size} bytes to {path.name!r} exceeds limit "
                f"{self.max_write_file_bytes}"
            )

    def check_command(
        self, workspace: Workspace, *, argv: list[str], timeout: int
    ) -> None:
        if not argv:
            raise ValueError("command argv must not be empty")
        if timeout <= 0 or timeout > self.command_timeout_seconds:
            raise CommandTimeoutError(
                f"command timeout {timeout}s is out of bounds "
                f"(max {self.command_timeout_seconds}s)"
            )


def _is_inside(path: Path, root: Path) -> bool:
    """Return ``True`` iff ``path`` is ``root`` or beneath it (both resolved)."""
    try:
        r = path.resolve(strict=False)
        if r == root:
            return True
        r.relative_to(root)
    except ValueError:
        return False
    return True


__all__ = ["Policy", "DefaultPolicy"]
