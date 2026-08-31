"""Build a data-only local staging directory for Hugging Face publication."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SOURCE_DIRS = ("raw", "annotated", "croissant", "manifests")
ALLOWED_TOP_LEVEL = {"README.md", "raw", "annotated", "croissant", "manifests", "neurips26"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a local, data-only Hugging Face dataset staging directory."
    )
    parser.add_argument("--output", type=Path, required=True, help="New or empty staging directory.")
    return parser.parse_args()


def validate_destination(output: Path) -> None:
    resolved = output.resolve()
    if resolved == DATA.resolve() or DATA.resolve() in resolved.parents:
        raise ValueError("The staging directory cannot be the source data directory or its child.")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty staging directory: {output}")


def reject_source_symlinks() -> None:
    symlinks = [path for path in DATA.rglob("*") if path.is_symlink()]
    if symlinks:
        display = [str(path.relative_to(DATA)) for path in symlinks[:5]]
        raise ValueError(f"Dataset source contains symlinks: {display}")


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    validate_destination(output)
    reject_source_symlinks()
    output.mkdir(parents=True, exist_ok=True)

    shutil.copy2(DATA / "README.md", output / "README.md")
    for dirname in SOURCE_DIRS:
        shutil.copytree(DATA / dirname, output / dirname)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish" / "build_neurips26_parquet.py"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
    )

    actual_top_level = {path.name for path in output.iterdir()}
    if actual_top_level != ALLOWED_TOP_LEVEL:
        raise AssertionError(f"Unexpected staging content: {sorted(actual_top_level)}")

    files = sorted(path for path in output.rglob("*") if path.is_file())
    manifest = {
        "dataset": "kl41r3/erc8004-vs-a2a-governance",
        "source": "data-only local staging package",
        "files": {
            str(path.relative_to(output)): {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in files
        },
    }
    manifest_path = output / "PUBLISH_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    total_bytes = sum(entry["bytes"] for entry in manifest["files"].values())
    print(f"Prepared data-only Hugging Face staging directory: {output}")
    print(f"Files: {len(files)}")
    print(f"Bytes: {total_bytes}")
    print("No network operation was performed.")


if __name__ == "__main__":
    main()
