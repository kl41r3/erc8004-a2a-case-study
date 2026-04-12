"""
4-stage Thematic-LM pipeline with checkpoint/resume support.

Stages:
  1. Coder        — open-code each record in batches
  2. Aggregator   — group codes into raw theme clusters
  3. Reviewer     — refine clusters into a clean codebook
  4. Theme coder  — assign a theme from the codebook to each record

Checkpoint files (in output/topic_discovery/thematic_lm/):
  stage1_codes.json   — {record_id: code}
  stage2_clusters.json — {theme_label: [codes]}
  stage3_codebook.json — [{theme_id, label, description, codes}]
  coded_records.json  — [{record_id, theme_id, confidence}]  (final)
  themes.json         — codebook (same as stage3_codebook.json, final copy)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .agents import (
    run_aggregator,
    run_coder_batch,
    run_reviewer,
    run_theme_coder_batch,
)

BOT_AUTHORS = {
    "gemini-code-assist[bot]", "google-cla[bot]", "github-actions[bot]",
    "codecov[bot]", "dependabot[bot]", "git-vote[bot]",
}

OUT_DIR = Path(__file__).parents[4] / "output" / "topic_discovery" / "thematic_lm"


def _load_records(data_path: Path, limit: int = 0) -> list[dict]:
    raw = json.loads(data_path.read_text())
    records = []
    for r in raw:
        author = r.get("author", "")
        if author in BOT_AUTHORS or author.endswith("[bot]"):
            continue
        text = (r.get("raw_text") or "").strip()
        if len(text) < 20:
            continue
        case = r.get("_case", "")
        if case not in {"ERC-8004", "Google-A2A"}:
            continue
        # Use url as primary key (unique per record); fall back to composite
        url = (r.get("url") or "").strip()
        if url:
            record_id = url
        else:
            uid = r.get("post_id") or r.get("comment_id") or r.get("issue_number") or r.get("pr_number")
            record_id = f"{case}_{r.get('source','?')}_{uid or hash(r.get('raw_text',''))}"
        records.append({**r, "_record_id": record_id})
    if limit:
        records = records[:limit]
    print(f"  Loaded {len(records)} usable records")
    return records


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def run_pipeline(
    client,
    model: str,
    data_path: Path,
    batch_size: int = 15,
    limit: int = 0,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stage1_path = OUT_DIR / "stage1_codes.json"
    stage2_path = OUT_DIR / "stage2_clusters.json"
    stage3_path = OUT_DIR / "stage3_codebook.json"
    final_coded = OUT_DIR / "coded_records.json"
    final_themes = OUT_DIR / "themes.json"

    records = _load_records(data_path, limit=limit)

    # ---- Stage 1: Coder ----
    if stage1_path.exists():
        existing_codes: dict = json.loads(stage1_path.read_text())
        print(f"[Stage 1] Resuming — {len(existing_codes)} already coded")
    else:
        existing_codes = {}

    todo = [r for r in records if r["_record_id"] not in existing_codes]
    batches = [todo[i:i+batch_size] for i in range(0, len(todo), batch_size)]
    print(f"[Stage 1] Coding {len(todo)} records in {len(batches)} batches …")

    for batch_idx, batch in enumerate(batches):
        results = run_coder_batch(client, model, batch)
        for item in results:
            if item["code"]:
                existing_codes[item["record_id"]] = item["code"]
        if (batch_idx + 1) % 10 == 0 or batch_idx == len(batches) - 1:
            _save(stage1_path, existing_codes)
            print(f"  … batch {batch_idx+1}/{len(batches)} saved ({len(existing_codes)} total)")
        time.sleep(0.3)

    _save(stage1_path, existing_codes)
    print(f"[Stage 1] Done — {len(existing_codes)} codes")

    # ---- Stage 2: Aggregator ----
    if stage2_path.exists():
        clusters = json.loads(stage2_path.read_text())
        print(f"[Stage 2] Loaded cached clusters ({len(clusters)} themes)")
    else:
        import random
        unique_codes = list(set(existing_codes.values()))
        # Sample up to 300 codes to keep prompt within MiniMax context limits
        if len(unique_codes) > 300:
            random.seed(42)
            sampled = random.sample(unique_codes, 300)
            print(f"[Stage 2] Aggregating sample of 300 / {len(unique_codes)} unique codes …")
        else:
            sampled = unique_codes
            print(f"[Stage 2] Aggregating {len(sampled)} unique codes …")
        clusters = run_aggregator(client, model, sampled)
        _save(stage2_path, clusters)
        print(f"[Stage 2] Done — {len(clusters)} raw theme clusters")

    # ---- Stage 3: Reviewer ----
    if stage3_path.exists():
        codebook = json.loads(stage3_path.read_text())
        print(f"[Stage 3] Loaded cached codebook ({len(codebook)} themes)")
    else:
        print("[Stage 3] Reviewing and refining codebook …")
        codebook = run_reviewer(client, model, clusters)
        _save(stage3_path, codebook)
        print(f"[Stage 3] Done — {len(codebook)} themes in final codebook")
        for entry in codebook:
            print(f"  {entry['theme_id']}: {entry['label']}")

    # ---- Stage 4: Theme coder ----
    if final_coded.exists():
        coded: dict = {
            item["record_id"]: item
            for item in json.loads(final_coded.read_text())
        }
        print(f"[Stage 4] Resuming — {len(coded)} already theme-coded")
    else:
        coded = {}

    todo4 = [r for r in records if r["_record_id"] not in coded]
    batches4 = [todo4[i:i+batch_size] for i in range(0, len(todo4), batch_size)]
    print(f"[Stage 4] Theme-coding {len(todo4)} records in {len(batches4)} batches …")

    for batch_idx, batch in enumerate(batches4):
        results = run_theme_coder_batch(client, model, codebook, batch)
        for item in results:
            coded[item["record_id"]] = item
        if (batch_idx + 1) % 10 == 0 or batch_idx == len(batches4) - 1:
            _save(final_coded, list(coded.values()))
            print(f"  … batch {batch_idx+1}/{len(batches4)} saved ({len(coded)} total)")
        time.sleep(0.3)

    _save(final_coded, list(coded.values()))
    _save(final_themes, codebook)
    print(f"\n[Done] {len(coded)} records theme-coded.")
    print(f"  Codebook → {final_themes}")
    print(f"  Coded records → {final_coded}")
