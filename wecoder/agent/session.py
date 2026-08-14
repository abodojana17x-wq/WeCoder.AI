"""In-memory agent session (Phase 04).

Holds the conversation, accumulated usage, turn count, and status for a single
``wecoder run`` invocation.  Persistence is explicitly deferred to Phase 08;
this object lives only for the duration of one process run.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal

from wecoder.models.types import Message, Usage
from wecoder.workspace.workspace import Workspace

SessionStatus = Literal["running", "succeeded", "failed", "blocked", "budget_exceeded"]


@dataclass
class Session:
    """One in-memory agent run bound to a workspace."""

    workspace: Workspace
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    messages: list[Message] = field(default_factory=list)
    turns: int = 0
    usage: Usage = field(default_factory=Usage)
    status: SessionStatus = "running"

    def add_message(self, message: Message) -> None:
        self.messages.append(message)

    def accumulate_usage(self, usage: Usage) -> None:
        """Add a model response's usage to the running totals."""
        current_in = self.usage.input_tokens or 0
        current_out = self.usage.output_tokens or 0
        add_in = usage.input_tokens or 0
        add_out = usage.output_tokens or 0
        self.usage = Usage(
            input_tokens=current_in + add_in,
            output_tokens=current_out + add_out,
            raw=None,
        )

    @property
    def total_tokens(self) -> int | None:
        """Total tokens if any usage component is known, else ``None``."""
        if self.usage.input_tokens is None and self.usage.output_tokens is None:
            return None
        return (self.usage.input_tokens or 0) + (self.usage.output_tokens or 0)


__all__ = ["Session", "SessionStatus"]
