"""
Discourse Network Analysis — entry point.

Usage:
    uv run python scripts/analyse/network_discourse/dna/run.py
    uv run python scripts/analyse/network_discourse/dna/run.py --min-shared 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT / "scripts/analyse/network_discourse"))

from dna.build import build, graph_to_edgelist
from dna.metrics import compute

OUT_DIR = ROOT / "output/network_discourse/dna"

CASE_COLORS = {"ERC-8004": "#E87722", "Google-A2A": "#4285F4"}
INST_PALETTE = {
    "Google": "#4285F4",
    "Independent": "#34A853",
    "Ethereum Foundation": "#9B59B6",
    "Coinbase": "#0052FF",
    "MetaMask": "#F6851B",
    "Unknown": "#95A5A6",
}


def _node_colors(G: nx.Graph, inst_map: dict[str, str]) -> list[str]:
    return [INST_PALETTE.get(inst_map.get(n, "Unknown"), "#95A5A6") for n in G.nodes()]


def visualize(G_erc: nx.Graph, G_a2a: nx.Graph,
              inst_erc: dict, inst_a2a: dict,
              out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    for ax, G, inst_map, title in [
        (axes[0], G_erc, inst_erc, "ERC-8004 Congruence Network"),
        (axes[1], G_a2a, inst_a2a, "Google A2A Congruence Network"),
    ]:
        if len(G.nodes) == 0:
            ax.set_title(title)
            ax.axis("off")
            continue

        weights = [d["weight"] for _, _, d in G.edges(data=True)]
        max_w = max(weights) if weights else 1
        edge_widths = [0.5 + 2.5 * w / max_w for w in weights]

        pos = nx.spring_layout(G, weight="weight", seed=42, k=1.5)
        nc = _node_colors(G, inst_map)
        degrees = dict(G.degree(weight="weight"))
        node_sizes = [50 + 300 * degrees.get(n, 0) / (max(degrees.values()) or 1) for n in G.nodes()]

        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, width=edge_widths, edge_color="#aaaaaa")
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=nc, node_size=node_sizes, alpha=0.85)

        # Label only top-5 degree nodes
        top5 = sorted(degrees, key=lambda n: -degrees[n])[:5]
        labels = {n: n for n in top5}
        nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=6)

        ax.set_title(f"{title}\n(N={G.number_of_nodes()}, E={G.number_of_edges()})", fontsize=11)
        ax.axis("off")

    # Legend
    handles = [plt.Line2D([0], [0], marker="o", color="w",
                          markerfacecolor=c, markersize=8, label=inst)
               for inst, c in INST_PALETTE.items() if inst != "Unknown"]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=8, title="Stakeholder")

    plt.suptitle("Discourse Network Analysis — Congruence Networks", fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0.06, 1, 1])
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path.name}")


def main(min_shared: int = 1) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading and building DNA networks...")
    data = build(min_shared=min_shared)

    all_metrics: dict = {}
    inst_maps: dict = {}

    for case in ("ERC-8004", "Google-A2A"):
        cd = data["by_case"][case]
        sub = cd["sub"]

        # Institution map for visualization
        inst_maps[case] = (
            sub.drop_duplicates("author")
            .set_index("author")["stakeholder_institution"]
            .to_dict()
        )

        m = compute(cd, sub)
        all_metrics[case] = m
        print(f"\n[{case}]")
        print(f"  Actors: {m['n_actors']}, Themes: {m['n_themes_active']}, Records: {m['n_records']}")
        print(f"  Congruence: {m['congruence']['edges']} edges, density={m['congruence']['density']}, "
              f"modularity={m['congruence']['modularity']}")
        print(f"  Conflict: {m['conflict']['edges']} edges")
        print(f"  Mean actor theme diversity: {m['mean_actor_theme_diversity']}")
        if m["congruence"]["top_betweenness"]:
            print(f"  Top-3 betweenness: {m['congruence']['top_betweenness'][:3]}")

        # Save edge lists
        el_cong = graph_to_edgelist(cd["congruence"])
        safe = case.replace("-", "").replace(" ", "_").lower()
        el_cong.to_csv(OUT_DIR / f"congruence_{safe}.csv", index=False)
        el_conf = graph_to_edgelist(cd["conflict"])
        el_conf.to_csv(OUT_DIR / f"conflict_{safe}.csv", index=False)

    # Save metrics
    (OUT_DIR / "dna_metrics.json").write_text(
        json.dumps(all_metrics, indent=2, ensure_ascii=False)
    )
    print("\nSaved dna_metrics.json")

    # Visualize
    G_erc = data["by_case"]["ERC-8004"]["congruence"]
    G_a2a = data["by_case"]["Google-A2A"]["congruence"]
    visualize(G_erc, G_a2a, inst_maps["ERC-8004"], inst_maps["Google-A2A"],
              OUT_DIR / "dna_comparison.png")

    print("\nDNA analysis complete.")
    print(f"Outputs: {OUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-shared", type=int, default=1,
                        help="Min shared themes to form a congruence/conflict edge (default: 1)")
    args = parser.parse_args()
    main(min_shared=args.min_shared)
