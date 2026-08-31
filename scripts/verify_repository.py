"""Verify the public code release and, optionally, downloaded dataset payloads."""

from __future__ import annotations

import argparse
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
    "data/raw/",
    "data/annotated/",
    "data/manifests/",
    "data/neurips26/",
)

FORBIDDEN_TRACKED_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "do.md",
    "do2.md",
    ".env",
    "scripts/analyse/analyze_governance_evidence.py",
    "scripts/reporting/build_revision_reports.py",
    "scripts/scrape/collect_adoption_metrics.py",
    "scripts/scrape/scrape_event_horizon_snapshot.py",
    "scripts/visualise/build_submission_figures.py",
}

ALLOWED_TRACKED_DATA = {
    "data/README.md",
    "data/croissant/neurips-croissant-validator-pass.png",
    "data/croissant/v1/CHECKSUMS.json",
    "data/croissant/v1/SCHEMA.md",
    "data/croissant/v1/croissant.json",
    "data/croissant/v1/release_manifest.json",
}

FORBIDDEN_LOCAL_PATH_MARKERS = (
    "/Users/" + "michelangelo/",
    "C:\\Users\\" + "michelangelo\\",
)

REQUIRED_REPOSITORY_PATHS = (
    ROOT / "README.md",
    ROOT / "data" / "README.md",
    ROOT / "data" / "croissant" / "v1" / "croissant.json",
    ROOT / "data" / "croissant" / "v1" / "release_manifest.json",
    ROOT / "data" / "croissant" / "v1" / "CHECKSUMS.json",
    ROOT / "data" / "croissant" / "neurips-croissant-validator-pass.png",
    ROOT / "scripts" / "publish" / "download_hf_dataset.py",
    ROOT / "scripts" / "publish" / "build_neurips26_parquet.py",
    ROOT / "scripts" / "publish" / "neurips26_schema.md",
    ROOT / "scripts" / "process" / "build_croissant_release.py",
    ROOT / "scripts" / "process" / "build_r1_paper_manifest.py",
    ROOT / "scripts" / "reproduce_release.py",
    ROOT / "pyproject.toml",
    ROOT / "uv.lock",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-data",
        action="store_true",
        help="Also validate Hugging Face payloads downloaded into data/.",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_files(*pathspecs: str) -> list[str]:
    command = ["git", "ls-files", *pathspecs]
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.splitlines()


def verify_repository_paths(errors: list[str]) -> None:
    for path in REQUIRED_REPOSITORY_PATHS:
        if not path.is_file():
            errors.append(f"Required repository path is missing: {path.relative_to(ROOT)}")


def verify_download_pointer(errors: list[str]) -> None:
    script = (ROOT / "scripts" / "publish" / "download_hf_dataset.py").read_text(encoding="utf-8")
    repository = re.search(r'^HF_REPO_ID = "([^"]+)"$', script, flags=re.MULTILINE)
    revision = re.search(r'^HF_REVISION = "([0-9a-f]{40})"$', script, flags=re.MULTILINE)
    if not repository or repository.group(1) != "kl41r3/erc8004-vs-a2a-governance":
        errors.append("Hugging Face downloader does not point to the released dataset repository")
    if not revision:
        errors.append("Hugging Face downloader must pin an immutable 40-character revision")


def verify_metadata_checksums(errors: list[str]) -> None:
    release_dir = ROOT / "data" / "croissant" / "v1"
    manifest = json.loads((release_dir / "CHECKSUMS.json").read_text(encoding="utf-8"))
    required_entries = {
        "SCHEMA.md",
        "croissant.json",
        "release_manifest.json",
        "r1_annotations.parquet",
        "r2_cross_model_consensus.parquet",
        "r2_cross_model_votes.parquet",
        "r2_cross_round_consensus.parquet",
        "r2_cross_round_votes.parquet",
    }
    if set(manifest) != required_entries:
        errors.append("Croissant checksum manifest does not describe the eight release files")
    for name in ("SCHEMA.md", "croissant.json", "release_manifest.json"):
        path = release_dir / name
        entry = manifest.get(name, {})
        if path.is_file() and sha256(path) != entry.get("sha256"):
            errors.append(f"Metadata checksum mismatch: data/croissant/v1/{name}")


def expected_checksum_files(base: Path, mode: str) -> dict[str, Path]:
    if mode == "recursive-json":
        files = (path for path in base.rglob("*.json") if path.name != "CHECKSUMS.json")
    else:
        files = (path for path in base.iterdir() if path.is_file() and path.name != "CHECKSUMS.json")
    return {str(path.relative_to(base)): path for path in sorted(files)}


def verify_checksum_manifest(manifest_path: Path, mode: str, errors: list[str]) -> None:
    if not manifest_path.is_file():
        errors.append(f"Missing downloaded checksum manifest: {manifest_path.relative_to(ROOT)}")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = expected_checksum_files(manifest_path.parent, mode)
    if set(expected) != set(manifest):
        errors.append(f"Checksum file set mismatch: {manifest_path.relative_to(ROOT)}")
        return
    for name, path in expected.items():
        if sha256(path) != manifest[name].get("sha256"):
            errors.append(f"Checksum mismatch: {path.relative_to(ROOT)}")
        expected_bytes = manifest[name].get("bytes")
        if expected_bytes is not None and expected_bytes != path.stat().st_size:
            errors.append(f"Byte-size mismatch: {path.relative_to(ROOT)}")


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
        path = release_dir / filename
        if not path.is_file():
            errors.append(f"Downloaded Croissant table is missing: {path.relative_to(ROOT)}")
            continue
        actual = pq.ParquetFile(path).metadata.num_rows
        if actual != manifest["counts"][key]:
            errors.append(f"Croissant row mismatch for {filename}: {actual}")

    cross_model_ids = set(
        pq.read_table(release_dir / tables["r2_cross_model"], columns=["record_id"])[
            "record_id"
        ].to_pylist()
    )
    cross_model_vote_ids = set(
        pq.read_table(release_dir / tables["r2_cross_model_votes"], columns=["record_id"])[
            "record_id"
        ].to_pylist()
    )
    cross_round_ids = set(
        pq.read_table(release_dir / tables["r2_cross_round"], columns=["record_id"])[
            "record_id"
        ].to_pylist()
    )
    cross_round_vote_ids = set(
        pq.read_table(release_dir / tables["r2_cross_round_votes"], columns=["record_id"])[
            "record_id"
        ].to_pylist()
    )
    if not cross_model_vote_ids <= cross_model_ids:
        errors.append("Cross-model vote table contains orphan record_id values")
    if not cross_round_vote_ids <= cross_round_ids:
        errors.append("Cross-round vote table contains orphan record_id values")


def verify_r1_paper_manifest(errors: list[str]) -> None:
    manifest_path = ROOT / "data" / "manifests" / "r1_paper_v1.jsonl"
    summary_path = ROOT / "data" / "manifests" / "r1_paper_v1_summary.json"
    if not manifest_path.is_file() or not summary_path.is_file():
        errors.append("R1 paper manifest has not been rebuilt")
        return
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line]
    if sha256(manifest_path) != summary.get("manifest_sha256"):
        errors.append("R1 paper manifest SHA-256 does not match its summary")
    if len(rows) != 4323 or summary.get("retained_rows") != 4323:
        errors.append(f"R1 paper manifest must contain 4,323 rows, found {len(rows)}")
    ids = [row.get("record_id") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("R1 paper manifest contains duplicate record_id values")
    case_counts: dict[str, int] = {}
    raw_cache: dict[str, list[dict]] = {}
    for row in rows:
        case = row.get("case")
        case_counts[case] = case_counts.get(case, 0) + 1
        relative = row.get("source_file", "")
        if relative not in raw_cache:
            path = ROOT / relative
            if not path.is_file():
                errors.append(f"R1 manifest source file is missing: {relative}")
                continue
            raw_cache[relative] = json.loads(path.read_text(encoding="utf-8"))
        source_rows = raw_cache[relative]
        index = row.get("source_index")
        if not isinstance(index, int) or not 0 <= index < len(source_rows):
            errors.append(f"Invalid R1 manifest row locator: {relative}:{index}")
            continue
        source = source_rows[index]
        text = str(source.get("raw_text") or "").strip()
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash != row.get("raw_text_sha256") or len(text) != row.get("text_length"):
            errors.append(f"R1 manifest content mismatch: {relative}:{index}")
        author = str(source.get("author") or "")
        historical_bots = {
            "gemini-code-assist[bot]",
            "google-cla[bot]",
            "github-actions[bot]",
            "codecov[bot]",
            "dependabot[bot]",
            "git-vote[bot]",
        }
        if len(text) < 20 or author in historical_bots or author.endswith("[bot]"):
            errors.append(f"Ineligible row appears in R1 paper manifest: {relative}:{index}")
    if case_counts != {"ERC-8004": 142, "Google-A2A": 4181}:
        errors.append(f"R1 paper manifest case counts are incorrect: {case_counts}")


def verify_dataset_card(errors: list[str]) -> None:
    card = (ROOT / "data" / "README.md").read_text(encoding="utf-8")
    paths = re.findall(r"^\s+path:\s+(.+\.parquet)\s*$", card, flags=re.MULTILINE)
    if len(paths) != 10:
        errors.append(f"Dataset card must declare ten Parquet configs, found {len(paths)}")
    for relative in paths:
        if not (ROOT / "data" / relative).is_file():
            errors.append(f"Downloaded dataset-card path is missing: data/{relative}")


def verify_neurips26_layer(errors: list[str]) -> None:
    base = ROOT / "data" / "neurips26"
    checksums_path = base / "CHECKSUMS.json"
    manifest_path = base / "release_manifest.json"
    schema_path = base / "SCHEMA.md"
    if not checksums_path.is_file() or not manifest_path.is_file() or not schema_path.is_file():
        errors.append("Rebuilt neurips26 dataset layer is incomplete")
        return
    checksums = json.loads(checksums_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("release") != "neurips26-v1.1.1":
        errors.append("neurips26 release version drift")
    for filename, metadata in checksums.items():
        path = base / filename
        if not path.is_file():
            errors.append(f"neurips26 table is missing: {filename}")
            continue
        if sha256(path) != metadata.get("sha256"):
            errors.append(f"neurips26 checksum mismatch: {filename}")
        if pq.ParquetFile(path).metadata.num_rows != metadata.get("rows"):
            errors.append(f"neurips26 row-count mismatch: {filename}")


def verify_public_boundary(errors: list[str]) -> None:
    tracked = git_files()
    for relative in tracked:
        if relative in FORBIDDEN_TRACKED_FILES or relative.startswith(FORBIDDEN_TRACKED_PREFIXES):
            errors.append(f"Private or dataset payload path is tracked: {relative}")
        if relative.startswith("data/") and relative not in ALLOWED_TRACKED_DATA:
            errors.append(f"Unexpected tracked data path: {relative}")
        path = ROOT / relative
        if path.is_file() and path.suffix in {".py", ".md", ".json", ".jsonl", ".csv", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(marker in text for marker in FORBIDDEN_LOCAL_PATH_MARKERS):
                errors.append(f"Tracked file contains a local researcher path: {relative}")


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    verify_repository_paths(errors)
    verify_download_pointer(errors)
    verify_metadata_checksums(errors)
    verify_public_boundary(errors)

    if args.with_data:
        for manifest, mode in CHECKSUM_SCOPES.items():
            verify_checksum_manifest(manifest, mode, errors)
        verify_croissant(errors)
        verify_r1_paper_manifest(errors)
        verify_dataset_card(errors)
        verify_neurips26_layer(errors)

    if errors:
        print("Repository verification failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    if args.with_data:
        print("Repository and downloaded Hugging Face dataset verification passed.")
        print("Verified 6 checksum manifests, 5 Croissant RecordSets, the 4,323-row R1 manifest, and 5 neurips26 tables.")
    else:
        print("Code-only GitHub release verification passed.")
        print("No dataset payload is tracked; the downloader pins an immutable Hugging Face revision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
