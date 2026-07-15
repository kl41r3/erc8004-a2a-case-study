"""Read-only integrity checks for the public RQ1 repository surface."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent.parent

CHECKSUM_SCOPES = {
    ROOT / "data" / "raw" / "CHECKSUMS.json": "recursive-json",
    ROOT / "data" / "annotated" / "CHECKSUMS.json": "recursive-json",
    ROOT / "data" / "annotated" / "r1" / "CHECKSUMS.json": "recursive-json",
    ROOT / "data" / "annotated" / "r2" / "cross-model" / "CHECKSUMS.json": "recursive-json",
    ROOT / "data" / "annotated" / "r2" / "cross-round" / "CHECKSUMS.json": "recursive-json",
    ROOT / "data" / "croissant" / "v1" / "CHECKSUMS.json": "all-files",
}

FORBIDDEN_TRACKED_PREFIXES = (
    "paper-acm/",
    "human-notes/",
    "tree-docs/",
    "local-tools/",
    "_trash/",
    "output/",
)

FORBIDDEN_TRACKED_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "do.md",
    "do2.md",
    ".env",
}

REQUIRED_PATHS = (
    ROOT / "README.md",
    ROOT / "data" / "README.md",
    ROOT / "data" / "croissant" / "v1" / "croissant.json",
    ROOT / "data" / "croissant" / "v1" / "release_manifest.json",
    ROOT / "scripts" / "process" / "build_croissant_release.py",
    ROOT / "scripts" / "process" / "extract_manual_institutions.py",
    ROOT / "pyproject.toml",
    ROOT / "uv.lock",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_files(*pathspecs: str) -> list[str]:
    command = ["git", "ls-files"]
    command.extend(pathspecs)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def expected_checksum_files(base: Path, mode: str) -> dict[str, Path]:
    if mode == "recursive-json":
        files = (path for path in base.rglob("*.json") if path.name != "CHECKSUMS.json")
    else:
        files = (path for path in base.iterdir() if path.is_file() and path.name != "CHECKSUMS.json")
    return {str(path.relative_to(base)): path for path in sorted(files)}


def verify_checksum_manifest(manifest_path: Path, mode: str, errors: list[str]) -> None:
    if not manifest_path.is_file():
        errors.append(f"Missing checksum manifest: {manifest_path.relative_to(ROOT)}")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = expected_checksum_files(manifest_path.parent, mode)
    missing_entries = sorted(set(expected) - set(manifest))
    stale_entries = sorted(set(manifest) - set(expected))
    if missing_entries:
        errors.append(f"{manifest_path.relative_to(ROOT)} missing entries: {missing_entries[:5]}")
    if stale_entries:
        errors.append(f"{manifest_path.relative_to(ROOT)} stale entries: {stale_entries[:5]}")
    for name in sorted(set(expected) & set(manifest)):
        actual = sha256(expected[name])
        if actual != manifest[name].get("sha256"):
            errors.append(f"Checksum mismatch: {expected[name].relative_to(ROOT)}")
        expected_bytes = manifest[name].get("bytes")
        if expected_bytes is not None and expected_bytes != expected[name].stat().st_size:
            errors.append(f"Byte-size mismatch: {expected[name].relative_to(ROOT)}")


def verify_croissant(errors: list[str]) -> None:
    release_dir = ROOT / "data" / "croissant" / "v1"
    manifest = json.loads((release_dir / "release_manifest.json").read_text(encoding="utf-8"))
    tables = {
        "r1": "r1_annotations.parquet",
        "r2_cross_model": "r2_cross_model_consensus.parquet",
        "r2_cross_model_votes": "r2_cross_model_votes.parquet",
        "r2_cross_round": "r2_cross_round_consensus.parquet",
        "r2_cross_round_votes": "r2_cross_round_votes.parquet",
    }
    for key, filename in tables.items():
        actual = pq.ParquetFile(release_dir / filename).metadata.num_rows
        expected = manifest["counts"][key]
        if actual != expected:
            errors.append(f"Croissant row mismatch for {filename}: {actual} != {expected}")

    cross_model_ids = set(
        pq.read_table(
            release_dir / tables["r2_cross_model"], columns=["record_id"]
        )["record_id"].to_pylist()
    )
    cross_model_vote_ids = set(
        pq.read_table(
            release_dir / tables["r2_cross_model_votes"], columns=["record_id"]
        )["record_id"].to_pylist()
    )
    cross_round_ids = set(
        pq.read_table(
            release_dir / tables["r2_cross_round"], columns=["record_id"]
        )["record_id"].to_pylist()
    )
    cross_round_vote_ids = set(
        pq.read_table(
            release_dir / tables["r2_cross_round_votes"], columns=["record_id"]
        )["record_id"].to_pylist()
    )
    if not cross_model_vote_ids <= cross_model_ids:
        errors.append("Cross-model vote table contains orphan record_id values")
    if not cross_round_vote_ids <= cross_round_ids:
        errors.append("Cross-round vote table contains orphan record_id values")


def verify_dataset_card(errors: list[str]) -> None:
    card = (ROOT / "data" / "README.md").read_text(encoding="utf-8")
    paths = re.findall(r"^\s+path:\s+(.+\.parquet)\s*$", card, flags=re.MULTILINE)
    if len(paths) != 5:
        errors.append(f"Dataset card must declare five Parquet configs, found {len(paths)}")
    for relative in paths:
        if not (ROOT / "data" / relative).is_file():
            errors.append(f"Dataset card path does not exist: {relative}")


def verify_public_boundary(errors: list[str]) -> None:
    tracked = git_files()
    for path in tracked:
        if path in FORBIDDEN_TRACKED_FILES or path.startswith(FORBIDDEN_TRACKED_PREFIXES):
            errors.append(f"Private or local-only path is tracked: {path}")
    for relative in git_files("scripts"):
        path = ROOT / relative
        if path.is_file() and path.suffix in {".py", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "/Users/" in text:
                errors.append(f"Tracked script contains a macOS user path: {relative}")


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_PATHS:
        if not path.is_file():
            errors.append(f"Required path is missing: {path.relative_to(ROOT)}")
    for manifest, mode in CHECKSUM_SCOPES.items():
        verify_checksum_manifest(manifest, mode, errors)
    verify_croissant(errors)
    verify_dataset_card(errors)
    verify_public_boundary(errors)

    if errors:
        print("Repository verification failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("Repository verification passed.")
    print(f"Verified {len(CHECKSUM_SCOPES)} checksum manifests and 5 Croissant RecordSets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
