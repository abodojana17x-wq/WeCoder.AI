"""Generic OpenAI-compatible chat-completions HTTP adapter."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator, Mapping

import httpx

from wecoder.models.errors import ModelConfigError, ModelResponseError
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

DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAICompatProvider:
    id = "openai_compat"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        api_key_env: str = "OPENAI_API_KEY",
        model: str = "",
        timeout: float = 120.0,
        env: Mapping[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url, self.api_key_env, self.model = base_url.rstrip("/"), api_key_env, model
        self._env = env if env is not None else os.environ
        self._client, self._owns_client = (
            client or httpx.AsyncClient(timeout=timeout),
            client is None,
        )

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(streaming=True, tool_calling=True, json_mode=True)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        try:
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=_payload(request, False),
                headers=self._headers(),
            )
            raise_for_status(response, self.id, self.base_url)
            data = response.json()
        except httpx.HTTPError as exc:
            raise transport_error(exc, self.id, self.base_url) from exc
        return _completion(data, request.model)

    async def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=_payload(request, True),
                headers=self._headers(),
            ) as response:
                raise_for_status(response, self.id, self.base_url)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield _chunk(_json(data))
        except httpx.HTTPError as exc:
            raise transport_error(exc, self.id, self.base_url) from exc

    async def ping(self) -> None:
        # Explicit command only: one minimal completion may incur provider usage.
        await self.complete(
            CompletionRequest(model=self.model, messages=[Message("user", "ping")], max_tokens=1)
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        key = self._env.get(self.api_key_env)
        if not key:
            raise ModelConfigError(
                f"openai_compat: API key environment variable {self.api_key_env!r} is not set"
            )
        return {"Authorization": f"Bearer {key}"}


def _payload(request: CompletionRequest, stream: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": request.model,
        "messages": [_message(item) for item in request.messages],
        "stream": stream,
    }
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens
    if request.tools:
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters or {},
                },
            }
            for t in request.tools
        ]
    return payload


def _message(message: Message) -> dict[str, object]:
    data: dict[str, object] = {"role": message.role, "content": message.content}
    if message.name is not None:
        data["name"] = message.name
    if message.tool_call_id is not None:
        data["tool_call_id"] = message.tool_call_id
    return data


def _completion(data: object, requested_model: str) -> CompletionResponse:
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("choices"), list)
        or not data["choices"]
        or not isinstance(data["choices"][0], dict)
    ):
        raise ModelResponseError("openai_compat: malformed completion response")
    choice = data["choices"][0]
    message = choice.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ModelResponseError("openai_compat: completion message has no content")
    return CompletionResponse(
        Message("assistant", message["content"], tool_calls=_tool_calls(message.get("tool_calls"))),
        _usage(data.get("usage")),
        _string(choice.get("finish_reason")),
        "openai_compat",
        _string(data.get("model")) or requested_model,
        data,
    )


def _chunk(data: object) -> CompletionChunk:
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("choices"), list)
        or not data["choices"]
        or not isinstance(data["choices"][0], dict)
    ):
        raise ModelResponseError("openai_compat: malformed stream chunk")
    choice = data["choices"][0]
    delta = choice.get("delta", {})
    if not isinstance(delta, dict) or not isinstance(delta.get("content", ""), str):
        raise ModelResponseError("openai_compat: malformed stream delta")
    return CompletionChunk(
        delta.get("content", ""),
        _string(choice.get("finish_reason")),
        _usage(data["usage"]) if isinstance(data.get("usage"), dict) else None,
    )


def _usage(value: object) -> Usage:
    if not isinstance(value, dict):
        return Usage()
    return Usage(
        _integer(value.get("prompt_tokens")), _integer(value.get("completion_tokens")), value
    )


def _tool_calls(value: object) -> list[ToolCall] | None:
    if not isinstance(value, list):
        return None
    result = []
    for c in value:
        if (
            isinstance(c, dict)
            and isinstance(c.get("function"), dict)
            and isinstance(c["function"].get("name"), str)
        ):
            result.append(
                ToolCall(
                    str(c.get("id", "")),
                    c["function"]["name"],
                    str(c["function"].get("arguments", "")),
                )
            )
    return result or None


def _json(value: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ModelResponseError("openai_compat: malformed stream JSON") from exc


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _string(value: object) -> str | None:
    return value if isinstance(value, str) else None
