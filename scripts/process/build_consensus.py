"""
build_consensus.py — Majority-vote consensus across 3 annotation models.

Merges deepseek / glm / kimi annotations for both ERC and A2A datasets
using majority vote (2-of-3) per field. Ties are broken by the model
with the highest field-level Fleiss κ:
  argument_type  → kimi    (κ=0.730)
  stance         → kimi    (κ=0.460)
  consensus_signal → deepseek (κ=0.329)
  stakeholder_institution → glm (κ=0.187)

Output:
  data/annotated/r2/cross-model/consensus/erc_annotations.json
  data/annotated/r2/cross-model/consensus/a2a_annotations.json
  data/annotated/r2/cross-model/consensus/consensus_stats.json

Usage:
  uv run python scripts/process/build_consensus.py
  uv run python scripts/process/build_consensus.py --dataset erc
  uv run python scripts/process/build_consensus.py --dataset a2a
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, DATA_ANNOTATED_R2_CROSS_MODEL, DATA_ANNOTATED_R2_CONSENSUS, DATA_ANNOTATED_R2_A2A, CONSENSUS_ERC, CONSENSUS_A2A, CONSENSUS_STATS
from lib.models import CANONICAL_MODELS, LEGACY_KEYS

OUT_DIR = DATA_ANNOTATED_R2_CONSENSUS
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = CANONICAL_MODELS
FIELDS = ["stakeholder_institution", "argument_type", "stance", "consensus_signal"]

# Tiebreaker model per field (highest Fleiss κ in ERC validation run)
TIEBREAKER = {
    "argument_type": "moonshot-v1-auto",
    "stance": "moonshot-v1-auto",
    "consensus_signal": "deepseek-v4-flash",
    "stakeholder_institution": "glm-4-plus",
}


def _record_id_erc(r: dict) -> str:
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("issue_number") or r.get("pr_number"))
    return f"{r.get('_case')}_{r.get('source')}_{cid}_{r.get('date')}"


def _record_id_a2a(r: dict) -> str:
    url = r.get("url", "")
    if url:
        return f"a2a__{url}"
    cid = r.get("issue_number") or r.get("pr_number") or ""
    return f"a2a__{r.get('source')}_{cid}_{r.get('date')}"


def load_model_set(base_dir: Path, id_fn) -> dict[str, dict[str, dict]]:
    """Returns {model: {record_id: record}} for all available models."""
    model_data = {}
    for model in MODELS:
        path = base_dir / model / "annotations.json"
        if not path.exists():
            print(f"  WARNING: {model} not found at {path}")
            continue
        recs = json.loads(path.read_text())
        valid = {id_fn(r): r for r in recs if r.get("annotation") is not None}
        model_data[model] = valid
        print(f"  {model}: {len(valid)} valid records")
    return model_data


def majority_vote(model_data: dict[str, dict], record_ids: list[str], id_fn) -> list[dict]:
    """Apply majority vote for each record × field."""
    results = []
    models_loaded = list(model_data.keys())
    if not models_loaded:
        return results

    consensus_counts = {f: {"unanimous": 0, "majority": 0, "tie": 0} for f in FIELDS}

    for rid in record_ids:
        # Use first available model's record as base (for metadata)
        base = None
        for m in models_loaded:
            if rid in model_data[m]:
                base = dict(model_data[m][rid])
                break
        if base is None:
            continue

        consensus_annotation = {}
        consensus_confidence = {}

        for field in FIELDS:
            votes = []
            for m in models_loaded:
                if rid in model_data[m]:
                    val = model_data[m][rid]["annotation"].get(field, "")
                    votes.append((m, val))

            if not votes:
                consensus_annotation[field] = ""
                consensus_confidence[field] = 0.0
                continue

            vote_values = [v for _, v in votes]
            counts = Counter(vote_values)
            top_val, top_count = counts.most_common(1)[0]
            n_votes = len(votes)

            if top_count > n_votes / 2:
                # Clear majority (or unanimous)
                consensus_annotation[field] = top_val
                consensus_confidence[field] = round(top_count / n_votes, 2)
                if top_count == n_votes:
                    consensus_counts[field]["unanimous"] += 1
                else:
                    consensus_counts[field]["majority"] += 1
            else:
                # 3-way tie: use tiebreaker model
                tb_model = TIEBREAKER.get(field, models_loaded[0])
                tb_val = model_data.get(tb_model, {}).get(rid, {}).get("annotation", {}).get(field, top_val)
                consensus_annotation[field] = tb_val
                consensus_confidence[field] = round(1.0 / n_votes, 2)
                consensus_counts[field]["tie"] += 1

        base["annotation"] = consensus_annotation
        base["consensus_confidence"] = consensus_confidence
        base["consensus_votes"] = {
            field: {m: model_data[m][rid]["annotation"].get(field, "")
                    for m in models_loaded if rid in model_data[m]}
            for field in FIELDS
        }
        base["annotation_error"] = None
        results.append(base)

    return results, consensus_counts


def run(dataset: str):
    if dataset == "erc":
        base_dir = DATA_ANNOTATED_R2_CROSS_MODEL
        id_fn = _record_id_erc
        out_file = CONSENSUS_ERC
    else:
        base_dir = DATA_ANNOTATED_R2_A2A
        id_fn = _record_id_a2a
        out_file = CONSENSUS_A2A

    print(f"\n=== Building consensus: {dataset.upper()} ===")
    print(f"Input: {base_dir}")

    model_data = load_model_set(base_dir, id_fn)
    if len(model_data) < 2:
        print(f"ERROR: need ≥2 models, got {len(model_data)}")
        return None

    # Intersection of record IDs across all loaded models
    all_sets = [set(d.keys()) for d in model_data.values()]
    common_ids = sorted(all_sets[0].intersection(*all_sets[1:]))
    print(f"\n  Records in ALL {len(model_data)} models: {len(common_ids)}")

    records, consensus_counts = majority_vote(model_data, common_ids, id_fn)
    out_file.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"  Wrote {len(records)} consensus records → {out_file}")

    # Per-field stats
    print("\n  Consensus breakdown per field:")
    n = len(records)
    for field in FIELDS:
        c = consensus_counts[field]
        print(f"    {field:<30} unanimous={c['unanimous']} "
              f"({c['unanimous']/n*100:.1f}%)  majority={c['majority']} "
              f"({c['majority']/n*100:.1f}%)  tie={c['tie']} ({c['tie']/n*100:.1f}%)")

    return {
        "dataset": dataset,
        "n_records": len(records),
        "models_used": list(model_data.keys()),
        "consensus_counts": consensus_counts,
        "output": str(out_file),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["erc", "a2a", "both"], default="both")
    args = parser.parse_args()

    datasets = ["erc", "a2a"] if args.dataset == "both" else [args.dataset]
    stats = {}
    for ds in datasets:
        result = run(ds)
        if result:
            stats[ds] = result

    stats_path = CONSENSUS_STATS
    stats["generated_at"] = datetime.now(timezone.utc).isoformat()
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"\n  Stats → {stats_path}")


if __name__ == "__main__":
    main()
