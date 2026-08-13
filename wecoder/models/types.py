"""Normalized, vendor-neutral model request and response types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class ToolCall:
    """A provider-normalized tool call, reserved for the Phase 04 tool layer."""

    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ToolSpec:
    """Tool declaration placeholder; execution is intentionally not implemented here."""

    name: str
    description: str | None = None
    parameters: dict[str, object] | None = None


@dataclass(frozen=True)
class Message:
    """One normalized chat message."""

    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass(frozen=True)
class Usage:
    """Provider usage, with ``None`` meaning the provider did not report it."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict[str, object] | None = None


@dataclass(frozen=True)
class ModelCapabilities:
    """Capabilities advertised by a provider adapter, not an individual model."""

    streaming: bool
    tool_calling: bool
    json_mode: bool


@dataclass(frozen=True)
class CompletionRequest:
    """A normalized chat-completion request."""

    model: str
    messages: list[Message]
    tools: list[ToolSpec] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


@dataclass(frozen=True)
class CompletionResponse:
    """A normalized non-streaming completion response."""

    message: Message
    usage: Usage
    finish_reason: str | None
    provider_id: str
    model: str
    raw: dict[str, object] | None = None


@dataclass(frozen=True)
class CompletionChunk:
    """An incremental normalized completion update."""

    content: str = ""
    finish_reason: str | None = None
    usage: Usage | None = None


__all__ = [
    "CompletionChunk",
    "CompletionRequest",
    "CompletionResponse",
    "Message",
    "ModelCapabilities",
    "Role",
    "ToolCall",
    "ToolSpec",
    "Usage",
]
