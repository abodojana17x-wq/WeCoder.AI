"""Ollama chat adapter using its local HTTP API."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from wecoder.models.errors import ModelResponseError
from wecoder.models.providers._http import raise_for_status, transport_error
from wecoder.models.types import (
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    Message,
    ModelCapabilities,
    ToolCall,
    Usage,
)

DEFAULT_BASE_URL = "http://127.0.0.1:11434"


class OllamaProvider:
    id = "ollama"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(streaming=True, tool_calling=True, json_mode=True)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload = _request_payload(request, stream=False)
        try:
            response = await self._client.post(f"{self.base_url}/api/chat", json=payload)
            raise_for_status(response, self.id, self.base_url)
            data = response.json()
        except httpx.HTTPError as exc:
            raise transport_error(exc, self.id, self.base_url) from exc
        return _completion(data, request.model)

    async def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        payload = _request_payload(request, stream=True)
        try:
            async with self._client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                raise_for_status(response, self.id, self.base_url)
                async for line in response.aiter_lines():
                    if line:
                        yield _chunk(_json_line(line))
        except httpx.HTTPError as exc:
            raise transport_error(exc, self.id, self.base_url) from exc

    async def ping(self) -> None:
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            raise_for_status(response, self.id, self.base_url)
        except httpx.HTTPError as exc:
            raise transport_error(exc, self.id, self.base_url) from exc

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


def _request_payload(request: CompletionRequest, *, stream: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": request.model,
        "messages": [_message(message) for message in request.messages],
        "stream": stream,
    }
    options: dict[str, object] = {}
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.max_tokens is not None:
        options["num_predict"] = request.max_tokens
    if options:
        payload["options"] = options
    if request.tools:
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters or {},
                },
            }
            for tool in request.tools
        ]
    return payload


def _message(message: Message) -> dict[str, object]:
    item: dict[str, object] = {"role": message.role, "content": message.content}
    if message.name is not None:
        item["name"] = message.name
    if message.tool_call_id is not None:
        item["tool_call_id"] = message.tool_call_id
    return item


def _completion(data: object, requested_model: str) -> CompletionResponse:
    if not isinstance(data, dict) or not isinstance(data.get("message"), dict):
        raise ModelResponseError("ollama: malformed completion response")
    message_data = data["message"]
    content = message_data.get("content")
    if not isinstance(content, str):
        raise ModelResponseError("ollama: completion message has no content")
    return CompletionResponse(
        Message("assistant", content, tool_calls=_tool_calls(message_data.get("tool_calls"))),
        Usage(
            _optional_int(data.get("prompt_eval_count")),
            _optional_int(data.get("eval_count")),
            data,
        ),
        _optional_str(data.get("done_reason")),
        "ollama",
        _optional_str(data.get("model")) or requested_model,
        data,
    )


def _chunk(data: object) -> CompletionChunk:
    if not isinstance(data, dict):
        raise ModelResponseError("ollama: malformed stream chunk")
    message = data.get("message", {})
    if not isinstance(message, dict) or not isinstance(message.get("content", ""), str):
        raise ModelResponseError("ollama: malformed stream message")
    usage = (
        Usage(
            _optional_int(data.get("prompt_eval_count")),
            _optional_int(data.get("eval_count")),
            data,
        )
        if data.get("done")
        else None
    )
    return CompletionChunk(
        message.get("content", ""), _optional_str(data.get("done_reason")), usage
    )


def _tool_calls(value: object) -> list[ToolCall] | None:
    if not isinstance(value, list):
        return None
    calls: list[ToolCall] = []
    for call in value:
        if not isinstance(call, dict) or not isinstance(call.get("function"), dict):
            continue
        function = call["function"]
        name, arguments = function.get("name"), function.get("arguments")
        if isinstance(name, str):
            calls.append(
                ToolCall(
                    str(call.get("id", "")),
                    name,
                    json.dumps(arguments) if not isinstance(arguments, str) else arguments,
                )
            )
    return calls or None


def _json_line(line: str) -> object:
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        raise ModelResponseError("ollama: malformed stream JSON") from exc


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None
