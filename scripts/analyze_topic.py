"""
analyze_topic.py

Produces:
  output/topic_argtype_comparison.png   — Figure 1: argument type distribution by case
  output/topic_stance_heatmap.png       — argument_type × stance cross-tabulation
  output/topic_temporal_erc8004.png     — argument type over ERC-8004 lifecycle
  output/topic_stats.json              — raw counts and percentages for paper

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
OUTPUT = ROOT / "output"

# ── palette ──────────────────────────────────────────────────────────────────
COLORS = {
    "Technical":           "#2980B9",
    "Process":             "#27AE60",
    "Governance-Principle":"#E67E22",
    "Economic":            "#8E44AD",
    "Off-topic":           "#BDC3C7",
    "Neutral":             "#95A5A6",
    "Unknown":             "#ECF0F1",
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
    out = OUTPUT / "topic_argtype_comparison.png"
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
    out = OUTPUT / "topic_stance_heatmap.png"
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
    ax.legend(loc="upper left", fontsize=8, framealpha=0.7)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = OUTPUT / "topic_temporal_erc8004.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {out}")


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
    stats_path = OUTPUT / "topic_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"  Saved → {stats_path}")

    print("\n── ERC-8004 Argument Types ──")
    for t, v in stats["erc8004"]["argument_type"].items():
        print(f"  {t:25s}: {v['count']:4d}  ({v['pct']:.1f}%)")

    print("\n── Google A2A Argument Types ──")
    for t, v in stats["a2a"]["argument_type"].items():
        print(f"  {t:25s}: {v['count']:5d}  ({v['pct']:.1f}%)")

    print("\n── ERC-8004 Stance ──")
    for s, v in stats["erc8004"]["stance"].items():
        print(f"  {s:15s}: {v['count']:4d}  ({v['pct']:.1f}%)")

    print("\nGenerating figures...")
    fig_argtype_comparison(records)
    fig_stance_heatmap(records)
    fig_temporal_erc8004(records)
    print("\nDone.")


if __name__ == "__main__":
    main()
