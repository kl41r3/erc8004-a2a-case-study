"""
Scrape Google A2A (Agent-to-Agent) governance data from GitHub.

Sources:
  - https://github.com/google/A2A  (commits, issues, PRs, releases)

A2A is developed under corporate hierarchy governance by Google.
We collect the same types of records as for ERC-8004 to enable
side-by-side comparison.

Output: data/raw/a2a_commits.json
        data/raw/a2a_issues.json
        data/raw/a2a_prs.json
        data/raw/a2a_manifest.json
"""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

REPO = "google/A2A"
API_BASE = "https://api.github.com"

_CURL_BASE = [
    "curl", "-sL", "--max-time", "30",
    "-H", "Accept: application/vnd.github+json",
    "-H", "User-Agent: Mozilla/5.0 (research scraper; academic use)",
]


def curl_get(url: str, token: str | None = None) -> dict | list:
    cmd = _CURL_BASE[:]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr[:200]}")
    data = json.loads(result.stdout)
    if isinstance(data, dict) and data.get("message") == "Not Found":
        raise RuntimeError(f"404: {url}")
    return data


def fetch_paginated(base_url: str, token: str | None = None,
                    max_pages: int = 20) -> list[dict]:
    records = []
    sep = "&" if "?" in base_url else "?"
    for page in range(1, max_pages + 1):
        url = f"{base_url}{sep}per_page=100&page={page}"
        try:
            items = curl_get(url, token)
        except Exception as e:
            print(f"    page {page} error: {e}")
            break
        if not isinstance(items, list) or not items:
            break
        records.extend(items)
        if len(items) < 100:
            break
        time.sleep(0.5)
    return records


# ---------------------------------------------------------------------------
# Commits
# ---------------------------------------------------------------------------

def fetch_commits(token: str | None = None) -> list[dict]:
    print(f"Fetching commits for {REPO}…")
    raw = fetch_paginated(f"{API_BASE}/repos/{REPO}/commits", token)
    records = []
    for c in raw:
        commit = c.get("commit", {})
        author = commit.get("author", {}) or {}
        committer = commit.get("committer", {}) or {}
        gh_author = c.get("author") or {}
        records.append({
            "source": "commit",
            "platform": "github",
            "sha": c.get("sha", "")[:10],
            "date": author.get("date") or committer.get("date"),
            "author": gh_author.get("login") or author.get("name"),
            "author_name": author.get("name"),
            "message": commit.get("message", "").strip(),
            "url": c.get("html_url"),
        })
    print(f"  {len(records)} commits")
    return records


# ---------------------------------------------------------------------------
# Issues (governance discussions)
# ---------------------------------------------------------------------------

def fetch_issues(token: str | None = None) -> list[dict]:
    print(f"Fetching issues for {REPO}…")
    # state=all to get both open and closed
    raw = fetch_paginated(f"{API_BASE}/repos/{REPO}/issues?state=all", token)
    records = []
    for issue in raw:
        if "pull_request" in issue:
            continue  # PRs show up in issues API — skip
        body = issue.get("body") or ""
        records.append({
            "source": "issue",
            "platform": "github",
            "issue_number": issue.get("number"),
            "date": issue.get("created_at"),
            "closed_at": issue.get("closed_at"),
            "author": (issue.get("user") or {}).get("login"),
            "title": issue.get("title", ""),
            "raw_text": body.strip(),
            "state": issue.get("state"),
            "labels": [lb["name"] for lb in (issue.get("labels") or [])],
            "url": issue.get("html_url"),
        })

    # Fetch issue comments
    print(f"  {len(records)} issues — fetching their comments…")
    comments = fetch_paginated(f"{API_BASE}/repos/{REPO}/issues/comments?state=all", token)
    for c in comments:
        body = c.get("body") or ""
        if not body.strip():
            continue
        records.append({
            "source": "issue_comment",
            "platform": "github",
            "comment_id": c.get("id"),
            "issue_url": c.get("issue_url", ""),
            "date": c.get("created_at"),
            "author": (c.get("user") or {}).get("login"),
            "raw_text": body.strip(),
            "url": c.get("html_url"),
        })

    print(f"  {len(records)} total (issues + comments)")
    return records


# ---------------------------------------------------------------------------
# Pull Requests
# ---------------------------------------------------------------------------

def fetch_prs(token: str | None = None) -> list[dict]:
    print(f"Fetching PRs for {REPO}…")
    raw = fetch_paginated(f"{API_BASE}/repos/{REPO}/pulls?state=all", token)
    records = []
    for pr in raw:
        body = pr.get("body") or ""
        records.append({
            "source": "pr",
            "platform": "github",
            "pr_number": pr.get("number"),
            "date": pr.get("created_at"),
            "merged_at": pr.get("merged_at"),
            "closed_at": pr.get("closed_at"),
            "author": (pr.get("user") or {}).get("login"),
            "title": pr.get("title", ""),
            "raw_text": body.strip(),
            "state": pr.get("state"),
            "merged": pr.get("merged_at") is not None,
            "labels": [lb["name"] for lb in (pr.get("labels") or [])],
            "url": pr.get("html_url"),
        })

    # Fetch PR review comments
    print(f"  {len(records)} PRs — fetching review comments…")
    review_comments = fetch_paginated(
        f"{API_BASE}/repos/{REPO}/pulls/comments", token
    )
    for c in review_comments:
        body = c.get("body") or ""
        if not body.strip():
            continue
        records.append({
            "source": "pr_review_comment",
            "platform": "github",
            "comment_id": c.get("id"),
            "pr_url": c.get("pull_request_url", ""),
            "date": c.get("created_at"),
            "author": (c.get("user") or {}).get("login"),
            "raw_text": body.strip(),
            "url": c.get("html_url"),
        })

    print(f"  {len(records)} total (PRs + review comments)")
    return records


# ---------------------------------------------------------------------------
# Repo metadata (for timeline anchoring)
# ---------------------------------------------------------------------------

def fetch_repo_meta(token: str | None = None) -> dict:
    data = curl_get(f"{API_BASE}/repos/{REPO}", token)
    return {
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "default_branch": data.get("default_branch"),
        "license": (data.get("license") or {}).get("spdx_id"),
        "url": data.get("html_url"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-token", default=None,
                        help="GitHub PAT — raises rate limit from 60 to 5000 req/hr")
    args = parser.parse_args()
    token = args.github_token

    # Repo metadata
    print(f"Fetching repo metadata for {REPO}…")
    try:
        meta = fetch_repo_meta(token)
        print(f"  Created: {meta['created_at']}  Stars: {meta['stars']}")
    except Exception as e:
        print(f"  Metadata fetch failed: {e}")
        meta = {}

    # Commits
    try:
        commits = fetch_commits(token)
        (RAW_DIR / "a2a_commits.json").write_text(
            json.dumps(commits, indent=2, ensure_ascii=False)
        )
    except Exception as e:
        print(f"Commit fetch failed: {e}")
        commits = []

    # Issues + comments
    try:
        issues = fetch_issues(token)
        (RAW_DIR / "a2a_issues.json").write_text(
            json.dumps(issues, indent=2, ensure_ascii=False)
        )
    except Exception as e:
        print(f"Issue fetch failed: {e}")
        issues = []

    # PRs + review comments
    try:
        prs = fetch_prs(token)
        (RAW_DIR / "a2a_prs.json").write_text(
            json.dumps(prs, indent=2, ensure_ascii=False)
        )
    except Exception as e:
        print(f"PR fetch failed: {e}")
        prs = []

    # Manifest
    manifest = {
        "case": "Google A2A",
        "repo": f"https://github.com/{REPO}",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "repo_meta": meta,
        "commits_count": len(commits),
        "issues_count": len([r for r in issues if r["source"] == "issue"]),
        "issue_comments_count": len([r for r in issues if r["source"] == "issue_comment"]),
        "prs_count": len([r for r in prs if r["source"] == "pr"]),
        "pr_review_comments_count": len([r for r in prs if r["source"] == "pr_review_comment"]),
        "total_discussion_records": len(issues) + len(prs),
    }
    (RAW_DIR / "a2a_manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"\n=== A2A Scrape Summary ===")
    print(f"  Commits:              {manifest['commits_count']}")
    print(f"  Issues:               {manifest['issues_count']}")
    print(f"  Issue comments:       {manifest['issue_comments_count']}")
    print(f"  PRs:                  {manifest['prs_count']}")
    print(f"  PR review comments:   {manifest['pr_review_comments_count']}")
    print(f"  Total discussion:     {manifest['total_discussion_records']}")
    print(f"\nData → {RAW_DIR}")


if __name__ == "__main__":
    main()
