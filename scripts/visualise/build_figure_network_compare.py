"""
build_figure_network_compare.py — Side-by-side co-participation network figure.

Produces paper-ready static output (PNG+PDF) and an interactive HTML version.
Uses R2 expanded consensus data with giant-component + isolated-sampling strategy.

Key visual features:
  - ERC shows dense connected network; A2A shows fragmentation (many isolates)
  - Nodes colour-coded by institutional affiliation
  - Large labels on top-N nodes (elbow cutoff by betweenness centrality)
  - Metric overlay panel: Gini, Density, GCR, Network Efficiency

Output:
  output/figures/r2/network_compare.png     300 DPI, paper-ready
  output/figures/r2/network_compare.pdf     Vector, for typesetting
  output/figures/r2/network_compare.html    Interactive vis.js version

Usage:
  uv run python scripts/visualise/build_figure_network_compare.py
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import (ROOT, DATA_ANNOTATED_R1_PROFILES,
    CONSENSUS_ERC, CONSENSUS_A2A, DATA_ANNOTATED_R2_CONSENSUS,
    ANALYSIS_ND_R2_DNA,
    OUTPUT_FIGURES, OUTPUT_INTERACTIVE)
from lib.models import BOTS, is_bot
from lib.colors import ERC_COLORS, A2A_COLORS, CB_PALETTE, COLOR_CARD
from lib.io import load_json

# ── Paths ────────────────────────────────────────────────────────────────────
CONSENSUS_DIR = DATA_ANNOTATED_R2_CONSENSUS
PROFILES_PATH = DATA_ANNOTATED_R1_PROFILES
OUTPUT_DIR = OUTPUT_FIGURES
METRICS_PATH = ANALYSIS_ND_R2_DNA / "dna_metrics.json"

matplotlib.use("Agg")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "figure.dpi": 150,
})

# ── Data loading / network building (reuses R2 logic) ─────────────────────────


def _thread_key_erc(r: dict) -> str | None:
    if r.get("source") == "forum":
        tid = r.get("topic_id")
        return f"forum_{tid}" if tid else None
    pn = r.get("pr_number")
    return f"pr_{pn}" if pn else None


def _thread_key_a2a(r: dict) -> str | None:
    import re
    src = r.get("source", "")
    if "issue" in src:
        n = r.get("issue_number")
        return f"issue_{n}" if n else None
    if "pr" in src or "review" in src:
        n = r.get("pr_number")
        return f"pr_{n}" if n else None
    if "discussion" in src:
        url = r.get("url", "")
        m = re.search(r"/discussions/(\d+)", url)
        return f"discussion_{m.group(1)}" if m else None
    return None


def build_coparticipation(
    records: list[dict], thread_key_fn: Callable
) -> tuple[dict, list]:
    """Build nodes dict and edge list from annotated records."""
    threads: dict[str, set[str]] = defaultdict(set)
    author_counts: Counter = Counter()

    for r in records:
        author = r.get("author", "")
        if is_bot(author):
            continue
        text = (r.get("raw_text") or "").strip()
        if len(text) < 10:
            continue
        key = thread_key_fn(r)
        if key:
            threads[key].add(author)
            author_counts[author] += 1

    edge_weights: Counter = Counter()
    for authors in threads.values():
        author_list = sorted(authors)
        for i in range(len(author_list)):
            for j in range(i + 1, len(author_list)):
                edge = (author_list[i], author_list[j])
                edge_weights[edge] += 1

    nodes = {}
    for author, count in author_counts.items():
        nodes[author] = {
            "id": author, "weight": count,
            "thread_count": sum(1 for a in threads.values() if author in a),
        }

    edges = []
    for (src, tgt), w in edge_weights.items():
        edges.append({"source": src, "target": tgt, "weight": w})

    return nodes, edges


def load_profiles() -> dict[str, dict]:
    if not PROFILES_PATH.exists():
        return {}
    profiles = json.loads(PROFILES_PATH.read_text())
    idx: dict[str, dict] = {}
    for p in profiles:
        idx[p["canonical_handle"]] = p
        if p.get("github_handle"):
            idx[p["github_handle"]] = p
        if p.get("forum_handle"):
            idx[p["forum_handle"]] = p
    return idx


# ── Institution colour assignment ─────────────────────────────────────────────


def assign_colour(
    institution: str, palette: dict[str, str], extra_count: int = 0
) -> str:
    """Exact match → substring match → palette fallback → CB fallback."""
    c = palette.get(institution)
    if c:
        return c
    for key, colour in palette.items():
        if key.lower() in institution.lower() or institution.lower() in key.lower():
            return colour
    # Dynamic fallback for unrecognized institutions
    if institution not in ("Independent", "Unknown"):
        idx = extra_count % len(CB_PALETTE)
        return CB_PALETTE[idx]
    return "#808080"


# ── Elbow cutoff ──────────────────────────────────────────────────────────────


def find_elbow_cutoff(values: list[float], floor: int = 3, cap: int = 30) -> int:
    if len(values) <= floor:
        return len(values)
    sorted_vals = sorted(values, reverse=True)
    rel_diffs = []
    for i in range(len(sorted_vals) - 1):
        if sorted_vals[i] > 0:
            rel_diffs.append((sorted_vals[i] - sorted_vals[i + 1]) / sorted_vals[i])
        else:
            rel_diffs.append(0.0)
    search_start = max(0, floor - 1)
    search_end = min(cap, len(rel_diffs))
    if search_end <= search_start:
        return min(cap, len(sorted_vals))
    segment = rel_diffs[search_start:search_end]
    return search_start + segment.index(max(segment)) + 1


# ── Static figure rendering ───────────────────────────────────────────────────


def _node_size(degree: int, deg_min: int, deg_max: int) -> float:
    """Log-scale node size mapping with aggressive spread (small→tiny, large→big).
    Minimum size bumped ~20% for visibility on white background."""
    if deg_max == deg_min:
        return 40
    log_d = math.log(degree + 1)
    log_min = math.log(deg_min + 1)
    log_max = math.log(deg_max + 1)
    return 28 + 452 * (log_d - log_min) / (log_max - log_min)


def _random_colour(node_id: str, seed: int = 42) -> str:
    """Deterministic random colour from COLOR_CARD for a given node id."""
    import hashlib
    h = hashlib.md5(f"{seed}:{node_id}".encode()).hexdigest()
    idx = int(h, 16) % len(COLOR_CARD)
    return COLOR_CARD[idx]


def _deoverlap_labels(
    ax: plt.Axes,
    label_positions: dict[str, tuple[float, float]],
    graph_center: tuple[float, float],
    label_texts: dict[str, str],
    font_size: int = 9,
) -> dict[str, tuple[float, float]]:
    """Iteratively repel overlapping labels away from each other.

    Returns adjusted positions (does NOT draw — caller draws with returned positions).
    """
    if len(label_positions) <= 1:
        return dict(label_positions)

    # Estimate label dimensions in data coordinates
    # Approx: each char ≈ font_size * 0.5 points wide, label has ~15 chars max + newline
    # Convert points to data coordinates later via axis transform
    # We'll work in display (pixel) space for overlap detection
    renderer = ax.figure.canvas.get_renderer()

    # Convert data positions to display (pixel) positions
    disp_positions = {}
    for node, (x, y) in label_positions.items():
        disp = ax.transData.transform((x, y))
        disp_positions[node] = np.array(disp)

    # Estimate bbox size in pixels for each label
    # Each line ~ 20 chars max, 2 lines → ~40 chars total
    # font_size=9 → ~6px per char width, ~12px per line height
    label_sizes = {}
    for node, text in label_texts.items():
        lines = text.split("\n")
        max_chars = max(len(l) for l in lines)
        n_lines = len(lines)
        w = max_chars * font_size * 0.52 + 10  # +padding from bbox
        h = n_lines * font_size * 1.6 + 8
        label_sizes[node] = np.array([w, h])

    # Iterative repulsion
    positions = dict(disp_positions)
    n_iter = 80
    for iteration in range(n_iter):
        moved = False
        nodes = list(positions.keys())
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                ni, nj = nodes[i], nodes[j]
                pi, pj = positions[ni], positions[nj]
                si, sj = label_sizes[ni], label_sizes[nj]

                # Check overlap: distance between centers < sum of half-sizes
                dist = np.linalg.norm(pi - pj)
                min_dist = (np.linalg.norm(si) + np.linalg.norm(sj)) / 2 * 0.85

                if dist < min_dist and dist > 0.01:
                    # Push apart
                    direction = (pi - pj) / dist
                    push = (min_dist - dist) * 0.5 + 2.0  # 2px extra margin
                    # Decay over iterations
                    decay = max(0.1, 1.0 - iteration / n_iter)
                    push *= decay
                    positions[ni] = pi + direction * push
                    positions[nj] = pj - direction * push
                    moved = True

        if not moved:
            break

    # Convert back to data coordinates
    result = {}
    for node, disp in positions.items():
        data = ax.transData.inverted().transform(disp)
        result[node] = (float(data[0]), float(data[1]))

    return result


def render_static_figure(
    erc_G: nx.Graph,
    erc_label_nodes: set[str],
    erc_isolate_nodes: set[str],
    a2a_G: nx.Graph,
    a2a_isolate_nodes: set[str],
    a2a_label_nodes: set[str],
    profiles_idx: dict[str, dict],
    erc_metrics: dict,
    a2a_metrics: dict,
    erc_top_authors: list[str],
    a2a_top_authors: list[str],
    pos_erc: dict | None = None,
    pos_a2a: dict | None = None,
) -> Path:
    """Render side-by-side static network figure with matplotlib.

    Uses vis.js ForceAtlas2 positions when provided, otherwise falls back
    to spring_layout (ERC) / spring+ring (A2A).
    """

    fig, (ax_l, ax_r) = plt.subplots(
        1, 2, figsize=(20, 10),
        constrained_layout=True,
    )
    fig.patch.set_facecolor("#FFFFFF")

    # ── Compute / use layouts ──────────────────────────────────────────────
    if pos_erc is None:
        pos_erc = nx.spring_layout(
            erc_G, k=2.0, iterations=500, seed=42, weight=None, scale=3.5,
        )
    else:
        # Ensure all nodes have positions (fill missing with spring fallback)
        missing = set(erc_G.nodes()) - set(pos_erc.keys())
        if missing:
            sub = erc_G.subgraph(missing)
            fallback = nx.spring_layout(sub, k=2.0, iterations=200, seed=42, scale=3.5)
            for n, xy in fallback.items():
                pos_erc[n] = np.array(xy)

    if pos_a2a is None:
        a2a_connected_graphs = []
        a2a_isolated_list = []
        for comp in nx.connected_components(a2a_G):
            if len(comp) > 1:
                a2a_connected_graphs.append(a2a_G.subgraph(comp).copy())
            else:
                a2a_isolated_list.extend(comp)
        giant = max(a2a_connected_graphs, key=lambda g: g.number_of_nodes()) if a2a_connected_graphs else nx.Graph()
        pos_a2a = {}
        if giant.number_of_nodes() > 1:
            pos_a2a.update(nx.spring_layout(giant, k=1.6, iterations=500, seed=42, weight=None, scale=2.5))
        small_comp_nodes = []
        for g in a2a_connected_graphs:
            if g.number_of_nodes() != giant.number_of_nodes():
                small_comp_nodes.extend(g.nodes())
        if small_comp_nodes:
            rng = np.random.RandomState(42)
            for i, node in enumerate(small_comp_nodes):
                angle = 2 * math.pi * i / len(small_comp_nodes) + rng.uniform(-0.1, 0.1)
                radius = rng.uniform(2.8, 3.8)
                pos_a2a[node] = np.array([radius * math.cos(angle), radius * math.sin(angle)])
        if a2a_isolated_list:
            rng = np.random.RandomState(42)
            for node in a2a_isolated_list:
                angle = rng.uniform(0, 2 * math.pi)
                radius = rng.uniform(4.0, 8.0)
                pos_a2a[node] = np.array([radius * math.cos(angle), radius * math.sin(angle)])

    degrees_erc = dict(erc_G.degree())
    deg_max_erc = max(degrees_erc.values()) if degrees_erc else 1
    deg_min_erc = min(degrees_erc.values()) if degrees_erc else 0

    degrees_a2a = dict(a2a_G.degree())
    deg_max_a2a = max(degrees_a2a.values()) if degrees_a2a else 1
    deg_min_a2a = min(degrees_a2a.values()) if degrees_a2a else 0

    # Compute graph centers for label de-overlap
    erc_center = np.mean([pos_erc[n] for n in erc_G.nodes() if n in pos_erc], axis=0)

    # ── Draw ERC ──────────────────────────────────────────────────────────
    ax_l.set_facecolor("#FFFFFF")

    # Edges
    nx.draw_networkx_edges(
        erc_G, pos_erc, ax=ax_l,
        edge_color="#B0C4DE", alpha=0.18, width=0.5,
    )

    # ALL non-label nodes, coloured randomly from COLOR_CARD
    erc_nonlabel = set(erc_G.nodes()) - erc_label_nodes
    if erc_nonlabel:
        nnl_list = sorted(erc_nonlabel)
        nl_colours = [_random_colour(n, seed=1) for n in nnl_list]
        nl_sizes = [_node_size(degrees_erc.get(n, 1), deg_min_erc, deg_max_erc)
                    for n in nnl_list]
        # ERC isolates among non-labels: slightly larger
        erc_iso_nl = erc_isolate_nodes - erc_label_nodes
        for i, n in enumerate(nnl_list):
            if n in erc_iso_nl:
                nl_sizes[i] *= 0.55
                nl_colours[i] = nl_colours[i]  # same colour, just larger
        nx.draw_networkx_nodes(
            erc_G, pos_erc, ax=ax_l,
            nodelist=nnl_list,
            node_size=nl_sizes,
            node_color=nl_colours,
            edgecolors="#FFFFFF",
            linewidths=0.3,
            alpha=0.85,
        )

    # Label nodes (larger, bold border, also coloured from COLOR_CARD)
    if erc_label_nodes:
        label_nodes_list = sorted(erc_label_nodes, key=lambda n: -degrees_erc.get(n, 0))
        label_colours = [_random_colour(n, seed=1) for n in label_nodes_list]
        nx.draw_networkx_nodes(
            erc_G, pos_erc, ax=ax_l,
            nodelist=label_nodes_list,
            node_size=[_node_size(degrees_erc.get(n, 1), deg_min_erc, deg_max_erc) * 1.3
                       for n in label_nodes_list],
            node_color=label_colours,
            edgecolors="#333333",
            linewidths=2.5,
            alpha=1.0,
        )

    # Labels with de-overlap
    erc_labels = {}
    for n in erc_label_nodes:
        p = profiles_idx.get(n, {})
        display = p.get("display_name", n)
        inst = p.get("institution_final", "Unknown")
        inst_short = inst.split("/")[0].strip()[:20]
        erc_labels[n] = f"{display}\n({inst_short})"

    # Get base positions from pos_erc, then de-overlap
    erc_base_pos = {n: (float(pos_erc[n][0]), float(pos_erc[n][1]))
                    for n in erc_label_nodes if n in pos_erc}
    erc_adj_pos = _deoverlap_labels(
        ax_l, erc_base_pos, (float(erc_center[0]), float(erc_center[1])),
        erc_labels, font_size=9,
    )

    nx.draw_networkx_labels(
        erc_G, erc_adj_pos, erc_labels, ax=ax_l,
        font_size=9, font_weight="bold", font_color="#1a1a2e",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.75,
                  edgecolor="#808080", linewidth=0.5),
    )

    # ── Draw A2A ──────────────────────────────────────────────────────────
    ax_r.set_facecolor("#FFFFFF")

    a2a_center = np.mean([pos_a2a[n] for n in a2a_G.nodes() if n in pos_a2a], axis=0)

    # Edges
    nx.draw_networkx_edges(
        a2a_G, pos_a2a, ax=ax_r,
        edge_color="#B0C4DE", alpha=0.18, width=0.5,
    )

    # ALL non-label nodes, coloured randomly from COLOR_CARD
    a2a_nonlabel = set(a2a_G.nodes()) - a2a_label_nodes
    if a2a_nonlabel:
        nnl_list = sorted(a2a_nonlabel)
        nl_colours = [_random_colour(n, seed=2) for n in nnl_list]
        nl_sizes = [_node_size(degrees_a2a.get(n, 1), deg_min_a2a, deg_max_a2a)
                    for n in nnl_list]
        # Isolates among non-labels: slightly larger
        for i, n in enumerate(nnl_list):
            if n in a2a_isolate_nodes:
                nl_sizes[i] *= 0.40
        nx.draw_networkx_nodes(
            a2a_G, pos_a2a, ax=ax_r,
            nodelist=nnl_list,
            node_size=nl_sizes,
            node_color=nl_colours,
            edgecolors="#FFFFFF",
            linewidths=0.3,
            alpha=0.85,
        )

    # Label nodes
    if a2a_label_nodes:
        label_nodes_list = sorted(a2a_label_nodes, key=lambda n: -degrees_a2a.get(n, 0))
        label_colours = [_random_colour(n, seed=2) for n in label_nodes_list]
        nx.draw_networkx_nodes(
            a2a_G, pos_a2a, ax=ax_r,
            nodelist=label_nodes_list,
            node_size=[_node_size(degrees_a2a.get(n, 1), deg_min_a2a, deg_max_a2a) * 1.3
                       for n in label_nodes_list],
            node_color=label_colours,
            edgecolors="#333333",
            linewidths=2.5,
            alpha=1.0,
        )

    a2a_labels = {}
    for n in a2a_label_nodes:
        p = profiles_idx.get(n, {})
        display = p.get("display_name", n)
        inst = p.get("institution_final", "Unknown")
        inst_short = inst.split("/")[0].strip()[:20]
        a2a_labels[n] = f"{display}\n({inst_short})"

    a2a_base_pos = {n: (float(pos_a2a[n][0]), float(pos_a2a[n][1]))
                    for n in a2a_label_nodes if n in pos_a2a}
    a2a_adj_pos = _deoverlap_labels(
        ax_r, a2a_base_pos, (float(a2a_center[0]), float(a2a_center[1])),
        a2a_labels, font_size=9,
    )

    nx.draw_networkx_labels(
        a2a_G, a2a_adj_pos, a2a_labels, ax=ax_r,
        font_size=9, font_weight="bold", font_color="#1a1a2e",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.75,
                  edgecolor="#808080", linewidth=0.5),
    )

    # ── Metric overlays (bottom-left corner of each panel) ──────────────────
    metric_text_erc = (
        f"Gini: {erc_metrics['degree_gini']:.3f}    "
        f"GCR: {erc_metrics['giant_component_ratio']:.3f}\n"
        f"Nodes: {erc_metrics['n_actors']}    "
        f"Density: {erc_metrics['density']:.4f}\n"
        f"Efficiency: {erc_metrics['network_efficiency']:.4f}    "
        f"{erc_metrics['n_components']} components ({erc_metrics.get('isolate_pct', '?')}% isolates)"
    )
    ax_l.text(
        0.02, 0.02, metric_text_erc, transform=ax_l.transAxes,
        fontsize=8, fontfamily="monospace", verticalalignment="bottom",
        color="#333333",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.92,
                  edgecolor="#999999"),
    )

    metric_text_a2a = (
        f"Gini: {a2a_metrics['degree_gini']:.3f}    "
        f"GCR: {a2a_metrics['giant_component_ratio']:.3f}\n"
        f"Nodes: {a2a_metrics['n_actors']}    "
        f"Density: {a2a_metrics['density']:.4f}\n"
        f"Efficiency: {a2a_metrics['network_efficiency']:.4f}    "
        f"{a2a_metrics['n_components']} components ({a2a_metrics.get('isolate_pct', '?')}% isolates)"
    )
    ax_r.text(
        0.02, 0.02, metric_text_a2a, transform=ax_r.transAxes,
        fontsize=8, fontfamily="monospace", verticalalignment="bottom",
        color="#333333",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.92,
                  edgecolor="#999999"),
    )

    # NOTE: Institution legends removed per user request.

    ax_l.axis("off")
    ax_r.axis("off")

    # Shared figure title
    fig.suptitle("Co-Participation Network (Left: ERC-8004, Right: Google A2A)",
                 fontsize=14, fontweight="bold", color="#1a1a2e", y=0.98)

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "network_compare.png"
    pdf_path = OUTPUT_DIR / "network_compare.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="#FFFFFF")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig)

    print(f"  Static figure → {png_path}")
    print(f"  Static figure → {pdf_path}")
    return png_path


# ── Interactive HTML rendering ────────────────────────────────────────────────


def render_html(
    erc_nodes: list[dict], erc_edges: list[dict],
    a2a_nodes: list[dict], a2a_edges: list[dict],
    erc_metrics: dict, a2a_metrics: dict,
) -> Path:
    """Render interactive side-by-side vis.js HTML."""

    erc_vn = json.dumps(erc_nodes, ensure_ascii=False)
    erc_ve = json.dumps(erc_edges, ensure_ascii=False)
    a2a_vn = json.dumps(a2a_nodes, ensure_ascii=False)
    a2a_ve = json.dumps(a2a_edges, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DAO vs Corporate Governance — Co-Participation Networks (R2 Expanded)</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
         background:#1a1a2e; color:#eee; }}
  #header {{ padding:12px 20px; background:#0c1445; display:flex; align-items:center; justify-content:space-between; }}
  #header h2 {{ margin:0; font-size:15px; color:#e2e8f0; }}
  #header .meta {{ font-size:11px; color:#94a3b8; }}
  #compare {{ display:flex; height:calc(100vh - 52px); gap:2px; background:#111; }}
  .panel {{ flex:1; display:flex; flex-direction:column; background:#1a1a2e; overflow:hidden; }}
  .panel-header {{ padding:8px 14px; background:#16213e; }}
  .panel-header h3 {{ margin:0; font-size:13px; color:#7dd3fc; }}
  .panel-header .sub {{ font-size:10px; color:#94a3b8; margin-top:2px; }}
  .panel-legend {{ padding:4px 14px; background:#0f3460; display:flex; flex-wrap:wrap; gap:5px; }}
  .panel-network {{ flex:1; min-height:0; }}
  .legend-item {{ display:flex; align-items:center; gap:4px; font-size:10px; }}
  .dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
  .metrics {{ padding:4px 14px; background:#0c1445; font-size:10px; font-family:monospace;
              display:flex; gap:24px; color:#aaa; }}
</style>
</head>
<body>
<div id="header">
  <h2>Governance Structure Comparison — Co-Participation Networks (R2 Expanded Data)</h2>
  <span class="meta">Node size = degree &bull; Colour = institution &bull; Thick border = top contributor &bull; Hover for details</span>
</div>
<div id="compare">
  <div class="panel">
    <div class="panel-header">
      <h3>Case A — ERC-8004 Cluster (DAO / Open Governance)</h3>
      <div class="sub">{len(erc_nodes)} participants &bull; {len(erc_edges)} co-participation edges &bull; {erc_metrics.get('n_components','?')} components</div>
    </div>
    <div class="metrics">
      <span>Gini: {erc_metrics['degree_gini']:.3f}</span>
      <span>Density: {erc_metrics['density']:.4f}</span>
      <span>GCR: {erc_metrics['giant_component_ratio']:.3f}</span>
      <span>Efficiency: {erc_metrics['network_efficiency']:.4f}</span>
      <span>Modularity: {erc_metrics['louvain_modularity']:.3f}</span>
    </div>
    <div class="panel-network" id="net-erc"></div>
  </div>
  <div class="panel">
    <div class="panel-header">
      <h3>Case B — Google A2A (Corporate / Hierarchical Governance)</h3>
      <div class="sub">{len(a2a_nodes)} participants &bull; {len(a2a_edges)} co-participation edges &bull; {a2a_metrics.get('n_components','?')} components</div>
    </div>
    <div class="metrics">
      <span>Gini: {a2a_metrics['degree_gini']:.3f}</span>
      <span>Density: {a2a_metrics['density']:.4f}</span>
      <span>GCR: {a2a_metrics['giant_component_ratio']:.3f}</span>
      <span>Efficiency: {a2a_metrics['network_efficiency']:.4f}</span>
      <span>Modularity: {a2a_metrics['louvain_modularity']:.3f}</span>
    </div>
    <div class="panel-network" id="net-a2a"></div>
  </div>
</div>
<script>
var opts = {{
  nodes: {{ shape:"dot", font:{{color:"#fff",size:11,strokeWidth:2,strokeColor:"#1a1a2e"}} }},
  edges: {{ smooth:{{type:"dynamic"}}, color:"#888888" }},
  physics: {{
    solver:"forceAtlas2Based",
    forceAtlas2Based:{{gravitationalConstant:-50,springLength:150,damping:0.4}},
    stabilization:{{iterations:300}}
  }},
  interaction:{{hover:true,tooltipDelay:80}}
}};
new vis.Network(document.getElementById("net-erc"),
  {{nodes: new vis.DataSet({erc_vn}), edges: new vis.DataSet({erc_ve})}}, opts);
new vis.Network(document.getElementById("net-a2a"),
  {{nodes: new vis.DataSet({a2a_vn}), edges: new vis.DataSet({a2a_ve})}}, opts);
</script>
</body>
</html>"""

    html_path = OUTPUT_DIR / "network_compare.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  Interactive HTML → {html_path}")
    return html_path


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print("=== Building Side-by-Side Co-Participation Network Figure ===\n")

    # ── Load data ─────────────────────────────────────────────────────────
    profiles_idx = load_profiles()
    print(f"Loaded {len(profiles_idx)} profile handles")

    erc_records = json.loads(
        (CONSENSUS_DIR / "erc_annotations.json").read_text()
    )
    a2a_records = json.loads(
        (CONSENSUS_DIR / "a2a_annotations.json").read_text()
    )
    print(f"Records: ERC={len(erc_records)}, A2A={len(a2a_records)}")

    # ── Load metrics ──────────────────────────────────────────────────────
    if METRICS_PATH.exists():
        all_metrics = json.loads(METRICS_PATH.read_text())
        erc_metrics = all_metrics["erc"]
        a2a_metrics = all_metrics["a2a"]
        print("Loaded metrics from build_network_r2.py output")
    else:
        print("WARNING: metrics file not found. Run build_network_r2.py first.")
        sys.exit(1)

    # ── Build networks ────────────────────────────────────────────────────
    erc_nodes, erc_edges = build_coparticipation(erc_records, _thread_key_erc)
    a2a_nodes, a2a_edges = build_coparticipation(a2a_records, _thread_key_a2a)
    print(f"Networks: ERC={len(erc_nodes)}n/{len(erc_edges)}e, "
          f"A2A={len(a2a_nodes)}n/{len(a2a_edges)}e")

    # ── Build NetworkX graphs ─────────────────────────────────────────────
    G_erc = nx.Graph()
    for nid in erc_nodes:
        G_erc.add_node(nid)
    for e in erc_edges:
        G_erc.add_edge(e["source"], e["target"], weight=e["weight"])

    G_a2a = nx.Graph()
    for nid in a2a_nodes:
        G_a2a.add_node(nid)
    for e in a2a_edges:
        G_a2a.add_edge(e["source"], e["target"], weight=e["weight"])

    # ── Identify giant components & isolates ──────────────────────────────
    erc_comps = list(nx.connected_components(G_erc))
    erc_giant = max(erc_comps, key=len) if erc_comps else set()
    print(f"ERC: {len(erc_comps)} components, giant={len(erc_giant)} nodes")

    a2a_comps = list(nx.connected_components(G_a2a))
    a2a_giant = max(a2a_comps, key=len) if a2a_comps else set()
    a2a_isolates = {comp.pop() for comp in a2a_comps if len(comp) == 1}
    print(f"A2A: {len(a2a_comps)} components, giant={len(a2a_giant)} nodes, "
          f"isolates={len(a2a_isolates)}")

    # ── Determine label nodes ─────────────────────────────────────────────
    # ERC: user-specified key contributors
    erc_top_authors = ["MarcoMetaMask", "spengrah", "pcarranzav"]
    # Filter to nodes actually present in the graph
    erc_top_authors = [n for n in erc_top_authors if n in G_erc.nodes()]
    print(f"  ERC labels (user-specified): {', '.join(erc_top_authors)}")

    # A2A: top 5 from TSC institutions by betweenness centrality
    bc_a2a = nx.betweenness_centrality(G_a2a, normalized=True)
    tsc_institutions = {
        "Google", "Microsoft", "Cisco", "Cisco Systems", "Red Hat",
        "IBM", "IBM Research", "Intuit", "CNCF", "Apoco", "Weave", "AGENIUM",
    }
    tsc_candidates = sorted(
        [n for n in G_a2a.nodes()
         if profiles_idx.get(n, {}).get("institution_final", "") in tsc_institutions],
        key=lambda n: -bc_a2a.get(n, 0),
    )
    a2a_top_authors = tsc_candidates[:5]
    print(f"  A2A labels (TSC top-5): {', '.join(a2a_top_authors)}")

    # ── Compute isolate percentages for metrics overlay ──────────────────
    # (use len(a2a_isolates) which was already computed above, before comp.pop() mutates sets)
    erc_iso_count = sum(1 for comp in erc_comps if len(comp) == 1)
    erc_iso_nodes = {comp.pop() for comp in erc_comps if len(comp) == 1}
    erc_metrics["isolate_pct"] = round(erc_iso_count / erc_metrics["n_actors"] * 100)
    a2a_metrics["isolate_pct"] = round(len(a2a_isolates) / a2a_metrics["n_actors"] * 100)
    print(f"Isolate counts: ERC={erc_iso_count} ({erc_metrics['isolate_pct']}%), "
          f"A2A={len(a2a_isolates)} ({a2a_metrics['isolate_pct']}%)")

    # ── Load vis.js positions ──────────────────────────────────────────────
    erc_pos_path = OUTPUT_DIR / "vis_positions_erc.json"
    a2a_pos_path = OUTPUT_DIR / "vis_positions_a2a.json"
    pos_erc = None
    pos_a2a = None
    if erc_pos_path.exists() and a2a_pos_path.exists():
        print("Loading vis.js positions...")
        raw_erc = json.loads(erc_pos_path.read_text())
        raw_a2a = json.loads(a2a_pos_path.read_text())
        # Convert {node: {x, y}} → {node: np.array([x, y])}
        pos_erc = {n: np.array([v["x"], v["y"]]) for n, v in raw_erc.items()}
        pos_a2a = {n: np.array([v["x"], v["y"]]) for n, v in raw_a2a.items()}
        print(f"  ERC positions: {len(pos_erc)} nodes, A2A: {len(pos_a2a)} nodes")
    else:
        print("WARNING: vis.js positions not found, falling back to spring_layout.")
        print(f"  Run: uv run python scripts/visualise/extract_vis_positions.py")

    # ── Render static figure (ALL nodes, no sampling) ─────────────────────
    print(f"\n[Rendering static figure — ERC: {len(G_erc.nodes())}n/{len(G_erc.edges())}e, "
          f"A2A: {len(G_a2a.nodes())}n/{len(G_a2a.edges())}e]")
    render_static_figure(
        erc_G=G_erc,
        erc_label_nodes=set(erc_top_authors),
        erc_isolate_nodes=erc_iso_nodes,
        a2a_G=G_a2a,
        a2a_isolate_nodes=a2a_isolates,
        a2a_label_nodes=set(a2a_top_authors),
        profiles_idx=profiles_idx,
        erc_metrics=erc_metrics,
        a2a_metrics=a2a_metrics,
        erc_top_authors=erc_top_authors,
        a2a_top_authors=a2a_top_authors,
        pos_erc=pos_erc,
        pos_a2a=pos_a2a,
    )

    # ── Render interactive HTML ───────────────────────────────────────────
    print("\n[Rendering interactive HTML]")

    # Build vis.js node objects for ERC
    erc_vis_nodes = []
    degrees_erc = dict(G_erc.degree())
    for node in sorted(G_erc.nodes()):
        p = profiles_idx.get(node, {})
        inst = p.get("institution_final", "Unknown")
        colour = assign_colour(inst, ERC_COLORS, 0)
        is_label = node in erc_top_authors
        size = _node_size(degrees_erc.get(node, 0), 0, max(degrees_erc.values(), default=1))
        label = p.get("display_name", node) if is_label else ""
        erc_vis_nodes.append({
            "id": node,
            "label": label,
            "title": f"{p.get('display_name', node)}\nInstitution: {inst}\nDegree: {degrees_erc.get(node, 0)}",
            "color": {"background": colour, "border": "#333" if is_label else "#888"},
            "borderWidth": 3 if is_label else 1,
            "size": size * 1.3 if is_label else size,
            "font": {"size": 12, "color": "#fff", "strokeWidth": 3, "strokeColor": "#1a1a2e"} if is_label else {"size": 0},
        })

    erc_vis_edges = []
    for e in erc_edges:
        w = e["weight"]
        erc_vis_edges.append({
            "from": e["source"], "to": e["target"],
            "width": max(0.3, min(3, 0.2 * math.log(w + 1))),
            "title": f"co-participation: {w} threads",
        })

    # Build vis.js node objects for A2A (full network for HTML)
    a2a_vis_nodes = []
    degrees_a2a = dict(G_a2a.degree())
    for node in sorted(G_a2a.nodes()):
        p = profiles_idx.get(node, {})
        inst = p.get("institution_final", "Unknown")
        colour = assign_colour(inst, A2A_COLORS, 0)
        is_label = node in a2a_top_authors
        is_isolate = node in a2a_isolates
        deg = degrees_a2a.get(node, 0)
        size = _node_size(deg, 0, max(degrees_a2a.values(), default=1))
        if is_isolate:
            size *= 0.4
            colour = colour + "60"  # add alpha hex
        label = p.get("display_name", node) if is_label else ""
        a2a_vis_nodes.append({
            "id": node,
            "label": label,
            "title": f"{p.get('display_name', node)}\nInstitution: {inst}\nDegree: {deg}" +
                     ("\n[ISOLATE]" if is_isolate else ""),
            "color": {"background": colour, "border": "#333" if is_label else "#888"},
            "borderWidth": 3 if is_label else 1,
            "size": size * 1.3 if is_label else size,
            "font": {"size": 12, "color": "#fff", "strokeWidth": 3, "strokeColor": "#1a1a2e"} if is_label else {"size": 0},
        })

    a2a_vis_edges = []
    for e in a2a_edges:
        w = e["weight"]
        a2a_vis_edges.append({
            "from": e["source"], "to": e["target"],
            "width": max(0.3, min(3, 0.2 * math.log(w + 1))),
            "title": f"co-participation: {w} threads",
        })

    render_html(erc_vis_nodes, erc_vis_edges, a2a_vis_nodes, a2a_vis_edges,
                erc_metrics, a2a_metrics)

    print("\nDone. Outputs in:", str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
