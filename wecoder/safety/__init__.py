"""Safety policy hooks (Phase 03).

Exposes the :class:`Policy` protocol and :class:`DefaultPolicy`.  Interactive
approval arrives in Phase 06; Phase 03 ships only the hard security boundary.
"""

from wecoder.safety.policy import DefaultPolicy, Policy

__all__ = ["Policy", "DefaultPolicy"]
