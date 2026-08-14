"""Structured agent result (Phase 04).

The single outcome object produced by the Developer agent loop and rendered by
the CLI.  ``changed_files`` and ``commands`` are derived from **actual** tool
calls, never from trusting the model's prose — so Phase 05/06 can rely on
them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from wecoder.models.types import Usage

AgentStatus = Literal["succeeded", "failed", "blocked", "budget_exceeded"]


@dataclass(frozen=True)
class CommandRecord:
    """One executed command, with its argv and exit code."""

    argv: list[str]
    exit_code: int


@dataclass(frozen=True)
class AgentResult:
    """The outcome of one ``wecoder run``."""

    status: AgentStatus
    summary: str
    plan: str | None = None
    changed_files: list[str] = field(default_factory=list)
    commands: list[CommandRecord] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    stop_reason: str = ""

    @property
    def exit_code(self) -> int:
        """CLI exit code: 0 on success, 1 on any expected operational failure."""
        return 0 if self.status == "succeeded" else 1


__all__ = ["AgentResult", "AgentStatus", "CommandRecord"]
