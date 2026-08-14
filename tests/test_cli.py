"""Smoke tests for the CLI entry point (main)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from wecoder import __version__
from wecoder.cli.app import main

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_help_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_version_prints_package_version(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_status_exits_zero(project_dir: Path, home_dir: Path, capsys) -> None:
    project_dir.mkdir(exist_ok=True)
    assert main(["status"], cwd=str(project_dir), home=str(home_dir)) == 0
    out = capsys.readouterr().out
    assert f"wecoder {__version__}" in out
    assert "python" in out
    assert "config: none" in out
    assert "provider: ollama" in out


def test_status_reports_config_file(
    project_dir: Path, home_dir: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    config_dir = project_dir / ".wecoder"
    config_dir.mkdir()
    config = config_dir / "config.toml"
    config.write_text('[model]\nprovider = "openai_compat"\n', encoding="utf-8")

    assert main(["status"], cwd=str(project_dir), home=str(home_dir)) == 0
    out = capsys.readouterr().out
    assert "config:" in out
    assert str(config) in out
    assert "provider: openai_compat" in out


def test_init_writes_default_config(project_dir: Path, home_dir: Path, capsys) -> None:
    project_dir.mkdir(exist_ok=True)
    assert main(["init"], cwd=str(project_dir), home=str(home_dir)) == 0

    config = project_dir / ".wecoder" / "config.toml"
    assert config.is_file()
    text = config.read_text(encoding="utf-8")
    assert 'provider = "ollama"' in text
    assert 'model = "qwen2.5-coder"' in text
    # The generated config must not contain secrets.
    assert "OPENAI_API_KEY" in text  # the env var *name*, not a secret value
    capsys.readouterr()


def test_init_refuses_overwrite_without_force(
    project_dir: Path, home_dir: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    assert main(["init"], cwd=str(project_dir), home=str(home_dir)) == 0
    capsys.readouterr()

    code = main(["init"], cwd=str(project_dir), home=str(home_dir))
    assert code == 1
    assert "already exists" in capsys.readouterr().err


def test_init_force_overwrites(project_dir: Path, home_dir: Path) -> None:
    project_dir.mkdir(exist_ok=True)
    config = project_dir / ".wecoder" / "config.toml"
    config.parent.mkdir()
    config.write_text('[model]\nprovider = "openai_compat"\n', encoding="utf-8")

    assert main(["init", "--force"], cwd=str(project_dir), home=str(home_dir)) == 0
    assert 'provider = "ollama"' in config.read_text(encoding="utf-8")


def test_unknown_command_is_usage_error(project_dir: Path, home_dir: Path) -> None:
    project_dir.mkdir(exist_ok=True)
    with pytest.raises(SystemExit) as excinfo:
        main(["bogus"], cwd=str(project_dir), home=str(home_dir))
    assert excinfo.value.code == 2  # argparse uses exit code 2 for usage errors


def test_unexpected_error_exits_two(project_dir: Path, home_dir: Path, monkeypatch) -> None:
    project_dir.mkdir(exist_ok=True)

    def _boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("wecoder.config.settings.Settings.load", staticmethod(_boom))
    code = main(["status"], cwd=str(project_dir), home=str(home_dir))
    assert code == 2


def test_python_dash_m_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "wecoder", "--version"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_inspect_works_on_temp_project(project_dir: Path, home_dir: Path, capsys) -> None:
    project_dir.mkdir(exist_ok=True)
    (project_dir / "main.py").write_text("print('hi')\n")
    (project_dir / "pyproject.toml").write_text("[project]\nname='x'\n")
    assert main(["inspect"], cwd=str(project_dir), home=str(home_dir)) == 0
    out = capsys.readouterr().out
    assert "workspace root:" in out
    assert "tools:" in out
    assert "read_file" in out
    assert "list_dir" in out
    assert "run_command" in out


def test_inspect_shows_language_hints(project_dir: Path, home_dir: Path, capsys) -> None:
    project_dir.mkdir(exist_ok=True)
    (project_dir / "app.py").write_text("x=1\n")
    (project_dir / "lib.ts").write_text("const x=1\n")
    assert main(["inspect"], cwd=str(project_dir), home=str(home_dir)) == 0
    out = capsys.readouterr().out
    assert "Python" in out
    assert "TypeScript" in out
