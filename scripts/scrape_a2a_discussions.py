"""scrape_a2a_discussions.py — Fetch all GitHub Discussions from a2aproject/A2A.

Uses GitHub GraphQL API (discussions are not available via REST).
Fetches: discussion metadata + body + all comments (paginated).

Outputs:
  data/raw/a2a_discussions.json   — all records (discussion bodies + comments)
  Updates a2a_manifest.json with discussion stats
"""

import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
OUT_JSON = DATA_RAW / "a2a_discussions.json"
MANIFEST = DATA_RAW / "a2a_manifest.json"

REPO_OWNER = "a2aproject"
REPO_NAME = "A2A"
GRAPHQL_URL = "https://api.github.com/graphql"


def load_token() -> str:
    env_path = ROOT / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("GITHUB_PERSONAL_ACCESS_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")


def gql(query: str, variables: dict, token: str) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


DISCUSSIONS_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: 50, after: $after, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      totalCount
      nodes {
        number
        title
        body
        createdAt
        updatedAt
        url
        category { name }
        author { login }
        upvoteCount
        comments {
          totalCount
        }
      }
    }
  }
}
"""

COMMENTS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    discussion(number: $number) {
      comments(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          author { login }
          body
          createdAt
          url
          upvoteCount
          replies(first: 20) {
            nodes {
              id
              author { login }
              body
              createdAt
              url
            }
          }
        }
      }
    }
  }
}
"""


def fetch_all_discussions(token: str) -> list[dict]:
    """Fetch all discussion metadata (not comments yet)."""
    discussions = []
    after = None
    total = None

    while True:
        variables = {"owner": REPO_OWNER, "name": REPO_NAME, "after": after}
        data = gql(DISCUSSIONS_QUERY, variables, token)
        repo = data.get("data", {}).get("repository", {})
        disc_data = repo.get("discussions", {})

        if total is None:
            total = disc_data.get("totalCount", 0)
            print(f"  Total discussions: {total}")

        nodes = disc_data.get("nodes", [])
        discussions.extend(nodes)
        print(f"  Fetched {len(discussions)}/{total}...")

        page_info = disc_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        after = page_info["endCursor"]
        time.sleep(0.5)

    return discussions


def fetch_discussion_comments(disc_number: int, token: str) -> list[dict]:
    """Fetch all comments (and replies) for a single discussion."""
    comments = []
    after = None

    while True:
        variables = {
            "owner": REPO_OWNER,
            "name": REPO_NAME,
            "number": disc_number,
            "after": after,
        }
        data = gql(COMMENTS_QUERY, variables, token)
        discussion = data.get("data", {}).get("repository", {}).get("discussion", {})
        if not discussion:
            break
        comment_data = discussion.get("comments", {})
        nodes = comment_data.get("nodes", [])
        comments.extend(nodes)

        page_info = comment_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        after = page_info["endCursor"]
        time.sleep(0.3)

    return comments


def build_records(discussions: list[dict], token: str) -> list[dict]:
    records = []
    total = len(discussions)

    for i, disc in enumerate(discussions, 1):
        number = disc["number"]
        title = disc["title"]
        author = (disc.get("author") or {}).get("login", "")
        category = (disc.get("category") or {}).get("name", "")
        n_comments = disc.get("comments", {}).get("totalCount", 0)
        created_at = disc.get("createdAt", "")
        body = disc.get("body", "") or ""

        print(f"  [{i}/{total}] #{number}: {title[:50]}  ({n_comments} comments)")

        # Discussion body as first record
        records.append({
            "source": "discussion",
            "platform": "github",
            "discussion_number": number,
            "discussion_title": title,
            "discussion_category": category,
            "record_type": "discussion_body",
            "author": author,
            "date": created_at,
            "raw_text": body,
            "url": disc.get("url", ""),
            "upvote_count": disc.get("upvoteCount", 0),
            "_case": "Google-A2A",
        })

        # Fetch and add comments if any
        if n_comments > 0:
            try:
                comments = fetch_discussion_comments(number, token)
            except Exception as e:
                print(f"    [error fetching comments] {e}")
                comments = []

            for c in comments:
                c_author = (c.get("author") or {}).get("login", "")
                c_body = c.get("body", "") or ""
                records.append({
                    "source": "discussion_comment",
                    "platform": "github",
                    "discussion_number": number,
                    "discussion_title": title,
                    "discussion_category": category,
                    "record_type": "discussion_comment",
                    "comment_id": c.get("id", ""),
                    "author": c_author,
                    "date": c.get("createdAt", ""),
                    "raw_text": c_body,
                    "url": c.get("url", ""),
                    "upvote_count": c.get("upvoteCount", 0),
                    "_case": "Google-A2A",
                })
                # Replies
                for reply in c.get("replies", {}).get("nodes", []):
                    r_author = (reply.get("author") or {}).get("login", "")
                    records.append({
                        "source": "discussion_reply",
                        "platform": "github",
                        "discussion_number": number,
                        "discussion_title": title,
                        "discussion_category": category,
                        "record_type": "discussion_reply",
                        "comment_id": reply.get("id", ""),
                        "parent_comment_id": c.get("id", ""),
                        "author": r_author,
                        "date": reply.get("createdAt", ""),
                        "raw_text": reply.get("body", "") or "",
                        "url": reply.get("url", ""),
                        "_case": "Google-A2A",
                    })
        time.sleep(0.3)

    return records


def update_manifest(n_discussions: int, n_records: int) -> None:
    if not MANIFEST.exists():
        manifest = {}
    else:
        manifest = json.loads(MANIFEST.read_text())

    manifest["discussions"] = {
        "total_discussions": n_discussions,
        "total_records": n_records,
        "file": "a2a_discussions.json",
        "note": "fetched via GitHub GraphQL API; includes discussion bodies, comments, and replies",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"Updated: {MANIFEST}")


def main():
    print("=== scrape_a2a_discussions.py ===")
    token = load_token()

    print("\n[1] Fetching discussion metadata...")
    discussions = fetch_all_discussions(token)
    print(f"Fetched {len(discussions)} discussion metadata entries")

    print("\n[2] Fetching comments for each discussion...")
    records = build_records(discussions, token)
    print(f"\nTotal records: {len(records)}")

    OUT_JSON.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Saved: {OUT_JSON}")

    update_manifest(len(discussions), len(records))

    # Quick stats
    from collections import Counter
    source_counts = Counter(r["source"] for r in records)
    print("\nRecord breakdown:")
    for k, v in source_counts.most_common():
        print(f"  {k}: {v}")

    authors = Counter(r["author"] for r in records if r["author"])
    print(f"\nUnique authors: {len(authors)}")
    print("Top 10:", authors.most_common(10))

    print("\nDone.")


if __name__ == "__main__":
    main()
