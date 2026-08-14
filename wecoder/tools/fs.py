"""Filesystem tools (Phase 03).

Implements ``list_dir``, ``read_file``, ``write_file``, and ``edit_file``.
Each tool resolves paths through :class:`Workspace`, honours the ignore
matcher and secret denylist, and returns a structured :class:`ToolResult`.

No model calls, no agent loop.  These are the primitives Phase 04 will call.
"""

from __future__ import annotations

from wecoder.errors import (
    DeniedSecretError,
    EditMismatchError,
    FileTooLargeError,
    PathEscapeError,
    ToolError,
)
from wecoder.tools.base import ToolContext, ToolResult
from wecoder.workspace.secrets import is_secret_path

# A small heuristic for binary detection: a file is treated as binary if it
# contains a NUL byte within the first chunk we read, mirroring how git
# classifies files.
_BINARY_SNIFF_BYTES = 8_192


def _is_binary(data: bytes) -> bool:
    return b"\x00" in data[:_BINARY_SNIFF_BYTES]


def _error_result(exc: Exception) -> ToolResult:
    """Map a :class:`ToolError` (or any exception) to a failure result."""
    if isinstance(exc, ToolError):
        return ToolResult.failure(str(exc), error_type=type(exc).__name__)
    return ToolResult.failure(f"{type(exc).__name__}: {exc}", error_type="ToolError")


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


class ListDir:
    """List entries in a workspace directory, respecting ignore rules."""

    name = "list_dir"
    description = (
        "List the entries of a directory inside the workspace. Respects the "
        "ignore rules (e.g. .git, node_modules) and caps the returned count."
    )
    parameters_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path relative to the workspace root. "
                "Defaults to the workspace root.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    async def execute(self, args: dict[str, object], ctx: ToolContext) -> ToolResult:
        try:
            rel = args.get("path") or "."
            target = ctx.workspace.resolve(str(rel))
            if not target.exists():
                return ToolResult.failure(f"path does not exist: {rel}")
            if not target.is_dir():
                return ToolResult.failure(f"not a directory: {rel}")
            limit = ctx.limits.max_list_dir_entries

            entries: list[tuple[str, str]] = []
            ignored = 0
            try:
                children = sorted(target.iterdir(), key=lambda p: p.name)
            except OSError as exc:
                return _error_result(exc)
            for child in children:
                if ctx.workspace.ignore.is_ignored(child):
                    ignored += 1
                    continue
                kind = "dir" if child.is_dir() else "file"
                entries.append((kind, child.name))
                if len(entries) >= limit:
                    break
            lines = [f"{k}\t{n}" for k, n in entries]
            header = f"{len(entries)} entries"
            if ignored:
                header += f", {ignored} ignored"
            output = header + "\n" + "\n".join(lines)
            return ToolResult.success(
                output,
                data={
                    "entries": [{"kind": k, "name": n} for k, n in entries],
                    "ignored": ignored,
                    "truncated": len(entries) >= limit,
                },
            )
        except (PathEscapeError, DeniedSecretError, ToolError) as exc:
            return _error_result(exc)


class ReadFile:
    """Read a text file from the workspace, refusing binary and secrets."""

    name = "read_file"
    description = (
        "Read a text file from the workspace. Refuses denylisted (secret) "
        "paths and binary files. Enforces a maximum file size."
    )
    parameters_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to the workspace root.",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict[str, object], ctx: ToolContext) -> ToolResult:
        try:
            rel = args.get("path")
            if not rel:
                return ToolResult.failure("'path' is required")
            resolved = ctx.workspace.resolve(str(rel))
            if not resolved.exists():
                return ToolResult.failure(f"file does not exist: {rel}")
            if resolved.is_dir():
                return ToolResult.failure(f"path is a directory: {rel}")
            size = resolved.stat().st_size
            ctx.policy.check_read(ctx.workspace, resolved, size=size)
            limit = ctx.limits.max_read_file_bytes
            if size > limit:
                raise FileTooLargeError(
                    f"file {resolved.name!r} is {size} bytes; limit is {limit}"
                )
            with resolved.open("rb") as fh:
                data = fh.read(limit + 1)
            if _is_binary(data):
                return ToolResult.failure(
                    f"refused to read binary file: {rel}",
                    error_type="FileTooLargeError",
                    data={"size": size, "binary": True},
                )
            text = data.decode("utf-8", errors="replace")
            if len(data) > limit:
                text = _truncate(text, limit)
            return ToolResult.success(
                text,
                data={
                    "path": str(rel),
                    "bytes": min(size, limit),
                    "truncated": size > limit,
                },
            )
        except (FileTooLargeError, PathEscapeError, DeniedSecretError, ToolError) as exc:
            return _error_result(exc)
        except OSError as exc:
            return _error_result(exc)


class WriteFile:
    """Write text to a workspace file, creating parents inside the jail."""

    name = "write_file"
    description = (
        "Write text content to a file inside the workspace, creating parent "
        "directories only inside the jail. Refuses secret paths and enforces "
        "a maximum write size."
    )
    parameters_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to the workspace root.",
            },
            "content": {
                "type": "string",
                "description": "The text content to write.",
            },
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict[str, object], ctx: ToolContext) -> ToolResult:
        try:
            rel = args.get("path")
            if not rel:
                return ToolResult.failure("'path' is required")
            content = args.get("content")
            if not isinstance(content, str):
                return ToolResult.failure("'content' must be a string")
            resolved = ctx.workspace.resolve(str(rel))
            size = len(content.encode("utf-8"))
            ctx.policy.check_write(ctx.workspace, resolved, size=size)
            limit = ctx.limits.max_write_file_bytes
            if size > limit:
                raise FileTooLargeError(
                    f"write of {size} bytes to {resolved.name!r} exceeds limit {limit}"
                )
            # Parents are created only after resolve() confirmed the target
            # is inside the jail; mkdir(parents=True) cannot escape because
            # the resolved path is already contained.
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with resolved.open("w", encoding="utf-8") as fh:
                fh.write(content)
            return ToolResult.success(
                f"wrote {size} bytes to {rel}",
                data={"path": str(rel), "bytes": size},
            )
        except (FileTooLargeError, PathEscapeError, DeniedSecretError, ToolError) as exc:
            return _error_result(exc)
        except OSError as exc:
            return _error_result(exc)


class EditFile:
    """Replace a unique occurrence of ``old_text`` with ``new_text``.

    Default behaviour replaces ``old_text`` only when it occurs exactly once.
    Use ``replace_all=True`` to replace every occurrence.
    """

    name = "edit_file"
    description = (
        "Edit a file by replacing old_text with new_text. By default the "
        "edit fails unless old_text occurs exactly once. Pass replace_all "
        "to replace every occurrence."
    )
    parameters_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to the workspace root.",
            },
            "old_text": {
                "type": "string",
                "description": "The exact text to replace.",
            },
            "new_text": {
                "type": "string",
                "description": "The replacement text.",
            },
            "replace_all": {
                "type": "boolean",
                "description": "If true, replace every occurrence. Default false.",
            },
        },
        "required": ["path", "old_text", "new_text"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict[str, object], ctx: ToolContext) -> ToolResult:
        try:
            rel = args.get("path")
            if not rel:
                return ToolResult.failure("'path' is required")
            old_text = args.get("old_text")
            new_text = args.get("new_text")
            if not isinstance(old_text, str) or not isinstance(new_text, str):
                return ToolResult.failure("'old_text' and 'new_text' must be strings")
            replace_all = bool(args.get("replace_all", False))

            resolved = ctx.workspace.resolve(str(rel))
            if not resolved.exists():
                return ToolResult.failure(f"file does not exist: {rel}")
            if resolved.is_dir():
                return ToolResult.failure(f"path is a directory: {rel}")
            if is_secret_path(resolved):
                return _error_result(
                    DeniedSecretError(
                        f"refused edit of secret-like path {resolved.name!r}"
                    )
                )
            with resolved.open("r", encoding="utf-8") as fh:
                content = fh.read()

            count = content.count(old_text)
            if count == 0:
                raise EditMismatchError(
                    f"old_text not found in {rel}; edit refused"
                )
            if count > 1 and not replace_all:
                raise EditMismatchError(
                    f"old_text occurs {count} times in {rel}; pass replace_all "
                    "to replace every occurrence"
                )

            new_content = (
                content.replace(old_text, new_text)
                if replace_all
                else content.replace(old_text, new_text, 1)
            )
            size = len(new_content.encode("utf-8"))
            ctx.policy.check_write(ctx.workspace, resolved, size=size)
            limit = ctx.limits.max_write_file_bytes
            if size > limit:
                raise FileTooLargeError(
                    f"edited file would be {size} bytes; limit is {limit}"
                )
            with resolved.open("w", encoding="utf-8") as fh:
                fh.write(new_content)
            replaced = count if replace_all else 1
            return ToolResult.success(
                f"replaced {replaced} occurrence(s) in {rel}",
                data={"path": str(rel), "replacements": replaced},
            )
        except (EditMismatchError, FileTooLargeError, PathEscapeError, ToolError) as exc:
            return _error_result(exc)
        except OSError as exc:
            return _error_result(exc)


__all__ = ["ListDir", "ReadFile", "WriteFile", "EditFile"]
