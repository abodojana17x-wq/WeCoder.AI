"""Workspace text search tool (Phase 03).

Searches text files inside the workspace for a literal substring, skipping
ignored paths, secret files, binary files, and oversized files.  Stops at the
match cap.  Results are size-bounded so they stay useful for a future agent
context without dumping a monorepo.
"""

from __future__ import annotations

from pathlib import Path

from wecoder.errors import PathEscapeError, ToolError
from wecoder.tools.base import ToolContext, ToolResult
from wecoder.tools.fs import _is_binary, _truncate
from wecoder.workspace.secrets import is_secret_path

# Maximum number of bytes read from a single candidate file during search.
_SEARCH_FILE_READ_LIMIT = 200_000


class SearchText:
    """Search for a literal substring across the workspace."""

    name = "search_text"
    description = (
        "Search the workspace for a literal query string. Skips ignored and "
        "secret files, skips binary files, and caps the number of matches."
    )
    parameters_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The literal text to search for.",
            },
            "path": {
                "type": "string",
                "description": "Optional directory to scope the search to, "
                "relative to the workspace root.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict[str, object], ctx: ToolContext) -> ToolResult:
        try:
            query = args.get("query")
            if not isinstance(query, str) or not query:
                return ToolResult.failure("'query' must be a non-empty string")
            rel = args.get("path") or "."
            root = ctx.workspace.resolve(str(rel))
            if not root.exists():
                return ToolResult.failure(f"path does not exist: {rel}")
            if not root.is_dir():
                return ToolResult.failure(f"not a directory: {rel}")

            max_matches = ctx.limits.max_search_matches
            max_files = 5_000
            matches: list[dict[str, object]] = []
            files_scanned = 0
            files_skipped = 0
            capped = False

            for file_path in _walk_files(root, ctx, max_files=max_files):
                files_scanned += 1
                if is_secret_path(file_path) or ctx.workspace.ignore.is_ignored(
                    file_path
                ):
                    files_skipped += 1
                    continue
                hit = _search_file(file_path, query)
                if hit is None:
                    # None means skipped (binary / too large / unreadable).
                    files_skipped += 1
                    continue
                for line_no, line_text in hit:
                    matches.append(
                        {
                            "path": str(file_path.relative_to(ctx.workspace.root)),
                            "line": line_no,
                            "text": line_text,
                        }
                    )
                    if len(matches) >= max_matches:
                        capped = True
                        break
                if capped:
                    break

            lines = [f"{m['path']}:{m['line']}: {m['text']}" for m in matches]
            header = f"{len(matches)} match(es) in {files_scanned} file(s)"
            if files_skipped:
                header += f", {files_skipped} skipped"
            if capped:
                header += ", capped at max matches"
            output = _truncate(header + "\n" + "\n".join(lines), 8_000)
            return ToolResult.success(
                output,
                data={
                    "matches": matches,
                    "files_scanned": files_scanned,
                    "files_skipped": files_skipped,
                    "capped": capped,
                },
            )
        except (PathEscapeError, ToolError) as exc:
            return _error_result(exc)
        except OSError as exc:
            return _error_result(exc)


def _error_result(exc: Exception) -> ToolResult:
    if isinstance(exc, ToolError):
        return ToolResult.failure(str(exc), error_type=type(exc).__name__)
    return ToolResult.failure(f"{type(exc).__name__}: {exc}", error_type="ToolError")


def _walk_files(root: Path, ctx: ToolContext, *, max_files: int):
    """Yield files under ``root`` up to ``max_files``, honouring the jail.

    Directory entries that are ignored are pruned so we never descend into
    ``.git`` or ``node_modules``.
    """
    count = 0
    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except OSError:
            continue
        for entry in entries:
            if count >= max_files:
                return
            if ctx.workspace.ignore.is_ignored(entry):
                continue
            if entry.is_dir():
                # Only descend into real directories inside the jail.
                try:
                    real = entry.resolve(strict=False)
                    real.relative_to(ctx.workspace.root)
                except (ValueError, OSError):
                    continue
                stack.append(entry)
            elif entry.is_file():
                count += 1
                yield entry


def _search_file(file_path: Path, query: str) -> list[tuple[int, str]] | None:
    """Return matching ``(line_no, line_text)`` pairs, or ``None`` if skipped."""
    try:
        size = file_path.stat().st_size
    except OSError:
        return None
    if size > _SEARCH_FILE_READ_LIMIT:
        return None
    try:
        with file_path.open("rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if _is_binary(data):
        return None
    text = data.decode("utf-8", errors="replace")
    hits: list[tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if query in line:
            hits.append((idx, _truncate(line.strip(), 240)))
    return hits


__all__ = ["SearchText"]
