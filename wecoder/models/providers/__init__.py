"""Built-in provider adapters."""

from wecoder.models.providers.ollama import OllamaProvider
from wecoder.models.providers.openai_compat import OpenAICompatProvider

__all__ = ["OllamaProvider", "OpenAICompatProvider"]
