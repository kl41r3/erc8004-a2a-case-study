"""
Thematic-LM R2 — entry point for paper-acm.

Re-runs Stages 2–4 using pre-computed Stage 1 open codes from:
  data/annotated/r2/thematic/{deepseek,glm,kimi}_themes.json   (ERC)
  data/annotated/r2/thematic/a2a/{deepseek,glm,kimi}_themes.json  (A2A)

Stage 1 is skipped (already done via annotate_thematic.py / annotate_thematic_a2a.py).
Outputs to: output/topic_discovery/r2/thematic_lm/

Backend for Stages 2–4: DeepSeek-V4-Flash (same as R2 annotation backbone).

Usage:
  uv run python scripts/analyse/topic_discovery/thematic_lm/run_r2.py
  uv run python scripts/analyse/topic_discovery/thematic_lm/run_r2.py --backend kimi
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from scripts.analyse.topic_discovery.thematic_lm.pipeline import (
    run_pipeline, _save
)
from scripts.analyse.topic_discovery.thematic_lm.agents import (
    run_aggregator, run_reviewer, run_theme_coder_batch,
)

THEMATIC_DIR = ROOT / "data" / "annotated" / "r2" / "thematic"
OUT_DIR = ROOT / "output" / "topic_discovery" / "r2" / "thematic_lm"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONSENSUS_DIR = ROOT / "data" / "annotated" / "r2" / "consensus"

BACKENDS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-plus",
        "api_key_env": "GLM_API_KEY",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-auto",
        "api_key_env": "KIMI_API_KEY",
    },
}

BOT_AUTHORS = {"github-actions[bot]", "eip-review-bot", "dependabot[bot]"}

THEMATIC_MODELS = ["deepseek", "glm", "kimi"]


def _record_id_erc(r: dict) -> str:
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("issue_number") or r.get("pr_number"))
    return f"{r.get('_case')}_{r.get('source')}_{cid}_{r.get('date')}"


def _record_id_a2a(r: dict) -> str:
    url = r.get("url", "")
    if url:
        return url  # use bare URL for A2A (matches pipeline convention)
    cid = r.get("issue_number") or r.get("pr_number") or ""
    return f"a2a__{r.get('source')}_{cid}_{r.get('date')}"


def load_stage1_from_thematic(thematic_base: Path, id_fn) -> dict[str, str]:
    """
    Convert annotate_thematic output to Stage 1 format:
      {record_id: "theme1; theme2; ..."}  (union of all models' first themes)
    """
    per_record: dict[str, list[str]] = {}

    for model in THEMATIC_MODELS:
        path = thematic_base / f"{model}_themes.json"
        if not path.exists():
            continue
        records = json.loads(path.read_text())
        for r in records:
            if (r.get("author", "") or "").endswith("[bot]"):
                continue
            rid = id_fn(r)
            themes = r.get("themes") or []
            labels = [t.get("theme", "").strip() for t in themes if t.get("theme", "").strip()]
            per_record.setdefault(rid, []).extend(labels)

    # Build stage1 codes: deduplicated theme labels per record, semicolon-joined
    stage1 = {}
    for rid, labels in per_record.items():
        seen = []
        for label in labels:
            if label not in seen:
                seen.append(label)
        if seen:
            stage1[rid] = "; ".join(seen[:5])  # cap at 5 unique labels

    return stage1


def load_all_records_for_coding() -> list[dict]:
    """
    Load all R2 records that have consensus annotations, for Stage 4 theme coding.
    Returns records with _record_id field set.
    """
    records = []
    erc_path = CONSENSUS_DIR / "erc_annotations.json"
    if erc_path.exists():
        for r in json.loads(erc_path.read_text()):
            if (r.get("author", "") or "").endswith("[bot]"):
                continue
            text = (r.get("raw_text") or "").strip()
            if len(text) < 20:
                continue
            rid = _record_id_erc(r)
            records.append({**r, "_record_id": rid})

    a2a_path = CONSENSUS_DIR / "a2a_annotations.json"
    if a2a_path.exists():
        for r in json.loads(a2a_path.read_text()):
            if (r.get("author", "") or "").endswith("[bot]"):
                continue
            text = (r.get("raw_text") or "").strip()
            if len(text) < 20:
                continue
            rid = _record_id_a2a(r)
            records.append({**r, "_record_id": rid})

    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="R2 Thematic-LM pipeline (Stages 2-4)")
    parser.add_argument("--backend", default="deepseek", choices=list(BACKENDS))
    parser.add_argument("--batch-size", type=int, default=15)
    args = parser.parse_args()

    cfg = BACKENDS[args.backend]
    api_key = os.environ.get(cfg["api_key_env"], "")
    if not api_key:
        sys.exit(f"Error: {cfg['api_key_env']} not set in .env")

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    model = cfg["model"]

    stage1_path = OUT_DIR / "stage1_codes.json"
    stage2_path = OUT_DIR / "stage2_clusters.json"
    stage3_path = OUT_DIR / "stage3_codebook.json"
    final_coded = OUT_DIR / "coded_records.json"
    final_themes = OUT_DIR / "themes.json"

    print(f"=== R2 Thematic-LM (Stages 2–4) ===")
    print(f"Backend: {args.backend} / {model}")
    print(f"Output:  {OUT_DIR}\n")

    # ── Stage 1: Load from pre-computed thematic annotations ────────────────
    print("[Stage 1] Loading from pre-computed thematic annotations…")
    erc_codes = load_stage1_from_thematic(THEMATIC_DIR, _record_id_erc)
    a2a_codes = load_stage1_from_thematic(THEMATIC_DIR / "a2a", _record_id_a2a)
    all_codes = {**erc_codes, **a2a_codes}
    print(f"  ERC open codes: {len(erc_codes)}")
    print(f"  A2A open codes: {len(a2a_codes)}")
    print(f"  Total: {len(all_codes)}")
    _save(stage1_path, all_codes)
    print(f"  Saved stage1_codes.json")

    # ── Stage 2: Aggregator ──────────────────────────────────────────────────
    if stage2_path.exists():
        clusters = json.loads(stage2_path.read_text())
        print(f"\n[Stage 2] Loaded cached clusters ({len(clusters)} themes)")
    else:
        import random
        unique_codes = list(set(all_codes.values()))
        if len(unique_codes) > 300:
            random.seed(42)
            sampled = random.sample(unique_codes, 300)
            print(f"\n[Stage 2] Aggregating sample of 300 / {len(unique_codes)} unique codes…")
        else:
            sampled = unique_codes
            print(f"\n[Stage 2] Aggregating {len(sampled)} unique codes…")
        clusters = run_aggregator(client, model, sampled)
        _save(stage2_path, clusters)
        print(f"  Done — {len(clusters)} raw theme clusters")

    # ── Stage 3: Reviewer ────────────────────────────────────────────────────
    if stage3_path.exists():
        codebook = json.loads(stage3_path.read_text())
        print(f"\n[Stage 3] Loaded cached codebook ({len(codebook)} themes)")
    else:
        print("\n[Stage 3] Reviewing and refining codebook…")
        codebook = run_reviewer(client, model, clusters)
        _save(stage3_path, codebook)
        print(f"  Done — {len(codebook)} themes")
        for entry in codebook:
            print(f"  {entry['theme_id']}: {entry['label']}")

    # ── Stage 4: Theme coder ─────────────────────────────────────────────────
    if final_coded.exists():
        coded_existing: dict = {
            c["record_id"]: c for c in json.loads(final_coded.read_text())
        }
        print(f"\n[Stage 4] Resuming — {len(coded_existing)} already coded")
    else:
        coded_existing = {}

    print("\n[Stage 4] Loading all R2 records for coding…")
    all_records = load_all_records_for_coding()
    print(f"  Total records to code: {len(all_records)}")

    todo = [r for r in all_records if r["_record_id"] not in coded_existing]
    batches = [todo[i:i + args.batch_size] for i in range(0, len(todo), args.batch_size)]
    print(f"  Coding {len(todo)} records in {len(batches)} batches…")

    for batch_idx, batch in enumerate(batches):
        results = run_theme_coder_batch(client, model, batch, codebook)
        for item in results:
            coded_existing[item["record_id"]] = {
                "record_id": item["record_id"],
                "theme_id": item["theme_id"],
                "confidence": item.get("confidence", 1.0),
            }
        if (batch_idx + 1) % 10 == 0 or batch_idx == len(batches) - 1:
            _save(final_coded, list(coded_existing.values()))
            print(f"  … batch {batch_idx+1}/{len(batches)} saved "
                  f"({len(coded_existing)} total)", flush=True)
        time.sleep(0.3)

    _save(final_coded, list(coded_existing.values()))
    _save(final_themes, codebook)

    # Summary
    total = len(coded_existing)
    classified = sum(1 for v in coded_existing.values() if v["theme_id"] != "Unclassified")
    print(f"\n[Stage 4] Done — {classified}/{total} records classified "
          f"({classified/total*100:.1f}% coverage)")

    print(f"\nR2 Thematic-LM complete. Outputs: {OUT_DIR}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    main()
