"""Vendor-neutral model abstraction layer (Phase 02)."""

from wecoder.models.base import ModelProvider
from wecoder.models.registry import ModelRegistry, default_registry
from wecoder.models.types import (
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    Message,
    ModelCapabilities,
    ToolCall,
    ToolSpec,
    Usage,
)

__all__ = [
    "CompletionChunk",
    "CompletionRequest",
    "CompletionResponse",
    "Message",
    "ModelCapabilities",
    "ModelProvider",
    "ModelRegistry",
    "ToolCall",
    "ToolSpec",
    "Usage",
    "default_registry",
]
