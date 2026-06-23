"""
annotate_thematic_a2a.py — Open-ended thematic analysis for Google A2A records.

Mirrors annotate_thematic.py but loads from annotated_records.json (A2A case).
Only processes deliberative records (text ≥ 50 chars). Filters out bot/auto
sources and extreme-brevity records.

Output: data/annotated/r2/thematic/a2a/{model}_themes.json

Usage:
  uv run python scripts/process/annotate_thematic_a2a.py --model deepseek
  uv run python scripts/process/annotate_thematic_a2a.py --model glm
  uv run python scripts/process/annotate_thematic_a2a.py --model kimi
  uv run python scripts/process/annotate_thematic_a2a.py --model deepseek --limit 10
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

SRC_FILE = ROOT / "data" / "annotated" / "annotated_records.json"
OUT_DIR = ROOT / "data" / "annotated" / "r2" / "thematic" / "a2a"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_TEXT = 50
# Exclude pure bot/automated records
BOT_AUTHORS = {"github-actions[bot]", "dependabot[bot]", "codecov[bot]"}

BACKENDS = {
    "deepseek": {
        "name": "DeepSeek-V4-Flash",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "api_key_env": "DEEPSEEK_API_KEY",
        "sleep": 0.15,
    },
    "glm": {
        "name": "GLM-4-Plus",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-plus",
        "api_key_env": "GLM_API_KEY",
        "sleep": 0.2,
    },
    "kimi": {
        "name": "Moonshot-v1-Auto",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-auto",
        "api_key_env": "KIMI_API_KEY",
        "sleep": 0.15,
    },
}

THEMATIC_PROMPT = """\
You are a qualitative researcher performing open-ended thematic coding on
governance discussions from a technology standardization process (Google A2A protocol).

For the text below, identify 1–5 emergent governance themes. Output ONLY a
JSON array — no explanation:

[
  {
    "theme": "<short label, ≤6 words>",
    "evidence": "<direct quote or close paraphrase from the text, ≤ 40 words>",
    "sentiment": "<Supportive | Critical | Neutral>"
  }
]

Rules:
- Themes should capture governance concerns: power, legitimacy, process,
  transparency, representation, efficiency, accountability, etc.
- Technical design debates count as governance when they affect who can
  participate or what decisions get made.
- Each theme must be grounded in the text (quote in "evidence").
- Sentiment = the author's attitude TOWARD that theme.
- Skip empty/meaningless text: return [].
- Output ONLY the JSON array, no markdown, no explanation.
"""


def load_a2a_deliberative() -> list[dict]:
    """Load A2A deliberative records (text ≥ 50 chars, non-bot)."""
    all_recs = json.loads(SRC_FILE.read_text())
    records = []
    for r in all_recs:
        if r.get("_case") != "Google-A2A":
            continue
        text = (r.get("raw_text") or "").strip()
        if len(text) < MIN_TEXT:
            continue
        author = r.get("author", "")
        if author in BOT_AUTHORS:
            continue
        records.append({
            "author": author,
            "date": r.get("date"),
            "platform": "github-a2a",
            "raw_text": text,
            "_case": "Google-A2A",
            "source": r.get("source"),
            "url": r.get("url", ""),
            "issue_number": r.get("issue_number"),
            "pr_number": r.get("pr_number"),
            "title": r.get("title", ""),
        })
    return records


def _record_id(r: dict) -> str:
    url = r.get("url", "")
    if url:
        return f"thematic_a2a__{url}"
    cid = r.get("issue_number") or r.get("pr_number") or ""
    return f"thematic_a2a__{r.get('source')}_{cid}_{r.get('date')}"


def strip_reasoning(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


def parse_themes(raw: str) -> tuple[list[dict] | None, str | None]:
    raw = strip_reasoning(raw)
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
        raw = raw.split("```")[0].strip()
    try:
        themes = json.loads(raw)
        if isinstance(themes, list):
            return themes, None
        return None, f"not_a_list: {raw[:80]}"
    except json.JSONDecodeError:
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group()), None
            except json.JSONDecodeError:
                pass
        return None, f"json_parse: {raw[:80]}"


def annotate(client: OpenAI, model: str, record: dict) -> dict:
    text = record.get("raw_text", "").strip()
    title = record.get("title", "")
    context = f"Title: {title}\n\n" if title else ""

    user_msg = (
        f"Author: {record.get('author', 'unknown')}\n"
        f"Case: Google A2A protocol governance\n"
        f"Platform: GitHub ({record.get('source', 'unknown')})\n\n"
        f"{context}Text:\n{text[:3000]}"
    )
    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": THEMATIC_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            raw = resp.choices[0].message.content.strip()
            if not raw:
                if attempt < 4:
                    time.sleep(3 * (2 ** attempt))
                    continue
                return {**record, "themes": [], "theme_error": "empty_response_exhausted"}
            themes, err = parse_themes(raw)
            if themes is not None:
                return {**record, "themes": themes, "theme_error": None}
            if attempt < 4:
                time.sleep(2 * (2 ** attempt))
                continue
            return {**record, "themes": [], "theme_error": (err or "json_parse_exhausted")[:80]}
        except Exception as e:
            es = str(e)
            if "429" not in es and "rate" not in es.lower() and attempt >= 4:
                return {**record, "themes": [], "theme_error": f"api_error: {es[:80]}"}
            wait = 10 * (2 ** attempt) if ("429" in es or "rate" in es.lower()) else 3 * (2 ** attempt)
            time.sleep(wait)
    return {**record, "themes": [], "theme_error": "5_retries_exhausted"}


def main():
    parser = argparse.ArgumentParser(description="A2A thematic analysis for paper-acm")
    parser.add_argument("--model", required=True, choices=list(BACKENDS))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()

    backend = BACKENDS[args.model]
    key = os.environ.get(backend["api_key_env"], "")
    if not key:
        raise SystemExit(f"{backend['api_key_env']} not set in .env")
    client = OpenAI(api_key=key, base_url=backend["base_url"])

    out_json = OUT_DIR / f"{args.model}_themes.json"

    records = load_a2a_deliberative()
    print(f"Loaded {len(records)} A2A deliberative records (text ≥ {MIN_TEXT} chars)")

    if args.limit:
        records = records[:args.limit]
        print(f"LIMITED to {args.limit}")

    annotated: list[dict] = []
    done_ids: set[str] = set()
    if out_json.exists():
        annotated = json.loads(out_json.read_text())
        done_ids = {_record_id(r) for r in annotated}
        print(f"Resuming: {len(done_ids)} already done")

    to_do = [r for r in records if _record_id(r) not in done_ids]
    if not to_do:
        print("All done.")
        return

    print(f"Thematic coding {len(to_do)} records with {backend['name']}…\n")
    t0 = time.time()

    for i, record in enumerate(to_do, 1):
        result = annotate(client, backend["model"], record)
        annotated.append(result)

        n_themes = len(result.get("themes") or [])
        err = (result.get("theme_error") or "?")[:40]
        status = f"{n_themes} themes" if n_themes else f"SKIP ({err})"
        elapsed = time.time() - t0
        rate = i / elapsed if elapsed > 0 else 0
        eta = (len(to_do) - i) / rate / 60 if rate > 0 else float("inf")
        print(f"  [{i}/{len(to_do)}] {str(record.get('author','?'))[:18]:<18} {status}  "
              f"({rate:.1f}/s  ETA {eta:.0f}m)", flush=True)

        if i % args.batch_size == 0:
            out_json.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))

        time.sleep(backend["sleep"])

    out_json.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))

    n_with = sum(1 for r in annotated if r.get("themes"))
    n_themes_total = sum(len(r.get("themes") or []) for r in annotated)
    print(f"\nDone. {n_with}/{len(annotated)} records have themes. "
          f"Total themes: {n_themes_total} (mean {n_themes_total/max(n_with,1):.1f}/record)")
    print(f"→ {out_json}")


if __name__ == "__main__":
    main()
