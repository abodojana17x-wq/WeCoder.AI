"""Budgeted project context packing (Phase 03).

Produces a :class:`ContextBundle`: a compact, size-capped sketch of a
workspace containing the root, language hints, a top-level tree excerpt, and
ignore statistics.  Never includes secret or ignored-bulky contents.  The
walk is hard-capped so a monorepo cannot be dumped into a future prompt by
accident (ADR-019).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from wecoder.tools.base import MAX_CONTEXT_SKETCH_BYTES, MAX_TREE_WALK_FILES
from wecoder.workspace.secrets import is_secret_path
from wecoder.workspace.workspace import Workspace

# Lightweight language detection from file extensions / manifests.  Kept
# deliberately small — Phase 12 may grow this into a plugin surface.
_LANGUAGE_HINTS: dict[str, str] = {
    ".py": "Python",
    ".rs": "Rust",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".c": "C/C++",
    ".h": "C/C++",
    ".cpp": "C/C++",
    ".cc": "C/C++",
    ".hpp": "C/C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".dart": "Dart",
}

# Files / lockfiles that also signal a language, even without a common ext.
_MANIFEST_HINTS: dict[str, str] = {
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "setup.py": "Python",
    "Pipfile": "Python",
    "Cargo.toml": "Rust",
    "package.json": "JavaScript",
    "go.mod": "Go",
    "pom.xml": "Java",
    "build.gradle": "Java",
    "build.gradle.kts": "Kotlin",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "pubspec.yaml": "Dart",
}

# Important top-level filenames always surfaced in the tree excerpt.
_IMPORTANT_NAMES: frozenset[str] = frozenset(
    {
        "README.md",
        "README.rst",
        "pyproject.toml",
        "setup.py",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        "Dockerfile",
        ".gitignore",
    }
)


@dataclass(frozen=True)
class ContextBundle:
    """The structured, budgeted sketch returned by :class:`ContextPacker`."""

    root: str
    language_hints: list[str]
    tree_excerpt: str
    notes: list[str] = field(default_factory=list)
    approx_bytes: int = 0


class ContextPacker:
    """Pack a workspace into a budgeted :class:`ContextBundle`."""

    def __init__(self, *, max_bytes: int = MAX_CONTEXT_SKETCH_BYTES) -> None:
        self._max_bytes = max_bytes

    def pack(
        self,
        workspace: Workspace,
        extra_paths: list[str] | None = None,
    ) -> ContextBundle:
        root = workspace.root
        notes: list[str] = []
        language_counter: Counter[str] = Counter()

        # Top-level scan for manifest language hints.
        try:
            top_entries = sorted(root.iterdir(), key=lambda p: p.name)
        except OSError:
            top_entries = []
        for entry in top_entries:
            hint = _MANIFEST_HINTS.get(entry.name)
            if hint:
                language_counter[hint] += 1

        # Bounded walk for language hints + tree excerpt.
        files_seen = 0
        ignored_count = 0
        tree_lines: list[str] = []
        capped = False

        for file_path, rel_str in _walk_bounded(workspace, MAX_TREE_WALK_FILES):
            files_seen += 1
            if files_seen >= MAX_TREE_WALK_FILES:
                capped = True
                break
            if workspace.ignore.is_ignored(file_path) or is_secret_path(file_path):
                ignored_count += 1
                continue
            hint = _LANGUAGE_HINTS.get(file_path.suffix.lower())
            if hint:
                language_counter[hint] += 1
            if _is_top_level(root, file_path) or file_path.name in _IMPORTANT_NAMES:
                tree_lines.append(rel_str)

        if capped:
            notes.append(f"tree walk capped at {MAX_TREE_WALK_FILES} files")
        if ignored_count:
            notes.append(f"ignored {ignored_count} paths")

        # Surface a small top-level listing even if no "important" file matched.
        if not tree_lines:
            tree_lines = [
                p.name for p in top_entries[:20] if not workspace.ignore.is_ignored(p)
            ]

        # Compose the tree excerpt, staying within the byte budget.
        tree_excerpt = _compose_tree(tree_lines, self._max_bytes)

        # Incorporate explicit extra paths as additional hints.
        if extra_paths:
            for ep in extra_paths:
                resolved = workspace.resolve(ep)
                hint = _LANGUAGE_HINTS.get(resolved.suffix.lower())
                if hint:
                    language_counter[hint] += 1

        language_hints = [lang for lang, _ in language_counter.most_common()]
        approx_bytes = len(tree_excerpt.encode("utf-8")) + sum(
            len(h.encode("utf-8")) for h in language_hints
        )

        return ContextBundle(
            root=str(root),
            language_hints=language_hints,
            tree_excerpt=tree_excerpt,
            notes=notes,
            approx_bytes=approx_bytes,
        )


def _walk_bounded(workspace: Workspace, max_files: int):
    """Yield ``(absolute_path, posix_rel)`` for files under the root, bounded."""
    root = workspace.root
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
            if workspace.ignore.is_ignored(entry):
                continue
            if entry.is_dir():
                try:
                    real = entry.resolve(strict=False)
                    real.relative_to(root)
                except (ValueError, OSError):
                    continue
                stack.append(entry)
            elif entry.is_file():
                count += 1
                try:
                    rel = entry.relative_to(root)
                except ValueError:
                    continue
                yield entry, rel.as_posix()


def _is_top_level(root: Path, file_path: Path) -> bool:
    try:
        rel = file_path.relative_to(root)
    except ValueError:
        return False
    return len(rel.parts) <= 1


def _compose_tree(lines: list[str], max_bytes: int) -> str:
    """Join ``lines`` into a tree string, truncating within the byte budget."""
    out: list[str] = []
    size = 0
    for line in lines:
        encoded = line.encode("utf-8")
        if size + len(encoded) + 1 > max_bytes:
            out.append(f"...[tree truncated at {max_bytes} bytes]")
            break
        out.append(line)
        size += len(encoded) + 1
    return "\n".join(out)


__all__ = ["ContextBundle", "ContextPacker"]
