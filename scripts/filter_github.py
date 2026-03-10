"""
Filter raw GitHub comments to keep only records directly related to ERC-8004
governance lifecycle (proposal, updates, status changes).

The GitHub search API returns any PR mentioning "ERC-8004", including ecosystem
ERCs that merely cite it as a dependency. This script retains only PRs that are
actual modifications to the ERC-8004 spec or its lifecycle status.

Input:  data/raw/github_comments.json
Output: data/raw/github_comments_filtered.json
        data/raw/filter_log.json
"""

import json
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# PRs that are direct ERC-8004 lifecycle changes (verified manually against GitHub).
# Source: https://github.com/ethereum/ERCs/pulls?q=erc-8004
ERC8004_CORE_PRS: dict[int, str] = {
    1170: "Add ERC: Trustless Agents (initial submission)",
    1244: "Update ERC-8004: Move to Review",
    1248: "Update ERC-8004: Add Requires field",
    1458: "Update ERC-8004: Update erc-8004.md",
    1462: "Update ERC-8004: Update erc-8004.md (typos)",
    1470: "Update ERC-8004: Move to Draft",
    1472: "Update ERC-8004: align metadataValue to bytes",
    1477: "Update ERC-8004: add co-author (Onchain Metadata; see PR #1237)",
    1488: "Update ERC-8004: Updates from community feedback",
}


def filter_comments(raw: list[dict]) -> tuple[list[dict], list[dict]]:
    kept, dropped = [], []
    for record in raw:
        pr = record.get("pr_number")
        if pr in ERC8004_CORE_PRS:
            kept.append({**record, "pr_description": ERC8004_CORE_PRS[pr]})
        else:
            dropped.append(record)
    return kept, dropped


def main():
    src = RAW_DIR / "github_comments.json"
    if not src.exists():
        raise FileNotFoundError(f"Run scrape_erc8004.py first: {src}")

    raw = json.loads(src.read_text())
    kept, dropped = filter_comments(raw)

    # Breakdown by PR for the log
    pr_counts: dict[int, int] = {}
    for r in kept:
        pr_counts[r["pr_number"]] = pr_counts.get(r["pr_number"], 0) + 1

    dropped_pr_counts: dict[int, int] = {}
    dropped_pr_titles: dict[int, str] = {}
    for r in dropped:
        pr = r["pr_number"]
        dropped_pr_counts[pr] = dropped_pr_counts.get(pr, 0) + 1

    log = {
        "total_raw": len(raw),
        "kept": len(kept),
        "dropped": len(dropped),
        "kept_by_pr": {str(k): {"count": v, "description": ERC8004_CORE_PRS[k]}
                       for k, v in sorted(pr_counts.items())},
        "dropped_by_pr": {str(k): {"count": v} for k, v in sorted(dropped_pr_counts.items())},
        "drop_reason": "PR mentions ERC-8004 as dependency but is not a lifecycle update to the spec itself",
    }

    (RAW_DIR / "github_comments_filtered.json").write_text(
        json.dumps(kept, indent=2, ensure_ascii=False)
    )
    (RAW_DIR / "filter_log.json").write_text(json.dumps(log, indent=2))

    print(f"Raw:     {len(raw)} records")
    print(f"Kept:    {len(kept)} records (core ERC-8004 PRs)")
    print(f"Dropped: {len(dropped)} records (ecosystem PRs citing ERC-8004)")
    print("\nKept PRs:")
    for pr_num, desc in sorted(ERC8004_CORE_PRS.items()):
        count = pr_counts.get(pr_num, 0)
        print(f"  PR #{pr_num} ({count} records): {desc}")
    print(f"\nFiltered data → {RAW_DIR / 'github_comments_filtered.json'}")


if __name__ == "__main__":
    main()
