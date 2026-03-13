"""
Scrape ERC-8004 governance discussion data from the Fellowship of Ethereum Magicians forum.

Output: data/raw/forum_posts.json
"""

import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

FORUM_TOPIC_URL = "https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098"
FORUM_TOPIC_ID = "25098"
FORUM_BASE = "https://ethereum-magicians.org"

_CURL_BASE = ["curl", "-s", "--max-time", "30", "-H", "Accept: application/json",
              "-H", "User-Agent: Mozilla/5.0 (research scraper; academic use)"]


def curl_get(url: str, extra_headers: list[str] | None = None) -> dict | list:
    """GET a URL via curl and return parsed JSON."""
    cmd = _CURL_BASE[:]
    if extra_headers:
        for h in extra_headers:
            cmd += ["-H", h]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed ({result.returncode}): {result.stderr[:200]}")
    return json.loads(result.stdout)


def fetch_forum_posts(topic_url: str) -> list[dict]:
    """Fetch all posts from a Discourse forum topic via its JSON API."""
    json_url = topic_url.rstrip("/") + ".json"
    posts = []

    print(f"Fetching forum topic: {json_url}")
    data = curl_get(json_url)

    topic_meta = {
        "title": data.get("title"),
        "posts_count": data.get("posts_count"),
        "created_at": data.get("created_at"),
        "last_posted_at": data.get("last_posted_at"),
    }
    print(f"  Topic: {topic_meta['title']} — {topic_meta['posts_count']} posts")

    post_stream = data.get("post_stream", {})
    all_post_ids = post_stream.get("stream", [])

    # First page is embedded in the topic JSON
    first_page_posts = post_stream.get("posts", [])
    posts.extend(_parse_forum_posts(first_page_posts))

    # Remaining posts: Discourse pagination via /t/{id}/posts.json?post_ids[]=
    fetched_ids = {p["id"] for p in first_page_posts}
    remaining = [pid for pid in all_post_ids if pid not in fetched_ids]

    batch_size = 20
    for i in range(0, len(remaining), batch_size):
        batch = remaining[i : i + batch_size]
        qs = "&".join(f"post_ids[]={pid}" for pid in batch)
        url = f"{FORUM_BASE}/t/{FORUM_TOPIC_ID}/posts.json?{qs}"
        print(f"  Fetching posts batch {i // batch_size + 2} ({len(batch)} posts)…")
        batch_data = curl_get(url)
        batch_posts = batch_data.get("post_stream", {}).get("posts", [])
        posts.extend(_parse_forum_posts(batch_posts))
        time.sleep(1)  # be polite

    return posts


def _parse_forum_posts(raw_posts: list[dict]) -> list[dict]:
    records = []
    for p in raw_posts:
        soup = BeautifulSoup(p.get("cooked", ""), "html.parser")
        text = soup.get_text(separator=" ").strip()

        records.append({
            "source": "forum",
            "platform": "ethereum-magicians",
            "post_id": p.get("id"),
            "post_number": p.get("post_number"),
            "date": p.get("created_at"),
            "author": p.get("username"),
            "author_display": p.get("name"),
            "raw_text": text,
            "reply_to_post_number": p.get("reply_to_post_number"),
            "like_count": p.get("actions_summary", [{}])[0].get("count", 0)
            if p.get("actions_summary")
            else 0,
        })
    return records


def main():
    try:
        forum_posts = fetch_forum_posts(FORUM_TOPIC_URL)
        out = RAW_DIR / "forum_posts.json"
        out.write_text(json.dumps(forum_posts, indent=2, ensure_ascii=False))
        print(f"\nSaved {len(forum_posts)} forum posts → {out}")
    except Exception as e:
        print(f"Forum scrape failed: {e}")

    manifest = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "forum_posts_count": len(forum_posts) if 'forum_posts' in dir() else 0,
        "source": FORUM_TOPIC_URL,
    }
    (RAW_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
