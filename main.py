"""Точка входа: настраивает пути и запускает CLI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from depviz.cli import main


if __name__ == "__main__":
    raise SystemExit(main())