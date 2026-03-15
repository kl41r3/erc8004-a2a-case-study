"""
Chi-square test for argument_type and stance distributions across cases.

Usage:
    uv run python scripts/compute_chi2.py

No external dependencies beyond the standard library.
scipy is used only if available; otherwise falls back to a manual implementation.
"""

import json
from collections import Counter
from pathlib import Path
import math

ROOT = Path(__file__).parent.parent.parent
ANNOTATED = ROOT / "data" / "annotated" / "annotated_records.json"


# ── chi-square (no scipy required) ────────────────────────────────────────────

def chi2_test(table: list[list[int]]) -> tuple[float, float, int]:
    """
    table: 2D list of observed counts, shape (n_rows, n_cols).
    Returns (chi2_stat, p_value, degrees_of_freedom).
    p_value computed via chi2 survival function approximation (good for large samples).
    """
    rows = len(table)
    cols = len(table[0])
    row_sums = [sum(table[r]) for r in range(rows)]
    col_sums = [sum(table[r][c] for r in range(rows)) for c in range(cols)]
    total = sum(row_sums)

    chi2 = 0.0
    for r in range(rows):
        for c in range(cols):
            expected = row_sums[r] * col_sums[c] / total
            if expected > 0:
                chi2 += (table[r][c] - expected) ** 2 / expected

    dof = (rows - 1) * (cols - 1)

    # p-value via regularized incomplete gamma function (scipy-free approximation)
    try:
        from scipy.stats import chi2 as scipy_chi2
        p = scipy_chi2.sf(chi2, dof)
    except ImportError:
        # fallback: very rough approximation using normal for large dof
        # for large chi2 and dof this gives a reasonable order-of-magnitude p
        z = ((chi2 / dof) ** (1/3) - (1 - 2/(9*dof))) / math.sqrt(2/(9*dof))
        p = 0.5 * math.erfc(z / math.sqrt(2))

    return chi2, p, dof


def effect_size_cramers_v(chi2: float, n: int, dof: int, n_rows: int, n_cols: int) -> float:
    """Cramér's V — effect size for chi-square on contingency tables."""
    k = min(n_rows, n_cols)
    return math.sqrt(chi2 / (n * (k - 1)))


# ── load data ─────────────────────────────────────────────────────────────────

with open(ANNOTATED) as f:
    data = json.load(f)

valid = [r for r in data
         if isinstance(r.get("annotation"), dict)
         and not r.get("annotation_error")]

erc = [r for r in valid if r.get("_case") == "ERC-8004"]
a2a = [r for r in valid if r.get("_case") == "Google-A2A"]

print(f"Valid records — ERC-8004: {len(erc)}, Google-A2A: {len(a2a)}\n")


# ── helper ────────────────────────────────────────────────────────────────────

def build_table(field: str, categories: list[str]) -> list[list[int]]:
    erc_counts = Counter(r["annotation"].get(field, "") for r in erc)
    a2a_counts = Counter(r["annotation"].get(field, "") for r in a2a)
    return [
        [erc_counts.get(cat, 0) for cat in categories],
        [a2a_counts.get(cat, 0) for cat in categories],
    ]


def print_table(field: str, categories: list[str], table: list[list[int]]):
    n_erc = sum(table[0])
    n_a2a = sum(table[1])
    col_w = max(len(c) for c in categories) + 2
    print(f"  {'':>{col_w}}", end="")
    for cat in categories:
        print(f"  {cat:>{col_w}}", end="")
    print(f"  {'N':>6}")
    for i, (label, row, n) in enumerate(
        [("ERC-8004", table[0], n_erc), ("Google-A2A", table[1], n_a2a)]
    ):
        print(f"  {label:>{col_w}}", end="")
        for count in row:
            pct = count / n * 100 if n else 0
            print(f"  {f'{count}({pct:.0f}%)':>{col_w}}", end="")
        print(f"  {n:>6}")


# ── run tests ─────────────────────────────────────────────────────────────────

fields = {
    "argument_type": ["Technical", "Process", "Governance-Principle", "Economic", "Off-topic"],
    "stance":        ["Support", "Modify", "Neutral", "Oppose", "Off-topic"],
}

for field, categories in fields.items():
    table = build_table(field, categories)
    chi2, p, dof = chi2_test(table)
    n_total = sum(table[0]) + sum(table[1])
    v = effect_size_cramers_v(chi2, n_total, dof, 2, len(categories))

    print(f"── {field} {'─'*(50 - len(field))}")
    print_table(field, categories, table)
    print()
    print(f"  χ²({dof}) = {chi2:.2f},  p = {p:.2e},  Cramér's V = {v:.3f}")

    if p < 0.001:
        sig = "p < .001 ***"
    elif p < 0.01:
        sig = "p < .01 **"
    elif p < 0.05:
        sig = "p < .05 *"
    else:
        sig = "p ≥ .05 (not significant)"

    if v < 0.1:
        effect = "negligible"
    elif v < 0.3:
        effect = "small"
    elif v < 0.5:
        effect = "medium"
    else:
        effect = "large"

    print(f"  {sig},  effect size: {effect}")
    print()
    print("  Paste into paper:")
    print(f'  "Distributions differed significantly across cases,')
    print(f'   χ²({dof}, N={n_total}) = {chi2:.2f}, {sig}, V = {v:.2f}."')
    print()
