"""
Cross-case topic distribution comparison using Jensen-Shannon divergence.

For each topic, computes the share in ERC-8004 vs. Google-A2A, then measures
JS divergence to quantify how differently the two cases use each topic.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def _js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen-Shannon divergence between two distributions (nats, base e)."""
    p = p + 1e-10
    q = q + 1e-10
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    return float(0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m)))


def build_comparison_table(
    topic_model,
    topics: list[int],
    cases: list[str],
) -> pd.DataFrame:
    """
    Build a DataFrame comparing topic proportions across cases.

    Columns: topic_id | label | keywords | erc8004_pct | a2a_pct | abs_diff | js_contribution
    """
    topic_info = topic_model.get_topic_info()

    case_arr = np.array(cases)
    topic_arr = np.array(topics)

    mask_erc = case_arr == "ERC-8004"
    mask_a2a = case_arr == "Google-A2A"

    rows = []
    for _, row in topic_info.iterrows():
        tid = row["Topic"]
        if tid == -1:
            continue
        label = row.get("Name", f"Topic {tid}")
        topic_terms = topic_model.get_topic(tid)
        keywords = ", ".join(w for w, _ in topic_terms[:8]) if topic_terms else ""

        erc_count = np.sum((topic_arr == tid) & mask_erc)
        a2a_count = np.sum((topic_arr == tid) & mask_a2a)
        erc_total = mask_erc.sum()
        a2a_total = mask_a2a.sum()

        erc_pct = erc_count / erc_total if erc_total else 0.0
        a2a_pct = a2a_count / a2a_total if a2a_total else 0.0

        rows.append({
            "topic_id": tid,
            "label": label,
            "keywords": keywords,
            "erc8004_n": int(erc_count),
            "a2a_n": int(a2a_count),
            "erc8004_pct": round(erc_pct * 100, 2),
            "a2a_pct": round(a2a_pct * 100, 2),
            "abs_diff": round(abs(erc_pct - a2a_pct) * 100, 2),
        })

    df = pd.DataFrame(rows)

    # Per-topic partial-KL against mixture M = (P+Q)/2, following Stine &
    # Agarwal (2020). Using M as denominator (not Q) keeps values finite even
    # when one case has zero probability for a topic.
    #   pkKL_erc_t = p_t * log(p_t / m_t)  →  sum = KL(P‖M)
    #   pkKL_a2a_t = q_t * log(q_t / m_t)  →  sum = KL(Q‖M)
    #   js_t       = 0.5*pkKL_erc_t + 0.5*pkKL_a2a_t  →  sum = JS(P‖Q)
    # Individual terms may be negative (when p_t < m_t or q_t < m_t);
    # the global sums are always non-negative.
    p = df["erc8004_pct"].values / 100
    q = df["a2a_pct"].values / 100
    eps = 1e-10
    p_s = p + eps; p_s = p_s / p_s.sum()
    q_s = q + eps; q_s = q_s / q_s.sum()
    m = 0.5 * (p_s + q_s)
    pkKL_erc = p_s * np.log(p_s / m)
    pkKL_a2a = q_s * np.log(q_s / m)
    js_contrib = 0.5 * pkKL_erc + 0.5 * pkKL_a2a
    df["pkKL_erc"] = np.round(pkKL_erc, 6)
    df["pkKL_a2a"] = np.round(pkKL_a2a, 6)
    df["js_contribution"] = np.round(js_contrib, 6)

    df = df.sort_values("js_contribution", ascending=False)
    global_js = float(js_contrib.sum())
    print(f"\n  Global JS divergence (ERC-8004 ‖ A2A): {global_js:.4f}")
    print(f"  KL(ERC‖M) = {pkKL_erc.sum():.4f},  KL(A2A‖M) = {pkKL_a2a.sum():.4f}")

    return df, global_js


def save_results(df: pd.DataFrame, global_js: float, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "divergence_table.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}")

    summary = {
        "global_js_divergence": round(global_js, 6),
        "n_topics": len(df),
        "top_divergent_topics": df.head(5)[["topic_id", "label", "erc8004_pct", "a2a_pct", "abs_diff"]].to_dict(orient="records"),
    }
    (out_dir / "topics_per_case.json").write_text(json.dumps(summary, indent=2))
    print(f"  Saved: {out_dir / 'topics_per_case.json'}")


def plot_comparison(df: pd.DataFrame, out_dir: Path, top_n: int = 20) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_df = df.head(top_n).sort_values("a2a_pct")

    labels = [row["label"].replace("_", " ") for _, row in plot_df.iterrows()]
    erc_vals = plot_df["erc8004_pct"].values
    a2a_vals = plot_df["a2a_pct"].values

    x = np.arange(len(labels))
    width = 0.38

    fig, ax = plt.subplots(figsize=(12, max(6, len(labels) * 0.42)))
    bars1 = ax.barh(x - width/2, erc_vals, width, label="ERC-8004", color="#2563eb", alpha=0.85)
    bars2 = ax.barh(x + width/2, a2a_vals, width, label="Google A2A", color="#dc2626", alpha=0.85)

    ax.set_yticks(x)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("% of corpus assigned to topic")
    ax.set_title(
        f"Topic Distribution: ERC-8004 vs. Google A2A\n(top {top_n} by absolute difference)",
        fontsize=12, pad=12,
    )
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    out_path = out_dir / "topic_comparison.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")
