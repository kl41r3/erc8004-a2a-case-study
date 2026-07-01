"""
validate_multimodel.py — Multi-model inter-coder reliability + triangulation.

Input:   data/annotated/r2/cross-model/erc/{model}/annotations.json       (--dataset erc)
         data/annotated/r2/cross-model/a2a/{model}/annotations.json   (--dataset a2a)
Output:  data/annotated/r2/cross-model/validation/   or   data/annotated/r2/cross-model/a2a/validation/

Computes:
  1. Pairwise Cohen's κ per field (3 models → 3 pairs)
  2. Fleiss' κ per field (all 3 models jointly)
  3. Confusion matrices per pair
  4. Agreement tiers: % records where 3/3, 2/3, 1/3 models agree
  5. Stratified verification sample (N=50) for human coding
  6. Model-specific bias analysis (institution/stance distributions)

Methodology follows standard multi-coder qualitative validation:
  - Landis & Koch (1977) κ interpretation
  - Investigator triangulation (Denzin 1978)
  - Convergent validity across independent LLM coders

Usage:
  uv run python scripts/analyse/validate_multimodel.py                 # ERC (default)
  uv run python scripts/analyse/validate_multimodel.py --dataset a2a   # A2A
  uv run python scripts/analyse/validate_multimodel.py --sample-size 50
"""

import csv
import json
import random
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, DATA_ANNOTATED_R2_ERC, DATA_ANNOTATED_R2_A2A, DATA_ANNOTATED_R2_CROSS_MODEL, DATA_ANNOTATED_R2_VALIDATION
from lib.models import CANONICAL_MODELS

ANNOTATED_R2 = DATA_ANNOTATED_R2_CROSS_MODEL
MODELS = CANONICAL_MODELS  # canonical model IDs
FIELDS = ["stakeholder_institution", "argument_type", "stance", "consensus_signal"]
SEED = 42

# ── κ implementations (no external deps) ───────────────────────────────────────

def cohen_kappa(a: list, b: list) -> float:
    """Cohen's κ between two raters."""
    assert len(a) == len(b)
    n = len(a)
    labels = sorted(set(a) | set(b))
    p_o = sum(x == y for x, y in zip(a, b)) / n
    a_counts = Counter(a)
    b_counts = Counter(b)
    p_e = sum((a_counts[l] / n) * (b_counts[l] / n) for l in labels)
    return 1.0 if p_e == 1.0 else (p_o - p_e) / (1.0 - p_e)


def fleiss_kappa(ratings: list[list]) -> float:
    """Fleiss' κ for ≥2 raters. ratings[i][j] = category index for rater i on item j."""
    n_raters = len(ratings)
    n_items = len(ratings[0]) if ratings else 0
    if n_items == 0:
        return float("nan")
    # Collect all categories
    cats = sorted(set(r for row in ratings for r in row))
    cat_idx = {c: i for i, c in enumerate(cats)}
    n_cats = len(cats)
    # Per-item: proportion of rater-pairs agreeing
    P_i = []
    for j in range(n_items):
        counts = Counter(ratings[i][j] for i in range(n_raters))
        P_i.append((sum(v * (v - 1) for v in counts.values())) / (n_raters * (n_raters - 1)))
    P_bar = sum(P_i) / n_items
    # Per-category proportion
    p_j = []
    for cat in cats:
        total = sum(1 for i in range(n_raters) for j in range(n_items) if ratings[i][j] == cat)
        p_j.append(total / (n_raters * n_items))
    P_e_bar = sum(p ** 2 for p in p_j)
    return 1.0 if P_e_bar == 1.0 else (P_bar - P_e_bar) / (1.0 - P_e_bar)


def kappa_label(k: float) -> str:
    if k < 0.20: return "Poor"
    if k < 0.40: return "Fair"
    if k < 0.60: return "Moderate"
    if k < 0.80: return "Substantial"
    return "Almost Perfect"


# ── Loading ────────────────────────────────────────────────────────────────────

def load_annotations(annot_dir: Path) -> dict[str, list[dict]]:
    """Load per-model annotations from annot_dir/{model}/annotations.json."""
    model_data = {}
    for model in MODELS:
        path = annot_dir / model / "annotations.json"
        if not path.exists():
            print(f"  WARNING: {model} annotations not found at {path}")
            continue
        all_recs = json.loads(path.read_text())
        # filter to successful annotations only
        valid = {_record_id(r): r for r in all_recs if r.get("annotation") is not None}
        model_data[model] = valid
        print(f"  {model}: {len(valid)} valid annotations")
    return model_data


def _record_id(r: dict) -> str:
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("issue_number") or r.get("pr_number"))
    return f"{r.get('_case')}_{r.get('source')}_{cid}_{r.get('date')}"


def align(model_data: dict[str, dict]) -> tuple[dict[str, list[dict]], set[str]]:
    """Find intersection of record IDs across all loaded models."""
    all_ids = [set(d.keys()) for d in model_data.values()]
    common = all_ids[0].intersection(*all_ids[1:]) if all_ids else set()
    print(f"\n  Intersection (records in ALL models): {len(common)}")
    aligned = {m: [model_data[m][rid] for rid in sorted(common)] for m in model_data}
    return aligned, common


# ── Analysis ───────────────────────────────────────────────────────────────────

def pairwise_kappa(aligned: dict[str, list[dict]]) -> dict:
    """Compute Cohen's κ for every model pair × field."""
    results = {}
    models = list(aligned.keys())
    for field in FIELDS:
        results[field] = {}
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                a = [r["annotation"].get(field, "") for r in aligned[models[i]]]
                b = [r["annotation"].get(field, "") for r in aligned[models[j]]]
                k = cohen_kappa(a, b)
                pct = sum(x == y for x, y in zip(a, b)) / len(a) * 100
                pair = f"{models[i]}↔{models[j]}"
                results[field][pair] = {"κ": round(k, 4), "%_agree": round(pct, 1)}
    return results


def fleiss_all(aligned: dict[str, list[dict]]) -> dict[str, float]:
    """Fleiss' κ for all models jointly per field."""
    results = {}
    models = list(aligned.keys())
    n = len(aligned[models[0]]) if models else 0
    if n == 0:
        return results
    for field in FIELDS:
        ratings = [[aligned[m][j]["annotation"].get(field, "") for j in range(n)] for m in models]
        results[field] = round(fleiss_kappa(ratings), 4)
    return results


def agreement_tiers(aligned: dict[str, list[dict]], common_ids: set[str]) -> dict:
    """For each field, count records where 3/3, 2/3, 0/3 models agree."""
    models = list(aligned.keys())
    n = len(aligned[models[0]]) if models else 0
    results = {}
    for field in FIELDS:
        tiers = {3: 0, 2: 0, 1: 0}
        for j in range(n):
            vals = [aligned[m][j]["annotation"].get(field, "") for m in models]
            max_agree = max(Counter(vals).values())
            tiers[max_agree] += 1
        for t in [3, 2, 1]:
            tiers[t] = round(tiers[t] / n * 100, 1)
        results[field] = dict(tiers)
    return results


def model_bias_report(aligned: dict[str, list[dict]]) -> dict:
    """Distribution of labels per model per field — detects systematic bias."""
    report = {}
    for field in FIELDS:
        report[field] = {}
        for model in aligned:
            dist = Counter(r["annotation"].get(field, "") for r in aligned[model])
            total = sum(dist.values()) or 1
            report[field][model] = {k: round(v / total * 100, 1) for k, v in dist.most_common(10)}
    return report


def generate_verification_sample(aligned: dict[str, list[dict]], common_ids: set[str],
                                 n: int = 50) -> list[dict]:
    """Stratified random sample for human verification.

    Uses _record_id as a stable key (avoiding dict identity issues in lists).
    Strata: (agreement tier) — oversamples disagreement records for efficient
    reliability estimation.
    """
    models = list(aligned.keys())
    records = [aligned[models[0]][i] for i in range(len(aligned[models[0]]))]

    # Tag records with agreement profile
    for j, r in enumerate(records):
        vals = [aligned[m][j]["annotation"].get("argument_type", "") for m in models]
        r["_agree_all"] = len(set(vals)) == 1
        r["_idx"] = j  # stable index into aligned arrays

    disagree = [r for r in records if not r["_agree_all"]]
    agree_all = [r for r in records if r["_agree_all"]]

    rng = random.Random(SEED)
    sample = []

    # ~60% from disagreements, ~40% from agreements
    n_d = min(n * 3 // 5, len(disagree))
    n_a = n - n_d
    n_a = min(n_a, len(agree_all))
    n_d = n - n_a  # take whatever slack there is

    def pick(pool, k):
        return rng.sample(pool, k) if pool and k > 0 else []

    sample = pick(disagree, n_d) + pick(agree_all, n_a)
    rng.shuffle(sample)
    return sample[:n]


def write_verification_csv(sample: list[dict], aligned: dict[str, list[dict]],
                           models: list[str], validation_dir: Path | None = None):
    """Write the human-verification CSV with all model labels side by side."""
    if validation_dir is None:
        validation_dir = ANNOTATED_R2 / "validation"
    path = validation_dir / "verification_sample.csv"
    # Build lookup: record → all model annotations
    id_to_idx = {}
    for m in models:
        for j, r in enumerate(aligned[m]):
            rid = _record_id(r)
            id_to_idx.setdefault(rid, {})[m] = j

    rows = []
    for i, r in enumerate(sample, 1):
        rid = _record_id(r)
        row = {"id": i, "case": r.get("_case", ""),
               "source": r.get("source", ""), "author": r.get("author", ""),
               "date": r.get("date", ""),
               "text_preview": (r.get("raw_text") or "").replace("\n", " ")[:300]}
        for field in FIELDS:
            for m in models:
                idx = id_to_idx.get(rid, {}).get(m)
                if idx is not None:
                    row[f"{m}_{field}"] = aligned[m][idx]["annotation"].get(field, "")
            row[f"human_{field}"] = ""
            row[f"agree_all_models"] = ""
        row["notes"] = ""
        rows.append(row)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n  Verification sample: {path}  ({len(rows)} records)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--dataset", choices=["erc", "a2a"], default="erc",
                        help="Which annotation set to validate (default: erc)")
    args = parser.parse_args()

    if args.dataset == "a2a":
        annot_dir = DATA_ANNOTATED_R2_A2A
        validation_dir = annot_dir / "validation"
    else:
        annot_dir = DATA_ANNOTATED_R2_ERC
        validation_dir = DATA_ANNOTATED_R2_VALIDATION
    validation_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Multi-Model Validation [{args.dataset.upper()}] ===\n")
    print(f"Input dir: {annot_dir}")
    print("Loading annotations…")
    model_data = load_annotations(annot_dir)
    loaded = list(model_data.keys())
    if len(loaded) < 2:
        print(f"ERROR: need ≥2 models, got {len(loaded)}: {loaded}")
        return

    aligned, common_ids = align(model_data)
    models = list(aligned.keys())

    # ── 1. Pairwise κ ──────────────────────────────────────────────────────
    print("\n── 1. Pairwise Cohen's κ ──")
    pairwise = pairwise_kappa(aligned)
    pairwise_rows = []
    for field in FIELDS:
        print(f"\n  {field}:")
        for pair, vals in pairwise[field].items():
            print(f"    {pair}: κ={vals['κ']:.3f} [{kappa_label(vals['κ'])}]  "
                  f"{vals['%_agree']}% agree")
            pairwise_rows.append({"field": field, "pair": pair,
                                  "kappa": vals['κ'], "pct_agree": vals['%_agree'],
                                  "interpretation": kappa_label(vals['κ'])})

    # Save pairwise CSV
    pw_path = validation_dir / "pairwise_kappa.csv"
    with open(pw_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pairwise_rows[0].keys())
        w.writeheader()
        w.writerows(pairwise_rows)
    print(f"\n  → {pw_path}")

    # ── 2. Fleiss' κ ──────────────────────────────────────────────────────
    print("\n── 2. Fleiss' κ (all models jointly) ──")
    fleiss = fleiss_all(aligned)
    for field, k in fleiss.items():
        print(f"  {field}: κ={k:.3f} [{kappa_label(k)}]")

    # ── 3. Agreement tiers ────────────────────────────────────────────────
    print("\n── 3. Agreement tiers (% records with N models agreeing) ──")
    tiers = agreement_tiers(aligned, common_ids)
    for field, t in tiers.items():
        print(f"  {field}: 3/3={t[3]}%  2/3={t[2]}%  1/3={t[1]}%")

    # ── 4. Model bias ─────────────────────────────────────────────────────
    print("\n── 4. Model bias (label distributions) ──")
    bias = model_bias_report(aligned)
    for field in FIELDS:
        print(f"\n  {field}:")
        for model in models:
            dist = bias[field][model]
            top3 = sorted(dist.items(), key=lambda x: -x[1])[:3]
            print(f"    {model}: {', '.join(f'{k}={v}%' for k, v in top3)}")

    # ── 5. Verification sample ────────────────────────────────────────────
    print(f"\n── 5. Verification sample (n={args.sample_size}) ──")
    sample = generate_verification_sample(aligned, common_ids, args.sample_size)
    write_verification_csv(sample, aligned, models, validation_dir)

    # ── 6. Summary report ─────────────────────────────────────────────────
    print("\n── 6. Summary ──")
    n_records = len(common_ids)
    print(f"  Records: {n_records}")
    print(f"  Models:  {', '.join(models)}")
    # Mean pairwise κ per field
    print("  Mean pairwise κ:")
    for field in FIELDS:
        ks = [v['κ'] for v in pairwise[field].values()]
        mean_k = sum(ks) / len(ks) if ks else 0
        print(f"    {field:<25} κ̄={mean_k:.3f} [{kappa_label(mean_k)}]")
    # Convergent records (%)
    arg3 = tiers.get("argument_type", {}).get(3, 0)
    stance3 = tiers.get("stance", {}).get(3, 0)
    print(f"  Full convergence (3/3 agree argument_type): {arg3}%")
    print(f"  Full convergence (3/3 agree stance):        {stance3}%")

    # Write full report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_records": n_records,
        "models": models,
        "n_models_loaded": len(loaded),
        "pairwise_kappa": {f: {p: v for p, v in pairwise[f].items()} for f in FIELDS},
        "fleiss_kappa": fleiss,
        "agreement_tiers": tiers,
        "verification_sample_n": args.sample_size,
        "verification_sample_path": str(validation_dir / "verification_sample.csv"),
        "dataset": args.dataset,
    }
    report_path = validation_dir / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n  Full report → {report_path}")


if __name__ == "__main__":
    main()
