"""Tool registry (Phase 03).

Holds the built-in tools, rejects duplicate registrations, lists tools in
deterministic order, and exports JSON Schema descriptions suitable for a
future model's tool-calling surface (Phase 04).  No model calls here.
"""

from __future__ import annotations

from wecoder.errors import ToolError
from wecoder.tools.base import Tool
from wecoder.tools.fs import EditFile, ListDir, ReadFile, WriteFile
from wecoder.tools.search import SearchText
from wecoder.tools.shell import RunCommand


class ToolRegistry:
    """A name-indexed registry of :class:`Tool` instances."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register ``tool`` by its ``name``.

        Raises:
            ToolError: if the name is empty or already registered.
        """
        name = getattr(tool, "name", "")
        if not name:
            raise ToolError("tool name cannot be empty")
        if name in self._tools:
            raise ToolError(f"tool already registered: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> Tool:
        """Return the tool registered as ``name``.

        Raises:
            ToolError: if no tool is registered under ``name``.
        """
        try:
            return self._tools[name]
        except KeyError as exc:
            known = ", ".join(self.names())
            raise ToolError(
                f"unknown tool {name!r}; known tools: {known}"
            ) from exc

    def names(self) -> tuple[str, ...]:
        """Return registered tool names in deterministic (sorted) order."""
        return tuple(sorted(self._tools))

    def tools(self) -> tuple[Tool, ...]:
        """Return registered tools sorted by name."""
        return tuple(self._tools[name] for name in self.names())

    def schemas(self) -> list[dict[str, object]]:
        """Export JSON Schema descriptions for every registered tool."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
            }
            for tool in self.tools()
        ]


def default_registry() -> ToolRegistry:
    """Return a registry pre-loaded with the six Phase 03 built-in tools."""
    registry = ToolRegistry()
    for tool in (
        ListDir(),
        ReadFile(),
        WriteFile(),
        EditFile(),
        SearchText(),
        RunCommand(),
    ):
        registry.register(tool)
    return registry


__all__ = ["ToolRegistry", "default_registry"]
