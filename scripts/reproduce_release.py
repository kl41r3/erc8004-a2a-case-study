"""Rebuild and verify the exact frozen R1 and R2 public release.

This command intentionally uses only committed artifacts. It does not scrape live
platforms or call hosted LLMs, whose content and behavior can change over time.

Usage:
    uv run python scripts/reproduce_release.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(relative_script: str) -> None:
    command = [sys.executable, str(ROOT / relative_script)]
    print(f"\nRunning: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("scripts/process/build_r1_paper_manifest.py")
    run("scripts/process/build_croissant_release.py")
    run("scripts/verify_repository.py")
    print("\nExact R1/R2 release reproduction passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
