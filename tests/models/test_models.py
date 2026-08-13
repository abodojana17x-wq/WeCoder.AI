from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from tests.models.fakes import FakeModel
from wecoder.config.settings import Settings
from wecoder.models.base import ModelProvider
from wecoder.models.errors import (
    ModelAuthError,
    ModelConfigError,
    ModelResponseError,
    ModelTimeoutError,
)
from wecoder.models.providers.ollama import OllamaProvider
from wecoder.models.providers.openai_compat import OpenAICompatProvider
from wecoder.models.registry import default_registry
from wecoder.models.types import CompletionRequest, CompletionResponse, Message, Usage


def client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def request():
    return CompletionRequest(
        "test", [Message("user", "secret prompt")], temperature=0.2, max_tokens=5
    )


def test_fake_contract():
    fake = FakeModel(
        [CompletionResponse(Message("assistant", "ok"), Usage(), "stop", "fake", "test")]
    )
    assert isinstance(fake, ModelProvider)
    assert asyncio.run(fake.complete(request())).provider_id == "fake"


def test_openai_normalizes_and_sends_request():
    def handler(r):
        assert r.headers["authorization"] == "Bearer fake-key"
        assert json.loads(r.content)["messages"][0]["content"] == "secret prompt"
        return httpx.Response(
            200,
            json={
                "model": "server-model",
                "choices": [
                    {"message": {"role": "assistant", "content": "hello"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2},
            },
        )

    provider = OpenAICompatProvider(
        base_url="https://example.test/v1",
        env={"KEY": "fake-key"},
        api_key_env="KEY",
        client=client(handler),
    )
    response = asyncio.run(provider.complete(request()))
    assert (
        response.message.content == "hello"
        and response.usage.input_tokens == 3
        and response.model == "server-model"
    )


def test_ollama_normalizes():
    provider = OllamaProvider(
        client=client(
            lambda _: httpx.Response(
                200,
                json={
                    "model": "q",
                    "message": {"role": "assistant", "content": "hello"},
                    "done_reason": "stop",
                    "prompt_eval_count": 3,
                    "eval_count": 2,
                },
            )
        )
    )
    response = asyncio.run(provider.complete(request()))
    assert response.provider_id == "ollama" and response.usage.output_tokens == 2


def test_missing_key_is_deferred_to_request():
    provider = OpenAICompatProvider(
        env={}, api_key_env="MISSING", client=client(lambda _: pytest.fail("network"))
    )
    with pytest.raises(ModelConfigError):
        asyncio.run(provider.complete(request()))


def test_http_errors_are_normalized_without_secrets():
    provider = OpenAICompatProvider(
        env={"KEY": "do-not-leak"}, api_key_env="KEY", client=client(lambda _: httpx.Response(401))
    )
    with pytest.raises(ModelAuthError) as error:
        asyncio.run(provider.complete(request()))
    assert "do-not-leak" not in str(error.value)


def test_malformed_response():
    provider = OllamaProvider(client=client(lambda _: httpx.Response(200, json={"bad": True})))
    with pytest.raises(ModelResponseError):
        asyncio.run(provider.complete(request()))


def test_timeout_is_normalized():
    async def handler(_: httpx.Request):
        raise httpx.ReadTimeout("nope")

    provider = OllamaProvider(client=client(handler))
    with pytest.raises(ModelTimeoutError):
        asyncio.run(provider.complete(request()))


def test_registry_uses_config_and_rejects_unknown(project_dir, home_dir):
    settings = Settings.load(cwd=project_dir, home=home_dir)
    assert default_registry().create(settings).id == "ollama"
    bad = Settings.load(cwd=project_dir, home=home_dir, env={"WECODER_MODEL_PROVIDER": "nope"})
    with pytest.raises(ModelConfigError, match="ollama"):
        default_registry().create(bad)


def test_models_list_marks_configured_provider(project_dir, home_dir, capsys) -> None:
    from wecoder.cli.app import main

    project_dir.mkdir()
    assert main(["models", "list"], cwd=project_dir, home=home_dir) == 0
    output = capsys.readouterr().out
    assert "ollama (configured)" in output
    assert "openai_compat" in output
