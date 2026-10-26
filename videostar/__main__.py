"""VideoStar application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    from .app import run

    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
