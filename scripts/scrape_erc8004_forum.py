"""
Scrape ERC-8004 governance discussion data from the Fellowship of Ethereum Magicians forum.

Output: data/raw/forum_posts.json

Fields added vs. original:
  - quoted_post_numbers: list of post_numbers quoted via <aside data-post="X"> in cooked HTML.
    This captures soft reply relationships that reply_to_post_number misses (when a user
    quotes a post but clicks the bottom "Reply" button instead of the post-specific one).
  - reply_count: number of posts that explicitly reply to THIS post (from Discourse API).
  - own_text: author's own words with quoted blocks stripped out.
"""

import json
import re
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
    cmd = _CURL_BASE[:]
    if extra_headers:
        for h in extra_headers:
            cmd += ["-H", h]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed ({result.returncode}): {result.stderr[:200]}")
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("curl returned empty response")
    return json.loads(text)


def fetch_forum_posts(topic_url: str) -> list[dict]:
    json_url = topic_url.rstrip("/") + ".json"
    posts = []

    print(f"Fetching forum topic: {json_url}")
    data = curl_get(json_url)

    posts_count = data.get("posts_count")
    print(f"  Topic: {data.get('title')} — {posts_count} posts")

    post_stream = data.get("post_stream", {})
    all_post_ids = post_stream.get("stream", [])

    first_page_posts = post_stream.get("posts", [])
    posts.extend(_parse_forum_posts(first_page_posts))

    fetched_ids = {p["id"] for p in first_page_posts}
    remaining = [pid for pid in all_post_ids if pid not in fetched_ids]

    batch_size = 20
    for i in range(0, len(remaining), batch_size):
        batch = remaining[i : i + batch_size]
        qs = "&".join(f"post_ids[]={pid}" for pid in batch)
        url = f"{FORUM_BASE}/t/{FORUM_TOPIC_ID}/posts.json?{qs}"
        print(f"  Fetching batch {i // batch_size + 2} ({len(batch)} posts)…")
        try:
            batch_data = curl_get(url)
            batch_posts = batch_data.get("post_stream", {}).get("posts", [])
            if not batch_posts:
                print(f"    WARNING: empty batch, retrying in 5s…")
                time.sleep(5)
                batch_data = curl_get(url)
                batch_posts = batch_data.get("post_stream", {}).get("posts", [])
        except Exception as e:
            print(f"    ERROR: {e}")
            batch_posts = []
        posts.extend(_parse_forum_posts(batch_posts))
        time.sleep(1.5)

    return posts


def _extract_quoted_post_numbers(cooked_html: str) -> list[int]:
    """Extract post_numbers from <aside data-post="X"> quote blocks (deduplicated)."""
    seen: set[int] = set()
    result: list[int] = []
    for match in re.finditer(r'data-post="(\d+)"', cooked_html):
        n = int(match.group(1))
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


def _parse_forum_posts(raw_posts: list[dict]) -> list[dict]:
    records = []
    for p in raw_posts:
        cooked = p.get("cooked", "")

        # Full text (includes quoted content — context for LLM)
        full_text = BeautifulSoup(cooked, "html.parser").get_text(separator=" ").strip()

        # Own text only (quoted blocks removed — cleaner for stance analysis)
        stripped_soup = BeautifulSoup(cooked, "html.parser")
        for aside in stripped_soup.find_all("aside", class_="quote"):
            aside.decompose()
        own_text = stripped_soup.get_text(separator=" ").strip()

        quoted = _extract_quoted_post_numbers(cooked)

        records.append({
            "source": "forum",
            "platform": "ethereum-magicians",
            "post_id": p.get("id"),
            "post_number": p.get("post_number"),
            "date": p.get("created_at"),
            "author": p.get("username"),
            "author_display": p.get("name"),
            "raw_text": full_text,
            "own_text": own_text,
            "reply_to_post_number": p.get("reply_to_post_number"),
            "quoted_post_numbers": quoted,
            "reply_count": p.get("reply_count", 0),
            "quote_count": p.get("quote_count", 0),
            "like_count": p.get("actions_summary", [{}])[0].get("count", 0)
            if p.get("actions_summary") else 0,
        })
    return records


def main():
    forum_posts: list[dict] = []
    try:
        forum_posts = fetch_forum_posts(FORUM_TOPIC_URL)
        out = RAW_DIR / "forum_posts.json"
        out.write_text(json.dumps(forum_posts, indent=2, ensure_ascii=False))
        print(f"\nSaved {len(forum_posts)} posts → {out}")

        has_reply_to = sum(1 for p in forum_posts if p["reply_to_post_number"] is not None)
        has_quotes   = sum(1 for p in forum_posts if p["quoted_post_numbers"])
        truly_isolated = sum(1 for p in forum_posts
                             if p["reply_to_post_number"] is None and not p["quoted_post_numbers"])
        print(f"\nReply topology:")
        print(f"  Explicit reply_to_post_number: {has_reply_to}/{len(forum_posts)}")
        print(f"  Quote links (data-post):       {has_quotes}/{len(forum_posts)}")
        print(f"  Truly isolated (no link):      {truly_isolated}/{len(forum_posts)}")
    except Exception as e:
        print(f"Forum scrape failed: {e}")
        raise

    manifest = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "forum_posts_count": len(forum_posts),
        "source": FORUM_TOPIC_URL,
    }
    (RAW_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
