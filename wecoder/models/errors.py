"""Normalized failures raised by model providers."""

from wecoder.errors import WecoderError


class ModelError(WecoderError):
    """Base class for expected model provider failures."""


class ModelConfigError(ModelError):
    """Provider configuration is absent or invalid."""


class ModelAuthError(ModelError):
    """A provider rejected authentication."""


class ModelUnavailableError(ModelError):
    """A provider cannot currently be reached or is unavailable."""


class ModelTimeoutError(ModelError):
    """A provider request exceeded its timeout."""


class ModelResponseError(ModelError):
    """A provider returned malformed or unexpected data."""


__all__ = [
    "ModelAuthError",
    "ModelConfigError",
    "ModelError",
    "ModelResponseError",
    "ModelTimeoutError",
    "ModelUnavailableError",
]
