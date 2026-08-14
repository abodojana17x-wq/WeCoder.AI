"""Tool-capable FakeModel for Phase 04 agent tests.

Wraps the Phase 02 :class:`FakeModel` so it advertises ``tool_calling=True``
and can return scripted tool calls.  Kept separate from
``tests/models/fakes.py`` so the Phase 02 contract fake stays unchanged.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from wecoder.models.types import (
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    ModelCapabilities,
)


class ToolFakeModel:
    """A deterministic, tool-capable test provider.

    ``responses`` are returned in order; each request is recorded in
    ``requests`` so tests can assert what the agent sent.
    """

    id = "fake"

    def __init__(self, responses: list[CompletionResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[CompletionRequest] = []

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(streaming=False, tool_calling=True, json_mode=False)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        if not self.responses:
            # If exhausted, return a final empty message to stop the loop.
            from wecoder.models.types import Message, Usage

            return CompletionResponse(
                Message("assistant", ""),
                Usage(input_tokens=0, output_tokens=0),
                "stop",
                "fake",
                "fake",
            )
        return self.responses.pop(0)

    async def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        if False:  # pragma: no cover
            yield CompletionChunk()

    async def ping(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


def response(
    content: str = "",
    *,
    tool_calls: list | None = None,
    input_tokens: int = 1,
    output_tokens: int = 1,
) -> CompletionResponse:
    """Build a :class:`CompletionResponse` with optional tool calls."""
    from wecoder.models.types import Message, ToolCall, Usage

    calls = None
    if tool_calls is not None:
        calls = [
            ToolCall(id=str(i), name=tc["name"], arguments=tc.get("arguments", ""))
            for i, tc in enumerate(tool_calls)
        ]
    return CompletionResponse(
        Message("assistant", content, tool_calls=calls),
        Usage(input_tokens=input_tokens, output_tokens=output_tokens),
        "stop",
        "fake",
        "fake",
    )
