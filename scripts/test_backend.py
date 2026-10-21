"""Run the backend unittest suite from any working directory."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"


def main() -> int:
    return subprocess.call(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=BACKEND,
    )


if __name__ == "__main__":
    raise SystemExit(main())
