"""Deterministic test-only provider implementing the Phase 02 protocol."""

from __future__ import annotations

from collections.abc import AsyncIterator

from wecoder.models.types import (
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    ModelCapabilities,
)


class FakeModel:
    id = "fake"

    def __init__(self, responses: list[CompletionResponse]) -> None:
        self.responses = responses
        self.requests: list[CompletionRequest] = []

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(False, False, False)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        return self.responses.pop(0)

    async def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        if False:
            yield CompletionChunk()

    async def ping(self) -> None:
        return None

    async def aclose(self) -> None:
        return None
