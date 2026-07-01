"""
scrape_r2_forum.py — Round-2 multi-topic forum scraper (ethereum-magicians).

Reads the sampling frame analysis/r2_agent_erc_universe.csv (include == "Y"),
scrapes EVERY post of EVERY included topic, and writes two clean, separate
deliverables:

  data/raw/r2/tier1/erc8004_forum.json    # ERC-8004 proper (anchor case)
  data/raw/r2/tier2/cluster_forum.json    # agent-standardization cluster

Each record carries tier / erc / topic_id / topic_title for full traceability.
Per-topic completeness is verified (scraped == stream length) and logged to a
manifest; incomplete topics are retried and flagged so nothing is silently lost.

Generalizes scripts/scrape/scrape_erc8004_forum.py (which hard-coded topic 25098
in the batch URL — fixed here by parameterizing topic_id per request).
"""

import csv
import json
import re
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import DATA_RAW_R2_TIER1, DATA_RAW_R2_TIER2, METRICS_R2_AGENT_ERC_UNIVERSE

from bs4 import BeautifulSoup

UNIVERSE_CSV = METRICS_R2_AGENT_ERC_UNIVERSE
OUT_TIER1 = DATA_RAW_R2_TIER1
OUT_TIER2 = DATA_RAW_R2_TIER2
FORUM_BASE = "https://ethereum-magicians.org"

_CURL_BASE = ["curl", "-s", "--max-time", "30", "-H", "Accept: application/json",
              "-H", "User-Agent: Mozilla/5.0 (research scraper; academic use)"]

BATCH_SIZE = 20
MAX_RETRIES = 4


def curl_get(url: str) -> dict | list:
    """GET JSON via system curl (Py 3.14 requests has SSL EOF vs this host)."""
    last_err = ""
    for attempt in range(MAX_RETRIES):
        result = subprocess.run(_CURL_BASE + [url], capture_output=True, text=True, timeout=90)
        if result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                last_err = f"json decode: {e}"
        else:
            last_err = f"curl rc={result.returncode}: {result.stderr[:120]}"
        time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"curl_get failed after {MAX_RETRIES} tries ({url}): {last_err}")


def _extract_quoted_post_numbers(cooked_html: str) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for m in re.finditer(r'data-post="(\d+)"', cooked_html):
        n = int(m.group(1))
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _parse_posts(raw_posts: list[dict], tier: str, erc: str,
                 topic_id: int, topic_title: str) -> list[dict]:
    records = []
    for p in raw_posts:
        cooked = p.get("cooked", "")
        full_text = BeautifulSoup(cooked, "html.parser").get_text(separator=" ").strip()
        stripped = BeautifulSoup(cooked, "html.parser")
        for aside in stripped.find_all("aside", class_="quote"):
            aside.decompose()
        own_text = stripped.get_text(separator=" ").strip()
        records.append({
            "tier": tier,
            "erc": erc,
            "topic_id": topic_id,
            "topic_title": topic_title,
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
            "quoted_post_numbers": _extract_quoted_post_numbers(cooked),
            "reply_count": p.get("reply_count", 0),
            "quote_count": p.get("quote_count", 0),
            "like_count": p.get("actions_summary", [{}])[0].get("count", 0)
            if p.get("actions_summary") else 0,
        })
    return records


def fetch_topic(topic_id: int, tier: str, erc: str) -> tuple[list[dict], dict]:
    """Fetch ALL posts of one topic; return (records, completeness_meta)."""
    data = curl_get(f"{FORUM_BASE}/t/{topic_id}.json")
    title = data.get("title", "")
    official = data.get("posts_count")
    stream = data.get("post_stream", {}).get("stream", [])
    first = data.get("post_stream", {}).get("posts", [])

    records = _parse_posts(first, tier, erc, topic_id, title)
    fetched = {p["id"] for p in first}
    remaining = [pid for pid in stream if pid not in fetched]

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i + BATCH_SIZE]
        qs = "&".join(f"post_ids[]={pid}" for pid in batch)
        url = f"{FORUM_BASE}/t/{topic_id}/posts.json?{qs}"
        batch_posts = []
        for attempt in range(MAX_RETRIES):
            try:
                bp = curl_get(url).get("post_stream", {}).get("posts", [])
                if bp:
                    batch_posts = bp
                    break
            except Exception as e:
                print(f"      batch retry {attempt+1}: {e}")
            time.sleep(3 + 2 * attempt)
        records.extend(_parse_posts(batch_posts, tier, erc, topic_id, title))
        time.sleep(1.2)

    meta = {
        "topic_id": topic_id, "erc": erc, "title": title,
        "official_posts_count": official,
        "stream_length": len(stream),
        "scraped_count": len(records),
        "complete": len(records) >= len(stream),
        "missing": max(0, len(stream) - len(records)),
    }
    flag = "OK" if meta["complete"] else f"INCOMPLETE missing={meta['missing']}"
    print(f"    topic {topic_id} ERC-{erc or '?'}: scraped {len(records)}/{len(stream)} "
          f"(official {official})  [{flag}]")
    return records, meta


def load_included() -> dict[str, list[dict]]:
    rows = list(csv.DictReader(open(UNIVERSE_CSV)))
    out = {"tier1": [], "tier2": []}
    for r in rows:
        if r["include"] == "Y":
            out[r["tier"]].append(r)
    return out


def scrape_tier(rows: list[dict], tier: str, out_dir: Path, out_name: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    all_records, metas = [], []
    print(f"\n=== {tier.upper()}: {len(rows)} topics ===")
    for r in sorted(rows, key=lambda x: -int(x["posts"])):
        recs, meta = fetch_topic(int(r["topic_id"]), tier, r["erc"])
        all_records.extend(recs)
        metas.append(meta)

    (out_dir / out_name).write_text(json.dumps(all_records, indent=2, ensure_ascii=False))
    incomplete = [m for m in metas if not m["complete"]]
    manifest = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "tier": tier,
        "source": "ethereum-magicians.org",
        "topics_scraped": len(metas),
        "total_records": len(all_records),
        "incomplete_topics": [m["topic_id"] for m in incomplete],
        "per_topic": metas,
    }
    (out_dir / f"{tier}_forum_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"  → saved {len(all_records)} records to {out_dir / out_name}")
    print(f"  → {len(incomplete)} incomplete topic(s): {[m['topic_id'] for m in incomplete]}")
    return manifest


def main():
    inc = load_included()
    m1 = scrape_tier(inc["tier1"], "tier1", OUT_TIER1, "erc8004_forum.json")
    m2 = scrape_tier(inc["tier2"], "tier2", OUT_TIER2, "cluster_forum.json")
    print("\n=== SUMMARY ===")
    print(f"Tier1: {m1['total_records']} posts / {m1['topics_scraped']} topics, "
          f"incomplete={m1['incomplete_topics']}")
    print(f"Tier2: {m2['total_records']} posts / {m2['topics_scraped']} topics, "
          f"incomplete={m2['incomplete_topics']}")


if __name__ == "__main__":
    main()
