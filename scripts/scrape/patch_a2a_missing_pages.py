"""
Recover pages that timed out during the initial A2A scrape.

Known gaps (from scrape log):
  - issues/comments page 10+ (got 9 pages = 900 comments)
  - pulls/comments  page 11+ (got 10 pages = 1000 comments)

Strategy:
  1. Fetch from the known-missing page onward until empty
  2. For PR review comments page 11 specifically: retry with longer timeout
  3. Merge new records into existing JSON files (dedup by id)
  4. Update CHECKSUMS.json
"""

import hashlib
import json
import subprocess
import time
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
REPO = "google/A2A"
API_BASE = "https://api.github.com"


def curl_get_json(url: str, token: str, timeout: int = 60) -> list | dict | None:
    cmd = [
        "curl", "-sL", f"--max-time", str(timeout),
        "-H", "Accept: application/vnd.github+json",
        "-H", f"Authorization: Bearer {token}",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def fetch_from_page(endpoint: str, start_page: int, token: str,
                    timeout: int = 60) -> list[dict]:
    """Fetch all records from start_page onward for a given endpoint."""
    records = []
    page = start_page
    while True:
        sep = "&" if "?" in endpoint else "?"
        url = f"{API_BASE}/repos/{REPO}/{endpoint}{sep}per_page=100&page={page}"
        print(f"  GET {endpoint} page {page}...", end=" ", flush=True)
        data = curl_get_json(url, token, timeout=timeout)
        if not isinstance(data, list) or not data:
            print(f"empty/error — stopping")
            break
        print(f"{len(data)} records")
        records.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.3)
    return records


def merge_into_file(path: Path, new_raw: list[dict],
                    parse_fn, id_key: str) -> tuple[int, int]:
    """Load existing records, merge new ones by id_key, save back."""
    existing = json.loads(path.read_text())
    existing_ids = {r[id_key] for r in existing if r.get(id_key)}

    new_parsed = []
    for item in new_raw:
        body = item.get("body") or ""
        if not body.strip():
            continue
        parsed = parse_fn(item)
        if parsed.get(id_key) not in existing_ids:
            new_parsed.append(parsed)
            existing_ids.add(parsed.get(id_key))

    combined = existing + new_parsed
    path.write_text(json.dumps(combined, indent=2, ensure_ascii=False))
    return len(new_parsed), len(combined)


def parse_issue_comment(item: dict) -> dict:
    return {
        "source": "issue_comment",
        "platform": "github",
        "comment_id": item.get("id"),
        "issue_url": item.get("issue_url", ""),
        "date": item.get("created_at"),
        "author": (item.get("user") or {}).get("login"),
        "raw_text": (item.get("body") or "").strip(),
        "url": item.get("html_url"),
    }


def parse_pr_review_comment(item: dict) -> dict:
    return {
        "source": "pr_review_comment",
        "platform": "github",
        "comment_id": item.get("id"),
        "pr_url": item.get("pull_request_url", ""),
        "date": item.get("created_at"),
        "author": (item.get("user") or {}).get("login"),
        "raw_text": (item.get("body") or "").strip(),
        "url": item.get("html_url"),
    }


def update_checksums():
    manifest = {}
    for f in sorted(RAW_DIR.glob("*.json")):
        if f.name == "CHECKSUMS.json":
            continue
        content = f.read_bytes()
        data = json.loads(content)
        manifest[f.name] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "records": len(data) if isinstance(data, list) else None,
            "bytes": len(content),
        }
    (RAW_DIR / "CHECKSUMS.json").write_text(json.dumps(manifest, indent=2))


def main():
    from dotenv import load_dotenv
    import os
    load_dotenv(Path(__file__).parent.parent / ".env")
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_PERSONAL_ACCESS_TOKEN not set in .env")

    print("=== Patching missing A2A pages ===\n")

    # --- Issue comments: we have pages 1-9, fetch page 10 onward ---
    print("1. Issue comments (missing from page 10):")
    raw_ic = fetch_from_page("issues/comments", start_page=10, token=token, timeout=60)
    added_ic, total_ic = merge_into_file(
        RAW_DIR / "a2a_issues.json",
        raw_ic,
        parse_fn=parse_issue_comment,
        id_key="comment_id",
    )
    print(f"   Added {added_ic} new records → {total_ic} total in a2a_issues.json\n")

    # --- PR review comments: we have pages 1-10, fetch page 11 onward ---
    # Page 11 previously returned truncated JSON; use longer timeout
    print("2. PR review comments (missing from page 11):")
    raw_pr = fetch_from_page("pulls/comments", start_page=11, token=token, timeout=90)
    added_pr, total_pr = merge_into_file(
        RAW_DIR / "a2a_prs.json",
        raw_pr,
        parse_fn=parse_pr_review_comment,
        id_key="comment_id",
    )
    print(f"   Added {added_pr} new records → {total_pr} total in a2a_prs.json\n")

    print("Updating CHECKSUMS.json...")
    update_checksums()

    print(f"\nDone. New records: +{added_ic} issue comments, +{added_pr} PR review comments")


if __name__ == "__main__":
    main()
