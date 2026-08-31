"""Download, rebuild, and verify the complete public v1.1.1 release.

Dataset payloads come from an immutable Hugging Face revision. This command does
not scrape live platforms or call hosted LLMs, whose content and behavior can
change over time.

Usage:
    uv run python scripts/reproduce_release.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(relative_script: str, *arguments: str) -> None:
    command = [sys.executable, str(ROOT / relative_script), *arguments]
    print(f"\nRunning: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("scripts/publish/download_hf_dataset.py")
    run("scripts/process/build_r1_paper_manifest.py")
    run("scripts/process/build_croissant_release.py")
    run("scripts/analyse/run_neurips26_robustness.py")
    run("scripts/publish/build_neurips26_parquet.py", "--output", "data")
    run("scripts/verify_repository.py", "--with-data")
    run("scripts/verify_neurips26.py")
    print("\nComplete v1.1.1 release reproduction passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
