"""Generate all paper figures for paper-acm/.

Primary output: output/figures/
Copy destination: paper-acm/ (for LaTeX inclusion)

Run:
    uv run python scripts/visualise/build_paper_figures.py
"""
from __future__ import annotations

import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from dateutil import parser as dateparser
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "paper-acm"
OUTPUT_FIGS = ROOT / "output" / "figures"
TD = ROOT / "output" / "topic_discovery"
ND = ROOT / "output" / "network_discourse"
ANALYSIS = ROOT / "analysis"
ANNOTATED = ROOT / "data" / "annotated" / "annotated_records.json"

# ── Colour palette ────────────────────────────────────────────────────────────
P1 = "#a30543"   # deep crimson  → A2A
P2 = "#f36f43"   # orange
P3 = "#fbda83"   # yellow
P4 = "#e9f4a3"   # light yellow-green
P5 = "#80cba4"   # sage green
P6 = "#4965b0"   # blue/indigo   → ERC-8004

ERC_COLOR = P6
A2A_COLOR = P1
SEED = 42

INST_PALETTE = {
    "Google":               P1,
    "MetaMask":             P2,
    "Ethereum Foundation":  P6,
    "Coinbase":             P5,
    "Microsoft":            P3,
    "AWS":                  P4,
    "Others":               "#c0bdb8",  # Independent + Unknown merged
}

def _inst_color(institution: str) -> str:
    """Normalize Independent/Unknown → Others, then look up palette."""
    key = institution if institution in INST_PALETTE else "Others"
    return INST_PALETTE[key]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
})


def _save(fig, stem: str) -> None:
    """Save PDF+PNG to output/figures/ and copy both to paper-acm/."""
    OUTPUT_FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        out = OUTPUT_FIGS / f"{stem}.{ext}"
        fig.savefig(out)
        shutil.copy2(out, PAPER_DIR / f"{stem}.{ext}")


# ── Figure: BERTopic divergence (enlarged font) ───────────────────────────────

def fig_bertopic_divergence() -> None:
    df = pd.read_csv(TD / "comparative_discourse" / "divergence_table.csv")
    df = df.sort_values("abs_diff", ascending=True)
    df["signed"] = df["erc8004_pct"] - df["a2a_pct"]
    df["short"] = df.apply(
        lambda r: f"T{int(r.topic_id)}: "
                  + ", ".join(r.keywords.split(", ")[:3]),
        axis=1,
    )

    fig, ax = plt.subplots(figsize=(7.0, 5.6))
    colors = [ERC_COLOR if v > 0 else A2A_COLOR for v in df["signed"]]
    ax.barh(df["short"], df["signed"], color=colors, edgecolor="white",
            linewidth=0.5)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("ERC-8004 share − A2A share (pp)")
    ax.set_title("BERTopic cross-case divergence (JSD = 0.288)")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=ERC_COLOR, label="ERC-8004 dominant"),
        Patch(color=A2A_COLOR, label="A2A dominant"),
    ], loc="lower right", frameon=False)

    _save(fig, "fig-bertopic-divergence")
    plt.close(fig)


# ── Figure: CryptoBERT topic frequency ────────────────────────────────────────

def fig_cryptobert_frequency() -> None:
    data = json.loads((TD / "crypto_bert" / "topics.json").read_text())
    # exclude noise; sort ascending so longest bar is at top
    topics = sorted(data["topics"], key=lambda t: t["pct"])

    labels = [
        f"T{t['id']}: " + ", ".join(t["keywords"][:3])
        for t in topics
    ]
    pcts = [t["pct"] for t in topics]

    # sequential palette: light → dark blue
    cmap_seq = mcolors.LinearSegmentedColormap.from_list(
        "cb_seq", [P4, P5, P6], N=256
    )
    n = len(pcts)
    bar_colors = [mcolors.to_hex(cmap_seq(v)) for v in np.linspace(0.2, 0.9, n)]

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    bars = ax.barh(labels, pcts, color=bar_colors, edgecolor="white", linewidth=0.5)
    for bar, pct in zip(bars, pcts):
        ax.text(pct + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%", va="center", fontsize=10)
    ax.set_xlabel("Share of ERC-8004 records (%)")
    ax.set_title(
        f"CryptoBERT topic frequency — ERC-8004 (N={data['n_records']}, "
        f"noise {data['noise_rate_pct']:.1f}% excluded)"
    )
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.set_xlim(0, max(pcts) * 1.28)

    _save(fig, "fig-cryptobert-frequency")
    plt.close(fig)


# ── Figure: combined thematic heatmap + butterfly (landscape) ─────────────────

def fig_combined_heatmap_butterfly() -> None:
    # ---- build heatmap data ----
    coded = json.loads((TD / "thematic_lm" / "coded_records.json").read_text())
    rec_df = pd.DataFrame(coded)

    def case_of(rid: str) -> str:
        rid_lower = rid.lower()
        if (rid_lower.startswith("erc") or "forum" in rid_lower
                or "ethereum/ercs" in rid_lower or "ethereum/eips" in rid_lower):
            return "ERC-8004"
        return "Google-A2A"

    rec_df["case"] = rec_df["record_id"].map(case_of)
    rec_df = rec_df[rec_df["theme_id"].notna()]
    total = rec_df.groupby("case").size()
    counts = rec_df.groupby(["case", "theme_id"]).size().unstack(fill_value=0)
    pct_heat = (counts.divide(total, axis=0) * 100.0).T

    themes = json.loads((TD / "thematic_lm" / "themes.json").read_text())
    label_map = {t["theme_id"]: t["label"] for t in themes}

    erc_col = [c for c in pct_heat.columns if "ERC" in c][0]
    a2a_col = [c for c in pct_heat.columns if c != erc_col][0]
    pct_heat["delta"] = pct_heat[erc_col] - pct_heat[a2a_col]
    pct_heat = pct_heat.sort_values("delta", ascending=False)
    theme_order = pct_heat.index.tolist()

    short_labels = [
        f"{tid}: {label_map.get(tid, tid)}" for tid in theme_order
    ]
    n_themes = len(theme_order)

    # ---- butterfly data (aligned to same theme order) ----
    df_but = pd.read_csv(ND / "sociosemantic" / "theme_actor_comparison.csv")
    df_but = df_but.set_index("theme_id")
    erc_pct_but = [
        float(df_but.loc[tid, "erc8004_pct"]) if tid in df_but.index else 0.0
        for tid in theme_order
    ]
    a2a_pct_but = [
        float(df_but.loc[tid, "a2a_pct"]) if tid in df_but.index else 0.0
        for tid in theme_order
    ]

    # ---- layout ----
    fig, (ax_heat, ax_but) = plt.subplots(
        1, 2,
        figsize=(15, max(7, n_themes * 0.55)),
        gridspec_kw={"width_ratios": [1, 2]},
    )

    # -- heatmap --
    mat = pct_heat[[erc_col, a2a_col]].values
    cmap_heat = mcolors.LinearSegmentedColormap.from_list(
        "heat_pal", ["#ffffff", P5, P6], N=256
    )
    im = ax_heat.imshow(mat, cmap=cmap_heat, vmin=0, vmax=35, aspect="auto")
    ax_heat.set_xticks([0, 1])
    ax_heat.set_xticklabels(["ERC-8004", "Google A2A"])
    ax_heat.set_yticks(range(n_themes))
    ax_heat.set_yticklabels(short_labels)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat[i, j]
            txt_color = "white" if val > 20 else "black"
            ax_heat.text(j, i, f"{val:.1f}", ha="center", va="center",
                         color=txt_color, fontsize=9)
    ax_heat.set_title("Record share (%)  ·  JSD = 0.216", pad=8)
    cbar = fig.colorbar(im, ax=ax_heat, shrink=0.55, pad=0.03)
    cbar.set_label("Share (%)", fontsize=10)

    # -- butterfly --
    y = np.arange(n_themes)
    ax_but.barh(y, [-v for v in erc_pct_but], color=ERC_COLOR,
                edgecolor="white", linewidth=0.4, label="ERC-8004")
    ax_but.barh(y, a2a_pct_but, color=A2A_COLOR,
                edgecolor="white", linewidth=0.4, label="Google A2A")
    for i, (e, a) in enumerate(zip(erc_pct_but, a2a_pct_but)):
        if e > 0:
            ax_but.text(-e - 0.8, i, f"{e:.1f}%", va="center", ha="right",
                        fontsize=9)
        if a > 0:
            ax_but.text(a + 0.8, i, f"{a:.1f}%", va="center", ha="left",
                        fontsize=9)
    ax_but.axvline(0, color="black", lw=0.7)
    ax_but.invert_yaxis()  # theme 0 at top, matching heatmap row order
    max_ext = max(max(erc_pct_but, default=10), max(a2a_pct_but, default=10)) * 1.35
    ax_but.set_xlim(-max_ext, max_ext)
    ticks = np.arange(-60, 61, 20)
    ax_but.set_xticks(ticks)
    ax_but.set_xticklabels([f"{abs(t)}" for t in ticks])
    ax_but.set_xlabel("Actor participation rate (%)")
    ax_but.set_title("Actor participation rate (butterfly)  ←ERC  |  A2A→", pad=8)
    ax_but.legend(frameon=False, loc="lower right")
    ax_but.set_yticks(y)
    ax_but.set_yticklabels([])
    for spine in ("top", "right"):
        ax_but.spines[spine].set_visible(False)

    fig.tight_layout(w_pad=3)
    _save(fig, "fig-combined-themes")
    plt.close(fig)


# ── Figure: DNA congruence networks ───────────────────────────────────────────

def _load_congruence(case_slug: str) -> nx.Graph:
    edges = pd.read_csv(ND / "dna" / f"congruence_{case_slug}.csv")
    g = nx.Graph()
    for _, r in edges.iterrows():
        g.add_edge(r.actor_a, r.actor_b, weight=float(r.weight))
    return g


def _actor_institutions(case_slug: str) -> dict:
    div = pd.read_csv(ND / "sociosemantic" / f"actor_diversity_{case_slug}.csv")
    return dict(zip(div["author"], div["stakeholder_institution"]))


def fig_dna_networks() -> None:
    erc_g = _load_congruence("erc8004")
    a2a_g = _load_congruence("googlea2a")
    erc_inst = _actor_institutions("erc8004")
    a2a_inst = _actor_institutions("googlea2a")

    top_a2a = sorted(a2a_g.degree(weight="weight"),
                     key=lambda x: x[1], reverse=True)[:100]
    a2a_sub = a2a_g.subgraph({n for n, _ in top_a2a}).copy()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))

    for ax, g, inst, title in [
        (axes[0], erc_g, erc_inst, "ERC-8004 (N=66, all actors)"),
        (axes[1], a2a_sub, a2a_inst, "Google A2A (top-100 by weighted degree)"),
    ]:
        pos = nx.spring_layout(g, k=0.55, seed=SEED, weight="weight",
                               iterations=60)
        degrees = dict(g.degree(weight="weight"))
        sizes = [20 + 4 * degrees[n] for n in g.nodes()]
        colors = [_inst_color(inst.get(n, "Others")) for n in g.nodes()]
        nx.draw_networkx_edges(g, pos, ax=ax, alpha=0.15,
                               edge_color="#555555", width=0.4)
        nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colors,
                               node_size=sizes, linewidths=0.4,
                               edgecolors="white")
        top3 = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:3]
        nx.draw_networkx_labels(g, pos, labels={n: n for n, _ in top3},
                                ax=ax, font_size=8)
        ax.set_title(title)
        ax.axis("off")

    from matplotlib.patches import Patch
    handles = [Patch(color=c, label=lbl) for lbl, c in INST_PALETTE.items()]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles),
               frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(
        "Discourse congruence networks (same-sign stance on ≥1 shared theme)",
        y=0.98,
    )
    _save(fig, "fig-dna-networks")
    plt.close(fig)


# ── Figure: DNA polarization bar ──────────────────────────────────────────────

def fig_dna_polarization() -> None:
    metrics = json.loads((ND / "dna" / "dna_metrics.json").read_text())
    erc = metrics["ERC-8004"]["congruence"]["polarization_index"]
    a2a = metrics["Google-A2A"]["congruence"]["polarization_index"]

    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.barh(
        ["ERC-8004\n(permissionless DAO)", "Google A2A\n(corporate TSC)"],
        [erc, a2a],
        color=[ERC_COLOR, A2A_COLOR],
        height=0.55,
    )
    for y_pos, v in enumerate([erc, a2a]):
        ax.text(v + 0.005, y_pos, f"{v:.3f}", va="center", fontsize=10)
    ax.set_xlim(0, max(erc, a2a) * 1.25)
    ax.set_xlabel("Cross-institutional polarization index π")
    ax.set_title("Share of congruence edges crossing institutions")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    _save(fig, "fig-dna-polarization")
    plt.close(fig)


# ── Figure: entropy KDE mountain curves (0-1 zone highlighted) ────────────────

def fig_ss_entropy() -> None:
    erc = pd.read_csv(ND / "sociosemantic" / "actor_diversity_erc8004.csv")
    a2a = pd.read_csv(ND / "sociosemantic" / "actor_diversity_googlea2a.csv")

    erc_h = erc["entropy"].dropna().values
    a2a_h = a2a["entropy"].dropna().values

    x_max = max(erc_h.max(), a2a_h.max()) + 0.3
    x_all = np.linspace(0, x_max, 600)

    # Reflection at x=0 to prevent KDE leaking into negative territory
    kde_erc = gaussian_kde(np.concatenate([-erc_h, erc_h]), bw_method=0.3)
    kde_a2a = gaussian_kde(np.concatenate([-a2a_h, a2a_h]), bw_method=0.3)
    y_erc = kde_erc(x_all) * 2   # ×2 because we doubled the sample
    y_a2a = kde_a2a(x_all) * 2

    y_top = max(y_erc.max(), y_a2a.max())

    fig, ax = plt.subplots(figsize=(6.4, 4.0))

    # Shaded 0-1 emphasis band (draw first, behind curves)
    ax.axvspan(0, 1, alpha=0.08, color="#888888", zorder=0)
    ax.axvline(1, color="#888888", lw=0.9, linestyle="--", alpha=0.55, zorder=1)
    ax.text(0.5, y_top * 1.02, "0–1 zone",
            ha="center", fontsize=9, color="#555555", style="italic")

    # ERC-8004 curve + fill
    ax.fill_between(x_all, y_erc, alpha=0.38, color=ERC_COLOR, zorder=2)
    ax.plot(x_all, y_erc, color=ERC_COLOR, lw=2.0, zorder=3,
            label=f"ERC-8004  (N={len(erc_h)}, μ={erc_h.mean():.2f})")

    # A2A curve + fill
    ax.fill_between(x_all, y_a2a, alpha=0.38, color=A2A_COLOR, zorder=2)
    ax.plot(x_all, y_a2a, color=A2A_COLOR, lw=2.0, zorder=3,
            label=f"Google A2A  (N={len(a2a_h)}, μ={a2a_h.mean():.2f})")

    ax.set_xlim(0, x_max)
    ax.set_ylim(0)
    ax.set_xlabel("Actor topic-diversity entropy H (bits)")
    ax.set_ylabel("Density")
    ax.set_title("Per-actor Shannon entropy over Thematic-LM themes")
    ax.legend(frameon=False, loc="upper right")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    _save(fig, "fig-ss-entropy")
    plt.close(fig)


# ── Shared topic palette ──────────────────────────────────────────────────────

ARG_COLORS = {
    "Technical":            P6,        # blue/indigo
    "Process":              P5,        # sage green
    "Governance-Principle": P1,        # crimson
    "Economic":             P2,        # orange
    "Off-topic":            "#d7d7d7", # light grey
}
ARG_ORDER = ["Technical", "Process", "Governance-Principle", "Economic", "Off-topic"]

EIP_STAGES = [
    ("2025-08-13", "Proposal"),
    ("2025-10-01", "Review"),
    ("2025-12-15", "Last Call"),
    ("2026-01-29", "Final"),
]


def _load_annotated():
    records = json.loads(ANNOTATED.read_text())
    return [r for r in records if r.get("annotation") and not r.get("annotation_error")]


def _get_field(record, field):
    ann = record.get("annotation") or {}
    return ann.get(field) or record.get(field)


# ── Figure: argument-type comparison (topic-compare) ─────────────────────────

def fig_topic_compare() -> None:
    records = _load_annotated()
    erc = [r for r in records if r.get("_case") == "ERC-8004"]
    a2a = [r for r in records if r.get("_case") == "Google-A2A"]

    def pct(recs):
        total = len(recs) or 1
        counts = Counter(_get_field(r, "argument_type") for r in recs)
        return [100.0 * counts.get(t, 0) / total for t in ARG_ORDER]

    erc_pct = pct(erc)
    a2a_pct = pct(a2a)
    x = np.arange(len(ARG_ORDER))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bar_colors = [ARG_COLORS.get(t, "#aaa") for t in ARG_ORDER]
    bars_erc = ax.bar(x - width / 2, erc_pct, width, color=bar_colors,
                      edgecolor="white", linewidth=0.8,
                      label=f"ERC-8004 (N={len(erc)})")
    bars_a2a = ax.bar(x + width / 2, a2a_pct, width, color=bar_colors,
                      edgecolor="white", linewidth=0.8, alpha=0.55, hatch="///",
                      label=f"Google A2A (N={len(a2a)})")

    for bar in bars_erc:
        h = bar.get_height()
        if h > 1.5:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=8)
    for bar in bars_a2a:
        h = bar.get_height()
        if h > 1.5:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=8, color="#555")

    ax.set_xticks(x)
    ax.set_xticklabels(ARG_ORDER)
    ax.set_ylabel("Share of records (%)")
    ax.set_title("Argument Type Distribution by Case")
    ax.set_ylim(0, max(erc_pct + a2a_pct) * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    _save(fig, "topic-compare")
    plt.close(fig)


# ── Figure: ERC-8004 lifecycle temporal (topic-erc) ──────────────────────────

def fig_topic_erc() -> None:
    records = _load_annotated()
    erc = [r for r in records if r.get("_case") == "ERC-8004"]

    dated = []
    for r in erc:
        raw = r.get("date") or r.get("created_at") or ""
        try:
            dt = dateparser.parse(raw)
            if dt:
                atype = _get_field(r, "argument_type")
                dated.append((dt, atype if atype in ARG_ORDER else "Off-topic"))
        except Exception:
            pass
    dated.sort(key=lambda x: x[0])
    if not dated:
        return

    from datetime import timedelta
    min_dt = dated[0][0]
    bin_days = 14
    bins: dict = defaultdict(Counter)
    for dt, atype in dated:
        idx = (dt - min_dt).days // bin_days
        bins[idx][atype] += 1

    indices = sorted(bins.keys())
    bin_dates = [min_dt + timedelta(days=i * bin_days) for i in indices]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bottoms = np.zeros(len(indices))
    for atype in ARG_ORDER:
        heights = [bins[i].get(atype, 0) for i in indices]
        ax.bar(range(len(indices)), heights, bottom=bottoms,
               color=ARG_COLORS.get(atype, "#ccc"), label=atype,
               edgecolor="white", linewidth=0.5)
        bottoms += np.array(heights, dtype=float)

    for stage_date_str, stage_name in EIP_STAGES[1:]:
        try:
            stage_dt = dateparser.parse(stage_date_str)
            x_pos = (stage_dt - min_dt).days / bin_days
            ax.axvline(x=x_pos, color="#555", linestyle="--", lw=0.9, alpha=0.75)
            ax.text(x_pos + 0.15, bottoms.max() * 0.97, stage_name,
                    fontsize=8, color="#333", rotation=90, va="top")
        except Exception:
            pass

    step = max(1, len(indices) // 10)
    ax.set_xticks(range(0, len(indices), step))
    ax.set_xticklabels(
        [bin_dates[i].strftime("%b '%y") for i in range(0, len(indices), step)],
        rotation=40, ha="right"
    )
    ax.set_ylabel("Records per 2-week bin")
    ax.set_title(f"ERC-8004: Argument Type over Lifecycle  (2-week bins, N={len(dated)})")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", frameon=False, ncol=2)

    _save(fig, "topic-erc")
    plt.close(fig)


# ── Figure: SNA network comparison (network-sna) ─────────────────────────────

def _load_csv_graph(nodes_csv: Path, edges_csv: Path):
    with open(nodes_csv) as f:
        nodes = {r["id"]: r for r in csv.DictReader(f)}
    with open(edges_csv) as f:
        edges = list(csv.DictReader(f))
    return nodes, edges


def _sna_adj(nodes: dict, edges: list):
    """Return (adj dict, degree Counter) for undirected graph."""
    adj: dict = defaultdict(set)
    degree: Counter = Counter()
    for e in edges:
        s, t = e["source"], e["target"]
        if s not in nodes or t not in nodes:
            continue
        adj[s].add(t)
        adj[t].add(s)
        degree[s] += 1
        degree[t] += 1
    return adj, degree


def _sna_spring_layout(nodes: dict, edges: list,
                        iterations: int = 150, k: float | None = None) -> dict:
    """Fruchterman-Reingold spring layout (faithful port from analyze_network.py)."""
    import random
    random.seed(42)
    pos = {nid: [random.uniform(-1, 1), random.uniform(-1, 1)] for nid in nodes}
    n = len(nodes)
    if n == 0:
        return pos
    k_val = k or math.sqrt(1.0 / n)
    t = 0.1
    node_list = list(nodes.keys())

    for _ in range(iterations):
        delta = {nid: [0.0, 0.0] for nid in node_list}
        for i, u in enumerate(node_list):
            for v in node_list[i + 1:]:
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = max(math.sqrt(dx * dx + dy * dy), 0.001)
                f = k_val * k_val / dist
                delta[u][0] += f * dx / dist
                delta[u][1] += f * dy / dist
                delta[v][0] -= f * dx / dist
                delta[v][1] -= f * dy / dist
        for e in edges:
            u, v = e["source"], e["target"]
            if u not in pos or v not in pos:
                continue
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            dist = max(math.sqrt(dx * dx + dy * dy), 0.001)
            f = dist * dist / k_val
            delta[u][0] -= f * dx / dist
            delta[u][1] -= f * dy / dist
            delta[v][0] += f * dx / dist
            delta[v][1] += f * dy / dist
        for nid in node_list:
            d = math.sqrt(delta[nid][0] ** 2 + delta[nid][1] ** 2)
            if d > 0:
                scale = min(d, t) / d
                pos[nid][0] += delta[nid][0] * scale
                pos[nid][1] += delta[nid][1] * scale
        t = max(t * 0.92, 0.001)

    return pos


def _sna_draw_panel(ax, nodes: dict, edges: list, pos: dict,
                     degree: Counter, title: str, metrics: dict,
                     vis_note=None) -> None:
    """Draw one SNA panel — identical logic to analyze_network.py, new palette."""
    ax.set_facecolor("white")
    ax.axis("off")
    ax.set_aspect("equal")

    for e in edges:
        s, t = e["source"], e["target"]
        if s not in pos or t not in pos:
            continue
        w = float(e.get("weight", 1))
        lw = min(0.3 + 0.15 * w, 2.0)
        ax.plot([pos[s][0], pos[t][0]], [pos[s][1], pos[t][1]],
                color="#CCCCCC", linewidth=lw, zorder=1, alpha=0.6)

    max_raw = max(
        (float(d.get("size", 10)) for d in nodes.values()), default=10
    )
    for nid, data in nodes.items():
        if nid not in pos:
            continue
        x, y = pos[nid]
        inst = data.get("institution", "Others")
        color = _inst_color(inst)
        raw_size = float(data.get("size", 10))
        node_size = 30 + 270 * (raw_size / max_raw)
        ax.scatter(x, y, s=node_size, c=color, zorder=3,
                   edgecolors="#555555", linewidths=0.4, alpha=0.9)

    top5 = sorted(nodes.keys(), key=lambda x: degree.get(x, 0), reverse=True)[:5]
    for nid in top5:
        if nid not in pos:
            continue
        x, y = pos[nid]
        ax.text(x, y + 0.07, nid[:12], ha="center", va="bottom",
                fontsize=6.5, color="#111", zorder=5,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))

    ax.set_title(title, fontsize=9, fontweight="bold", pad=6)
    note_line = f" (visualising top-{vis_note} by degree)" if vis_note else ""
    txt = (f"N={metrics['n_nodes']} nodes{note_line}, {metrics['n_edges']} edges\n"
           f"Density={metrics['density']:.3f}  "
           f"Modularity(Louvain)={metrics['modularity_louvain']:.3f}\n"
           f"Gini(degree)={metrics['gini_degree']:.3f}  "
           f"Giant={metrics['giant_component_ratio']:.2f}")
    ax.text(0.02, 0.02, txt, transform=ax.transAxes,
            fontsize=7, va="bottom", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="#F8F9FA", ec="#CCCCCC", lw=0.8))


def fig_network_sna() -> None:
    nodes_erc, edges_erc = _load_csv_graph(
        ANALYSIS / "network_nodes_erc8004.csv",
        ANALYSIS / "network_edges_erc8004.csv",
    )
    nodes_a2a, edges_a2a = _load_csv_graph(
        ANALYSIS / "network_nodes_a2a_top50.csv",
        ANALYSIS / "network_edges_a2a_top50.csv",
    )
    metrics_raw = json.loads((ROOT / "output" / "network_metrics.json").read_text())
    m_erc = metrics_raw.get("erc8004", {})
    m_a2a = metrics_raw.get("a2a", {})

    _, deg_erc = _sna_adj(nodes_erc, edges_erc)
    _, deg_a2a = _sna_adj(nodes_a2a, edges_a2a)

    print("  Computing layouts (this may take ~10 s)…")
    pos_erc = _sna_spring_layout(nodes_erc, edges_erc, iterations=200, k=0.35)
    pos_a2a = _sna_spring_layout(nodes_a2a, edges_a2a, iterations=300, k=0.45)

    fig, (ax_erc, ax_a2a) = plt.subplots(1, 2, figsize=(12, 6))
    fig.patch.set_facecolor("white")

    _sna_draw_panel(ax_erc, nodes_erc, edges_erc, pos_erc, deg_erc,
                    "ERC-8004 Governance Network\n(Permissionless DAO)", m_erc)
    _sna_draw_panel(ax_a2a, nodes_a2a, edges_a2a, pos_a2a, deg_a2a,
                    "Google A2A Governance Network (top-50)\n(Corporate Hierarchy)",
                    m_a2a, vis_note=50)

    from matplotlib.patches import Patch
    legend_handles = [Patch(color=c, label=lbl) for lbl, c in INST_PALETTE.items()]
    fig.legend(handles=legend_handles, loc="lower center",
               ncol=len(legend_handles),
               fontsize=8, framealpha=0.9, bbox_to_anchor=(0.5, -0.01))
    plt.tight_layout(rect=[0, 0.08, 1, 1])

    _save(fig, "network-sna")
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUTPUT_FIGS.mkdir(parents=True, exist_ok=True)
    print("• BERTopic divergence (enlarged font)…")
    fig_bertopic_divergence()
    print("• CryptoBERT frequency chart…")
    fig_cryptobert_frequency()
    print("• Combined thematic heatmap + butterfly…")
    fig_combined_heatmap_butterfly()
    print("• DNA congruence networks…")
    fig_dna_networks()
    print("• DNA polarization…")
    fig_dna_polarization()
    print("• Entropy KDE mountain curves…")
    fig_ss_entropy()
    print("• Argument-type comparison (topic-compare)…")
    fig_topic_compare()
    print("• ERC-8004 lifecycle temporal (topic-erc)…")
    fig_topic_erc()
    print("• SNA network comparison (network-sna)…")
    fig_network_sna()
    print(f"\nDone — output/figures/  +  paper-acm/")
