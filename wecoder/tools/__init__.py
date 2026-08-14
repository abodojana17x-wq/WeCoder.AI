"""Tool system (Phase 03).

Exposes the :class:`Tool` protocol, :class:`ToolResult`, :class:`ToolContext`,
the :class:`ToolRegistry` with the six built-in tools, and the tool error
hierarchy.  No model calls; these are the primitives Phase 04 consumes.
"""

from wecoder.tools.base import (
    DEFAULT_COMMAND_TIMEOUT_SECONDS,
    MAX_COMMAND_OUTPUT_BYTES,
    MAX_CONTEXT_SKETCH_BYTES,
    MAX_LIST_DIR_ENTRIES,
    MAX_READ_FILE_BYTES,
    MAX_SEARCH_MATCHES,
    MAX_TREE_WALK_FILES,
    MAX_WRITE_FILE_BYTES,
    Tool,
    ToolContext,
    ToolLimits,
    ToolResult,
)
from wecoder.tools.errors import (
    CommandFailedError,
    CommandTimeoutError,
    DeniedSecretError,
    EditMismatchError,
    FileTooLargeError,
    PathEscapeError,
    ToolError,
)
from wecoder.tools.fs import EditFile, ListDir, ReadFile, WriteFile
from wecoder.tools.registry import ToolRegistry, default_registry
from wecoder.tools.search import SearchText
from wecoder.tools.shell import RunCommand

__all__ = [
    "Tool",
    "ToolResult",
    "ToolContext",
    "ToolLimits",
    "ToolRegistry",
    "default_registry",
    "ListDir",
    "ReadFile",
    "WriteFile",
    "EditFile",
    "SearchText",
    "RunCommand",
    "ToolError",
    "PathEscapeError",
    "DeniedSecretError",
    "FileTooLargeError",
    "EditMismatchError",
    "CommandTimeoutError",
    "CommandFailedError",
    "MAX_READ_FILE_BYTES",
    "MAX_WRITE_FILE_BYTES",
    "MAX_LIST_DIR_ENTRIES",
    "MAX_SEARCH_MATCHES",
    "MAX_COMMAND_OUTPUT_BYTES",
    "DEFAULT_COMMAND_TIMEOUT_SECONDS",
    "MAX_CONTEXT_SKETCH_BYTES",
    "MAX_TREE_WALK_FILES",
]
