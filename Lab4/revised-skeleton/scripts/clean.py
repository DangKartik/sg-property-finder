"""Remove local build and Python cache artefacts."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "frontend" / "dist",
    ROOT / "frontend" / "node_modules" / ".vite",
]


def main() -> int:
    for target in TARGETS:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            print(f"Removed {target.relative_to(ROOT)}")
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
    for path in ROOT.rglob(".pytest_cache"):
        shutil.rmtree(path, ignore_errors=True)
    print("Clean complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
