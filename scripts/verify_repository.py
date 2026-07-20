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
    "data/raw/r3/",
    "analysis/metrics/r3/",
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

FORBIDDEN_LOCAL_PATH_MARKERS = (
    "/Users/" + "michelangelo/",
    "C:\\Users\\" + "michelangelo\\",
)

REQUIRED_PATHS = (
    ROOT / "README.md",
    ROOT / "data" / "README.md",
    ROOT / "data" / "croissant" / "v1" / "croissant.json",
    ROOT / "data" / "croissant" / "v1" / "release_manifest.json",
    ROOT / "scripts" / "process" / "build_croissant_release.py",
    ROOT / "scripts" / "process" / "build_r1_paper_manifest.py",
    ROOT / "scripts" / "reproduce_release.py",
    ROOT / "scripts" / "process" / "extract_manual_institutions.py",
    ROOT / "data" / "manifests" / "r1_paper_v1.jsonl",
    ROOT / "data" / "manifests" / "r1_paper_v1_summary.json",
    ROOT / "pyproject.toml",
    ROOT / "uv.lock",
)


def verify_r1_paper_manifest(errors: list[str]) -> None:
    manifest_path = ROOT / "data" / "manifests" / "r1_paper_v1.jsonl"
    summary_path = ROOT / "data" / "manifests" / "r1_paper_v1_summary.json"
    if not manifest_path.is_file() or not summary_path.is_file():
        return

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    payload = manifest_path.read_bytes()
    if sha256(manifest_path) != summary.get("manifest_sha256"):
        errors.append("R1 paper manifest SHA-256 does not match its summary")

    rows = [json.loads(line) for line in payload.splitlines() if line.strip()]
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
        source_rows = raw_cache.get(relative)
        index = row.get("source_index")
        if source_rows is None or not isinstance(index, int) or not 0 <= index < len(source_rows):
            errors.append(f"Invalid R1 manifest row locator: {relative}:{index}")
            continue
        source = source_rows[index]
        text = str(source.get("raw_text") or "").strip()
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash != row.get("raw_text_sha256") or len(text) != row.get("text_length"):
            errors.append(f"R1 manifest content mismatch: {relative}:{index}")
        author = str(source.get("author") or "")
        historical_bots = {
            "gemini-code-assist[bot]", "google-cla[bot]", "github-actions[bot]",
            "codecov[bot]", "dependabot[bot]", "git-vote[bot]",
        }
        if len(text) < 20 or author in historical_bots or author.endswith("[bot]"):
            errors.append(f"Ineligible row appears in R1 paper manifest: {relative}:{index}")

    expected_cases = {"ERC-8004": 142, "Google-A2A": 4181}
    if case_counts != expected_cases or summary.get("retained_by_case") != expected_cases:
        errors.append(f"R1 paper manifest case counts do not match {expected_cases}: {case_counts}")


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
    for relative in tracked:
        path = ROOT / relative
        if path.is_file() and path.suffix in {".py", ".md", ".json", ".jsonl", ".csv", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(marker in text for marker in FORBIDDEN_LOCAL_PATH_MARKERS):
                errors.append(f"Tracked file contains a local researcher path: {relative}")


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_PATHS:
        if not path.is_file():
            errors.append(f"Required path is missing: {path.relative_to(ROOT)}")
    for manifest, mode in CHECKSUM_SCOPES.items():
        verify_checksum_manifest(manifest, mode, errors)
    verify_croissant(errors)
    verify_r1_paper_manifest(errors)
    verify_dataset_card(errors)
    verify_public_boundary(errors)

    if errors:
        print("Repository verification failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("Repository verification passed.")
    print(
        f"Verified {len(CHECKSUM_SCOPES)} checksum manifests, 5 Croissant RecordSets, "
        "and the 4,323-row R1 paper manifest."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
