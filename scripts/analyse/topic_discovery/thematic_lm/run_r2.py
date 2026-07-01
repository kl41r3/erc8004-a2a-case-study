"""
Thematic-LM R2 — fixed pipeline for paper-acm.

Re-runs Stages 2–4 using pre-computed Stage 1 open codes from:
  data/annotated/r2/cross-model/thematic/{deepseek,glm,kimi}_themes.json   (ERC)
  data/annotated/r2/cross-model/thematic/a2a/{glm,kimi}_themes.json  (A2A)

CRITICAL FIX: Stage 1 now extracts INDIVIDUAL theme labels (normalized case),
not semicolon-joined compound strings. Stage 2 uses frequency-based top-200
sampling instead of random sampling of long compound strings.

Run once per backend model; all 3 produce independent codebooks that are
then merged via merge_codebooks.py.

Usage:
  uv run python scripts/analyse/topic_discovery/thematic_lm/run_r2.py --backend deepseek
  uv run python scripts/analyse/topic_discovery/thematic_lm/run_r2.py --backend glm
  uv run python scripts/analyse/topic_discovery/thematic_lm/run_r2.py --backend kimi
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

from lib.paths import DATA_ANNOTATED_R2_THEMATIC, DATA_ANNOTATED_R2_CONSENSUS, ANALYSIS_TD_R2_CROSS_MODEL_THEMATIC
from lib.models import BACKENDS_THEMATIC, CANONICAL_MODELS, LEGACY_KEYS, is_bot

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from scripts.analyse.topic_discovery.thematic_lm.agents import (
    run_aggregator, run_reviewer, run_theme_coder_batch,
)

THEMATIC_DIR = DATA_ANNOTATED_R2_THEMATIC
OUT_DIR = ANALYSIS_TD_R2_CROSS_MODEL_THEMATIC
CONSENSUS_DIR = DATA_ANNOTATED_R2_CONSENSUS

BACKENDS = BACKENDS_THEMATIC

THEMATIC_MODELS = CANONICAL_MODELS


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _record_id_erc(r: dict) -> str:
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("issue_number") or r.get("pr_number"))
    return f"{r.get('_case')}_{r.get('source')}_{cid}_{r.get('date')}"


def _record_id_a2a(r: dict) -> str:
    url = r.get("url", "")
    if url:
        return url
    cid = r.get("issue_number") or r.get("pr_number") or ""
    return f"a2a__{r.get('source')}_{cid}_{r.get('date')}"


def load_stage1_individual(thematic_base: Path, id_fn) -> dict[str, set[str]]:
    """
    Extract INDIVIDUAL theme labels from all models' thematic outputs.
    Returns {record_id: set of lowercased individual labels}.

    CRITICAL FIX: Previously joined labels with "; " creating compound strings
    that the aggregator couldn't process. Now we keep individual labels and
    normalize case for dedup.
    """
    per_record: dict[str, set[str]] = {}

    for model in THEMATIC_MODELS:
        path = thematic_base / f"{model}_themes.json"
        if not path.exists():
            print(f"  ⚠ {path.name} NOT FOUND — skipping")
            continue
        records = json.loads(path.read_text())
        n_added = 0
        for r in records:
            if is_bot(r.get("author", "")):
                continue
            rid = id_fn(r)
            themes = r.get("themes") or []
            labels = []
            for t in themes:
                label = t.get("theme", "").strip()
                if label:
                    labels.append(label.lower())  # normalize case
            if labels:
                per_record.setdefault(rid, set()).update(labels)
                n_added += 1
        print(f"  {path.name}: {n_added} labeled records → {len(per_record)} cumulative")

    return per_record


def load_all_records_for_coding() -> list[dict]:
    """Load all R2 consensus records for Stage 4 theme coding."""
    records = []
    erc_path = CONSENSUS_DIR / "erc_annotations.json"
    if erc_path.exists():
        for r in json.loads(erc_path.read_text()):
            if is_bot(r.get("author", "")):
                continue
            text = (r.get("raw_text") or "").strip()
            if len(text) < 20:
                continue
            records.append({**r, "_record_id": _record_id_erc(r)})

    a2a_path = CONSENSUS_DIR / "a2a_annotations.json"
    if a2a_path.exists():
        for r in json.loads(a2a_path.read_text()):
            if is_bot(r.get("author", "")):
                continue
            text = (r.get("raw_text") or "").strip()
            if len(text) < 20:
                continue
            records.append({**r, "_record_id": _record_id_a2a(r)})

    return records


def aggregate_in_batches(client, model: str, labels: list[str],
                          batch_size: int = 100) -> dict[str, list[str]]:
    """
    Aggregate labels into themes, potentially in multiple batches + merge round.
    If single call returns empty, try batch-wise + merge.
    """
    # First try: all at once
    raw = run_aggregator(client, model, labels)
    if raw and len(raw) >= 3:
        print(f"    aggregated {len(labels)} labels → {len(raw)} themes (single pass)")
        return raw

    # Fallback: split into batches of batch_size
    print(f"    single pass returned {len(raw)} themes — trying batched ({batch_size}/batch)…")
    batches = [labels[i:i + batch_size] for i in range(0, len(labels), batch_size)]
    all_clusters: dict[str, list[str]] = {}
    for bi, batch in enumerate(batches):
        result = run_aggregator(client, model, batch)
        if result:
            all_clusters.update(result)
        print(f"    batch {bi+1}/{len(batches)}: {len(batch)} labels → {len(result)} themes")
        time.sleep(0.5)

    if len(all_clusters) >= 3:
        return all_clusters

    # Last resort: merge the batched results via another LLM call
    print(f"    batched returned {len(all_clusters)} themes — merging…")
    merge_labels = list(all_clusters.keys())
    merged = run_aggregator(client, model, merge_labels)
    if merged and len(merged) >= 3:
        return merged

    # Absolute fallback: return whatever we have
    return all_clusters if all_clusters else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="R2 Thematic-LM pipeline (Stages 2-4, fixed)")
    parser.add_argument("--backend", required=True,
                        choices=sorted(set(list(LEGACY_KEYS.keys()) + list(BACKENDS_THEMATIC.keys()))))
    parser.add_argument("--batch-size", type=int, default=15)
    parser.add_argument("--aggregation-labels", type=int, default=200,
                        help="Number of top-frequency labels to send to aggregator")
    parser.add_argument("--force", action="store_true",
                        help="Ignore cached stages and re-run everything")
    args = parser.parse_args()

    backend = LEGACY_KEYS.get(args.backend, args.backend)
    cfg = BACKENDS_THEMATIC[backend]
    api_key = os.environ.get(cfg["api_key_env"], "")
    if not api_key:
        sys.exit(f"Error: {cfg['api_key_env']} not set in .env")

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])
    model = cfg["model"]

    # Per-model output
    model_out = OUT_DIR / backend
    model_out.mkdir(parents=True, exist_ok=True)

    stage1_path = model_out / "stage1_codes.json"
    stage2_path = model_out / "stage2_clusters.json"
    stage3_path = model_out / "stage3_codebook.json"
    final_coded = model_out / "coded_records.json"
    final_themes = model_out / "themes.json"

    print(f"=== R2 Thematic-LM (Stages 2–4, FIXED) ===")
    print(f"Backend: {args.backend} / {model}")
    print(f"Output:  {model_out}\n")

    # ── Stage 1: Extract INDIVIDUAL labels from thematic annotations ──────
    if stage1_path.exists() and not args.force:
        per_record = {k: set(v) for k, v in json.loads(stage1_path.read_text()).items()}
        print(f"[Stage 1] Loaded cached: {len(per_record)} records with individual labels")
    else:
        print("[Stage 1] Extracting individual theme labels from all models…")
        erc_labels_sets = load_stage1_individual(THEMATIC_DIR, _record_id_erc)
        a2a_labels_sets = load_stage1_individual(THEMATIC_DIR / "a2a", _record_id_a2a)
        per_record = {**erc_labels_sets, **a2a_labels_sets}
        # Save as JSON-serializable {rid: list of labels}
        serializable = {rid: sorted(list(labels)) for rid, labels in per_record.items()}
        _save(stage1_path, serializable)
        print(f"  ERC records: {len(erc_labels_sets)}")
        print(f"  A2A records: {len(a2a_labels_sets)}")
        print(f"  Total: {len(per_record)} records with individual labels")

    # ── Stage 2: Aggregator (frequency-sorted, not random) ────────────────
    if stage2_path.exists() and not args.force:
        clusters = json.loads(stage2_path.read_text())
        print(f"\n[Stage 2] Loaded cached clusters ({len(clusters)} themes)")
    else:
        # Collect ALL individual labels with frequency
        label_freq: Counter = Counter()
        for labels in per_record.values():
            label_freq.update(labels)

        # Use top-K by frequency instead of random sample
        top_labels = [lbl for lbl, _ in label_freq.most_common(args.aggregation_labels)]
        print(f"\n[Stage 2] Aggregating top {len(top_labels)} labels "
              f"(from {len(label_freq)} unique) by frequency…")
        print(f"  Top-5: {top_labels[:5]} (freq: {[label_freq[l] for l in top_labels[:5]]})")

        clusters = aggregate_in_batches(client, model, top_labels, batch_size=100)
        _save(stage2_path, clusters)
        print(f"  Done — {len(clusters)} raw theme clusters")
        if len(clusters) < 3:
            print(f"  ⚠ WARNING: Only {len(clusters)} clusters — may need manual fix")
            for k, v in list(clusters.items())[:5]:
                print(f"    {k}: {v[:3]}...")

    # ── Stage 3: Reviewer ─────────────────────────────────────────────────
    if stage3_path.exists() and not args.force:
        codebook = json.loads(stage3_path.read_text())
        print(f"\n[Stage 3] Loaded cached codebook ({len(codebook)} themes)")
    else:
        if not clusters or len(clusters) < 2:
            print(f"\n[Stage 3] ⚠ Insufficient clusters ({len(clusters)}) — "
                  f"building fallback codebook from top labels")
            # Fallback: use top-15 labels as themes
            label_freq = Counter()
            for labels in per_record.values():
                label_freq.update(labels)
            top = label_freq.most_common(15)
            codebook = []
            for i, (label, cnt) in enumerate(top):
                codebook.append({
                    "theme_id": f"T{i+1:02d}",
                    "label": label.title(),
                    "description": f"Theme covering {label} and related concepts ({cnt} occurrences).",
                    "codes": [label],
                })
            _save(stage3_path, codebook)
            print(f"  Fallback codebook: {len(codebook)} themes from top labels")
        else:
            print("\n[Stage 3] Reviewing and refining codebook…")
            codebook = run_reviewer(client, model, clusters)
            _save(stage3_path, codebook)
            print(f"  Done — {len(codebook)} themes in final codebook")
        for entry in codebook:
            print(f"  {entry.get('theme_id','?')}: {entry.get('label','?')}")

    # ── Stage 4: Theme coder ──────────────────────────────────────────────
    if final_coded.exists() and not args.force:
        coded_existing: dict = {
            c["record_id"]: c for c in json.loads(final_coded.read_text())
        }
        # Remove records where theme_id is "Unclassified" and confidence is "low"
        pending = {rid: c for rid, c in coded_existing.items()
                   if c["theme_id"] == "Unclassified" and c.get("confidence") == "low"}
        if pending:
            print(f"\n[Stage 4] Resuming — {len(coded_existing)} coded "
                  f"({len(pending)} low-confidence pending retry)")
            for rid in pending:
                del coded_existing[rid]
        else:
            print(f"\n[Stage 4] Resuming — {len(coded_existing)} already coded")
    else:
        coded_existing = {}

    print("\n[Stage 4] Loading all R2 records for coding…")
    all_records = load_all_records_for_coding()
    print(f"  Total records to code: {len(all_records)}")

    todo = [r for r in all_records if r["_record_id"] not in coded_existing]
    batches = [todo[i:i + args.batch_size] for i in range(0, len(todo), args.batch_size)]
    print(f"  Coding {len(todo)} records in {len(batches)} batches…")

    errs = 0
    for batch_idx, batch in enumerate(batches):
        results = run_theme_coder_batch(client, model, codebook, batch)
        n_classified = 0
        for item in results:
            if item["theme_id"] == "Unclassified":
                errs += 1
            else:
                n_classified += 1
            coded_existing[item["record_id"]] = {
                "record_id": item["record_id"],
                "theme_id": item["theme_id"],
                "confidence": item.get("confidence", 1.0),
            }
        if (batch_idx + 1) % 10 == 0 or batch_idx == len(batches) - 1:
            _save(final_coded, list(coded_existing.values()))
            elapsed = batch_idx + 1
            print(f"  … batch {elapsed}/{len(batches)} saved "
                  f"({len(coded_existing)} total, {errs} unclassified)", flush=True)
        time.sleep(0.3)

    _save(final_coded, list(coded_existing.values()))
    _save(final_themes, codebook)

    total = len(coded_existing)
    classified = sum(1 for v in coded_existing.values() if v["theme_id"] != "Unclassified")
    print(f"\n[Stage 4] Done — {classified}/{total} records classified "
          f"({classified/total*100:.1f}% coverage)")

    print(f"\nR2 Thematic-LM ({args.backend}) complete. Outputs: {model_out}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    main()
