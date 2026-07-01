"""
DNA run_r2.py — Discourse Network Analysis on R2 consensus + new Thematic-LM.

Identical to run.py but uses loader_r2.load_joined_r2() as the data source.

Usage:
  uv run python scripts/analyse/network_discourse/dna/run_r2.py
  uv run python scripts/analyse/network_discourse/dna/run_r2.py --min-shared 2
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

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT / "scripts/analyse/network_discourse"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from lib.paths import ANALYSIS_ND_R2_DNA

from dna.build import build, graph_to_edgelist
from dna.metrics import compute
from loader_r2 import load_joined_r2

OUT_DIR = ANALYSIS_ND_R2_DNA

CASE_COLORS = {"ERC-8004": "#E87722", "Google-A2A": "#4285F4"}
INST_PALETTE = {
    "Google": "#4285F4",
    "Microsoft": "#7B9EA6",
    "Salesforce": "#00A1E0",
    "Atlassian": "#0052CC",
    "Cisco": "#6FAE8C",
    "Independent": "#34A853",
    "Ethereum Foundation": "#9B59B6",
    "Unknown": "#95A5A6",
}


def _node_colors(G: nx.Graph, inst_map: dict[str, str]) -> list[str]:
    return [INST_PALETTE.get(inst_map.get(n, "Unknown"), "#95A5A6") for n in G.nodes()]


def visualize(G_erc: nx.Graph, G_a2a: nx.Graph,
              inst_erc: dict, inst_a2a: dict,
              out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    for ax, G, inst_map, title in [
        (axes[0], G_erc, inst_erc, "ERC Agent Cluster\nCongruence Network"),
        (axes[1], G_a2a, inst_a2a, "Google A2A\nCongruence Network"),
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

        top5 = sorted(degrees, key=lambda n: -degrees[n])[:5]
        labels = {n: n for n in top5}
        nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=6)

        ax.set_title(f"{title}\n(N={G.number_of_nodes()}, E={G.number_of_edges()})", fontsize=11)
        ax.axis("off")

    handles = [plt.Line2D([0], [0], marker="o", color="w",
                          markerfacecolor=c, markersize=8, label=inst)
               for inst, c in INST_PALETTE.items() if inst != "Unknown"]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=8, title="Stakeholder")

    plt.suptitle("R2 Discourse Network Analysis — Congruence Networks", fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0.06, 1, 1])
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path.name}")


def main(min_shared: int = 1) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading R2 data and building DNA networks...")
    data = build(min_shared=min_shared, load_fn=load_joined_r2)

    all_metrics: dict = {}
    inst_maps: dict = {}

    for case in ("ERC-8004", "Google-A2A"):
        if case not in data["by_case"]:
            print(f"  WARNING: {case} not found in R2 data")
            continue
        cd = data["by_case"][case]
        sub = cd["sub"]

        inst_maps[case] = (
            sub.drop_duplicates("author")
            .set_index("author")["stakeholder_institution"]
            .to_dict()
        )

        m = compute(cd, sub)
        all_metrics[case] = m
        print(f"\n[{case}]")
        print(f"  Actors: {m['n_actors']}, Themes: {m['n_themes_active']}, Records: {m['n_records']}")
        print(f"  Congruence: {m['congruence']['edges']} edges, "
              f"density={m['congruence']['density']}, modularity={m['congruence']['modularity']}")
        print(f"  Conflict: {m['conflict']['edges']} edges")
        if m["congruence"]["top_betweenness"]:
            print(f"  Top-3 betweenness: {m['congruence']['top_betweenness'][:3]}")

        safe = case.replace("-", "").replace(" ", "_").lower()
        graph_to_edgelist(cd["congruence"]).to_csv(OUT_DIR / f"congruence_{safe}.csv", index=False)
        graph_to_edgelist(cd["conflict"]).to_csv(OUT_DIR / f"conflict_{safe}.csv", index=False)

    (OUT_DIR / "dna_metrics.json").write_text(
        json.dumps(all_metrics, indent=2, ensure_ascii=False)
    )
    print("\nSaved dna_metrics.json")

    if "ERC-8004" in data["by_case"] and "Google-A2A" in data["by_case"]:
        G_erc = data["by_case"]["ERC-8004"]["congruence"]
        G_a2a = data["by_case"]["Google-A2A"]["congruence"]
        visualize(G_erc, G_a2a, inst_maps.get("ERC-8004", {}), inst_maps.get("Google-A2A", {}),
                  OUT_DIR / "r2_dna_comparison.png")

    print(f"\nR2 DNA analysis complete. Outputs: {OUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-shared", type=int, default=1)
    args = parser.parse_args()
    main(min_shared=args.min_shared)
