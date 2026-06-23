"""
patch_r2_tier2_github.py — fix two data-quality issues in the Tier-2 GitHub pull.

1) Dedup: ERC-8183 (forum topics 27902 + 27970) and ERC-8259 (28521 + 28473)
   each map to one set of repo PRs, which were therefore scraped twice
   (24 duplicate records). Dedup by (pr_number, comment_id).

2) Number drift: forum thread 28012 titles itself "ERC-8184 (draft): Payment
   Channels with Signed Vouchers", but the repo PR #1592 of the same title
   created ERCS/erc-8190.md (no erc-8184.md exists). discover_prs() correctly
   found "no PR", so we add #1592 explicitly here, tagged erc=8184 with a note
   recording the 8184(forum)→8190(repo) drift, for full traceability.

Idempotent: re-running re-dedups and re-adds #1592 only if absent.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scrape_r2_github import fetch_pr, load_token  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "raw" / "r2" / "tier2"
JSON_PATH = OUT / "cluster_github.json"
MAN_PATH = OUT / "tier2_github_manifest.json"

DRIFT_PR = 1592          # repo PR that created erc-8190.md
DRIFT_FORUM_ERC = "8184"  # number used on the forum thread (28012)


def dedup(records):
    seen, out = set(), []
    for r in records:
        k = (r["pr_number"], r.get("comment_id"))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def main():
    token = load_token()
    records = json.loads(JSON_PATH.read_text())
    before = len(records)
    records = dedup(records)
    print(f"dedup: {before} → {len(records)} ({before - len(records)} removed)")

    have_1592 = any(r["pr_number"] == DRIFT_PR for r in records)
    if not have_1592:
        print(f"scraping drift PR #{DRIFT_PR} (forum ERC-{DRIFT_FORUM_ERC} → repo erc-8190)…")
        recs = fetch_pr(DRIFT_PR, f"ERC-{DRIFT_FORUM_ERC} (forum) / erc-8190 (repo)",
                        "tier2", DRIFT_FORUM_ERC, token)
        for r in recs:
            r["_note"] = "forum thread 28012 numbered 8184; repo PR #1592 created erc-8190.md"
        records.extend(recs)
        print(f"  added {len(recs)} records for #{DRIFT_PR}")
    else:
        print(f"PR #{DRIFT_PR} already present — skip")

    records = dedup(records)
    JSON_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False))

    # update manifest
    man = json.loads(MAN_PATH.read_text())
    man["total_records"] = len(records)
    man["raw_records_before_dedup"] = before
    man["by_source"] = dict(Counter(r["source"] for r in records))
    man["patched_at"] = datetime.now(timezone.utc).isoformat()
    man["patch_notes"] = [
        "deduped (pr_number, comment_id): 8183/8259 reached via two forum topics each",
        "added PR #1592 for forum-8184 → repo-8190 number drift",
    ]
    # 8184 is no longer forum-only
    man["ercs_with_no_pr"] = [e for e in man.get("ercs_with_no_pr", []) if str(e) != "8184"]
    for p in man.get("per_erc", []):
        if p.get("erc") == DRIFT_FORUM_ERC:
            p["prs_found"] = sorted(set(p.get("prs_found", []) + [DRIFT_PR]))
            p["discovery"] = {**p.get("discovery", {}), str(DRIFT_PR): "manual_drift_8184_to_8190"}
    MAN_PATH.write_text(json.dumps(man, indent=2, ensure_ascii=False))

    print(f"\nfinal: {len(records)} records → {JSON_PATH}")
    print("by_source:", man["by_source"])
    print("ercs_with_no_pr:", man["ercs_with_no_pr"])


if __name__ == "__main__":
    main()
