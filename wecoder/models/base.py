"""The stable asynchronous provider boundary used by future layers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from wecoder.models.types import (
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    ModelCapabilities,
)


@runtime_checkable
class ModelProvider(Protocol):
    """A vendor-neutral chat model adapter."""

    id: str

    def capabilities(self) -> ModelCapabilities: ...
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]: ...
    async def ping(self) -> None: ...
    async def aclose(self) -> None: ...


__all__ = ["ModelProvider"]
