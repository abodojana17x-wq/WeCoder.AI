"""Allow running the CLI as ``python -m wecoder``."""

from __future__ import annotations

import sys

from wecoder.cli.app import main

if __name__ == "__main__":
    sys.exit(main())
