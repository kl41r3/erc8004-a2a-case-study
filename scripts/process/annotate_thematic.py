"""
annotate_thematic.py — Open-ended thematic analysis for governance discussions.

Unlike structured 5-field annotation (stance/institution/argument_type/etc.),
thematic analysis lets the LLM extract emergent themes from discussion text
without pre-imposed categories. This is the standard qualitative coding step
that precedes structured categorization.

Each record gets a list of 1–5 themes, each with:
  - theme: short label (≤6 words)
  - evidence: direct quote or paraphrase from the text
  - sentiment: Supportive | Critical | Neutral toward the theme

Output per model: data/annotated/r2/cross-model/thematic/{model}_themes.json

Runs DeepSeek-V4-Flash, GLM-4-Plus and Moonshot-v1-Auto (three models for
triangulation — convergent themes are more trustworthy).

Usage:
  uv run python scripts/process/annotate_thematic.py --model deepseek
  uv run python scripts/process/annotate_thematic.py --model glm
  uv run python scripts/process/annotate_thematic.py --model deepseek --limit 20
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, DATA_RAW_R2, DATA_ANNOTATED_R2_THEMATIC
from lib.models import BACKENDS_THEMATIC, LEGACY_KEYS

load_dotenv(ROOT / ".env")

R2_DIR = DATA_RAW_R2
OUT_DIR = DATA_ANNOTATED_R2_THEMATIC
OUT_DIR.mkdir(parents=True, exist_ok=True)

THEMATIC_PROMPT = """\
You are a qualitative researcher performing open-ended thematic coding on
governance discussions from a technology standardization process.

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
- Each theme must be grounded in the text (quote in "evidence").
- Sentiment = the author's attitude TOWARD that theme (not toward the proposal).
- Skip empty/meaningless text: return [].
- Output ONLY the JSON array, no markdown, no explanation.
"""


def load_r2_deliberative(include_tier2_github: bool = False) -> list[dict]:
    """Load deliberative records (forum + optionally tier2 github).
    Focuses on forum posts for thematic analysis since they contain richer
    qualitative content. Tier 2 GitHub records optional (many are brief reviews).
    """
    records = []
    for tier, tier_label in [("tier1", "ERC-8004"), ("tier2", "ERC-cluster")]:
        tier_dir = R2_DIR / tier
        for fname in sorted(tier_dir.glob("*.json")):
            if "manifest" in fname.name:
                continue
            is_github = "github" in fname.name
            if is_github:
                if tier == "tier1":
                    pass  # always include tier1 github (small, 37 records)
                elif not include_tier2_github:
                    continue  # skip tier2 github by default (large, review-heavy)
            data = json.loads(fname.read_text())
            for r in data:
                text = (r.get("raw_text") or "").strip()
                if len(text) < 50:  # thematic needs more text than structured
                    continue
                r["_case"] = tier_label
                # only keep fields needed for thematic (reduce memory)
                records.append({
                    "author": r.get("author"),
                    "date": r.get("date"),
                    "platform": r.get("platform"),
                    "raw_text": text,
                    "_case": tier_label,
                    "source": r.get("source"),
                    "post_id": r.get("post_id"),
                    "comment_id": r.get("comment_id"),
                    "pr_number": r.get("pr_number"),
                })
    return records


def _record_id(r: dict) -> str:
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("pr_number"))
    return f"thematic_{r.get('_case')}_{cid}"


def strip_reasoning(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


def parse_themes(raw: str) -> tuple[list[dict] | None, str | None]:
    """Parse LLM output as JSON array of theme objects."""
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
        # try to find JSON array
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group()), None
            except json.JSONDecodeError:
                pass
        return None, f"json_parse: {raw[:80]}"


def annotate(client: OpenAI, model: str, record: dict) -> dict:
    text = record.get("raw_text", "").strip()
    if len(text) < 50:
        return {**record, "themes": [], "theme_error": "text_too_short"}

    user_msg = (
        f"Author: {record.get('author', 'unknown')}\n"
        f"Case: {record.get('_case', 'unknown')}\n"
        f"Platform: {record.get('platform', 'unknown')}\n\n"
        f"Text:\n{text[:3000]}"
    )
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
        themes, err = parse_themes(raw)
        return {**record, "themes": themes or [], "theme_error": err}
    except Exception as e:
        return {**record, "themes": [],
                "theme_error": f"api_error: {type(e).__name__}: {str(e)[:120]}"}


def main():
    parser = argparse.ArgumentParser(description="R2 Thematic analysis")
    parser.add_argument("--model", required=True,
                        choices=sorted(set(list(LEGACY_KEYS.keys()) + list(BACKENDS_THEMATIC.keys()))),
                        help="LLM backend")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--include-tier2-github", action="store_true",
                        help="Include tier2 github records (default: forum only + tier1 github)")
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()

    canonical_id = LEGACY_KEYS.get(args.model, args.model)
    backend = BACKENDS_THEMATIC[canonical_id]
    key = os.environ.get(backend["api_key_env"], "")
    if not key:
        raise SystemExit(f"{backend['api_key_env']} not set in .env")
    client = OpenAI(api_key=key, base_url=backend["base_url"])
    sleep_s = backend.get("sleep", 0.15)

    out_json = OUT_DIR / f"{canonical_id}_themes.json"
    out_manifest = OUT_DIR / f"{canonical_id}_themes_manifest.json"

    records = load_r2_deliberative(include_tier2_github=args.include_tier2_github)
    print(f"Loaded {len(records)} deliberative records (forum + tier1 github)")
    if args.include_tier2_github:
        print("  (tier2 github included)")

    if args.limit:
        records = records[:args.limit]
        print(f"LIMITED to {args.limit}")

    # Resume
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

    print(f"Thematic coding {len(to_do)} records…\n")
    t0 = time.time()

    for i, record in enumerate(to_do, 1):
        result = annotate(client, backend["model"], record)
        annotated.append(result)

        n_themes = len(result.get("themes", []))
        status = f"{n_themes} themes" if n_themes else f"SKIP ({(result.get('theme_error') or '?')[:40]})"
        elapsed = time.time() - t0
        rate = i / elapsed if elapsed > 0 else 0
        eta = (len(to_do) - i) / rate / 60 if rate > 0 else float("inf")
        print(f"  [{i}/{len(to_do)}] {record.get('_case','')} "
              f"{str(record.get('author','?'))[:16]:<16} {status}  "
              f"({rate:.1f}/s ETA {eta:.0f}m)", flush=True)

        if i % args.batch_size == 0:
            out_json.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))
        time.sleep(sleep_s)

    out_json.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))

    n_themed = sum(1 for r in annotated if r.get("themes") and not r.get("theme_error"))
    total_themes = sum(len(r.get("themes", [])) for r in annotated)
    manifest = {
        "backend": backend["name"], "model": backend["model"],
        "annotated_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(annotated),
        "with_themes": n_themed,
        "total_themes_extracted": total_themes,
        "runtime_s": round(time.time() - t0),
    }
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nDone. {n_themed}/{len(annotated)} with themes "
          f"({total_themes} total themes) → {out_json}")


if __name__ == "__main__":
    main()
