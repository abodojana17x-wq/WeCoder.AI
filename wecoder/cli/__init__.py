"""Command-line interface for WeCoder.AI (Phase 01 skeleton).

Commands: ``init`` (write a default config), ``status`` (print version,
config source, python version).  Global flags: ``--help``, ``--version``,
``--verbose``.  The ``run``/``models``/``tools``/``agents`` commands are
deliberately absent until later phases.
"""

from wecoder.cli.app import main

__all__ = ["main"]
