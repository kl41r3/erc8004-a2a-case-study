"""
analyze_network.py

Computes SNA metrics and produces:
  output/network_metrics.json           — degree centrality, core-periphery, modularity, etc.
  output/network_sna_comparison.png     — Figure 2: side-by-side network comparison (static, white bg)
  output/network_degree_dist.png        — degree distribution comparison
  analysis/network_metrics_table.csv    — metrics table for paper

Method reference: paper [7] (Aave DeFi SNA — Borgatti-Everett core-periphery,
  modularity, giant component ratio, degree centrality)

Data:
  analysis/network_edges_erc8004.csv
  analysis/network_edges_a2a.csv
  analysis/network_nodes_erc8004.csv
  analysis/network_nodes_a2a.csv
"""

import csv
import json
import math
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).parent.parent
ANALYSIS = ROOT / "analysis"
OUTPUT = ROOT / "output"

# institution → color
INST_COLORS = {
    "Google":                               "#EA4335",
    "Microsoft":                            "#00A4EF",
    "MetaMask":                             "#E2761B",
    "Ethereum Foundation":                  "#627EEA",
    "Edge and Node / The Graph Protocol":   "#6747ED",
    "Cisco Systems":                        "#00BCEB",
    "Coinbase":                             "#0052FF",
    "Independent":                          "#27AE60",
    "Unknown":                              "#BDC3C7",
}
DEFAULT_COLOR = "#95A5A6"


# ── graph utilities ───────────────────────────────────────────────────────────

def load_graph(case):
    with open(ANALYSIS / f"network_nodes_{case}.csv") as f:
        nodes = {r["id"]: r for r in csv.DictReader(f)}
    with open(ANALYSIS / f"network_edges_{case}.csv") as f:
        edges = list(csv.DictReader(f))
    return nodes, edges


def build_adj(nodes, edges, directed=False):
    """Return adjacency list and degree dict."""
    adj = defaultdict(set)
    degree = Counter()
    for e in edges:
        s, t = e["source"], e["target"]
        if s not in nodes or t not in nodes:
            continue
        adj[s].add(t)
        degree[s] += 1
        if not directed:
            adj[t].add(s)
            degree[t] += 1
    return adj, degree


def connected_components(nodes, adj):
    """Returns list of sets (undirected components)."""
    visited = set()
    components = []
    for node in nodes:
        if node in visited:
            continue
        stack = [node]
        comp = set()
        while stack:
            n = stack.pop()
            if n in visited:
                continue
            visited.add(n)
            comp.add(n)
            for nb in adj.get(n, []):
                if nb not in visited:
                    stack.append(nb)
        components.append(comp)
    return components


def compute_modularity(nodes, edges, institution_field="institution"):
    """
    Simplified Newman modularity Q for institution-based communities.
    Q = sum_c [ L_c/m - (d_c/2m)^2 ]
    where L_c = edges within community c, d_c = sum of degrees in c, m = total edges.
    """
    m = len(edges)
    if m == 0:
        return 0.0

    # Build community map
    community = {nid: data.get(institution_field, "Unknown")
                 for nid, data in nodes.items()}

    # degree per node (undirected): count each edge endpoint once
    degree = Counter()
    for e in edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1

    # L_c: edges within community c
    # d_c: sum of degrees of all nodes in community c (computed directly from node set)
    L = Counter()
    d = Counter()
    for e in edges:
        s, t = e["source"], e["target"]
        cs, ct = community.get(s, "?"), community.get(t, "?")
        if cs == ct:
            L[cs] += 1

    # d_c = sum of node degrees per community (each node counted once)
    for nid, comm in community.items():
        d[comm] += degree.get(nid, 0)

    Q = sum(L[c] / m - (d[c] / (2 * m)) ** 2 for c in set(community.values()))
    return round(Q, 4)


def gini_coefficient(values):
    """Gini coefficient of a list of positive values."""
    arr = sorted(values)
    n = len(arr)
    if n == 0 or sum(arr) == 0:
        return 0.0
    cumsum = 0.0
    for i, v in enumerate(arr):
        cumsum += v * (2 * (i + 1) - n - 1)
    return round(cumsum / (n * sum(arr)), 4)


def compute_metrics(case, nodes, edges, adj, degree):
    """Compute all SNA metrics for one case."""
    n = len(nodes)
    m = len(edges)
    if n == 0:
        return {}

    # Degree stats
    deg_vals = [degree.get(nid, 0) for nid in nodes]
    max_deg = max(deg_vals) if deg_vals else 0
    mean_deg = round(sum(deg_vals) / n, 3)
    std_deg  = round((sum((d - mean_deg)**2 for d in deg_vals) / n) ** 0.5, 3)

    # Normalised degree centrality (max possible = n-1)
    max_norm_dc = max(d / (n - 1) for d in deg_vals) if n > 1 else 0
    mean_norm_dc = round(sum(d / (n - 1) for d in deg_vals) / n, 4) if n > 1 else 0

    # Top-3 contributors by degree
    top3 = sorted(nodes.keys(), key=lambda x: degree.get(x, 0), reverse=True)[:3]
    top3_share = round(sum(degree.get(x, 0) for x in top3) / (2 * m) if m else 0, 4)

    # Components
    comps = connected_components(list(nodes.keys()), adj)
    n_components = len(comps)
    giant = max(comps, key=len) if comps else set()
    giant_ratio = round(len(giant) / n, 4)

    # Density
    max_edges = n * (n - 1) / 2
    density = round(m / max_edges, 4) if max_edges > 0 else 0

    # Gini of degree (concentration)
    gini = gini_coefficient(deg_vals)

    # Modularity (institution-based communities)
    modularity = compute_modularity(nodes, edges)

    # Institution breakdown (by node count)
    inst_counter = Counter(data.get("institution", "Unknown") for data in nodes.values())
    top_inst = inst_counter.most_common(3)

    return {
        "case": case,
        "n_nodes": n,
        "n_edges": m,
        "density": density,
        "mean_degree": mean_deg,
        "std_degree": std_deg,
        "max_degree": max_deg,
        "top3_degree_share": top3_share,
        "top3_nodes": [(nid, degree.get(nid, 0)) for nid in top3],
        "n_components": n_components,
        "giant_component_ratio": giant_ratio,
        "gini_degree": gini,
        "modularity_institution": modularity,
        "top_institutions": top_inst,
    }


# ── Figure 2: network comparison (static spring layout) ──────────────────────

def spring_layout(nodes, edges, iterations=150, k=None):
    """Simple Fruchterman-Reingold spring layout."""
    import random
    random.seed(42)
    pos = {nid: [random.uniform(-1, 1), random.uniform(-1, 1)]
           for nid in nodes}
    n = len(nodes)
    if n == 0:
        return pos
    k_val = k or math.sqrt(1.0 / n)
    t = 0.1  # temperature

    node_list = list(nodes.keys())

    for _ in range(iterations):
        delta = {nid: [0.0, 0.0] for nid in node_list}

        # Repulsion
        for i, u in enumerate(node_list):
            for v in node_list[i+1:]:
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = max(math.sqrt(dx*dx + dy*dy), 0.001)
                f = k_val * k_val / dist
                delta[u][0] += f * dx / dist
                delta[u][1] += f * dy / dist
                delta[v][0] -= f * dx / dist
                delta[v][1] -= f * dy / dist

        # Attraction
        for e in edges:
            u, v = e["source"], e["target"]
            if u not in pos or v not in pos:
                continue
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            dist = max(math.sqrt(dx*dx + dy*dy), 0.001)
            f = dist * dist / k_val
            delta[u][0] -= f * dx / dist
            delta[u][1] -= f * dy / dist
            delta[v][0] += f * dx / dist
            delta[v][1] += f * dy / dist

        # Update with temperature
        for nid in node_list:
            d = math.sqrt(delta[nid][0]**2 + delta[nid][1]**2)
            if d > 0:
                scale = min(d, t) / d
                pos[nid][0] += delta[nid][0] * scale
                pos[nid][1] += delta[nid][1] * scale

        t = max(t * 0.92, 0.001)

    return pos


def draw_network(ax, nodes, edges, pos, degree, title, metrics):
    ax.set_facecolor("white")
    ax.axis("off")
    ax.set_aspect("equal")

    # Draw edges first
    for e in edges:
        s, t = e["source"], e["target"]
        if s not in pos or t not in pos:
            continue
        w = float(e.get("weight", 1))
        lw = min(0.3 + 0.15 * w, 2.0)
        ax.plot([pos[s][0], pos[t][0]], [pos[s][1], pos[t][1]],
                color="#CCCCCC", linewidth=lw, zorder=1, alpha=0.6)

    # Draw nodes
    max_deg = max(degree.values()) if degree else 1
    for nid, data in nodes.items():
        if nid not in pos:
            continue
        x, y = pos[nid]
        inst = data.get("institution", "Unknown")
        color = INST_COLORS.get(inst, DEFAULT_COLOR)
        raw_size = float(data.get("size", 10))
        # Scale node size: 20–300 range mapped to 30–300
        node_size = 30 + 270 * (raw_size / max(float(n.get("size", 10)) for n in nodes.values()))
        ax.scatter(x, y, s=node_size, c=color, zorder=3,
                   edgecolors="#555555", linewidths=0.4, alpha=0.9)

    # Label top 5 nodes
    top5 = sorted(nodes.keys(), key=lambda x: degree.get(x, 0), reverse=True)[:5]
    for nid in top5:
        if nid not in pos:
            continue
        x, y = pos[nid]
        ax.text(x, y + 0.07, nid[:12], ha="center", va="bottom",
                fontsize=6.5, color="#111", zorder=5,
                bbox=dict(boxstyle="round,pad=0.1", fc="white",
                          ec="none", alpha=0.7))

    ax.set_title(title, fontsize=9, fontweight="bold", pad=6)

    # Metrics inset
    txt = (f"N={metrics['n_nodes']} nodes, {metrics['n_edges']} edges\n"
           f"Density={metrics['density']:.3f}  "
           f"Modularity={metrics['modularity_institution']:.3f}\n"
           f"Gini(degree)={metrics['gini_degree']:.3f}  "
           f"Giant={metrics['giant_component_ratio']:.2f}")
    ax.text(0.02, 0.02, txt, transform=ax.transAxes,
            fontsize=7, va="bottom", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="#F8F9FA",
                      ec="#CCCCCC", lw=0.8))


def fig_sna_comparison(nodes_erc, edges_erc, nodes_a2a, edges_a2a,
                        metrics_erc, metrics_a2a):
    print("  Computing layouts (this may take ~10s)...")
    _, deg_erc = build_adj(nodes_erc, edges_erc)
    _, deg_a2a = build_adj(nodes_a2a, edges_a2a)
    pos_erc = spring_layout(nodes_erc, edges_erc, iterations=200, k=0.35)
    pos_a2a = spring_layout(nodes_a2a, edges_a2a, iterations=200, k=0.25)

    fig, (ax_erc, ax_a2a) = plt.subplots(1, 2, figsize=(12, 6))
    fig.patch.set_facecolor("white")

    draw_network(ax_erc, nodes_erc, edges_erc, pos_erc, deg_erc,
                 "ERC-8004 Governance Network\n(Permissionless DAO)",
                 metrics_erc)
    draw_network(ax_a2a, nodes_a2a, edges_a2a, pos_a2a, deg_a2a,
                 "Google A2A Governance Network (top-50)\n(Corporate Hierarchy)",
                 metrics_a2a)

    # Shared institution legend
    seen_insts = set(d.get("institution", "Unknown")
                     for nodes in [nodes_erc, nodes_a2a]
                     for d in nodes.values())
    legend_handles = [
        mpatches.Patch(color=INST_COLORS.get(i, DEFAULT_COLOR), label=i)
        for i in sorted(seen_insts) if i != "Unknown"
    ] + [mpatches.Patch(color=INST_COLORS["Unknown"], label="Unknown")]

    fig.legend(handles=legend_handles, loc="lower center",
               ncol=min(len(legend_handles), 5),
               fontsize=7.5, framealpha=0.9,
               bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    out = OUTPUT / "network_sna_comparison.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved → {out}")


# ── degree distribution ───────────────────────────────────────────────────────

def fig_degree_distribution(nodes_erc, edges_erc, nodes_a2a, edges_a2a):
    _, deg_erc = build_adj(nodes_erc, edges_erc)
    _, deg_a2a = build_adj(nodes_a2a, edges_a2a)

    vals_erc = sorted([deg_erc.get(n, 0) for n in nodes_erc], reverse=True)
    vals_a2a = sorted([deg_a2a.get(n, 0) for n in nodes_a2a], reverse=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("white")
    fig.suptitle("Degree Distribution by Case", fontsize=10, fontweight="bold")

    for ax, vals, label, color in [
        (ax1, vals_erc, f"ERC-8004 (N={len(vals_erc)})", "#627EEA"),
        (ax2, vals_a2a, f"Google A2A top-50 (N={len(vals_a2a)})", "#EA4335"),
    ]:
        ax.set_facecolor("white")
        ax.bar(range(len(vals)), vals, color=color, edgecolor="white", linewidth=0.4)
        ax.set_xlabel("Node rank (by degree)", fontsize=8)
        ax.set_ylabel("Degree", fontsize=8)
        ax.set_title(label, fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        # Annotate top 3
        for i, v in enumerate(vals[:3]):
            nid = sorted(ax1.patches if ax == ax1 else [],
                         key=lambda p: p.get_height(), reverse=True)
            ax.text(i, v + 0.3, str(v), ha="center", va="bottom", fontsize=7.5)

    plt.tight_layout()
    out = OUTPUT / "network_degree_dist.png"
    plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved → {out}")


# ── metrics table ─────────────────────────────────────────────────────────────

def save_metrics_table(metrics_erc, metrics_a2a):
    rows = [
        ("Nodes", metrics_erc["n_nodes"], metrics_a2a["n_nodes"]),
        ("Edges", metrics_erc["n_edges"], metrics_a2a["n_edges"]),
        ("Density", metrics_erc["density"], metrics_a2a["density"]),
        ("Mean degree", metrics_erc["mean_degree"], metrics_a2a["mean_degree"]),
        ("Std degree", metrics_erc["std_degree"], metrics_a2a["std_degree"]),
        ("Max degree", metrics_erc["max_degree"], metrics_a2a["max_degree"]),
        ("Top-3 degree share", metrics_erc["top3_degree_share"], metrics_a2a["top3_degree_share"]),
        ("Gini(degree)", metrics_erc["gini_degree"], metrics_a2a["gini_degree"]),
        ("# Components", metrics_erc["n_components"], metrics_a2a["n_components"]),
        ("Giant component ratio", metrics_erc["giant_component_ratio"], metrics_a2a["giant_component_ratio"]),
        ("Modularity (institution)", metrics_erc["modularity_institution"], metrics_a2a["modularity_institution"]),
    ]

    out = ANALYSIS / "network_metrics_table.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "ERC-8004", "Google A2A (top-50)"])
        for row in rows:
            writer.writerow(row)
    print(f"  Saved → {out}")
    return rows


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading graphs...")
    nodes_erc, edges_erc = load_graph("erc8004")
    nodes_a2a, edges_a2a = load_graph("a2a")

    print("Building adjacency and computing metrics...")
    adj_erc, deg_erc = build_adj(nodes_erc, edges_erc)
    adj_a2a, deg_a2a = build_adj(nodes_a2a, edges_a2a)

    metrics_erc = compute_metrics("ERC-8004", nodes_erc, edges_erc, adj_erc, deg_erc)
    metrics_a2a = compute_metrics("Google-A2A", nodes_a2a, edges_a2a, adj_a2a, deg_a2a)

    # Save JSON
    all_metrics = {"erc8004": metrics_erc, "a2a": metrics_a2a}
    json_path = OUTPUT / "network_metrics.json"
    with open(json_path, "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)
    print(f"  Saved → {json_path}")

    print("\n── ERC-8004 Network Metrics ──")
    for k, v in metrics_erc.items():
        print(f"  {k:35s}: {v}")

    print("\n── Google A2A Network Metrics ──")
    for k, v in metrics_a2a.items():
        print(f"  {k:35s}: {v}")

    print("\nSaving metrics table...")
    rows = save_metrics_table(metrics_erc, metrics_a2a)

    print("\nGenerating figures...")
    print(" Figure 2: SNA comparison...")
    fig_sna_comparison(nodes_erc, edges_erc, nodes_a2a, edges_a2a,
                       metrics_erc, metrics_a2a)
    print(" Degree distribution...")
    fig_degree_distribution(nodes_erc, edges_erc, nodes_a2a, edges_a2a)

    print("\nDone.")


if __name__ == "__main__":
    main()
