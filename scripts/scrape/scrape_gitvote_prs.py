"""scrape_gitvote_prs.py — Fetch complete data for the two A2A git-vote PRs.

PRs:
  #1206: feat(spec): Add last update time to Task  (rejected)
  #831:  feat(spec): Add tasks/list method          (passed)

Outputs:
  data/raw/a2a_gitvote_prs.json     — all records (PR body + comments + reviews)
  analysis/gitvote_analysis.md      — focused analysis of vote content & rationale
"""

import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_RAW = ROOT / "data" / "raw"
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)

OUT_JSON = DATA_RAW / "a2a_gitvote_prs.json"
OUT_MD = ANALYSIS / "gitvote_analysis.md"

TOKEN_PATH = ROOT / ".env"
PR_NUMBERS = [831, 1206]
REPO = "a2aproject/A2A"


def load_token() -> str:
    for line in TOKEN_PATH.read_text().splitlines():
        if line.startswith("GITHUB_PERSONAL_ACCESS_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")


def gh(path: str, token: str) -> dict | list:
    url = f"https://api.github.com/{path.lstrip('/')}"
    cmd = [
        "curl", "-sL", "--max-time", "20",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github+json",
        url,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return json.loads(out)


def fetch_all_pages(path: str, token: str) -> list:
    results = []
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        data = gh(f"{path}{sep}per_page=100&page={page}", token)
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.3)
    return results


def fetch_pr(pr_num: int, token: str) -> dict:
    print(f"\n[PR #{pr_num}] Fetching...")

    # PR metadata
    pr_meta = gh(f"repos/{REPO}/pulls/{pr_num}", token)
    title = pr_meta.get("title", "")
    body = pr_meta.get("body", "") or ""
    state = pr_meta.get("state", "")
    merged = pr_meta.get("merged", False)
    labels = [l["name"] for l in pr_meta.get("labels", [])]
    created_at = pr_meta.get("created_at", "")
    merged_at = pr_meta.get("merged_at")
    closed_at = pr_meta.get("closed_at")
    author = pr_meta.get("user", {}).get("login", "")

    print(f"  Title: {title}")
    print(f"  State: {state} | Merged: {merged} | Labels: {labels}")

    records = []

    # PR body
    records.append({
        "pr_number": pr_num,
        "record_type": "pr_body",
        "author": author,
        "date": created_at,
        "text": body,
        "labels": labels,
        "state": state,
        "merged": merged,
        "merged_at": merged_at,
        "closed_at": closed_at,
        "title": title,
    })

    # Issue comments (regular comments + bot vote comments)
    comments = fetch_all_pages(f"repos/{REPO}/issues/{pr_num}/comments", token)
    print(f"  Issue comments: {len(comments)}")
    for c in comments:
        records.append({
            "pr_number": pr_num,
            "record_type": "issue_comment",
            "comment_id": c["id"],
            "author": c["user"]["login"],
            "date": c["created_at"],
            "text": c["body"] or "",
            "url": c["html_url"],
        })
    time.sleep(0.3)

    # PR reviews
    reviews = fetch_all_pages(f"repos/{REPO}/pulls/{pr_num}/reviews", token)
    print(f"  Reviews: {len(reviews)}")
    for r in reviews:
        records.append({
            "pr_number": pr_num,
            "record_type": "review",
            "review_id": r["id"],
            "author": r["user"]["login"],
            "date": r["submitted_at"],
            "state": r["state"],  # APPROVED / CHANGES_REQUESTED / COMMENTED
            "text": r["body"] or "",
            "url": r["html_url"],
        })
    time.sleep(0.3)

    # Review comments (inline)
    review_comments = fetch_all_pages(f"repos/{REPO}/pulls/{pr_num}/comments", token)
    print(f"  Review comments: {len(review_comments)}")
    for rc in review_comments:
        records.append({
            "pr_number": pr_num,
            "record_type": "review_comment",
            "comment_id": rc["id"],
            "author": rc["user"]["login"],
            "date": rc["created_at"],
            "text": rc["body"] or "",
            "diff_hunk": rc.get("diff_hunk", "")[:200],
            "url": rc["html_url"],
        })

    return {"pr_number": pr_num, "title": title, "records": records}


def parse_vote_results(records: list[dict]) -> dict:
    """Extract vote tallies from git-vote bot comments."""
    vote_lines = []
    final_status = ""
    voters_in_favor = []
    voters_against = []

    for r in records:
        if r.get("author") == "git-vote[bot]":
            text = r.get("text", "")
            if "Vote status" in text or "Vote created" in text or "Vote closed" in text:
                vote_lines.append(text[:800])
            if "passed" in text.lower():
                final_status = "PASSED"
            elif "closed" in text.lower() and "passed" not in text.lower():
                final_status = "CLOSED/REJECTED"
            # Parse voter mentions
            import re
            if_favor = re.findall(r":white_check_mark:[^\n]*@(\w[\w-]*)", text)
            against = re.findall(r":x:[^\n]*@(\w[\w-]*)", text)
            voters_in_favor.extend(if_favor)
            voters_against.extend(against)

    # Get /vote trigger comment
    vote_triggers = [
        r for r in records
        if r.get("record_type") == "issue_comment"
        and r.get("text", "").strip() == "/vote"
    ]

    return {
        "final_status": final_status,
        "vote_triggers": vote_triggers,
        "voters_in_favor": list(set(voters_in_favor)),
        "voters_against": list(set(voters_against)),
        "bot_log_count": len(vote_lines),
    }


def extract_key_discussion(records: list[dict]) -> list[dict]:
    """Return non-bot, non-empty substantive comments."""
    bots = {"git-vote[bot]", "gemini-code-assist[bot]", "google-cla[bot]"}
    substantive = []
    for r in records:
        author = r.get("author", "")
        text = r.get("text", "")
        if author in bots or not text.strip():
            continue
        if len(text.strip()) < 30:
            continue
        substantive.append({
            "author": author,
            "date": r.get("date", ""),
            "type": r.get("record_type", ""),
            "text": text[:600],
        })
    return substantive


def write_analysis(pr_data: list[dict]) -> None:
    lines = [
        "# Git-Vote PRs: Deep Analysis",
        "",
        "Two A2A PRs that triggered a formal TSC vote via git-vote bot.",
        "Both carry labels: `TSC Review` + `gitvote`.",
        "",
    ]

    for prd in pr_data:
        pr_num = prd["pr_number"]
        title = prd["title"]
        records = prd["records"]
        vote = parse_vote_results(records)
        discussion = extract_key_discussion(records)

        # Count by type
        from collections import Counter
        type_counts = Counter(r["record_type"] for r in records)

        # Who participated
        authors = Counter(
            r["author"] for r in records
            if r.get("author") not in {"git-vote[bot]", "gemini-code-assist[bot]", "google-cla[bot]"}
        )

        lines += [
            f"---",
            f"",
            f"## PR #{pr_num}: {title}",
            f"",
            f"**URL**: https://github.com/a2aproject/A2A/pull/{pr_num}",
            f"",
            f"### Vote Outcome",
            f"",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Final status | **{vote['final_status'] or 'unknown'}** |",
            f"| /vote triggered by | {', '.join(r['author'] for r in vote['vote_triggers']) or 'N/A'} |",
            f"| Voters in favor | {', '.join(vote['voters_in_favor']) or 'none recorded'} |",
            f"| Voters against | {', '.join(vote['voters_against']) or 'none recorded'} |",
            f"| Bot log entries | {vote['bot_log_count']} |",
            f"| Records by type | PR body: {type_counts.get('pr_body',0)}, comments: {type_counts.get('issue_comment',0)}, reviews: {type_counts.get('review',0)}, review comments: {type_counts.get('review_comment',0)} |",
            f"",
            f"### Why Was a Vote Called?",
            f"",
        ]

        # Pull PR body as context
        pr_body = next((r["text"] for r in records if r["record_type"] == "pr_body"), "")
        lines.append(f"**PR Description (excerpt)**:")
        lines.append(f"")
        lines.append(f"> {pr_body[:600].replace(chr(10), chr(10)+'> ')}")
        lines.append(f"")

        lines += [
            f"### Key Discussion Points",
            f"",
            f"Participants: {', '.join(a for a, _ in authors.most_common(12))}",
            f"",
        ]

        for i, c in enumerate(discussion[:15], 1):
            lines.append(f"**[{i}] {c['author']} ({c['type']}, {c['date'][:10]})**")
            excerpt = c["text"][:400].replace("\n", " ").replace("\r", "")
            lines.append(f"> {excerpt}")
            lines.append(f"")

        lines += [
            f"### Governance Interpretation",
            f"",
            f"- **Vote mechanism**: `git-vote[bot]` tracks reactions on a pinned comment; TSC members cast binding votes",
            f"- **Threshold**: Majority of TSC members must approve (typically >50%)",
            f"- **Implications**: The use of an explicit voting mechanism signals that this change was **contested** — consensus could not be reached through ordinary review. This is a key indicator of governance tension.",
            f"",
        ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved analysis: {OUT_MD}")


def main():
    print("=== scrape_gitvote_prs.py ===")
    token = load_token()

    all_pr_data = []
    all_records = []

    for pr_num in PR_NUMBERS:
        prd = fetch_pr(pr_num, token)
        all_pr_data.append(prd)
        # Flatten for JSON output
        for r in prd["records"]:
            r["_case"] = "Google-A2A"
            r["_note"] = "gitvote_pr"
            all_records.append(r)

    OUT_JSON.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    print(f"\nSaved JSON: {OUT_JSON} ({len(all_records)} records)")

    write_analysis(all_pr_data)
    print("Done.")


if __name__ == "__main__":
    main()
