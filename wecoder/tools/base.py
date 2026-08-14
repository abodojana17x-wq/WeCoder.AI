"""Tool system contracts (Phase 03).

Defines the :class:`Tool` protocol, the structured :class:`ToolResult`, the
:class:`ToolContext` carrying the workspace and budgets, and the budget
constants.  Phase 04 will select tools from the registry and feed their
results to a model — no model calls live here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from wecoder.safety.policy import Policy
from wecoder.workspace.workspace import Workspace

# --- Budgets (defaults; constants are fine for Phase 03) ---------------------

MAX_READ_FILE_BYTES = 200_000
MAX_WRITE_FILE_BYTES = 200_000
MAX_LIST_DIR_ENTRIES = 200
MAX_SEARCH_MATCHES = 50
MAX_COMMAND_OUTPUT_BYTES = 32_000
DEFAULT_COMMAND_TIMEOUT_SECONDS = 30
MAX_CONTEXT_SKETCH_BYTES = 20_000
MAX_TREE_WALK_FILES = 5_000


@dataclass(frozen=True)
class ToolLimits:
    """Carries the per-context budget caps.

    Defaults mirror the Phase 03 contract; a caller may construct a smaller
    set (e.g. for tests) without touching module globals.
    """

    max_read_file_bytes: int = MAX_READ_FILE_BYTES
    max_write_file_bytes: int = MAX_WRITE_FILE_BYTES
    max_list_dir_entries: int = MAX_LIST_DIR_ENTRIES
    max_search_matches: int = MAX_SEARCH_MATCHES
    max_command_output_bytes: int = MAX_COMMAND_OUTPUT_BYTES
    command_timeout_seconds: int = DEFAULT_COMMAND_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ToolContext:
    """Everything a tool needs at execution time.

    Carries the bound workspace, the active policy, and the budget limits.
    Tools never reach outside this context for paths or permissions.
    """

    workspace: Workspace
    policy: Policy
    limits: ToolLimits = field(default_factory=ToolLimits)


@dataclass(frozen=True)
class ToolResult:
    """Structured result returned by every tool.

    ``output`` is the model-facing textual representation (size-capped by
    the tool).  ``data`` is optional structured information.  ``error_type``
    is the class name of the failure when ``ok`` is ``False``.
    """

    ok: bool
    output: str = ""
    data: dict[str, object] | None = None
    error_type: str | None = None

    @classmethod
    def success(cls, output: str, data: dict[str, object] | None = None) -> ToolResult:
        return cls(ok=True, output=output, data=data, error_type=None)

    @classmethod
    def failure(
        cls,
        output: str,
        *,
        error_type: str | None = "ToolError",
        data: dict[str, object] | None = None,
    ) -> ToolResult:
        return cls(ok=False, output=output, data=data, error_type=error_type)


@runtime_checkable
class Tool(Protocol):
    """The stable tool surface consumed by the registry and Phase 04.

    Each tool advertises a name, a description, a JSON Schema for its
    parameters, and an async ``execute`` returning a :class:`ToolResult`.
    """

    name: str
    description: str
    parameters_schema: dict[str, object]

    async def execute(self, args: dict[str, object], ctx: ToolContext) -> ToolResult: ...


__all__ = [
    "MAX_READ_FILE_BYTES",
    "MAX_WRITE_FILE_BYTES",
    "MAX_LIST_DIR_ENTRIES",
    "MAX_SEARCH_MATCHES",
    "MAX_COMMAND_OUTPUT_BYTES",
    "DEFAULT_COMMAND_TIMEOUT_SECONDS",
    "MAX_CONTEXT_SKETCH_BYTES",
    "MAX_TREE_WALK_FILES",
    "ToolLimits",
    "ToolContext",
    "ToolResult",
    "Tool",
]
