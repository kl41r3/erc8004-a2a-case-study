"""
Scrape ERC-8004 core lifecycle PR data DIRECTLY by PR number.

Problem with original scrape_erc8004.py:
  It used GitHub search (q=ERC-8004 repo:ethereum/ERCs) which returned ecosystem
  PRs that merely *cite* ERC-8004 as a dependency. The actual 9 lifecycle PRs
  (#1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488) were largely
  absent from the search results, leaving them with 0–2 comments in the raw data.

This script:
  - Fetches each of the 9 PRs directly by number
  - Collects: PR body, issue comments, review comments, reviews (with bodies)
  - Writes data/raw/github_comments.json  (overwrites)
  - Then re-runs the filter to update github_comments_filtered.json

Usage:
  uv run python scripts/scrape_erc8004_prs.py
  uv run python scripts/scrape_erc8004_prs.py --github-token ghp_xxx
  (token is auto-loaded from .env if GITHUB_PERSONAL_ACCESS_TOKEN is set)
"""

import json
import os
import subprocess
import time
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

REPO = "ethereum/ERCs"
BASE_API = "https://api.github.com"

# The 9 PRs that directly modify ERC-8004 spec or lifecycle status.
# Verified manually: https://github.com/ethereum/ERCs/pulls?q=erc-8004
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


def load_token() -> str | None:
    """Load GitHub PAT from environment or .env file."""
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token:
        return token
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("GITHUB_PERSONAL_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def curl_get(url: str, token: str | None) -> dict | list:
    """GET via curl, return parsed JSON. Uses PAT if provided."""
    cmd = [
        "curl", "-s", "-L", "--max-time", "30",
        "-H", "Accept: application/vnd.github+json",
        "-H", "User-Agent: Mozilla/5.0 (research scraper; academic use)",
    ]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed ({result.returncode}): {result.stderr[:300]}")
    parsed = json.loads(result.stdout)
    # GitHub returns {"message": "...", "documentation_url": "..."} on error
    if isinstance(parsed, dict) and "message" in parsed and "documentation_url" in parsed:
        raise RuntimeError(f"GitHub API error: {parsed['message']}")
    return parsed


def fetch_paginated(base_url: str, token: str | None, label: str) -> list[dict]:
    """Fetch all pages from a paginated GitHub API endpoint."""
    records = []
    page = 1
    while True:
        sep = "&" if "?" in base_url else "?"
        url = f"{base_url}{sep}per_page=100&page={page}"
        try:
            items = curl_get(url, token)
        except Exception as e:
            print(f"    [{label}] page {page} error: {e}")
            break
        if not isinstance(items, list) or not items:
            break
        records.extend(items)
        print(f"    [{label}] page {page}: {len(items)} items")
        if len(items) < 100:
            break
        page += 1
        time.sleep(0.3)
    return records


def fetch_pr(pr_number: int, pr_desc: str, token: str | None) -> list[dict]:
    """Fetch all governance-relevant content for a single PR."""
    records = []

    # 1. PR body (description written by author)
    try:
        pr_data = curl_get(f"{BASE_API}/repos/{REPO}/pulls/{pr_number}", token)
        body = (pr_data.get("body") or "").strip()
        if body:
            records.append({
                "source": "github_pr_body",
                "platform": "github",
                "pr_number": pr_number,
                "pr_description": pr_desc,
                "comment_id": f"pr_{pr_number}_body",
                "date": pr_data.get("created_at"),
                "author": (pr_data.get("user") or {}).get("login"),
                "raw_text": body,
                "state": pr_data.get("state"),
                "url": pr_data.get("html_url"),
            })
            print(f"    [pr_body] 1 item (len={len(body)})")
        else:
            print(f"    [pr_body] empty body")
    except Exception as e:
        print(f"    [pr_body] error: {e}")

    # 2. Issue comments (general discussion on the PR)
    raw_issue = fetch_paginated(
        f"{BASE_API}/repos/{REPO}/issues/{pr_number}/comments", token,
        label="issue_comments"
    )
    for item in raw_issue:
        body = (item.get("body") or "").strip()
        if not body:
            continue
        records.append({
            "source": "github_issue_comment",
            "platform": "github",
            "pr_number": pr_number,
            "pr_description": pr_desc,
            "comment_id": item.get("id"),
            "date": item.get("created_at"),
            "author": (item.get("user") or {}).get("login"),
            "raw_text": body,
            "state": None,
            "url": item.get("html_url"),
        })

    # 3. Review comments (inline code review comments)
    raw_review = fetch_paginated(
        f"{BASE_API}/repos/{REPO}/pulls/{pr_number}/comments", token,
        label="review_comments"
    )
    for item in raw_review:
        body = (item.get("body") or "").strip()
        if not body:
            continue
        records.append({
            "source": "github_review_comment",
            "platform": "github",
            "pr_number": pr_number,
            "pr_description": pr_desc,
            "comment_id": item.get("id"),
            "date": item.get("created_at"),
            "author": (item.get("user") or {}).get("login"),
            "raw_text": body,
            "state": None,
            "url": item.get("html_url"),
        })

    # 4. Reviews with body text (approve/request changes with explanation)
    raw_reviews = fetch_paginated(
        f"{BASE_API}/repos/{REPO}/pulls/{pr_number}/reviews", token,
        label="reviews"
    )
    for item in raw_reviews:
        body = (item.get("body") or "").strip()
        if not body:
            continue
        records.append({
            "source": "github_review",
            "platform": "github",
            "pr_number": pr_number,
            "pr_description": pr_desc,
            "comment_id": item.get("id"),
            "date": item.get("submitted_at"),
            "author": (item.get("user") or {}).get("login"),
            "raw_text": body,
            "state": item.get("state"),
            "url": item.get("html_url"),
        })

    print(f"  PR #{pr_number}: {len(records)} total records")
    return records


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scrape ERC-8004 core lifecycle PRs directly by number")
    parser.add_argument("--github-token", default=None, help="GitHub PAT (or set GITHUB_PERSONAL_ACCESS_TOKEN in .env)")
    args = parser.parse_args()

    token = args.github_token or load_token()
    if token:
        print("GitHub PAT loaded — using authenticated requests (5,000 req/hr)")
    else:
        print("WARNING: No GitHub PAT — using anonymous requests (60 req/hr). May rate-limit.")

    all_records: list[dict] = []
    for pr_number, pr_desc in sorted(ERC8004_CORE_PRS.items()):
        print(f"\nFetching PR #{pr_number}: {pr_desc}")
        records = fetch_pr(pr_number, pr_desc, token)
        all_records.extend(records)
        time.sleep(0.5)

    # Summary
    from collections import Counter
    by_pr = Counter(r["pr_number"] for r in all_records)
    by_source = Counter(r["source"] for r in all_records)

    print(f"\n=== Summary ===")
    print(f"Total records: {len(all_records)}")
    print("By PR:")
    for pr_num in sorted(ERC8004_CORE_PRS):
        desc = ERC8004_CORE_PRS[pr_num]
        count = by_pr.get(pr_num, 0)
        print(f"  #{pr_num}: {count:3d} records  — {desc}")
    print("By source type:")
    for src, count in sorted(by_source.items()):
        print(f"  {src}: {count}")

    # Write github_comments.json (replaces old search-based data)
    out_path = RAW_DIR / "github_comments.json"
    out_path.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(all_records)} records → {out_path}")

    # Auto-run filter
    print("\nRunning filter_github.py…")
    import importlib.util, sys
    filter_path = Path(__file__).parent / "filter_github.py"
    spec = importlib.util.spec_from_file_location("filter_github", filter_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


if __name__ == "__main__":
    main()
