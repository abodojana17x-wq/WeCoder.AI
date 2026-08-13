"""Shared, private HTTP error normalization for provider adapters."""

from __future__ import annotations

import httpx

from wecoder.models.errors import (
    ModelAuthError,
    ModelResponseError,
    ModelTimeoutError,
    ModelUnavailableError,
)


def raise_for_status(response: httpx.Response, provider_id: str, base_url: str) -> None:
    if response.status_code in (401, 403):
        raise ModelAuthError(f"{provider_id}: authentication failed")
    if response.status_code == 503:
        raise ModelUnavailableError(f"{provider_id}: unavailable at {base_url}")
    if response.is_error:
        raise ModelResponseError(f"{provider_id}: provider returned HTTP {response.status_code}")


def transport_error(exc: httpx.HTTPError, provider_id: str, base_url: str) -> Exception:
    if isinstance(exc, httpx.TimeoutException):
        return ModelTimeoutError(f"{provider_id}: request timed out at {base_url}")
    return ModelUnavailableError(f"{provider_id}: unavailable at {base_url}")
