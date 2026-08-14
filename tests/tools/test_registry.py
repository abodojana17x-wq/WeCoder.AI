"""Tool registry tests (Phase 03)."""

from __future__ import annotations

from pathlib import Path

import pytest
from wecoder.errors import ToolError
from wecoder.tools.base import ToolResult
from wecoder.tools.registry import ToolRegistry, default_registry

EXPECTED_TOOLS = {
    "list_dir",
    "read_file",
    "write_file",
    "edit_file",
    "search_text",
    "run_command",
}


def test_default_registry_has_six_tools() -> None:
    registry = default_registry()
    assert set(registry.names()) == EXPECTED_TOOLS
    assert len(registry.names()) == 6


def test_registry_schemas_are_valid_json_schema() -> None:
    registry = default_registry()
    schemas = registry.schemas()
    assert len(schemas) == 6
    for entry in schemas:
        assert "name" in entry and isinstance(entry["name"], str)
        assert "description" in entry and isinstance(entry["description"], str)
        params = entry["parameters"]
        assert isinstance(params, dict)
        assert params["type"] == "object"
        assert "properties" in params
        assert isinstance(params["properties"], dict)


def test_registry_get_returns_tool() -> None:
    registry = default_registry()
    tool = registry.get("read_file")
    assert tool.name == "read_file"
    assert hasattr(tool, "execute")


def test_registry_get_unknown_raises() -> None:
    registry = default_registry()
    with pytest.raises(ToolError):
        registry.get("does-not-exist")


def test_registry_rejects_duplicate(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    registry = default_registry()
    with pytest.raises(ToolError):
        registry.register(registry.get("read_file"))


def test_registry_rejects_empty_name() -> None:
    class _EmptyName:
        name = ""
        description = "x"
        parameters_schema = {"type": "object"}

        async def execute(self, args, ctx):  # pragma: no cover
            return ToolResult.success("")

    registry = ToolRegistry()
    with pytest.raises(ToolError):
        registry.register(_EmptyName())  # type: ignore[arg-type]


def test_registry_names_are_deterministic() -> None:
    r1 = default_registry()
    r2 = default_registry()
    assert r1.names() == r2.names()
    assert r1.names() == tuple(sorted(EXPECTED_TOOLS))
