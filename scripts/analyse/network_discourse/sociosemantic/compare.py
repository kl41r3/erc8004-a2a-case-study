"""
Socio-semantic cross-case comparison and visualization.

Computes:
  - Per-case summary metrics (mean entropy, Gini of entropy, bipartite modularity)
  - Thematic overlap coefficient between ERC-8004 and A2A
  - Topic gatekeepers (high betweenness in actor-actor projection)
  - Visualizations: bipartite graph, entropy distributions
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import networkx.algorithms.community as nx_comm
import numpy as np
import pandas as pd


CASE_COLORS = {"ERC-8004": "#E87722", "Google-A2A": "#4285F4"}


# ── summary metrics ─────────────────────────────────────────────────────────

def _louvain_modularity(G: nx.Graph) -> float:
    if G.number_of_edges() == 0:
        return 0.0
    try:
        comms = nx_comm.louvain_communities(G, weight="weight", seed=42)
        return round(nx_comm.modularity(G, comms, weight="weight"), 4)
    except Exception:
        return 0.0


def _gini(values: np.ndarray) -> float:
    v = np.sort(values.astype(float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * (idx * v).sum() / (n * v.sum())) - (n + 1) / n)


def summary_metrics(case_data: dict) -> dict:
    div = case_data["actor_diversity"]
    conc = case_data["theme_concentration"]
    G_actor = case_data["actor_graph"]
    B = case_data["B"]

    ent = div["entropy"].values
    n_actors = len(div)
    n_themes = len(B.columns)

    # Gatekeepers: top-5 betweenness in actor projection
    if G_actor.number_of_edges() > 0:
        bc = nx.betweenness_centrality(G_actor, weight="weight", normalized=True)
        gatekeepers = sorted(bc.items(), key=lambda x: -x[1])[:5]
    else:
        bc = {}
        gatekeepers = []

    # Bipartite modularity via actor-side community detection
    mod_actor = _louvain_modularity(G_actor)

    return {
        "n_actors": n_actors,
        "n_themes": n_themes,
        "n_edges_actor_proj": G_actor.number_of_edges(),
        "actor_entropy": {
            "mean": round(float(ent.mean()), 3),
            "median": round(float(np.median(ent)), 3),
            "gini": round(_gini(ent), 3),
            "max": round(float(ent.max()), 3),
        },
        "actor_modularity": mod_actor,
        "theme_concentration": {
            "mean_gini": round(float(conc["gini_actors"].mean()), 3),
            "most_concentrated": conc.iloc[0]["theme_id"] if len(conc) > 0 else None,
        },
        "gatekeepers": [{"actor": a, "bc": round(v, 4)} for a, v in gatekeepers],
    }


# ── thematic overlap ─────────────────────────────────────────────────────────

def thematic_overlap(case_erc: dict, case_a2a: dict) -> dict:
    """
    Overlap coefficient = |themes_erc ∩ themes_a2a| / min(|themes_erc|, |themes_a2a|)
    Also compares per-theme actor share ratios.
    """
    themes_erc = set(case_erc["B"].columns)
    themes_a2a = set(case_a2a["B"].columns)
    shared = themes_erc & themes_a2a
    overlap_coeff = len(shared) / min(len(themes_erc), len(themes_a2a))

    # Per-theme actor proportions
    rows = []
    all_themes = themes_erc | themes_a2a
    for t in sorted(all_themes):
        n_erc = int((case_erc["B"][t] > 0).sum()) if t in case_erc["B"].columns else 0
        n_a2a = int((case_a2a["B"][t] > 0).sum()) if t in case_a2a["B"].columns else 0
        erc_pct = round(100 * n_erc / len(case_erc["B"]), 1) if len(case_erc["B"]) > 0 else 0
        a2a_pct = round(100 * n_a2a / len(case_a2a["B"]), 1) if len(case_a2a["B"]) > 0 else 0
        rows.append({"theme_id": t, "erc8004_actors": n_erc, "a2a_actors": n_a2a,
                     "erc8004_pct": erc_pct, "a2a_pct": a2a_pct,
                     "abs_diff": abs(erc_pct - a2a_pct)})

    df = pd.DataFrame(rows).sort_values("abs_diff", ascending=False).reset_index(drop=True)
    return {
        "overlap_coefficient": round(overlap_coeff, 3),
        "n_shared_themes": len(shared),
        "n_erc_only": len(themes_erc - themes_a2a),
        "n_a2a_only": len(themes_a2a - themes_erc),
        "theme_actor_comparison": df,
    }


# ── visualizations ───────────────────────────────────────────────────────────

def plot_entropy_comparison(case_erc: dict, case_a2a: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

    for ax, (case, cd) in zip(axes, [("ERC-8004", case_erc), ("Google-A2A", case_a2a)]):
        ent = cd["actor_diversity"]["entropy"].values
        ax.hist(ent, bins=15, color=CASE_COLORS[case], alpha=0.75, edgecolor="white")
        ax.axvline(ent.mean(), color="black", linestyle="--", linewidth=1.2,
                   label=f"mean={ent.mean():.2f}")
        ax.set_title(f"{case}\n(N={len(ent)} actors)", fontsize=11)
        ax.set_xlabel("Shannon Entropy (topic diversity)", fontsize=9)
        ax.set_ylabel("Number of Actors", fontsize=9)
        ax.legend(fontsize=8)

    plt.suptitle("Actor Topic Diversity — Socio-semantic Network", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path.name}")


def plot_theme_actor_comparison(overlap_df: pd.DataFrame, themes_meta: dict,
                                 out_path: Path) -> None:
    """Horizontal grouped bar chart: % of actors per case per theme."""
    df = overlap_df.sort_values("abs_diff", ascending=False).head(15)

    # Add readable labels
    df = df.copy()
    df["label"] = df["theme_id"].map(
        lambda t: f"{t}: {themes_meta.get(t, t)[:30]}"
    )

    y = np.arange(len(df))
    h = 0.35

    fig, ax = plt.subplots(figsize=(11, max(6, len(df) * 0.55)))
    ax.barh(y + h / 2, df["erc8004_pct"], h, color=CASE_COLORS["ERC-8004"],
            label="ERC-8004", alpha=0.85)
    ax.barh(y - h / 2, df["a2a_pct"], h, color=CASE_COLORS["Google-A2A"],
            label="Google A2A", alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(df["label"], fontsize=8)
    ax.set_xlabel("% of actors in case who discussed this theme", fontsize=9)
    ax.set_title("Socio-semantic: Actor Participation per Theme (top 15 by divergence)",
                 fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path.name}")
