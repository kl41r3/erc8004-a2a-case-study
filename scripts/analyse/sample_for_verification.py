"""
Stratified random sample for inter-rater reliability (Cohen's κ).

Sampling design
---------------
N = 50 total, split across two strata (case) and sub-strata (source type):

  ERC-8004   → 20 records
    forum                : 16  (proportional to 113/144)
    github (all types)   :  4  (remaining 31 records)

  Google-A2A → 30 records
    Issues   (issue + issue_comment)                      : 17
    PRs      (pr + pr_body + pr_review_comment + review
              + review_comment)                           :  9
    Discussions (discussion + discussion_comment
                 + discussion_reply)                      :  4

Random seed is fixed for reproducibility.
"""

import json
import random
import csv
from pathlib import Path

SEED = 42
ERC_FORUM_URL = "https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098"

ROOT = Path(__file__).parent.parent.parent
ANNOTATED = ROOT / "data" / "annotated" / "annotated_records.json"
OUT_CSV  = ROOT / "verification" / "sample_50.csv"
OUT_JSON = ROOT / "verification" / "sample_50.json"

# ── helpers ──────────────────────────────────────────────────────────────────

def make_url(r: dict) -> str:
    """Return a direct link to the original post."""
    src = r.get("source", "")
    case = r.get("_case", "")

    if src == "forum":
        return f"{ERC_FORUM_URL}/{r['post_number']}"

    # GitHub records already carry a url field
    if "url" in r and r["url"]:
        return r["url"]

    # Fallback for A2A sources that might lack url
    return ""


def classify_a2a(source: str) -> str:
    if source in ("issue", "issue_comment"):
        return "issues"
    if source in ("pr", "pr_body", "pr_review_comment", "review", "review_comment"):
        return "prs"
    if source in ("discussion", "discussion_comment", "discussion_reply"):
        return "discussions"
    return "other"


def sample_from(pool: list, n: int, rng: random.Random) -> list:
    n = min(n, len(pool))
    return rng.sample(pool, n)


# ── load & filter ─────────────────────────────────────────────────────────────

with open(ANNOTATED) as f:
    data = json.load(f)

valid = [r for r in data if isinstance(r.get("annotation"), dict) and not r.get("annotation_error")]
print(f"Valid annotated records: {len(valid)}")

erc  = [r for r in valid if r.get("_case") == "ERC-8004"]
a2a  = [r for r in valid if r.get("_case") == "Google-A2A"]
print(f"  ERC-8004: {len(erc)}   Google-A2A: {len(a2a)}")

# ── stratified sampling ───────────────────────────────────────────────────────

rng = random.Random(SEED)

# ERC-8004
erc_forum  = [r for r in erc if r.get("source") == "forum"]
erc_github = [r for r in erc if r.get("source") != "forum"]

s_erc_forum  = sample_from(erc_forum,  16, rng)
s_erc_github = sample_from(erc_github,  4, rng)
s_erc = s_erc_forum + s_erc_github

# Google-A2A
a2a_issues  = [r for r in a2a if classify_a2a(r.get("source","")) == "issues"]
a2a_prs     = [r for r in a2a if classify_a2a(r.get("source","")) == "prs"]
a2a_discuss = [r for r in a2a if classify_a2a(r.get("source","")) == "discussions"]

s_a2a_issues  = sample_from(a2a_issues,  17, rng)
s_a2a_prs     = sample_from(a2a_prs,      9, rng)
s_a2a_discuss = sample_from(a2a_discuss,  4, rng)
s_a2a = s_a2a_issues + s_a2a_prs + s_a2a_discuss

sample = s_erc + s_a2a
print(f"\nSample size: {len(sample)}  (ERC-8004={len(s_erc)}, Google-A2A={len(s_a2a)})")

# ── build output rows ─────────────────────────────────────────────────────────

rows = []
for i, r in enumerate(sample, 1):
    ann  = r.get("annotation", {})
    text = r.get("raw_text", "").strip().replace("\n", " ")[:300]
    rows.append({
        "id":              i,
        "case":            r.get("_case", ""),
        "source":          r.get("source", ""),
        "date":            r.get("date", ""),
        "author":          r.get("author", r.get("author_display", "")),
        "url":             make_url(r),
        "text_preview":    text,
        # LLM labels — these are what you will independently code
        "llm_argument_type":   ann.get("argument_type", ""),
        "llm_stance":          ann.get("stance", ""),
        "llm_consensus_signal":ann.get("consensus_signal", ""),
        # blank columns for your human coding
        "human_argument_type":   "",
        "human_stance":          "",
        "human_consensus_signal":"",
        "agree_argument_type":   "",
        "agree_stance":          "",
        "agree_consensus_signal":"",
        "notes":                 "",
    })

# ── save ──────────────────────────────────────────────────────────────────────

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

# also save full records for reference
with open(OUT_JSON, "w") as f:
    json.dump(sample, f, ensure_ascii=False, indent=2)

print(f"\nSaved:\n  {OUT_CSV}\n  {OUT_JSON}")

# ── print summary table ───────────────────────────────────────────────────────

from collections import Counter
print("\n── Sample breakdown ──────────────────────────────────────────────────────")
breakdown = Counter((r.get("_case"), r.get("source")) for r in sample)
for (case, src), cnt in sorted(breakdown.items()):
    print(f"  {case:<15}  {src:<25}  n={cnt}")
