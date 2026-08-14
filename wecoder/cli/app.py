"""The WeCoder.AI command-line application (Phase 01+).

Exit codes:
    0  success
    1  usage / configuration error
    2  unexpected (internal) error

Later phases may add codes, but 0/1/2 retain these meanings.
"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import sys
from collections.abc import Sequence
from pathlib import Path

from wecoder import __version__
from wecoder.cli.inspect_cmd import inspect as inspect_workspace
from wecoder.cli.models_cmd import list_models, ping_model
from wecoder.config.settings import DEFAULT_CONFIG_TEXT, Settings
from wecoder.errors import ConfigError, WecoderError
from wecoder.observability.logging import configure_logging

_PROG = "wecoder"
_LOGGER = logging.getLogger("wecoder.cli")

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_INTERNAL = 2


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser (exported for tests)."""
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description="WeCoder.AI — an offline-first, model-agnostic AI software "
        "development team (engineering foundation).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="increase log verbosity to DEBUG",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    init_parser = subparsers.add_parser(
        "init", help="write a default project config (.wecoder/config.toml)"
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing config file",
    )

    subparsers.add_parser("status", help="print version, config source, and environment status")
    models_parser = subparsers.add_parser(
        "models", help="inspect or explicitly check model providers"
    )
    models_subparsers = models_parser.add_subparsers(dest="models_command", required=True)
    models_subparsers.add_parser("list", help="list registered providers (no network calls)")
    models_subparsers.add_parser(
        "ping", help="explicitly check the configured provider; may contact it"
    )

    # Phase 03: workspace / tool / context inspection. No model call.
    subparsers.add_parser(
        "inspect",
        help="print the resolved workspace root, tree excerpt, language "
        "hints, and available tool names (no model call)",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    cwd: str | Path | None = None,
    home: str | Path | None = None,
) -> int:
    """Run the CLI and return an exit code.

    ``cwd``/``home`` are forwarded to :meth:`Settings.load` so tests can run
    against isolated directories.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = Settings.load(cwd=cwd, home=home)
        effective_level = "DEBUG" if args.verbose else settings.logging.level
        configure_logging(effective_level)

        if args.command is None:
            parser.print_help(sys.stdout)
            return EXIT_OK

        if args.command == "init":
            workdir = Path(cwd) if cwd is not None else Path.cwd()
            return _cmd_init(workdir, force=args.force)

        if args.command == "status":
            _cmd_status(settings)
            return EXIT_OK

        if args.command == "models":
            if args.models_command == "list":
                list_models(settings)
            elif args.models_command == "ping":
                ping_model(settings)
            return EXIT_OK

        if args.command == "inspect":
            inspect_workspace(settings, cwd=cwd)
            return EXIT_OK

        # Unreachable for known commands; argparse rejects unknown ones.
        parser.print_help(sys.stdout)
        return EXIT_OK

    except ConfigError as exc:
        _print_error(exc)
        return EXIT_USAGE

    except WecoderError as exc:
        _print_error(exc)
        return EXIT_USAGE

    except Exception as exc:  # pragma: no cover - guards against unexpected bugs
        _LOGGER.debug("Unexpected error", exc_info=True)
        print(f"{_PROG}: internal error: {exc}", file=sys.stderr)
        return EXIT_INTERNAL


def _cmd_init(workdir: Path, *, force: bool) -> int:
    config_dir = workdir / ".wecoder"
    target = config_dir / "config.toml"

    if target.exists() and not force:
        raise ConfigError(
            f"config already exists: {target} (use --force to overwrite)"
        )

    # O_EXCL without --force keeps a concurrent writer from being clobbered;
    # with --force we truncate any existing file.
    flags = os.O_CREAT | os.O_WRONLY
    flags |= os.O_TRUNC if force else os.O_EXCL

    config_dir.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(str(target), flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(DEFAULT_CONFIG_TEXT)
    except BaseException:
        # Ensure the descriptor is not leaked if the write fails.
        try:
            os.close(fd)
        except OSError:
            pass
        raise

    print(f"Wrote {target}")
    return EXIT_OK


def _cmd_status(settings: Settings) -> None:
    print(f"{_PROG} {__version__}")
    print(f"python {platform.python_version()}")

    if settings.config_paths:
        for path in settings.config_paths:
            print(f"config: {path}")
    else:
        print("config: none")

    print(f"provider: {settings.model.provider}")
    print(f"model: {settings.model.model}")
    print(f"logging level: {settings.logging.level}")


def _print_error(exc: Exception) -> None:
    print(f"{_PROG}: error: {exc}", file=sys.stderr)


__all__ = ["main", "build_parser"]
