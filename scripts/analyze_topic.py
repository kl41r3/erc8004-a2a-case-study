"""
analyze_topic.py

Produces:
  output/figures/topic_argtype_comparison.png    — argument type distribution by case
  output/figures/topic_stance_heatmap.png        — argument_type × stance cross-tabulation
  output/figures/topic_temporal_erc8004.png      — argument type over ERC-8004 lifecycle (legacy)
  output/figures/topic_temporal_comparison.png   — ERC-8004 vs A2A temporal evolution (two-panel)
  output/stats/topic_stats.json                  — raw counts, percentages, chi-square results

Data: data/annotated/annotated_records.json
Method: structured LLM classification (argument_type, stance, date, _case)
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from dateutil import parser as dateparser

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "annotated" / "annotated_records.json"
OUTPUT   = ROOT / "output"
FIGURES  = ROOT / "output" / "figures"
STATS    = ROOT / "output" / "stats"

# ── palette ──────────────────────────────────────────────────────────────────
COLORS = {
    "Technical":           "#7B9BAD",  # muted steel blue
    "Process":             "#91A882",  # sage green
    "Governance-Principle":"#C4956A",  # dusty terracotta
    "Economic":            "#9B8FAF",  # muted mauve
    "Off-topic":           "#C2C2C2",  # light grey
    "Neutral":             "#AEAEAE",
    "Unknown":             "#E8E8E8",
}

ARG_ORDER = ["Technical", "Process", "Governance-Principle", "Economic", "Off-topic"]
STANCE_ORDER = ["Support", "Modify", "Neutral", "Oppose", "Off-topic"]

# ERC-8004 lifecycle stage boundaries (dates)
EIP_STAGES = [
    ("2025-08-13", "Proposal"),
    ("2025-10-01", "Review"),
    ("2025-12-15", "Last Call"),
    ("2026-01-29", "Final"),
]


# ── load ─────────────────────────────────────────────────────────────────────

def load_records():
    with open(DATA) as f:
        records = json.load(f)
    annotated = [r for r in records if r.get("annotation") and not r.get("annotation_error")]
    return annotated


def get_field(record, field):
    ann = record.get("annotation", {}) or {}
    return ann.get(field) or record.get(field)


# ── Figure 1: argument type distribution ─────────────────────────────────────

def fig_argtype_comparison(records):
    erc = [r for r in records if r.get("_case") == "ERC-8004"]
    a2a = [r for r in records if r.get("_case") == "Google-A2A"]

    def pct(recs, types=ARG_ORDER):
        total = len(recs)
        counts = Counter(get_field(r, "argument_type") for r in recs)
        return [100.0 * counts.get(t, 0) / total if total else 0 for t in types]

    erc_pct = pct(erc)
    a2a_pct = pct(a2a)

    x = np.arange(len(ARG_ORDER))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars_erc = ax.bar(x - width/2, erc_pct, width,
                      label=f"ERC-8004 (N={len(erc)})",
                      color=[COLORS.get(t, "#aaa") for t in ARG_ORDER],
                      edgecolor="white", linewidth=0.8)
    bars_a2a = ax.bar(x + width/2, a2a_pct, width,
                      label=f"Google A2A (N={len(a2a)})",
                      color=[COLORS.get(t, "#aaa") for t in ARG_ORDER],
                      edgecolor="white", linewidth=0.8, alpha=0.55,
                      hatch="///")

    # Value labels
    for bar in bars_erc:
        h = bar.get_height()
        if h > 1.5:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.4,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=7.5)
    for bar in bars_a2a:
        h = bar.get_height()
        if h > 1.5:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.4,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=7.5, color="#555")

    ax.set_xticks(x)
    ax.set_xticklabels(ARG_ORDER, fontsize=9)
    ax.set_ylabel("Share of records (%)", fontsize=9)
    ax.set_title("Figure 1: Argument Type Distribution by Case", fontsize=10, fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_ylim(0, max(erc_pct + a2a_pct) * 1.18)
    ax.spines[["top", "right"]].set_visible(False)

    # Manual legend for case distinction
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#888", label=f"ERC-8004 (N={len(erc)})", edgecolor="white"),
        Patch(facecolor="#888", label=f"Google A2A (N={len(a2a)})",
              edgecolor="white", alpha=0.55, hatch="///"),
    ]
    ax.legend(handles=legend_elements, fontsize=8.5, loc="upper right")

    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    out = FIGURES / "topic_argtype_comparison.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {out}")
    return erc_pct, a2a_pct


# ── Figure 2: stance × argument_type heatmap ─────────────────────────────────

def fig_stance_heatmap(records):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fig.patch.set_facecolor("white")
    fig.suptitle("Stance × Argument Type Cross-Tabulation (%)",
                 fontsize=10, fontweight="bold")

    for ax, case_name, case_label in [
        (axes[0], "ERC-8004", "ERC-8004"),
        (axes[1], "Google-A2A", "Google A2A"),
    ]:
        case_recs = [r for r in records if r.get("_case") == case_name]
        matrix = np.zeros((len(STANCE_ORDER), len(ARG_ORDER)))
        for r in case_recs:
            stance = get_field(r, "stance")
            atype  = get_field(r, "argument_type")
            if stance in STANCE_ORDER and atype in ARG_ORDER:
                si = STANCE_ORDER.index(stance)
                ai = ARG_ORDER.index(atype)
                matrix[si, ai] += 1

        # normalise by row (stance total) to show conditional distribution
        row_totals = matrix.sum(axis=1, keepdims=True)
        row_totals[row_totals == 0] = 1
        matrix_pct = 100.0 * matrix / row_totals

        im = ax.imshow(matrix_pct, cmap="Blues", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(len(ARG_ORDER)))
        ax.set_xticklabels(ARG_ORDER, rotation=30, ha="right", fontsize=8)
        ax.set_yticks(range(len(STANCE_ORDER)))
        ax.set_yticklabels(STANCE_ORDER, fontsize=8.5)
        ax.set_title(f"{case_label} (N={len(case_recs)})", fontsize=9)
        ax.set_facecolor("white")

        for si in range(len(STANCE_ORDER)):
            for ai in range(len(ARG_ORDER)):
                val = matrix_pct[si, ai]
                if val > 3:
                    ax.text(ai, si, f"{val:.0f}%", ha="center", va="center",
                            fontsize=7, color="white" if val > 55 else "#111")

        plt.colorbar(im, ax=ax, shrink=0.8, label="% within stance row")

    plt.tight_layout()
    out = FIGURES / "topic_stance_heatmap.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {out}")


# ── Figure 3: ERC-8004 temporal evolution ───────────────────────────────────

def fig_temporal_erc8004(records):
    erc = [r for r in records if r.get("_case") == "ERC-8004"]

    # Parse dates
    dated = []
    for r in erc:
        raw_date = r.get("date") or r.get("created_at") or ""
        try:
            dt = dateparser.parse(raw_date)
            dated.append((dt, get_field(r, "argument_type")))
        except Exception:
            pass

    dated.sort(key=lambda x: x[0])
    if not dated:
        print("No dated ERC-8004 records found for temporal plot.")
        return

    # Group by 2-week bins
    min_dt = dated[0][0]
    max_dt = dated[-1][0]
    bin_days = 14
    total_days = (max_dt - min_dt).days + 1
    n_bins = max(1, total_days // bin_days + 1)

    bins = defaultdict(Counter)
    for dt, atype in dated:
        bin_idx = (dt - min_dt).days // bin_days
        bins[bin_idx][atype if atype in ARG_ORDER else "Off-topic"] += 1

    bin_indices = sorted(bins.keys())
    # x-axis: approximate date of bin start
    from datetime import timedelta
    bin_dates = [min_dt + timedelta(days=i * bin_days) for i in bin_indices]

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bottoms = np.zeros(len(bin_indices))
    for atype in ARG_ORDER:
        heights = [bins[i].get(atype, 0) for i in bin_indices]
        ax.bar(range(len(bin_indices)), heights, bottom=bottoms,
               color=COLORS.get(atype, "#ccc"), label=atype,
               edgecolor="white", linewidth=0.5)
        bottoms += np.array(heights)

    # Stage markers
    for stage_date_str, stage_name in EIP_STAGES[1:]:  # skip proposal (start)
        try:
            stage_dt = dateparser.parse(stage_date_str)
            x_pos = (stage_dt - min_dt).days / bin_days
            ax.axvline(x=x_pos, color="#555", linestyle="--", linewidth=0.8, alpha=0.7)
            ax.text(x_pos + 0.1, bottoms.max() * 0.95, stage_name,
                    fontsize=7.5, color="#333", rotation=90, va="top")
        except Exception:
            pass

    ax.set_xticks(range(len(bin_indices)))
    ax.set_xticklabels(
        [d.strftime("%b %d") for d in bin_dates],
        rotation=45, ha="right", fontsize=7.5
    )
    ax.set_ylabel("Records per 2-week bin", fontsize=9)
    ax.set_title("ERC-8004: Argument Type Over Lifecycle (2-week bins)",
                 fontsize=10, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.7)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = FIGURES / "topic_temporal_erc8004.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {out}")


# ── Figure 4: two-panel temporal comparison ──────────────────────────────────

def _parse_dated_records(records, case_name):
    """Return list of (datetime, argument_type) for a given case, sorted by date."""
    dated = []
    for r in records:
        if r.get("_case") != case_name:
            continue
        raw = r.get("date") or r.get("created_at") or ""
        try:
            dt = dateparser.parse(raw)
            if dt is None:
                continue
            atype = get_field(r, "argument_type")
            dated.append((dt, atype if atype in ARG_ORDER else "Off-topic"))
        except Exception:
            pass
    dated.sort(key=lambda x: x[0])
    return dated


def _bin_to_pct_matrix(dated, bin_days):
    """
    Group (datetime, argtype) pairs into time bins of `bin_days` days.
    Returns (bin_start_dates, matrix) where matrix[i] = {argtype: pct}.
    Bins with zero records are skipped.
    """
    if not dated:
        return [], {}
    from datetime import timedelta
    min_dt = dated[0][0]
    bins = defaultdict(Counter)
    for dt, atype in dated:
        idx = (dt - min_dt).days // bin_days
        bins[idx][atype] += 1

    indices = sorted(bins.keys())
    bin_dates = [min_dt + timedelta(days=i * bin_days) for i in indices]
    matrix = []
    for i in indices:
        total = sum(bins[i].values())
        row = {t: 100.0 * bins[i].get(t, 0) / total for t in ARG_ORDER}
        matrix.append(row)
    return bin_dates, matrix


def fig_temporal_comparison(records):
    """
    Two-panel stacked 100% bar chart.
    Top: ERC-8004 (2-week bins, lifecycle stage markers)
    Bottom: Google A2A (monthly bins)
    """
    from datetime import timedelta

    erc_dated = _parse_dated_records(records, "ERC-8004")
    a2a_dated = _parse_dated_records(records, "Google-A2A")

    erc_dates, erc_matrix = _bin_to_pct_matrix(erc_dated, bin_days=14)
    a2a_dates, a2a_matrix = _bin_to_pct_matrix(a2a_dated, bin_days=30)

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), gridspec_kw={"hspace": 0.45})
    fig.patch.set_facecolor("white")

    def draw_panel(ax, bin_dates, matrix, title, stage_markers=None):
        ax.set_facecolor("white")
        n = len(bin_dates)
        if n == 0:
            ax.set_title(title, fontsize=9, fontweight="bold")
            return

        x = np.arange(n)
        bottoms = np.zeros(n)
        for atype in ARG_ORDER:
            heights = [row.get(atype, 0) for row in matrix]
            ax.bar(x, heights, bottom=bottoms,
                   color=COLORS.get(atype, "#ccc"), label=atype,
                   edgecolor="white", linewidth=0.4, width=0.85)
            bottoms += np.array(heights)

        # Lifecycle stage markers (ERC-8004 only)
        if stage_markers:
            min_dt = bin_dates[0]
            bin_days = (bin_dates[1] - bin_dates[0]).days if len(bin_dates) > 1 else 14
            for stage_date_str, stage_name in stage_markers:
                try:
                    stage_dt = dateparser.parse(stage_date_str)
                    x_pos = (stage_dt - min_dt).days / bin_days
                    ax.axvline(x=x_pos, color="#555", linestyle="--",
                               linewidth=0.9, alpha=0.75)
                    ax.text(x_pos + 0.15, 97, stage_name, fontsize=7,
                            color="#333", rotation=90, va="top")
                except Exception:
                    pass

        # x-axis labels
        step = max(1, n // 10)
        tick_pos = list(range(0, n, step))
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(
            [bin_dates[i].strftime("%b '%y") for i in tick_pos],
            rotation=40, ha="right", fontsize=7.5
        )
        ax.set_ylabel("Share (%)", fontsize=8.5)
        ax.set_ylim(0, 105)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
        ax.set_title(title, fontsize=9.5, fontweight="bold", pad=6)
        ax.spines[["top", "right"]].set_visible(False)

    draw_panel(
        axes[0], erc_dates, erc_matrix,
        f"ERC-8004: Argument Type over Lifecycle  (2-week bins, N={len(erc_dated)})",
        stage_markers=EIP_STAGES[1:]
    )
    draw_panel(
        axes[1], a2a_dates, a2a_matrix,
        f"Google A2A: Argument Type over Time  (monthly bins, N={len(a2a_dated)})"
    )

    # Shared legend at bottom
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS.get(t, "#ccc"), label=t)
               for t in ARG_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=5,
               fontsize=8.5, bbox_to_anchor=(0.5, -0.02), framealpha=0.0)

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    out = FIGURES / "topic_temporal_comparison.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {out}")


# ── Chi-square tests ───────────────────────────────────────────────────────────

def compute_chisquare(records):
    """
    Two chi-square tests:
    1. Cross-case: ERC-8004 vs A2A argument type distributions
    2. Within ERC-8004: argument type by lifecycle phase
    Returns dict with test results.
    """
    from scipy.stats import chi2_contingency
    import math

    results = {}

    # --- Test 1: cross-case ---
    erc = [r for r in records if r.get("_case") == "ERC-8004"]
    a2a = [r for r in records if r.get("_case") == "Google-A2A"]
    types = [t for t in ARG_ORDER if t != "Off-topic"]

    erc_counts = Counter(get_field(r, "argument_type") for r in erc)
    a2a_counts = Counter(get_field(r, "argument_type") for r in a2a)
    contingency = np.array([
        [erc_counts.get(t, 0) for t in types],
        [a2a_counts.get(t, 0) for t in types],
    ])
    chi2, p, dof, expected = chi2_contingency(contingency)
    n_total = contingency.sum()
    cramers_v = math.sqrt(chi2 / (n_total * (min(contingency.shape) - 1)))
    results["cross_case"] = {
        "test": "chi2_contingency",
        "categories": types,
        "observed_erc8004": [int(erc_counts.get(t, 0)) for t in types],
        "observed_a2a": [int(a2a_counts.get(t, 0)) for t in types],
        "chi2": round(chi2, 3),
        "p_value": round(p, 6),
        "dof": int(dof),
        "cramers_v": round(cramers_v, 4),
        "interpretation": (
            "significant" if p < 0.05 else "not significant"
        ),
    }

    # --- Test 2: ERC-8004 lifecycle phases (2-month bins) ---
    # ERC-8004 span: 2025-08-13 (proposed) → 2026-01-29 (Final) ≈ 5.5 months → 3 bins
    phase_labels = ["Aug–Oct 2025", "Oct–Dec 2025", "Dec 2025–Feb 2026"]
    phase_bounds = [
        ("2025-08-13", "2025-10-13"),
        ("2025-10-13", "2025-12-13"),
        ("2025-12-13", "2026-02-13"),
    ]
    phase_counts = {ph: Counter() for ph in phase_labels}
    for r in erc:
        raw = r.get("date") or r.get("created_at") or ""
        try:
            dt = dateparser.parse(raw)
            if dt is None:
                continue
            dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
            for label, (start_str, end_str) in zip(phase_labels, phase_bounds):
                start = dateparser.parse(start_str).replace(tzinfo=None)
                end   = dateparser.parse(end_str).replace(tzinfo=None)
                if start <= dt_naive < end:
                    atype = get_field(r, "argument_type")
                    phase_counts[label][atype if atype in types else "Off-topic"] += 1
                    break
        except Exception:
            pass

    phase_matrix = np.array([
        [phase_counts[ph].get(t, 0) for t in types]
        for ph in phase_labels
    ])
    # Drop phases with all-zero rows
    nonzero_phases = [i for i, row in enumerate(phase_matrix) if row.sum() > 0]
    if len(nonzero_phases) >= 2:
        sub = phase_matrix[nonzero_phases]
        chi2_p, p_p, dof_p, _ = chi2_contingency(sub)
        n_p = sub.sum()
        v_p = math.sqrt(chi2_p / (n_p * (min(sub.shape) - 1)))
        results["erc8004_lifecycle"] = {
            "test": "chi2_contingency",
            "phases": [phase_labels[i] for i in nonzero_phases],
            "categories": types,
            "observed": sub.tolist(),
            "chi2": round(chi2_p, 3),
            "p_value": round(p_p, 6),
            "dof": int(dof_p),
            "cramers_v": round(v_p, 4),
            "interpretation": (
                "significant" if p_p < 0.05 else "not significant"
            ),
        }
    else:
        results["erc8004_lifecycle"] = {"note": "insufficient phases with data"}

    return results


# ── statistics ────────────────────────────────────────────────────────────────

def compute_stats(records):
    stats = {}
    for case_name, label in [("ERC-8004", "erc8004"), ("Google-A2A", "a2a")]:
        recs = [r for r in records if r.get("_case") == case_name]
        total = len(recs)
        arg_counts = Counter(get_field(r, "argument_type") for r in recs)
        stance_counts = Counter(get_field(r, "stance") for r in recs)
        stats[label] = {
            "total": total,
            "argument_type": {
                t: {"count": arg_counts.get(t, 0),
                    "pct": round(100.0 * arg_counts.get(t, 0) / total, 1) if total else 0}
                for t in ARG_ORDER
            },
            "stance": {
                s: {"count": stance_counts.get(s, 0),
                    "pct": round(100.0 * stance_counts.get(s, 0) / total, 1) if total else 0}
                for s in STANCE_ORDER
            },
        }
    return stats


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading annotated records...")
    records = load_records()
    print(f"  Total annotated: {len(records)}")

    print("\nComputing stats...")
    stats = compute_stats(records)

    print("\nRunning chi-square tests...")
    chi2_results = compute_chisquare(records)
    stats["chi2_tests"] = chi2_results

    stats_path = STATS / "topic_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"  Saved → {stats_path}")

    print("\n── ERC-8004 Argument Types ──")
    for t, v in stats["erc8004"]["argument_type"].items():
        print(f"  {t:25s}: {v['count']:4d}  ({v['pct']:.1f}%)")

    print("\n── Google A2A Argument Types ──")
    for t, v in stats["a2a"]["argument_type"].items():
        print(f"  {t:25s}: {v['count']:5d}  ({v['pct']:.1f}%)")

    print("\n── Chi-square: cross-case ──")
    cc = chi2_results.get("cross_case", {})
    print(f"  χ²={cc.get('chi2')}, p={cc.get('p_value')}, "
          f"df={cc.get('dof')}, Cramér's V={cc.get('cramers_v')}  [{cc.get('interpretation')}]")

    print("\n── Chi-square: ERC-8004 lifecycle ──")
    lc = chi2_results.get("erc8004_lifecycle", {})
    if "chi2" in lc:
        print(f"  χ²={lc.get('chi2')}, p={lc.get('p_value')}, "
              f"df={lc.get('dof')}, Cramér's V={lc.get('cramers_v')}  [{lc.get('interpretation')}]")
        print(f"  Phases: {lc.get('phases')}")
    else:
        print(f"  {lc.get('note', 'no result')}")

    print("\nGenerating figures...")
    fig_argtype_comparison(records)
    fig_stance_heatmap(records)
    fig_temporal_erc8004(records)
    fig_temporal_comparison(records)
    print("\nDone.")


if __name__ == "__main__":
    main()
