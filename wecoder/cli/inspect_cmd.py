"""``wecoder inspect`` command (Phase 03).

Prints a human-readable workspace sketch: resolved root, language hints, a
tree excerpt, the available tool names, and ignore/context statistics.  It
makes no model call and works against a temporary test project.
"""

from __future__ import annotations

from pathlib import Path

from wecoder.config.settings import Settings
from wecoder.context.packer import ContextPacker
from wecoder.tools.registry import default_registry
from wecoder.workspace.workspace import Workspace


def inspect(settings: Settings, *, cwd: str | Path | None = None) -> None:
    """Print the workspace sketch to stdout.

    ``cwd`` is the directory the CLI was invoked from; a relative
    ``settings.project.workspace`` (e.g. the default ``"."``) is resolved
    against it so ``inspect`` looks at the intended project, not the
    process's current directory in tests.
    """
    workspace_path = settings.project.workspace or "."
    base = Path(cwd) if cwd is not None else Path.cwd()
    wp = Path(workspace_path)
    resolved_path = wp if wp.is_absolute() else (base / wp)
    workspace = Workspace.open(resolved_path)

    packer = ContextPacker()
    bundle = packer.pack(workspace)

    registry = default_registry()

    print(f"workspace root: {bundle.root}")
    if bundle.language_hints:
        print(f"language hints: {', '.join(bundle.language_hints)}")
    else:
        print("language hints: (none detected)")

    print("tree excerpt:")
    if bundle.tree_excerpt:
        for line in bundle.tree_excerpt.splitlines():
            print(f"  {line}")
    else:
        print("  (empty)")

    if bundle.notes:
        print("notes:")
        for note in bundle.notes:
            print(f"  - {note}")

    print(f"approx bytes: {bundle.approx_bytes}")
    print("tools:")
    for name in registry.names():
        print(f"  {name}")


__all__ = ["inspect"]
