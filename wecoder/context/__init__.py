"""Budgeted project context (Phase 03).

Exposes :class:`ContextPacker` and :class:`ContextBundle`.  Produces a
size-capped workspace sketch that Phase 04 can drop into a system prompt.
"""

from wecoder.context.packer import ContextBundle, ContextPacker

__all__ = ["ContextBundle", "ContextPacker"]
