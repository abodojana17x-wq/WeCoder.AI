"""Shared test fixtures.

Tests never write into the real repository's ``.wecoder/`` or the user's
home directory — they use throwaway directories under ``tmp_path`` and, where
needed, pass explicit ``cwd``/``home`` into ``Settings.load`` / ``main``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the repository root importable so tests run even without an editable
# install (keeps the suite offline and dependency-light).
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """A throwaway project directory (created on demand by each test)."""
    return tmp_path / "project"


@pytest.fixture
def home_dir(tmp_path: Path) -> Path:
    """A throwaway fake home directory."""
    return tmp_path / "home"
