"""Small registry that constructs configured model providers."""

from __future__ import annotations

from collections.abc import Callable

from wecoder.config.settings import Settings
from wecoder.models.base import ModelProvider
from wecoder.models.errors import ModelConfigError
from wecoder.models.providers.ollama import DEFAULT_BASE_URL as OLLAMA_URL
from wecoder.models.providers.ollama import OllamaProvider
from wecoder.models.providers.openai_compat import (
    DEFAULT_BASE_URL as OPENAI_URL,
)
from wecoder.models.providers.openai_compat import (
    OpenAICompatProvider,
)

Factory = Callable[[Settings], ModelProvider]


class ModelRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Factory] = {}

    def register(self, provider_id: str, factory: Factory) -> None:
        if not provider_id:
            raise ModelConfigError("provider id cannot be empty")
        self._factories[provider_id] = factory

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    def create(self, settings: Settings) -> ModelProvider:
        try:
            return self._factories[settings.model.provider](settings)
        except KeyError as exc:
            known_providers = ", ".join(self.ids())
            message = (
                f"unknown model provider {settings.model.provider!r}; "
                f"known providers: {known_providers}"
            )
            raise ModelConfigError(message) from exc


def default_registry() -> ModelRegistry:
    registry = ModelRegistry()
    registry.register("ollama", lambda s: OllamaProvider(base_url=s.model.base_url or OLLAMA_URL))
    registry.register(
        "openai_compat",
        lambda s: OpenAICompatProvider(
            base_url=s.model.base_url or OPENAI_URL,
            api_key_env=s.model.api_key_env,
            model=s.model.model,
        ),
    )
    return registry
