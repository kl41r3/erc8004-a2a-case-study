"""Reconstruct the exact R1 paper corpus from the frozen March 2026 raw files.

The historical filtering policy is preserved in git commit 503a10e:

* strip ``raw_text`` and retain records with at least 20 Unicode code points;
* exclude the six named bot accounts used by that revision;
* exclude any author handle ending in ``[bot]``.

The five input files in the current repository are byte identical to the files in
that commit.  This builder records every retained row, the source row locator,
content digest, source-file digest, and the policy provenance needed to reproduce
the reported 142 ERC-8004 and 4,181 A2A records.

Usage:
    uv run python scripts/process/build_r1_paper_manifest.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import DATA_RAW, ROOT


SCHEMA_VERSION = "1.0.0"
SNAPSHOT_ID = "r1-paper-2026-03-14"
POLICY_GIT_COMMIT = "503a10edb127cec623414b964dbd703287886004"
MIN_TEXT_LENGTH = 20
HISTORICAL_BOT_AUTHORS = {
    "gemini-code-assist[bot]",
    "google-cla[bot]",
    "github-actions[bot]",
    "codecov[bot]",
    "dependabot[bot]",
    "git-vote[bot]",
}

INPUTS = (
    ("ERC-8004", "forum_posts.json"),
    ("ERC-8004", "github_comments_filtered.json"),
    ("Google-A2A", "a2a_issues.json"),
    ("Google-A2A", "a2a_prs.json"),
    ("Google-A2A", "a2a_discussions.json"),
)

EXPECTED_SHA256 = {
    "forum_posts.json": "b414e8b7153df6d89a2885a702f72ed5ead1cfa21cdb6b455ae86677cad3e66d",
    "github_comments_filtered.json": "41a65aa867db3e6441024854604ba951e3987e0776c32b02a84027ef2a28c8ba",
    "a2a_issues.json": "e48ebc63933380b4a68c42ea30c98168e64710640b269849d9066eeadf79cbbb",
    "a2a_prs.json": "a7043491cc4ace44bc01eb0fbe681e659c284765493d046e7a22adc942a67747",
    "a2a_discussions.json": "1f060770b539c79761b6d12d929db4d996536398b9da9c31124f861897730049",
}

EXPECTED_COUNTS = {
    "forum_posts.json": {"raw": 113, "retained": 113},
    "github_comments_filtered.json": {"raw": 36, "retained": 29},
    "a2a_issues.json": {"raw": 3104, "retained": 2136},
    "a2a_prs.json": {"raw": 1955, "retained": 1243},
    "a2a_discussions.json": {"raw": 822, "retained": 802},
}

OUTPUT_DIR = ROOT / "data" / "manifests"
OUTPUT_ROWS = OUTPUT_DIR / "r1_paper_v1.jsonl"
OUTPUT_SUMMARY = OUTPUT_DIR / "r1_paper_v1_summary.json"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def native_identity(record: dict[str, Any]) -> str:
    for key in (
        "post_id",
        "comment_id",
        "discussion_number",
        "issue_number",
        "pr_number",
        "sha",
        "topic_id",
    ):
        value = record.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    for key in ("url", "pr_url", "issue_url"):
        value = str(record.get(key) or "").strip()
        if value:
            return f"{key}:{value}"
    return "no_native_id"


def exclusion_reason(record: dict[str, Any]) -> str | None:
    text = str(record.get("raw_text") or "").strip()
    author = str(record.get("author") or "")
    if len(text) < MIN_TEXT_LENGTH:
        return "text_length_below_20"
    if author in HISTORICAL_BOT_AUTHORS or author.endswith("[bot]"):
        return "historical_bot_policy"
    return None


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    retained_rows: list[dict[str, Any]] = []
    source_summary: dict[str, Any] = {}
    exclusion_counts: Counter[str] = Counter()
    seen_ids: set[str] = set()

    for case, filename in INPUTS:
        path = DATA_RAW / filename
        payload = path.read_bytes()
        actual_sha = sha256_bytes(payload)
        if actual_sha != EXPECTED_SHA256[filename]:
            raise SystemExit(
                f"Input drift for {filename}: expected {EXPECTED_SHA256[filename]}, got {actual_sha}"
            )
        records = json.loads(payload)
        file_retained = 0
        file_exclusions: Counter[str] = Counter()

        for source_index, record in enumerate(records):
            reason = exclusion_reason(record)
            if reason:
                exclusion_counts[reason] += 1
                file_exclusions[reason] += 1
                continue

            text = str(record.get("raw_text") or "").strip()
            text_sha = sha256_bytes(text.encode("utf-8"))
            source = str(record.get("source") or record.get("record_type") or "unknown")
            identity_key = "|".join(
                (
                    SNAPSHOT_ID,
                    case,
                    filename,
                    native_identity(record),
                    str(record.get("date") or ""),
                    str(record.get("author") or ""),
                    text_sha,
                    str(source_index),
                )
            )
            record_id = "r1p_" + sha256_bytes(identity_key.encode("utf-8"))
            if record_id in seen_ids:
                raise SystemExit(f"Duplicate manifest record_id: {record_id}")
            seen_ids.add(record_id)
            retained_rows.append(
                {
                    "record_id": record_id,
                    "case": case,
                    "source_file": f"data/raw/{filename}",
                    "source_file_sha256": actual_sha,
                    "source_index": source_index,
                    "source": source,
                    "native_identity": native_identity(record),
                    "date": record.get("date"),
                    "author": record.get("author"),
                    "text_length": len(text),
                    "raw_text_sha256": text_sha,
                }
            )
            file_retained += 1

        expected = EXPECTED_COUNTS[filename]
        if len(records) != expected["raw"] or file_retained != expected["retained"]:
            raise SystemExit(
                f"Count drift for {filename}: raw={len(records)}, retained={file_retained}, expected={expected}"
            )
        source_summary[filename] = {
            "case": case,
            "raw_rows": len(records),
            "retained_rows": file_retained,
            "excluded_rows": len(records) - file_retained,
            "exclusions": dict(sorted(file_exclusions.items())),
            "sha256": actual_sha,
        }

    case_counts = Counter(row["case"] for row in retained_rows)
    if case_counts != Counter({"ERC-8004": 142, "Google-A2A": 4181}):
        raise SystemExit(f"Unexpected case counts: {dict(case_counts)}")

    rows_payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in retained_rows
    ).encode("utf-8")
    OUTPUT_ROWS.write_bytes(rows_payload)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": SNAPSHOT_ID,
        "description": "Exact row-level manifest for the R1 corpus reported in the paper.",
        "policy_provenance_git_commit": POLICY_GIT_COMMIT,
        "filter_policy": {
            "minimum_stripped_raw_text_unicode_codepoints": MIN_TEXT_LENGTH,
            "named_bot_authors": sorted(HISTORICAL_BOT_AUTHORS),
            "exclude_author_suffix": "[bot]",
            "rule_order": ["text_length", "bot_author"],
        },
        "source_files": source_summary,
        "raw_rows": sum(item["raw_rows"] for item in source_summary.values()),
        "retained_rows": len(retained_rows),
        "excluded_rows": sum(exclusion_counts.values()),
        "retained_by_case": dict(sorted(case_counts.items())),
        "exclusions": dict(sorted(exclusion_counts.items())),
        "manifest_path": str(OUTPUT_ROWS.relative_to(ROOT)),
        "manifest_sha256": sha256_bytes(rows_payload),
        "rebuild_command": "uv run python scripts/process/build_r1_paper_manifest.py",
    }
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"R1 manifest: {len(retained_rows)} rows")
    print(f"  ERC-8004: {case_counts['ERC-8004']}")
    print(f"  Google-A2A: {case_counts['Google-A2A']}")
    print(f"  JSONL SHA-256: {summary['manifest_sha256']}")
    print(f"  Output: {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"  Summary: {OUTPUT_SUMMARY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
