"""Developer system-prompt loader (Phase 04).

Loads the developer prompt from ``developer.md`` next to this module so the
prompt text is not hardcoded in the CLI or the loop.  The file is read once
and cached.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPT_DIR = Path(__file__).resolve().parent
_DEVELOPER_PROMPT_FILE = _PROMPT_DIR / "developer.md"


@lru_cache(maxsize=1)
def load_developer_prompt() -> str:
    """Return the Developer agent system prompt text."""
    return _DEVELOPER_PROMPT_FILE.read_text(encoding="utf-8")


__all__ = ["load_developer_prompt"]
