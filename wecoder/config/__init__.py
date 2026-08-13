"""Configuration layer for WeCoder.AI.

This package exposes a frozen, layered :class:`~wecoder.config.settings.Settings`
object.  Precedence (highest last wins):

1. Built-in defaults
2. User file ``~/.wecoder/config.toml`` if present
3. Project file ``<cwd>/.wecoder/config.toml`` if present
4. Environment variables prefixed with ``WECODER_``
5. CLI flags (handled by the CLI layer)
"""

from wecoder.config.settings import (
    LimitsSettings,
    LoggingSettings,
    ModelSettings,
    ProjectSettings,
    Settings,
)

__all__ = [
    "Settings",
    "ProjectSettings",
    "ModelSettings",
    "LimitsSettings",
    "LoggingSettings",
]
