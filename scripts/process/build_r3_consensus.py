"""
build_r3_consensus.py — Build per-model consensus (3-round majority vote) and
cross-model consensus (3-model majority vote) for R3 annotations.

Usage:
  uv run python scripts/process/build_r3_consensus.py --case erc
  uv run python scripts/process/build_r3_consensus.py --case a2a
  uv run python scripts/process/build_r3_consensus.py --case both
"""
import argparse, json
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent.parent
R3_DIR = ROOT / "data" / "annotated" / "r3"
FIELDS = ["argument_type", "stance", "consensus_signal"]
MODELS = ["deepseek-v4-flash", "glm-4-plus", "moonshot-v1-auto"]
ROUNDS = [1, 2, 3]


def _rid_erc(r: dict) -> str:
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("issue_number") or r.get("pr_number"))
    return f"{r.get('_case','')}_{r.get('source','')}_{cid}_{r.get('date','')}"


def _rid_a2a(r: dict) -> str:
    url = r.get("url", "")
    return url if url else f"a2a_{r.get('source','')}_{r.get('issue_number','')}_{r.get('date','')}"


# ── Per-model consensus (within-model, across rounds) ────────────────────────

def build_model_consensus(case: str, model: str, id_fn) -> dict | None:
    """Majority vote across 3 rounds for a single model. Returns consensus list."""
    model_dir = R3_DIR / case / model
    round_recs = {}
    for rnd in ROUNDS:
        path = model_dir / f"round_{rnd}" / "annotations.json"
        if not path.exists():
            print(f"  WARNING: {model} round_{rnd} not found at {path}")
            return None
        recs = json.loads(path.read_text())
        valid = {id_fn(r): r for r in recs if r.get("annotation") is not None}
        round_recs[rnd] = valid
        print(f"  {model} round_{rnd}: {len(valid)} valid records")

    # Intersection across all 3 rounds
    ids_sets = [set(round_recs[r].keys()) for r in ROUNDS]
    common_ids = ids_sets[0].intersection(*ids_sets[1:])
    print(f"  → Intersection (all 3 rounds): {len(common_ids)} records")

    if not common_ids:
        return None

    results = []
    for rid in sorted(common_ids):
        base = dict(round_recs[1][rid])  # Use round_1 as base
        votes_per_field = {f: {} for f in FIELDS}
        for rnd in ROUNDS:
            ann = round_recs[rnd][rid].get("annotation", {})
            for f in FIELDS:
                votes_per_field[f][f"R{rnd}"] = ann.get(f, "")

        # Majority vote per field (2-of-3)
        consensus = {}
        confidence = {}
        for f in FIELDS:
            values = [votes_per_field[f][f"R{r}"] for r in ROUNDS]
            counts = Counter(values)
            top_val, top_count = counts.most_common(1)[0]
            consensus[f] = top_val
            confidence[f] = round(top_count / 3, 4)

        base["annotation"] = consensus
        base["annotation_error"] = None
        base["consensus_confidence"] = confidence
        base["consensus_votes"] = votes_per_field
        results.append(base)

    # Save
    out_path = model_dir / "consensus.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"  → Wrote {len(results)} consensus records to {out_path}")
    return results


# ── Cross-model consensus (across models, using each model's consensus) ──────

def build_cross_consensus(case: str, id_fn) -> list[dict] | None:
    """Majority vote across models, using each model's per-model consensus."""
    model_recs = {}
    for model in MODELS:
        path = R3_DIR / case / model / "consensus.json"
        if not path.exists():
            print(f"  WARNING: {model} consensus not found, skipping")
            continue
        recs = json.loads(path.read_text())
        valid = {id_fn(r): r for r in recs if r.get("annotation") is not None}
        model_recs[model] = valid
        print(f"  {model}: {len(valid)} consensus records")

    if len(model_recs) < 2:
        print("  ERROR: need ≥2 models")
        return None

    # Intersection across all models
    ids_sets = [set(model_recs[m].keys()) for m in model_recs]
    common_ids = ids_sets[0].intersection(*ids_sets[1:])
    print(f"  → Intersection (all {len(model_recs)} models): {len(common_ids)} records")

    if not common_ids:
        return None

    models_loaded = list(model_recs.keys())
    results = []
    for rid in sorted(common_ids):
        base = dict(model_recs[models_loaded[0]][rid])
        votes_per_field = {f: {} for f in FIELDS}
        for m in models_loaded:
            ann = model_recs[m][rid].get("annotation", {})
            for f in FIELDS:
                votes_per_field[f][m] = ann.get(f, "")

        # Majority vote per field
        consensus = {}
        confidences = []
        for f in FIELDS:
            values = [votes_per_field[f][m] for m in models_loaded]
            counts = Counter(values)
            top_val, top_count = counts.most_common(1)[0]
            consensus[f] = top_val
            confidences.append(top_count / len(models_loaded))

        overall_confidence = round(sum(confidences) / len(confidences), 4)
        base["annotation"] = consensus
        base["annotation_error"] = None
        base["consensus_confidence"] = overall_confidence
        base["consensus_votes"] = votes_per_field
        results.append(base)

    # Save
    out_path = R3_DIR / f"{case}_cross_consensus.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"  → Wrote {len(results)} cross-consensus records to {out_path}")

    # Summary
    full_agree = sum(1 for r in results if r["consensus_confidence"] >= 1.0)
    partial = sum(1 for r in results if 0.5 <= r["consensus_confidence"] < 1.0)
    print(f"  Full agree: {full_agree} ({full_agree/len(results)*100:.1f}%)")
    print(f"  Partial (2-of-3): {partial} ({partial/len(results)*100:.1f}%)")

    return results


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=["erc", "a2a", "both"], default="both")
    ap.add_argument("--model", choices=MODELS + ["all"], default="all",
                    help="Build per-model consensus for specific model")
    ap.add_argument("--cross-only", action="store_true",
                    help="Only rebuild cross-model consensus (skip per-model)")
    args = ap.parse_args()

    cases = ["erc", "a2a"] if args.case == "both" else [args.case]
    models_to_build = MODELS if args.model == "all" else [args.model]

    for case in cases:
        id_fn = _rid_erc if case == "erc" else _rid_a2a
        print(f"\n{'='*60}")
        print(f"Building consensus: {case.upper()}")
        print(f"{'='*60}")

        # Step 1: Per-model consensus
        if not args.cross_only:
            print(f"\n--- Per-model consensus ---")
            for model in models_to_build:
                print(f"\n[{model}]")
                build_model_consensus(case, model, id_fn)

        # Step 2: Cross-model consensus
        print(f"\n--- Cross-model consensus ---")
        build_cross_consensus(case, id_fn)


if __name__ == "__main__":
    main()
