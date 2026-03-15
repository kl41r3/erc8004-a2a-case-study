"""
Compute governance metrics from annotated records for both cases:
  Case A: ERC-8004 (DAO / permissionless governance)
  Case B: Google A2A (corporate hierarchy governance)

Also produces a non-annotated structural metrics table that does NOT
require LLM annotation (participation counts, timeline, etc.) so the
comparison can begin even before annotation is complete.

Input:
  data/raw/forum_posts.json
  data/raw/github_comments_filtered.json
  data/raw/a2a_commits.json
  data/raw/a2a_issues.json
  data/raw/a2a_prs.json
  data/annotated/annotated_records.json   (optional — for annotation-based metrics)

Output:
  analysis/structural_metrics.csv         (no annotation needed)
  output/findings_summary.md
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from dateutil import parser as dateutil_parser

import pandas as pd


def _parse_date(s: str | None):
    """Robustly parse an ISO date string; returns UTC-aware datetime or NaT."""
    if not s:
        return pd.NaT
    try:
        dt = dateutil_parser.parse(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return pd.Timestamp(dt)
    except Exception:
        return pd.NaT

RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
ANNOTATED_DIR = Path(__file__).parent.parent.parent / "data" / "annotated"
ANALYSIS_DIR = Path(__file__).parent.parent.parent / "analysis"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Key dates (from public record)
ERC8004_PROPOSAL = datetime(2025, 8, 13, tzinfo=timezone.utc)
ERC8004_MAINNET = datetime(2026, 1, 29, tzinfo=timezone.utc)
A2A_FIRST_COMMIT = datetime(2025, 3, 25, tzinfo=timezone.utc)  # from scrape
A2A_PUBLIC_ANNOUNCE = datetime(2025, 4, 9, tzinfo=timezone.utc)  # Google blog post

ERC8004_INITIATING_ORG = "Ethereum Foundation"
A2A_INITIATING_ORG = "Google"


# ---------------------------------------------------------------------------
# Structural metrics (no annotation required)
# ---------------------------------------------------------------------------

def compute_erc8004_structural() -> dict:
    """Compute structural metrics for ERC-8004 from raw scraped data."""
    records: list[dict] = []

    forum_path = RAW_DIR / "forum_posts.json"
    if forum_path.exists():
        records.extend(json.loads(forum_path.read_text()))

    gh_path = RAW_DIR / "github_comments_filtered.json"
    if gh_path.exists():
        records.extend(json.loads(gh_path.read_text()))

    df = pd.DataFrame(records)
    df["date"] = df["date"].apply(_parse_date)
    df = df[df["date"].notna()]

    unique_authors = df["author"].nunique()
    earliest = df["date"].min()
    latest = df["date"].max()
    days_active = (latest - earliest).days if pd.notna(earliest) else None

    # Reply rate (forum only)
    forum_df = df[df.get("source", pd.Series(dtype=str)).isin(["forum"]) if "source" in df.columns else pd.Series([True]*len(df))]
    forum_df2 = df[df["source"] == "forum"] if "source" in df.columns else pd.DataFrame()
    reply_count = forum_df2["reply_to_post_number"].notna().sum() if "reply_to_post_number" in forum_df2.columns else 0
    reply_rate = reply_count / len(forum_df2) if len(forum_df2) > 0 else 0

    # Governance timeline
    days_proposal_to_consensus = (ERC8004_MAINNET - ERC8004_PROPOSAL).days

    # Post volume by week
    forum_only = df[df.get("source", pd.Series(dtype=str)) == "forum"] if "source" in df.columns else df
    weekly = forum_only.set_index("date").resample("W")["author"].count() if len(forum_only) > 0 else pd.Series()
    peak_week_posts = int(weekly.max()) if len(weekly) > 0 else 0

    return {
        "case": "ERC-8004",
        "governance_type": "Permissionless DAO",
        "proposal_date": ERC8004_PROPOSAL.strftime("%Y-%m-%d"),
        "consensus_date": ERC8004_MAINNET.strftime("%Y-%m-%d"),
        "days_to_consensus": days_proposal_to_consensus,
        "discussion_days_active": days_active,
        "total_discussion_records": len(df),
        "forum_posts": len(df[df["source"] == "forum"]) if "source" in df.columns else len(df),
        "github_records": len(df[df["platform"] == "github"]) if "platform" in df.columns else 0,
        "unique_contributors": unique_authors,
        "reply_rate_forum": round(float(reply_rate), 3),
        "peak_week_posts": peak_week_posts,
        # Openness: all non-EF contributors / total (estimated; refined by annotation)
        "openness_note": "refined by LLM annotation",
    }


def compute_a2a_structural() -> dict:
    """Compute structural metrics for Google A2A from raw scraped data."""
    import re

    commits   = json.loads((RAW_DIR / "a2a_commits.json").read_text())    if (RAW_DIR / "a2a_commits.json").exists()    else []
    issues    = json.loads((RAW_DIR / "a2a_issues.json").read_text())     if (RAW_DIR / "a2a_issues.json").exists()     else []
    prs       = json.loads((RAW_DIR / "a2a_prs.json").read_text())        if (RAW_DIR / "a2a_prs.json").exists()        else []
    discs     = json.loads((RAW_DIR / "a2a_discussions.json").read_text()) if (RAW_DIR / "a2a_discussions.json").exists() else []

    # ── Discussion record counts by source type ───────────────────────────
    n_issues         = sum(1 for r in issues if r.get("source") == "issue")
    n_issue_comments = sum(1 for r in issues if r.get("source") == "issue_comment")
    n_prs            = sum(1 for r in prs    if r.get("source") == "pr")
    n_pr_reviews     = sum(1 for r in prs    if r.get("source") == "pr_review_comment")
    n_discussions    = sum(1 for r in discs  if r.get("source") == "discussion")
    n_disc_comments  = sum(1 for r in discs  if r.get("source") in ("discussion_comment", "discussion_reply"))
    total_discussion = n_issues + n_issue_comments + n_prs + n_pr_reviews + n_discussions + n_disc_comments

    # ── Unique discussion contributors ────────────────────────────────────
    all_discussion = issues + prs + discs
    unique_authors = len({r["author"] for r in all_discussion if r.get("author")})

    # ── Gitvote events ────────────────────────────────────────────────────
    # Commands are issued as issue comments; parse the associated issue number
    # from issue_url (e.g. https://api.github.com/repos/…/issues/831)
    def _issue_num(r: dict) -> str | None:
        for field in ("issue_url", "url"):
            m = re.search(r"/issues/(\d+)", r.get(field, "") or "")
            if m:
                return m.group(1)
        return None

    vote_records    = [r for r in issues if "/vote"        in r.get("raw_text", "")]
    cancel_records  = [r for r in issues if "/cancel-vote" in r.get("raw_text", "")]
    voted_issues    = sorted({_issue_num(r) for r in vote_records    if _issue_num(r)}, key=int)
    cancelled_issues= sorted({_issue_num(r) for r in cancel_records  if _issue_num(r)}, key=int)
    n_vote_commands   = len(vote_records)
    n_cancel_commands = len(cancel_records)
    n_voted_threads   = len(voted_issues)   # unique issues/PRs that received a /vote

    # ── PR stats ──────────────────────────────────────────────────────────
    actual_prs  = [r for r in prs if r.get("source") == "pr"]
    merged      = sum(1 for p in actual_prs if p.get("merged"))
    merge_rate  = merged / len(actual_prs) if actual_prs else 0

    # ── Commit stats ──────────────────────────────────────────────────────
    commit_authors = len({c["author"] for c in commits if c.get("author")})
    commit_dates   = sorted(c["date"] for c in commits if c.get("date"))
    first_commit   = commit_dates[0][:10]  if commit_dates else "unknown"
    last_commit    = commit_dates[-1][:10] if commit_dates else "unknown"

    # ── Review comment authors ────────────────────────────────────────────
    review_comment_authors = len({r["author"] for r in prs
                                  if r.get("source") == "pr_review_comment" and r.get("author")})

    return {
        "case":                        "Google A2A",
        "governance_type":             "Corporate Hierarchy",
        "proposal_date":               A2A_PUBLIC_ANNOUNCE.strftime("%Y-%m-%d"),
        "first_commit":                first_commit,
        "last_commit":                 last_commit,
        "consensus_date":              "N/A (ongoing)",
        "days_to_consensus":           "N/A",
        # ── Commits ──
        "total_commits":               len(commits),
        "commit_authors":              commit_authors,
        # ── PRs ──
        "total_prs":                   len(actual_prs),
        "merged_prs":                  merged,
        "pr_merge_rate":               round(merge_rate, 3),
        "review_comment_authors":      review_comment_authors,
        # ── Discussion breakdown ──
        "disc_issues":                 n_issues,
        "disc_issue_comments":         n_issue_comments,
        "disc_prs":                    n_prs,
        "disc_pr_review_comments":     n_pr_reviews,
        "disc_github_discussions":     n_discussions,
        "disc_discussion_comments":    n_disc_comments,
        "total_discussion_records":    total_discussion,
        "unique_contributors_discussion": unique_authors,
        # ── Formal governance (gitvote) ──
        "gitvote_vote_commands":       n_vote_commands,
        "gitvote_cancel_commands":     n_cancel_commands,
        "gitvote_voted_threads":       n_voted_threads,
        "gitvote_voted_issue_nums":    ", ".join(f"#{n}" for n in voted_issues),
        "gitvote_cancelled_issue_nums": ", ".join(f"#{n}" for n in cancelled_issues),
        "openness_note":               "refined by LLM annotation",
    }


# ---------------------------------------------------------------------------
# Annotation-based metrics
# ---------------------------------------------------------------------------

def compute_annotated_metrics(case_filter: str) -> dict | None:
    ann_path = ANNOTATED_DIR / "annotated_records.json"
    if not ann_path.exists():
        return None

    records = json.loads(ann_path.read_text())
    rows = []
    for r in records:
        if r.get("_case") != case_filter:
            continue
        ann = r.get("annotation") or {}
        rows.append({
            "author": r.get("author"),
            "date": r.get("date"),
            "stakeholder_institution": ann.get("stakeholder_institution", "Unknown"),
            "argument_type": ann.get("argument_type", "Unknown"),
            "stance": ann.get("stance", "Unknown"),
            "consensus_signal": ann.get("consensus_signal", "Unknown"),
        })

    if not rows:
        return None

    df = pd.DataFrame(rows)
    inst_counts = df["stakeholder_institution"].value_counts().to_dict()
    initiating_org = ERC8004_INITIATING_ORG if case_filter == "ERC-8004" else A2A_INITIATING_ORG

    outside = df[df["stakeholder_institution"] != initiating_org]["author"].nunique()
    total = df["author"].nunique()
    openness = round(outside / total, 3) if total > 0 else 0

    return {
        "unique_institutions": df["stakeholder_institution"].nunique(),
        "institution_breakdown": inst_counts,
        "argument_type_dist": df["argument_type"].value_counts().to_dict(),
        "stance_dist": df["stance"].value_counts().to_dict(),
        "openness_index": openness,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_structural_csv(erc: dict, a2a: dict):
    rows = []
    shared_keys = ["case", "governance_type", "proposal_date", "days_to_consensus",
                   "total_discussion_records", "unique_contributors"]
    # Merge only common keys
    erc_row = {k: erc.get(k, "N/A") for k in erc}
    a2a_row = {k: a2a.get(k, "N/A") for k in a2a}
    df = pd.DataFrame([erc_row, a2a_row])
    path = ANALYSIS_DIR / "structural_metrics.csv"
    df.to_csv(path, index=False)
    print(f"Structural metrics → {path}")
    return df


def write_findings_summary(erc: dict, a2a: dict, erc_ann: dict | None, a2a_ann: dict | None):
    def fmt(v):
        return str(v) if v is not None else "TBD"

    erc_unique = erc.get("unique_contributors", "?")
    a2a_unique = a2a.get("unique_contributors_discussion", "?")
    a2a_review_authors = a2a.get("review_comment_authors", "?")

    erc_inst = erc_ann.get("unique_institutions", "TBD (annotation pending)") if erc_ann else "TBD (annotation pending)"
    a2a_inst = a2a_ann.get("unique_institutions", "TBD (annotation pending)") if a2a_ann else "TBD (annotation pending)"
    erc_open = erc_ann.get("openness_index", "TBD") if erc_ann else "TBD"
    a2a_open = a2a_ann.get("openness_index", "TBD") if a2a_ann else "TBD"

    erc_inst_table = ""
    if erc_ann and erc_ann.get("institution_breakdown"):
        total = sum(erc_ann["institution_breakdown"].values())
        for inst, n in sorted(erc_ann["institution_breakdown"].items(), key=lambda x: -x[1])[:6]:
            erc_inst_table += f"  - {inst}: {n} ({round(n/total*100,1)}%)\n"

    a2a_inst_table = ""
    if a2a_ann and a2a_ann.get("institution_breakdown"):
        total = sum(a2a_ann["institution_breakdown"].values())
        for inst, n in sorted(a2a_ann["institution_breakdown"].items(), key=lambda x: -x[1])[:6]:
            a2a_inst_table += f"  - {inst}: {n} ({round(n/total*100,1)}%)\n"

    # A2A discussion breakdown string
    a2a_disc_breakdown = (
        f"{fmt(a2a.get('disc_issues'))} issues + "
        f"{fmt(a2a.get('disc_issue_comments'))} issue comments + "
        f"{fmt(a2a.get('disc_prs'))} PR bodies + "
        f"{fmt(a2a.get('disc_pr_review_comments'))} PR review comments + "
        f"{fmt(a2a.get('disc_github_discussions'))} discussions + "
        f"{fmt(a2a.get('disc_discussion_comments'))} discussion comments"
    )
    a2a_gitvote_str = (
        f"{fmt(a2a.get('gitvote_vote_commands'))} /vote commands, "
        f"{fmt(a2a.get('gitvote_cancel_commands'))} /cancel-vote commands "
        f"across {fmt(a2a.get('gitvote_voted_threads'))} threads "
        f"({a2a.get('gitvote_voted_issue_nums', 'unknown')})"
    )

    summary = f"""# RQ1 Governance Metrics — Findings Summary
Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

---

## Comparative Governance Metrics

| Metric | ERC-8004 (DAO) | Google A2A (Corporate) |
|--------|---------------|------------------------|
| Governance type | Permissionless DAO | Corporate Hierarchy |
| First public date | {erc.get('proposal_date', '?')} | {a2a.get('proposal_date', '?')} (first commit: {a2a.get('first_commit', '?')}) |
| Consensus / status | {erc.get('consensus_date', '?')} (mainnet) | {a2a.get('consensus_date', '?')} (last commit: {a2a.get('last_commit', '?')}) |
| **Days to consensus** | **{fmt(erc.get('days_to_consensus'))}** | {fmt(a2a.get('days_to_consensus'))} |
| **Total discussion records** | **{fmt(erc.get('total_discussion_records'))}** | **{fmt(a2a.get('total_discussion_records'))}** |
| _— Forum posts_ | {fmt(erc.get('forum_posts'))} | N/A |
| _— GitHub comments_ | {fmt(erc.get('github_records'))} | {fmt(a2a.get('disc_issue_comments'))} issue comments + {fmt(a2a.get('disc_pr_review_comments'))} PR review comments |
| _— Issue/PR bodies_ | N/A | {fmt(a2a.get('disc_issues'))} issues + {fmt(a2a.get('disc_prs'))} PR bodies |
| _— GitHub Discussions_ | N/A | {fmt(a2a.get('disc_github_discussions'))} discussions + {fmt(a2a.get('disc_discussion_comments'))} replies |
| **Unique discussion contributors** | **{fmt(erc_unique)}** | **{fmt(a2a_unique)}** |
| _— Commit authors_ | N/A | {fmt(a2a.get('commit_authors'))} |
| _— PR review comment authors_ | N/A | {fmt(a2a.get('review_comment_authors'))} |
| **Unique institutions** | {fmt(erc_inst)} | {fmt(a2a_inst)} |
| Openness index | {fmt(erc_open)} | {fmt(a2a_open)} |
| Total commits | N/A | {fmt(a2a.get('total_commits'))} |
| Total PRs (merged / total) | N/A | {fmt(a2a.get('merged_prs'))} / {fmt(a2a.get('total_prs'))} ({round(float(a2a.get('pr_merge_rate', 0))*100, 1)}%) |
| Forum reply rate | {fmt(erc.get('reply_rate_forum'))} | N/A |
| **Formal governance votes** | None (EIP stage structure) | {a2a_gitvote_str} |

> **Openness index** = unique contributors from outside initiating org / total unique contributors (0–1; higher = more open).
> **ERC-8004 initiating org**: Ethereum Foundation. **A2A initiating org**: Google.

---

## A2A Discussion Record Breakdown

Total {fmt(a2a.get('total_discussion_records'))} records = {a2a_disc_breakdown}

## A2A Gitvote Details

- `/vote` commands issued: {fmt(a2a.get('gitvote_vote_commands'))}
- `/cancel-vote` commands issued: {fmt(a2a.get('gitvote_cancel_commands'))}
- Unique threads with a vote: {fmt(a2a.get('gitvote_voted_threads'))} ({a2a.get('gitvote_voted_issue_nums', '')})
- Threads where vote was cancelled: {a2a.get('gitvote_cancelled_issue_nums', 'none')}

---

## ERC-8004 Participation Breakdown (LLM-annotated)

{erc_inst_table if erc_inst_table else "_Annotation pending — run: uv run python scripts/annotate_llm.py_"}

## Google A2A Participation Breakdown (LLM-annotated)

{a2a_inst_table if a2a_inst_table else "_Annotation pending — run: uv run python scripts/annotate_llm.py_"}

---

## Data Sources

| Case | Source | Records | Link |
|------|--------|---------|------|
| ERC-8004 | Ethereum Magicians forum | {fmt(erc.get('forum_posts'))} posts | https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098 |
| ERC-8004 | GitHub ethereum/ERCs (9 core PRs) | {fmt(erc.get('github_records'))} records | https://github.com/ethereum/ERCs/pulls |
| Google A2A | Issues + issue comments | {fmt(a2a.get('disc_issues'))} + {fmt(a2a.get('disc_issue_comments'))} | https://github.com/a2aproject/A2A/issues |
| Google A2A | PRs + PR review comments | {fmt(a2a.get('disc_prs'))} + {fmt(a2a.get('disc_pr_review_comments'))} | https://github.com/a2aproject/A2A/pulls |
| Google A2A | GitHub Discussions + replies | {fmt(a2a.get('disc_github_discussions'))} + {fmt(a2a.get('disc_discussion_comments'))} | https://github.com/a2aproject/A2A/discussions |
| Google A2A | Commits | {fmt(a2a.get('total_commits'))} | https://github.com/a2aproject/A2A/commits |

---

## Theoretical Interpretation (Draft)

**Williamson puzzle**: ERC-8004 involved high asset specificity (AI agent protocol)
and high uncertainty (novel domain). TCE predicts hierarchy. Instead, competing
firms cooperated via permissionless DAO in {fmt(erc.get('days_to_consensus'))} days.

**Contrast**: Google A2A was developed entirely inside Google's corporate hierarchy.
Both produced a technically similar protocol addressing the same problem.
The governance form differed radically.

**Three DAO-enabling mechanisms (proposed)**:
1. Blockchain-enforced commitment substitutes for contractual safeguards
2. On-chain reputation removes free-rider incentive
3. Permissionless participation lowers coordination costs across heterogeneous stakeholders

---

*To complete: run `uv run python scripts/annotate_llm.py` (requires MiniMax/OpenAI/Anthropic API key with balance).*
"""
    out = OUTPUT_DIR / "findings_summary.md"
    out.write_text(summary, encoding="utf-8")
    print(f"Findings summary → {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Computing structural metrics (no annotation required)…")
    erc = compute_erc8004_structural()
    a2a = compute_a2a_structural()

    print("\n=== ERC-8004 ===")
    for k, v in erc.items():
        print(f"  {k}: {v}")

    print("\n=== Google A2A ===")
    for k, v in a2a.items():
        print(f"  {k}: {v}")

    write_structural_csv(erc, a2a)

    print("\nChecking for annotation data…")
    erc_ann = compute_annotated_metrics("ERC-8004")
    a2a_ann = compute_annotated_metrics("Google-A2A")
    if erc_ann:
        print(f"  ERC-8004 annotation available: {sum(erc_ann['institution_breakdown'].values())} records")
    else:
        print("  ERC-8004 annotation: not yet available")
    if a2a_ann:
        print(f"  Google A2A annotation available: {sum(a2a_ann['institution_breakdown'].values())} records")
    else:
        print("  Google A2A annotation: not yet available")

    write_findings_summary(erc, a2a, erc_ann, a2a_ann)
    print("\nDone.")


if __name__ == "__main__":
    main()
