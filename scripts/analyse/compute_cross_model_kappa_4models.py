"""Compute cross-model Kappa across 4 models (MiniMax-M2.5 + 3 cross-round models).

Models:
  1. MiniMax-M2.5 (R1 baseline, from annotated_records.json)
  2. deepseek-v4-flash (cross-round, per-model consensus)
  3. glm-4-plus (cross-round, per-model consensus)
  4. moonshot-v1-auto (cross-round, per-model consensus)

Outputs:
  - Pairwise Cohen's Kappa for each field (argument_type, stance, consensus_signal)
  - Fleiss' Kappa across all 4 models for each field
  - Separate results for ERC and A2A cases
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import (
    DATA_ANNOTATED_R1_RECORDS,
    DATA_ANNOTATED_R2_CROSS_ROUND,
    METRICS_R2_KAPPA_4MODELS,
)
from lib.models import CANONICAL_MODELS

R1_PATH = DATA_ANNOTATED_R1_RECORDS
OUT_PATH = METRICS_R2_KAPPA_4MODELS

FIELDS = ["argument_type", "stance", "consensus_signal"]
MODELS = ["MiniMax-M2.5"] + CANONICAL_MODELS


def load_r1_annotations():
    """Load MiniMax-M2.5 annotations from R1 annotated_records.json."""
    with open(R1_PATH) as f:
        data = json.load(f)

    erc, a2a = {}, {}
    for r in data:
        ann = r.get("annotation")
        if not ann:
            continue
        case = r.get("_case", "")
        if case == "ERC-8004":
            erc[_erc_key(r)] = {f: ann.get(f) for f in FIELDS}
        elif case == "Google-A2A":
            url = r.get("url", "")
            if url:
                a2a[url] = {f: ann.get(f) for f in FIELDS}
    return erc, a2a


def load_cross_round_annotations(model, case):
    """Load cross-round per-model consensus annotations for a given model and case.
    Falls back to round_1/annotations.json if consensus.json not yet built."""
    cross_round_dir = DATA_ANNOTATED_R2_CROSS_ROUND / case
    # Prefer consensus file (majority vote across rounds)
    consensus_path = cross_round_dir / model / "consensus.json"
    if consensus_path.exists():
        with open(consensus_path) as f:
            data = json.load(f)
        print(f"    Using consensus.json ({len(data)} records)")
    else:
        path = cross_round_dir / model / "round_1" / "annotations.json"
        if not path.exists():
            print(f"  WARNING: {path} not found")
            return {}
        with open(path) as f:
            data = json.load(f)
        print(f"    Using round_1/annotations.json ({len(data)} records)")

    result = {}
    for r in data:
        ann = r.get("annotation")
        if not ann:
            continue
        if case == "erc":
            result[_erc_key(r)] = {f: ann.get(f) for f in FIELDS}
        else:
            url = r.get("url", "")
            if url:
                result[url] = {f: ann.get(f) for f in FIELDS}
    return result


def _erc_key(r):
    src = r.get("source", "?")
    pid = str(r.get("post_id") or r.get("comment_id") or r.get("sha") or "")
    date = (r.get("date") or "")[:10]
    return (src, pid, date)


def cohens_kappa(ann1, ann2, labels):
    """Compute Cohen's Kappa between two annotators.

    Args:
        ann1, ann2: lists of label strings (same length, aligned)
        labels: set of all possible labels

    Returns:
        kappa: float
    """
    n = len(ann1)
    if n == 0:
        return float("nan")

    # Build confusion matrix
    label_list = sorted(labels)
    idx = {lab: i for i, lab in enumerate(label_list)}
    m = len(label_list)
    mat = np.zeros((m, m))

    for a, b in zip(ann1, ann2):
        if a in idx and b in idx:
            mat[idx[a], idx[b]] += 1
        elif a in idx:
            mat[idx[a], :] += 0  # skip mismatched
        elif b in idx:
            mat[:, idx[b]] += 0

    # Use only pairs where both raters used known labels
    valid = sum(
        1 for a, b in zip(ann1, ann2) if a in idx and b in idx
    )
    if valid == 0:
        return float("nan")

    mat = np.zeros((m, m))
    for a, b in zip(ann1, ann2):
        if a in idx and b in idx:
            mat[idx[a], idx[b]] += 1

    total = mat.sum()
    po = np.trace(mat) / total  # observed agreement
    row_sums = mat.sum(axis=1)
    col_sums = mat.sum(axis=0)
    pe = (row_sums @ col_sums) / (total * total)  # expected agreement by chance

    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def fleiss_kappa(annotations, labels):
    """Compute Fleiss' Kappa for multiple raters.

    Args:
        annotations: list of lists, each inner list is one item's ratings from N raters
        labels: set of all possible labels

    Returns:
        kappa: float
    """
    label_list = sorted(labels)
    n_labels = len(label_list)
    n_items = len(annotations)
    n_raters = len(annotations[0]) if annotations else 0

    if n_items == 0 or n_raters < 2 or n_labels < 2:
        return float("nan")

    # Count matrix: items × labels
    counts = np.zeros((n_items, n_labels))
    for i, item_anns in enumerate(annotations):
        for ann in item_anns:
            if ann in labels:
                counts[i, label_list.index(ann)] += 1

    # Fleiss' Kappa formula
    # P_i = (1/(n(n-1))) * (sum_j n_ij^2 - n)  for each item
    # P_bar = mean(P_i)
    # P_e = sum_j p_j^2 where p_j = (1/(N*n)) * sum_i n_ij

    n = n_raters
    # Per-item agreement
    P_i = (np.sum(counts**2, axis=1) - n) / (n * (n - 1))
    P_bar = np.mean(P_i)

    # Expected agreement
    p_j = np.sum(counts, axis=0) / (n_items * n)
    P_e = np.sum(p_j**2)

    if P_e == 1.0:
        return 1.0
    return (P_bar - P_e) / (1 - P_e)


def compute_all(erc_annotations, a2a_annotations, case_label):
    """Compute all pairwise + Fleiss Kappa for a single case."""
    model_names = list(erc_annotations.keys()) if case_label == "ERC" else list(a2a_annotations.keys())

    if case_label == "ERC":
        anns = erc_annotations
    else:
        anns = a2a_annotations

    # Find overlap: keys present in ALL models
    all_keys = None
    for model in model_names:
        if not anns[model]:
            continue
        keys = set(anns[model].keys())
        if all_keys is None:
            all_keys = keys
        else:
            all_keys &= keys

    if not all_keys:
        print(f"  No overlapping keys for {case_label}")
        return {"n_overlap": 0}

    print(f"  {case_label}: {len(all_keys)} overlapping records across {len(model_names)} models")

    results = {
        "n_overlap": len(all_keys),
        "models": model_names,
        "pairwise": {},
        "fleiss": {},
    }

    for field in FIELDS:
        # Collect annotations for each model for the field
        field_anns = {}
        for model in model_names:
            field_anns[model] = [
                anns[model][k].get(field, "MISSING") for k in sorted(all_keys)
            ]

        # Convert None to "NONE" string for consistent comparison
        has_none = any(None in field_anns[m] for m in model_names)
        for model in model_names:
            field_anns[model] = ["NONE" if v is None else v for v in field_anns[model]]

        # Find all labels used by any model for this field
        all_labels = set()
        for model in model_names:
            all_labels.update(field_anns[model])
        all_labels.discard("MISSING")

        # Pairwise Cohen's Kappa
        pairwise = {}
        for i, m1 in enumerate(model_names):
            for j, m2 in enumerate(model_names):
                if i >= j:
                    continue
                pair_key = f"{m1} vs {m2}"
                k = cohens_kappa(field_anns[m1], field_anns[m2], all_labels)
                pairwise[pair_key] = round(k, 4) if not np.isnan(k) else None

        results["pairwise"][field] = pairwise

        # Fleiss' Kappa across all models
        # Each item gets N model annotations
        item_anns = []
        for idx in range(len(all_keys)):
            item_anns.append([field_anns[m][idx] for m in model_names])

        fk = fleiss_kappa(item_anns, all_labels)
        results["fleiss"][field] = round(fk, 4) if not np.isnan(fk) else None

    return results


def main():
    print("=" * 70)
    print("Cross-Model Kappa: 4 Models (MiniMax-M2.5 + 3 cross-round models)")
    print("=" * 70)

    # 1. Load MiniMax-M2.5 (R1)
    print("\n[1/4] Loading MiniMax-M2.5 (R1 annotated_records.json)…")
    r1_erc, r1_a2a = load_r1_annotations()
    print(f"  ERC: {len(r1_erc)} records, A2A: {len(r1_a2a)} records")

    # 2. Load cross-round models
    cross_round_models = CANONICAL_MODELS
    all_erc = {"MiniMax-M2.5": r1_erc}
    all_a2a = {"MiniMax-M2.5": r1_a2a}

    for i, model in enumerate(cross_round_models, 2):
        print(f"\n[{i}/4] Loading {model} (cross-round consensus)…")
        erc_ann = load_cross_round_annotations(model, "erc")
        a2a_ann = load_cross_round_annotations(model, "a2a")
        print(f"  ERC: {len(erc_ann)} records, A2A: {len(a2a_ann)} records")
        all_erc[model] = erc_ann
        all_a2a[model] = a2a_ann

    # 3. Compute Kappa for ERC
    print("\n" + "=" * 70)
    print("ERC Case")
    print("=" * 70)
    erc_results = compute_all(all_erc, {}, "ERC")

    # 4. Compute Kappa for A2A
    print("\n" + "=" * 70)
    print("A2A Case")
    print("=" * 70)
    a2a_results = compute_all({}, all_a2a, "A2A")

    # 5. Print summary tables
    final = {"erc": erc_results, "a2a": a2a_results}

    for case in ["erc", "a2a"]:
        r = final[case]
        if r.get("n_overlap", 0) == 0:
            continue

        print(f"\n{'='*70}")
        print(f"{case.upper()} — Summary ({r['n_overlap']} overlapping records)")
        print(f"{'='*70}")

        for field in FIELDS:
            print(f"\n--- {field} ---")

            # Fleiss
            fk = r["fleiss"].get(field)
            print(f"  Fleiss' κ (4 models): {fk}")

            # Pairwise table
            print(f"  Pairwise Cohen's κ:")
            pw = r["pairwise"].get(field, {})
            for pair, kappa in sorted(pw.items()):
                print(f"    {pair}: {kappa}")

    # Save
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
