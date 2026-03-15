"""
Compute Cohen's κ between LLM annotations and human annotations.

Usage:
    uv run python scripts/compute_kappa.py

Input:  verification/sample_50.csv  (human_* columns must be filled)
Output: prints κ per field + confusion matrices
"""

import csv
from pathlib import Path
from collections import Counter

ROOT   = Path(__file__).parent.parent.parent
CSV    = ROOT / "verification" / "sample_50.csv"
FIELDS = ["argument_type", "stance", "consensus_signal", "stakeholder_institution"]


# ── Cohen's κ (no external dependencies) ─────────────────────────────────────

def cohen_kappa(llm: list, human: list) -> float:
    assert len(llm) == len(human)
    n = len(llm)
    labels = sorted(set(llm) | set(human))

    # observed agreement
    p_o = sum(a == b for a, b in zip(llm, human)) / n

    # expected agreement
    llm_counts   = Counter(llm)
    human_counts = Counter(human)
    p_e = sum((llm_counts[l] / n) * (human_counts[l] / n) for l in labels)

    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1.0 - p_e)


def confusion_matrix(llm: list, human: list) -> str:
    labels = sorted(set(llm) | set(human))
    col_w  = max(len(l) for l in labels) + 2
    header = f"{'':>{col_w}}" + "".join(f"{l:>{col_w}}" for l in labels)
    lines  = [header]
    for row_label in labels:
        counts = [sum(a == row_label and b == c for a, b in zip(llm, human)) for c in labels]
        lines.append(f"{row_label:>{col_w}}" + "".join(f"{c:>{col_w}}" for c in counts))
    return "\n".join(lines)


def kappa_interpretation(k: float) -> str:
    if k < 0.20: return "Poor"
    if k < 0.40: return "Fair"
    if k < 0.60: return "Moderate"
    if k < 0.80: return "Substantial"
    return "Almost Perfect"


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    with open(CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # filter rows where human annotation is complete
    complete = [r for r in rows if r.get("human_argument_type", "").strip()]
    if not complete:
        print("ERROR: No human annotations found.")
        print("Fill in the human_argument_type / human_stance / human_consensus_signal columns in:")
        print(f"  {CSV}")
        return

    print(f"Rows with human annotations: {len(complete)} / {len(rows)}")
    print()

    results = {}
    for field in FIELDS:
        llm_col   = f"llm_{field}"
        human_col = f"human_{field}"

        llm_vals   = [r[llm_col].strip()   for r in complete if r.get(llm_col, "").strip()]
        human_vals = [r[human_col].strip() for r in complete if r.get(llm_col, "").strip()]

        if not llm_vals:
            print(f"[{field}] — skipped (no data)\n")
            continue

        kappa = cohen_kappa(llm_vals, human_vals)
        agree = sum(a == b for a, b in zip(llm_vals, human_vals)) / len(llm_vals)
        results[field] = kappa

        print(f"── {field} ──────────────────────────────────────────────")
        print(f"  n             = {len(llm_vals)}")
        print(f"  % agreement   = {agree*100:.1f}%")
        print(f"  Cohen's κ     = {kappa:.3f}  [{kappa_interpretation(kappa)}]")
        print()
        print("  Confusion matrix (rows=LLM, cols=Human):")
        for line in confusion_matrix(llm_vals, human_vals).splitlines():
            print("  " + line)
        print()

    if results:
        print("── Summary ───────────────────────────────────────────────")
        for field, k in results.items():
            print(f"  {field:<25} κ = {k:.3f}  [{kappa_interpretation(k)}]")
        print()
        print("Paste into paper §III:")
        vals = list(results.values())
        avg  = sum(vals) / len(vals)
        print(f'  "Inter-rater agreement was κ={results.get("argument_type", 0):.2f} for argument type,')
        print(f'   κ={results.get("stance", 0):.2f} for stance, and')
        print(f'   κ={results.get("consensus_signal", 0):.2f} for consensus signal')
        print(f'   (mean κ={avg:.2f}), indicating {kappa_interpretation(avg).lower()} agreement')
        print(f'   (Landis & Koch 1977)."')


if __name__ == "__main__":
    main()
