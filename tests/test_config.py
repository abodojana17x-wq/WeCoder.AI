"""Tests for the configuration layer (defaults, files, env, redaction)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from wecoder.config.settings import Settings
from wecoder.errors import ConfigError


def _write_config(project_dir: Path, text: str) -> Path:
    config_dir = project_dir / ".wecoder"
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "config.toml"
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def _write_user_config(home_dir: Path, text: str) -> Path:
    config_dir = home_dir / ".wecoder"
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "config.toml"
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def test_defaults_load_without_files(project_dir: Path, home_dir: Path) -> None:
    settings = Settings.load(cwd=project_dir, home=home_dir)
    assert settings.project.workspace == "."
    assert settings.model.provider == "ollama"
    assert settings.model.model == "qwen2.5-coder"
    assert settings.model.base_url == ""
    assert settings.model.api_key_env == "OPENAI_API_KEY"
    assert settings.limits.max_turns == 20
    assert settings.limits.max_tokens == 100000
    assert settings.logging.level == "INFO"
    assert settings.config_paths == ()


def test_project_toml_overrides_defaults(project_dir: Path, home_dir: Path) -> None:
    path = _write_config(
        project_dir,
        """
        [model]
        provider = "openai_compat"
        model = "gpt-4o-mini"

        [logging]
        level = "DEBUG"

        [limits]
        max_turns = 5
        """,
    )
    settings = Settings.load(cwd=project_dir, home=home_dir)
    assert settings.model.provider == "openai_compat"
    assert settings.model.model == "gpt-4o-mini"
    assert settings.logging.level == "DEBUG"
    assert settings.limits.max_turns == 5
    # Unset keys keep their defaults.
    assert settings.limits.max_tokens == 100000
    assert settings.project.workspace == "."
    assert settings.config_paths == (path,)


def test_user_file_is_lower_precedence_than_project(
    project_dir: Path, home_dir: Path
) -> None:
    _write_user_config(home_dir, '[model]\nprovider = "user_provider"\n')
    _write_config(project_dir, '[model]\nprovider = "project_provider"\n')

    settings = Settings.load(cwd=project_dir, home=home_dir)
    assert settings.model.provider == "project_provider"
    assert settings.config_paths[0] == home_dir / ".wecoder" / "config.toml"
    assert settings.config_paths[1] == project_dir / ".wecoder" / "config.toml"


def test_env_overrides_file(project_dir: Path, home_dir: Path) -> None:
    _write_config(project_dir, '[logging]\nlevel = "INFO"\n')
    settings = Settings.load(
        cwd=project_dir,
        home=home_dir,
        env={"WECODER_LOGGING_LEVEL": "DEBUG"},
    )
    assert settings.logging.level == "DEBUG"


def test_env_int_coercion(project_dir: Path, home_dir: Path) -> None:
    settings = Settings.load(
        cwd=project_dir,
        home=home_dir,
        env={"WECODER_LIMITS_MAX_TURNS": "7"},
    )
    assert settings.limits.max_turns == 7


def test_invalid_toml_raises_config_error(project_dir: Path, home_dir: Path) -> None:
    path = _write_config(project_dir, "[model\nthis is not valid toml")
    with pytest.raises(ConfigError) as excinfo:
        Settings.load(cwd=project_dir, home=home_dir)
    assert str(path) in str(excinfo.value)


def test_redacted_masks_planted_secret(project_dir: Path, home_dir: Path) -> None:
    settings = Settings.load(
        cwd=project_dir,
        home=home_dir,
        env={"WECODER_MODEL_API_KEY_ENV": "PLANTED_FAKE_SECRET"},
    )
    redacted = settings.redacted()
    # The planted fake secret must not leak, and non-sensitive values remain.
    assert "PLANTED_FAKE_SECRET" not in str(redacted)
    assert redacted["model"]["api_key_env"] == "***"
    assert redacted["model"]["provider"] == "ollama"
    assert redacted["logging"]["level"] == "INFO"
