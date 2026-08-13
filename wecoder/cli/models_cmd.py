"""Phase 02 CLI model-provider introspection commands."""

from __future__ import annotations

import asyncio

from wecoder.config.settings import Settings
from wecoder.models.registry import default_registry


def list_models(settings: Settings) -> None:
    """Print registered provider ids without constructing or contacting one."""
    for provider_id in default_registry().ids():
        marker = " (configured)" if provider_id == settings.model.provider else ""
        print(f"{provider_id}{marker}")


def ping_model(settings: Settings) -> None:
    """Perform an explicit provider health check; it may contact a configured service."""
    provider = default_registry().create(settings)
    try:
        asyncio.run(provider.ping())
    finally:
        asyncio.run(provider.aclose())
    print(f"{settings.model.provider}: reachable")
