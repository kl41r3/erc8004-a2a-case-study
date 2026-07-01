"""
Merge 3 model codebooks into a single consensus codebook, then run Stage 4.

Usage:
  uv run python scripts/analyse/topic_discovery/thematic_lm/merge_codebooks.py
  uv run python scripts/analyse/topic_discovery/thematic_lm/merge_codebooks.py --backend deepseek
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.paths import ANALYSIS_TD_R2_CROSS_MODEL_THEMATIC
from lib.models import BACKENDS_THEMATIC, CANONICAL_MODELS, LEGACY_KEYS

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from scripts.analyse.topic_discovery.thematic_lm.agents import run_theme_coder_batch
from scripts.analyse.topic_discovery.thematic_lm.run_r2 import (
    load_all_records_for_coding, _save,
)

THEMATIC_LM_DIR = ANALYSIS_TD_R2_CROSS_MODEL_THEMATIC
MERGED_DIR = THEMATIC_LM_DIR / "merged"
MODELS = CANONICAL_MODELS


def load_codebooks() -> dict[str, list[dict]]:
    """Load codebooks from all 3 models."""
    result = {}
    for m in MODELS:
        p = THEMATIC_LM_DIR / m / "stage3_codebook.json"
        if p.exists():
            cb = json.loads(p.read_text())
            result[m] = cb
            print(f"  {m}: {len(cb)} themes")
        else:
            print(f"  {m}: MISSING")
    return result


def merge_codebooks(all_cbs: dict[str, list[dict]]) -> list[dict]:
    """
    Merge codebooks from multiple models.
    Strategy: collect all themes, dedup by label similarity, build unified codebook.
    """
    # Collect all themes with source
    all_themes: list[dict] = []
    for model, cb in all_cbs.items():
        for entry in cb:
            all_themes.append({
                **entry,
                "_source_model": model,
            })

    # Group by normalized label
    groups: dict[str, list[dict]] = {}
    for t in all_themes:
        key = t.get("label", "").strip().lower()
        groups.setdefault(key, []).append(t)

    # For labels that differ slightly, try to merge
    merged: list[dict] = []
    seen_keys: set[str] = set()
    theme_counter = 1

    for key, entries in sorted(groups.items(), key=lambda x: -len(x[1])):
        if key in seen_keys:
            continue

        # Collect all codes from all entries
        all_codes: list[str] = []
        for e in entries:
            all_codes.extend(e.get("codes", []))
        # Dedup
        unique_codes = list(dict.fromkeys(all_codes))

        # Use the description from the entry with most codes
        best = max(entries, key=lambda e: len(e.get("codes", [])))
        n_models = len(set(e.get("_source_model", "?") for e in entries))

        merged.append({
            "theme_id": f"T{theme_counter:02d}",
            "label": best.get("label", key.title()),
            "description": best.get("description", ""),
            "codes": unique_codes[:30],  # cap at 30 codes per theme
            "_n_models": n_models,
            "_original_labels": sorted(set(e.get("label", "") for e in entries)),
        })
        theme_counter += 1
        seen_keys.add(key)

    print(f"\n  Merged {len(all_themes)} themes from {len(all_cbs)} models → {len(merged)} themes")
    print(f"  Consensus >= 2 models:")
    for t in merged:
        consensus_mark = "★★" if t["_n_models"] >= 2 else "  "
        print(f"  {consensus_mark} {t['theme_id']}: {t['label']} "
              f"({t['_n_models']} models, {len(t['codes'])} codes)")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge Thematic-LM codebooks and run Stage 4")
    parser.add_argument("--backend", default="deepseek-v4-flash",
                        choices=sorted(set(list(LEGACY_KEYS.keys()) + list(BACKENDS_THEMATIC.keys()))),
                        help="LLM backend for Stage 4 theme coding")
    parser.add_argument("--batch-size", type=int, default=15)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    backend = LEGACY_KEYS.get(args.backend, args.backend)
    cfg = BACKENDS_THEMATIC[backend]
    api_key = os.environ.get(cfg["api_key_env"], "")
    if not api_key:
        sys.exit(f"Error: {cfg['api_key_env']} not set in .env")

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    model = cfg["model"]

    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    final_coded = MERGED_DIR / "coded_records.json"
    final_themes = MERGED_DIR / "themes.json"

    # Load and merge codebooks
    print("=== Merging Thematic-LM Codebooks ===")
    all_cbs = load_codebooks()
    if len(all_cbs) < 2:
        print("ERROR: Need at least 2 codebooks to merge")
        sys.exit(1)

    codebook = merge_codebooks(all_cbs)
    _save(final_themes, codebook)
    print(f"\n  Merged codebook saved to {final_themes}")

    # Stage 4: Theme coding with merged codebook
    if final_coded.exists() and not args.force:
        coded_existing = {c["record_id"]: c for c in json.loads(final_coded.read_text())}
        print(f"\n[Stage 4] Resuming — {len(coded_existing)} already coded")
    else:
        coded_existing = {}

    print("\n[Stage 4] Loading all R2 records for coding…")
    all_records = load_all_records_for_coding()
    print(f"  Total records to code: {len(all_records)}")

    todo = [r for r in all_records if r["_record_id"] not in coded_existing]
    batches = [todo[i:i + args.batch_size] for i in range(0, len(todo), args.batch_size)]
    print(f"  Coding {len(todo)} records in {len(batches)} batches with merged codebook…")

    errs = 0
    t0 = time.time()
    for batch_idx, batch in enumerate(batches):
        results = run_theme_coder_batch(client, model, codebook, batch)
        for item in results:
            if item["theme_id"] == "Unclassified":
                errs += 1
            coded_existing[item["record_id"]] = {
                "record_id": item["record_id"],
                "theme_id": item["theme_id"],
                "confidence": item.get("confidence", 1.0),
            }
        if (batch_idx + 1) % 10 == 0 or batch_idx == len(batches) - 1:
            _save(final_coded, list(coded_existing.values()))
            elapsed = time.time() - t0
            rate = (batch_idx + 1) / max(elapsed, 0.1)
            eta = (len(batches) - batch_idx - 1) / max(rate, 0.01) / 60
            print(f"  … batch {batch_idx+1}/{len(batches)} saved "
                  f"({len(coded_existing)} total, rate={rate:.1f}/s, ETA={eta:.0f}m, errs={errs})",
                  flush=True)
        time.sleep(0.3)

    _save(final_coded, list(coded_existing.values()))
    _save(final_themes, codebook)

    total = len(coded_existing)
    classified = sum(1 for v in coded_existing.values() if v["theme_id"] != "Unclassified")
    print(f"\n[Done] {classified}/{total} records classified ({classified/total*100:.1f}%)")
    print(f"  Codebook: {final_themes}")
    print(f"  Coded records: {final_coded}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    main()
