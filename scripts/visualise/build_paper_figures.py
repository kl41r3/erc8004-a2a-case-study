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

# ── Dark-theme palette (for two-col cinematic figure) ─────────────────────────
DARK_BG    = "#0D1117"
DARK_PANEL = "#161B22"
INST_PALETTE_DARK = {
    "Google":               "#FF5252",
    "MetaMask":             "#FF9F43",
    "Ethereum Foundation":  "#748EFF",
    "Coinbase":             "#26D9C7",
    "Microsoft":            "#FFD93D",
    "AWS":                  "#82EDB2",
    "Others":               "#6B7280",
}
ERC_HUB_DARK = "#FFD700"   # gold
A2A_HUB_DARK = "#DA70D6"   # orchid

INST_PALETTE = {
    "Google":               P1,
    "MetaMask":             P2,
    "Ethereum Foundation":  P6,
    "Coinbase":             P5,
    "Microsoft":            P3,
    "AWS":                  P4,
    "Others":               "#c0bdb8",  # Independent + Unknown merged
}

# Human-readable semantic labels for BERTopic and CryptoBERT topics
_BERT_SEMANTIC: dict[int, str] = {
    0:  "Agent Discourse",
    1:  "Task / Message Protocol",
    2:  "PR Review Chatter",
    3:  "JSON / Proto Spec",
    4:  "Contributing / PR Flow",
    5:  "Python SDK Samples",
    6:  "Versioning",
    7:  "UI Assets",
    8:  "Voting / Governance",
    9:  "Corporate Actors (SAP, LinkedIn)",
    10: "Push Notifications",
    11: "Code of Conduct",
    12: "Partner / Discord Links",
    13: "Gemini AI Review",
    14: "Lint / CI Config",
    15: "UI Polling / Demo",
    16: "Docs / MkDocs",
    17: "OpenAI / Azure",
    18: "Null / None Types",
}
_CRYPTO_SEMANTIC: dict[int, str] = {
    0: "Onchain Agent Registry",
    1: "Implementation Scope",
    2: "Trust & Reputation",
    3: "Reviewer / Admin",
    4: "GitHub PR Process",
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


# ── Figure: BERTopic + CryptoBERT integrated dashboard ───────────────────────

def fig_bertopic_cryptobert_integrated() -> None:
    """Unified divergence dashboard combining BERTopic (left) and CryptoBERT (right).

    OPTION A design: signed divergence bars (ERC right, A2A left) share the
    left panel; CryptoBERT ERC-only lollipop occupies the right panel.
    ~45 % height reduction vs. two separate figures.
    """
    # ── data ──────────────────────────────────────────────────────────────────
    bert_df = pd.read_csv(TD / "comparative_discourse" / "divergence_table.csv")
    bert_df = bert_df.sort_values("abs_diff", ascending=False).reset_index(drop=True)
    bert_df["signed"] = bert_df["erc8004_pct"] - bert_df["a2a_pct"]

    crypto_data = json.loads((TD / "crypto_bert" / "topics.json").read_text())
    crypto_topics = sorted(crypto_data["topics"], key=lambda t: t["pct"], reverse=True)
    n_bert = len(bert_df)
    n_crypto = len(crypto_topics)

    # ── semantic labels ────────────────────────────────────────────────────────
    def _blabel(row) -> str:
        sem = _BERT_SEMANTIC.get(int(row["topic_id"]))
        if sem:
            return f"T{int(row['topic_id'])}  {sem}"
        kws = [k.strip() for k in str(row["keywords"]).split(",")[:2]]
        return f"T{int(row['topic_id'])}  {' · '.join(kws)}"

    bert_df["label"] = bert_df.apply(_blabel, axis=1)
    crypto_labels = [
        f"T{t['id']}  {_CRYPTO_SEMANTIC.get(t['id'], ' · '.join(t['keywords'][:2]))}"
        for t in crypto_topics
    ]
    crypto_pcts = [t["pct"] for t in crypto_topics]

    # ── layout ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(8.5, 5.0), facecolor="white")
    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.65, 1.0], wspace=0.46,
        left=0.02, right=0.97, top=0.86, bottom=0.11,
    )
    ax_bert   = fig.add_subplot(gs[0])
    ax_crypto = fig.add_subplot(gs[1])

    # ── panel A: BERTopic signed divergence ───────────────────────────────────
    y_b    = np.arange(n_bert)
    signed = bert_df["signed"].values
    max_div = float(np.max(np.abs(signed)))

    bar_colors = [ERC_COLOR if v > 0 else A2A_COLOR for v in signed]
    alphas     = [0.40 + 0.60 * abs(float(v)) / max_div for v in signed]
    for i, (val, col, alpha) in enumerate(zip(signed, bar_colors, alphas)):
        ax_bert.barh(i, float(val), color=col, alpha=alpha, edgecolor="none", height=0.70)

    # value annotations (|diff| >= 3 pp); T0 gets cross-panel marker
    for i, val in enumerate(signed):
        if abs(val) < 3.0:
            continue
        if i == 0:
            ax_bert.text(
                float(val) + 0.8, 0, f"+{val:.1f}pp  · see B",
                va="center", ha="left", fontsize=5.5,
                color=ERC_COLOR, family="monospace", alpha=0.85,
            )
        else:
            x_tip = float(val) + (0.8 if val > 0 else -0.8)
            ax_bert.text(
                x_tip, i, f"+{val:.1f}" if val > 0 else f"{val:.1f}",
                va="center", ha="left" if val > 0 else "right",
                fontsize=5.5, color="#444", family="monospace",
            )

    ax_bert.axvline(0, color="#333", lw=0.7, zorder=5)
    xlim_max = max_div * 1.28
    ax_bert.set_xlim(-xlim_max, xlim_max)
    ax_bert.text( xlim_max * 0.52, n_bert - 0.3,
                  "ERC-8004 →", fontsize=6.0, color=ERC_COLOR, ha="center", alpha=0.78)
    ax_bert.text(-xlim_max * 0.52, n_bert - 0.3,
                  "← A2A",     fontsize=6.0, color=A2A_COLOR, ha="center", alpha=0.78)
    ax_bert.set_yticks(y_b)
    ax_bert.set_yticklabels(bert_df["label"].values, fontsize=6.4)
    ax_bert.invert_yaxis()  # index 0 (T0, most divergent) → visual top
    ax_bert.set_xlabel("Share difference  (ERC − A2A, pp)", fontsize=7, labelpad=2)
    ax_bert.set_title("A   BERTopic cross-case divergence  (JSD = 0.288)",
                       fontsize=8.5, fontweight="bold", pad=5, loc="left")
    ax_bert.tick_params(left=False, pad=1)
    ax_bert.xaxis.grid(True, alpha=0.15, lw=0.3)
    for spine in ax_bert.spines.values():
        spine.set_visible(False)

    # ── panel B: CryptoBERT ERC-only lollipop ─────────────────────────────────
    y_c = np.arange(n_crypto)
    cmap_seq = mcolors.LinearSegmentedColormap.from_list("cb_seq", ["#c6d9f0", P6], N=256)
    lolly_colors = [mcolors.to_hex(cmap_seq(v))
                    for v in np.linspace(0.92, 0.25, n_crypto)]

    ax_crypto.hlines(y_c, 0, crypto_pcts, colors=lolly_colors, linewidth=2.0, alpha=0.72)
    ax_crypto.scatter(crypto_pcts, y_c, color=lolly_colors, s=46,
                      zorder=4, edgecolors="white", linewidth=0.5)
    for i, pct in enumerate(crypto_pcts):
        ax_crypto.text(pct + 1.5, i, f"{pct:.1f}%", va="center", fontsize=7, color="#444")

    t0t2_sum = sum(t["pct"] for t in crypto_topics if t["id"] in (0, 2))
    ax_crypto.text(
        0.97, 0.02, f"T0 + T2 = {t0t2_sum:.1f}%\ngovernance core",
        transform=ax_crypto.transAxes, fontsize=6.5, color=ERC_COLOR,
        ha="right", va="bottom",
        bbox=dict(boxstyle="round,pad=0.3", fc="#eef2fb", ec="none"),
    )

    ax_crypto.set_yticks(y_c)
    ax_crypto.set_yticklabels(crypto_labels, fontsize=6.5)
    ax_crypto.invert_yaxis()  # index 0 (T0, most frequent) → visual top
    ax_crypto.set_xlim(0, max(crypto_pcts) * 1.38)
    ax_crypto.set_xlabel("ERC-8004 record share (%)", fontsize=7, labelpad=2)
    ax_crypto.set_title(
        f"B   CryptoBERT — ERC-8004 only\n"
        f"    N={crypto_data['n_records']},  noise {crypto_data['noise_rate_pct']:.1f}% excl.",
        fontsize=8.5, fontweight="bold", pad=5, loc="left",
    )
    ax_crypto.tick_params(left=False, pad=1)
    ax_crypto.xaxis.grid(True, alpha=0.15, lw=0.3)
    for spine in ("top", "left", "right"):
        ax_crypto.spines[spine].set_visible(False)

    # ── suptitle ──────────────────────────────────────────────────────────────
    fig.suptitle(
        "Discourse topic structure: ERC-8004 concentrates on a governance core; "
        "A2A disperses into implementation tooling",
        fontsize=8.5, fontweight="bold", y=0.97, x=0.50,
    )

    _save(fig, "fig-bertopic-integrated")
    plt.close(fig)


# ── Figure: combined thematic heatmap + butterfly (overlaid, one-column) ────────

def fig_combined_heatmap_butterfly() -> None:
    """Overlaid diverging bar + line chart: bars = record share, lines = actor
    participation rate.  Single-axis design for one-column figure."""

    # ---- build record-share (former heatmap) data ----
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
    n_themes = len(theme_order)

    # Exact codebook labels; wrap long ones at '&' or the first space past mid
    def _wrap_label(tid: str) -> str:
        base = f"{tid}: {label_map.get(tid, tid)}"
        if len(base) <= 38:
            return base
        # try splitting on ' & '
        if " & " in base:
            return base.replace(" & ", " &\n")
        # otherwise split at a space near the midpoint of the label part
        parts = base.split(": ", 1)
        if len(parts) == 2 and len(parts[1]) > 32:
            mid = len(parts[1]) // 2
            for off in range(12):
                for direction in (1, -1):
                    idx = mid + off * direction
                    if 0 < idx < len(parts[1]) and parts[1][idx] == " ":
                        parts[1] = parts[1][:idx] + "\n" + parts[1][idx + 1:]
                        return ": ".join(parts)
        return base

    theme_labels = [_wrap_label(tid) for tid in theme_order]

    # ---- actor-participation (former butterfly) data ----
    df_but = pd.read_csv(ND / "sociosemantic" / "theme_actor_comparison.csv")
    df_but = df_but.set_index("theme_id")
    erc_but = [float(df_but.loc[tid, "erc8004_pct"]) if tid in df_but.index else 0.0
               for tid in theme_order]
    a2a_but = [float(df_but.loc[tid, "a2a_pct"]) if tid in df_but.index else 0.0
               for tid in theme_order]

    # ---- record-share values ----
    erc_share = [float(pct_heat.loc[tid, erc_col]) for tid in theme_order]
    a2a_share = [float(pct_heat.loc[tid, a2a_col]) for tid in theme_order]

    # ---- single-axis diverging bar + line overlay ----
    fig, ax = plt.subplots(figsize=(7.2, max(4.2, n_themes * 0.38)))
    y = np.arange(n_themes)

    # Bars — record share (diverging)
    bh = 0.50
    ax.barh(y, erc_share, bh, color=ERC_COLOR, alpha=0.55, lw=0.3,
            label="ERC-8004 record share")
    ax.barh(y, [-v for v in a2a_share], bh, color=A2A_COLOR, alpha=0.55, lw=0.3,
            label="A2A record share")

    # Lines — actor participation (thick, bold, white-filled markers)
    ax.plot(erc_but, y, color=ERC_COLOR, lw=2.8, marker='D', ms=5.0,
            markerfacecolor='white', markeredgecolor=ERC_COLOR,
            markeredgewidth=1.4, label="ERC-8004 actor participation")
    ax.plot([-v for v in a2a_but], y, color=A2A_COLOR, lw=2.8, marker='s', ms=5.0,
            markerfacecolor='white', markeredgecolor=A2A_COLOR,
            markeredgewidth=1.4, label="A2A actor participation")

    # Inline annotations for prominent participation rates
    for i in range(n_themes):
        if erc_but[i] > 5:
            ax.text(erc_but[i] + 1.2, i, f"{erc_but[i]:.0f}%",
                    va="center", fontsize=6.0, color=ERC_COLOR, fontweight='bold')
        if a2a_but[i] > 5:
            ax.text(-a2a_but[i] - 1.2, i, f"{a2a_but[i]:.0f}%",
                    va="center", ha="right", fontsize=6.0, color=A2A_COLOR,
                    fontweight='bold')

    # Zero line, labels, and cosmetics
    ax.axvline(0, color="#333", lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(theme_labels, fontsize=6.6, linespacing=0.92)
    ax.invert_yaxis()

    max_val = max(max(erc_share + erc_but), max(a2a_share + a2a_but))
    x_max = max(max_val * 1.45, 40)
    ax.set_xlim(-40, x_max)

    # Absolute-value tick labels for the diverging axis
    tick_step = 20
    ticks = sorted(set(list(range(-40, int(x_max) + tick_step, tick_step)) + [0]))
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{abs(t):.0f}" for t in ticks])
    ax.set_xlabel("Record share / Actor participation rate (%)", fontsize=7)
    ax.set_title("Thematic-LM: record share (bar) & actor participation (line)",
                 fontsize=8, fontweight='bold', loc='left')
    ax.legend(frameon=False, fontsize=6.2, loc="lower right", ncol=1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.grid(True, alpha=0.12, lw=0.3)
    ax.tick_params(left=False, pad=1)

    # JSD annotation (top-right corner, inside the plot)
    ax.text(0.97, 0.97, "JSD = 0.216", transform=ax.transAxes,
            fontsize=7, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.25", fc="#F8F9FA", ec="#CCCCCC", lw=0.5))

    fig.tight_layout()
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


# ── Figure: combined pie + lifecycle (topic-pie-erc) ─────────────────────────

def _draw_pie_with_leaders(ax, pcts, colors, title, n_total, threshold=4.0):
    """Draw a pie chart; labels inside for large slices, outside with leader line for small."""
    wedges, _ = ax.pie(
        pcts,
        colors=colors,
        startangle=90,
        wedgeprops=dict(linewidth=0.6, edgecolor="white"),
    )
    ax.set_title(title, fontsize=9, pad=4)

    for wedge, val in zip(wedges, pcts):
        if val < 0.5:
            continue
        angle = (wedge.theta1 + wedge.theta2) / 2
        rad = np.radians(angle)
        cos_a, sin_a = np.cos(rad), np.sin(rad)
        label = f"{val:.0f}%"

        if val >= threshold:
            # Large slice: label inside, white text
            ax.text(
                0.65 * cos_a, 0.65 * sin_a, label,
                ha="center", va="center", fontsize=8,
                color="white" if val > 15 else "#222",
                fontweight="bold",
            )
        else:
            # Small slice: leader line pointing outward
            x_tip = 0.88 * cos_a
            y_tip = 0.88 * sin_a
            x_out = 1.30 * cos_a
            y_out = 1.30 * sin_a
            ax.annotate(
                label,
                xy=(x_tip, y_tip),
                xytext=(x_out, y_out),
                fontsize=7.5,
                ha="left" if cos_a >= 0 else "right",
                va="center",
                arrowprops=dict(
                    arrowstyle="-",
                    color="#666",
                    lw=0.7,
                    shrinkA=0,
                    shrinkB=2,
                ),
            )
    return wedges


def fig_topic_pie_erc() -> None:
    """Left: two pie charts (ERC-8004 / A2A) stacked vertically.
    Right: ERC-8004 argument-type lifecycle (identical to fig_topic_erc)."""
    records = _load_annotated()
    erc_all = [r for r in records if r.get("_case") == "ERC-8004"]
    a2a_all = [r for r in records if r.get("_case") == "Google-A2A"]

    def pct_counts(recs):
        total = len(recs) or 1
        counts = Counter(_get_field(r, "argument_type") for r in recs)
        return [100.0 * counts.get(t, 0) / total for t in ARG_ORDER]

    erc_pct = pct_counts(erc_all)
    a2a_pct = pct_counts(a2a_all)
    pie_colors = [ARG_COLORS.get(t, "#aaa") for t in ARG_ORDER]

    # ── lifecycle data ────────────────────────────────────────────────────────
    dated = []
    for r in erc_all:
        raw = r.get("date") or r.get("created_at") or ""
        try:
            dt = dateparser.parse(raw)
            if dt:
                atype = _get_field(r, "argument_type")
                dated.append((dt, atype if atype in ARG_ORDER else "Off-topic"))
        except Exception:
            pass
    dated.sort(key=lambda x: x[0])

    from datetime import timedelta
    bin_days = 14
    bins: dict = defaultdict(Counter)
    min_dt = None
    if dated:
        min_dt = dated[0][0]
        for dt, atype in dated:
            idx = (dt - min_dt).days // bin_days
            bins[idx][atype] += 1

    indices = sorted(bins.keys())
    bin_dates = [min_dt + timedelta(days=i * bin_days) for i in indices] if min_dt else []

    # ── layout ───────────────────────────────────────────────────────────────
    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=(12, 5))
    gs = gridspec.GridSpec(2, 2, width_ratios=[1, 2.2], hspace=0.5, wspace=0.08)

    # top-left pie: ERC-8004
    ax_pie_erc = fig.add_subplot(gs[0, 0])
    _draw_pie_with_leaders(
        ax_pie_erc, erc_pct, pie_colors,
        "ERC-8004", len(erc_all),
    )

    # bottom-left pie: A2A
    ax_pie_a2a = fig.add_subplot(gs[1, 0])
    _draw_pie_with_leaders(
        ax_pie_a2a, a2a_pct, pie_colors,
        "Google A2A", len(a2a_all),
    )

    # legend will be added to ax_bar after it is built (avoids title overlap)

    # right panel: lifecycle (spans both rows)
    ax_bar = fig.add_subplot(gs[:, 1])
    if indices:
        bottoms = np.zeros(len(indices))
        for atype in ARG_ORDER:
            heights = [bins[i].get(atype, 0) for i in indices]
            ax_bar.bar(
                range(len(indices)), heights, bottom=bottoms,
                color=ARG_COLORS.get(atype, "#ccc"), label=atype,
                edgecolor="white", linewidth=0.5,
            )
            bottoms += np.array(heights, dtype=float)

        for stage_date_str, stage_name in EIP_STAGES[1:]:
            try:
                stage_dt = dateparser.parse(stage_date_str)
                x_pos = (stage_dt - min_dt).days / bin_days
                ax_bar.axvline(x=x_pos, color="#555", linestyle="--", lw=0.9, alpha=0.75)
                ax_bar.text(x_pos + 0.15, bottoms.max() * 0.97, stage_name,
                            fontsize=8, color="#333", rotation=90, va="top")
            except Exception:
                pass

        # x-axis: one label per calendar month (no duplicates)
        tick_pos, tick_lbl = [], []
        last_month = None
        for i, bd in enumerate(bin_dates):
            if bd.month != last_month:
                tick_pos.append(i)
                tick_lbl.append(bd.strftime("%b '%y"))
                last_month = bd.month
        ax_bar.set_xticks(tick_pos)
        ax_bar.set_xticklabels(tick_lbl, rotation=40, ha="right")

        ax_bar.set_ylabel("Records per 2-week bin")
        ax_bar.set_title(
            "ERC-8004: Argument Type over Lifecycle  (2-week bins)",
            fontsize=10,
        )
        ax_bar.spines[["top", "right"]].set_visible(False)
        ax_bar.legend(loc="upper right", frameon=False, ncol=2, fontsize=8)

    _save(fig, "topic-pie-erc")
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


def _build_nx_graph_from_csv(nodes: dict, edges: list) -> nx.Graph:
    G = nx.Graph()
    for nid in nodes:
        G.add_node(nid)
    for e in edges:
        s, t = e["source"], e["target"]
        if s in nodes and t in nodes:
            G.add_edge(s, t, weight=float(e.get("weight", 1)))
    return G


def _compress_pos(pos: dict, factor: float = 0.72) -> dict:
    """Pull positions toward the centroid to eliminate peripheral whitespace."""
    if not pos:
        return pos
    vals = list(pos.values())
    cx = float(np.mean([v[0] for v in vals]))
    cy = float(np.mean([v[1] for v in vals]))
    return {n: ((p[0] - cx) * factor + cx, (p[1] - cy) * factor + cy)
            for n, p in pos.items()}


def _radial_sparse_layout(G: nx.Graph) -> dict:
    """ERC-8004: kamada-kawai on the connected subgraph only; isolates are excluded."""
    isolates = set(nx.isolates(G))
    connected = [n for n in G.nodes() if n not in isolates]
    pos: dict = {}

    if connected:
        sub = G.subgraph(connected)
        pos_sub = nx.spring_layout(sub, k=0.18, seed=SEED, iterations=400,
                                    weight="weight")
        vals = list(pos_sub.values())
        xs = [v[0] for v in vals]
        ys = [v[1] for v in vals]
        span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1
        # Use centroid (mean), not bounding-box midpoint, for centering
        xc = float(np.mean(xs))
        yc = float(np.mean(ys))
        for n, (x, y) in pos_sub.items():
            pos[n] = ((x - xc) / span * 0.55, (y - yc) / span * 0.55)

    return pos


def _compact_dense_layout(G: nx.Graph) -> dict:
    """A2A layout: kamada-kawai → normalize to [-0.85,0.85] for dense, compact look."""
    if len(G.nodes()) == 0:
        return {}
    try:
        pos_raw = nx.kamada_kawai_layout(G, weight="weight")
    except Exception:
        pos_raw = nx.spring_layout(G, k=0.15, seed=SEED, iterations=300, weight="weight")
    # Clip extreme outliers at 95th percentile distance from centroid
    vals = list(pos_raw.values())
    cx = float(np.mean([v[0] for v in vals]))
    cy = float(np.mean([v[1] for v in vals]))
    dists = [math.hypot(v[0] - cx, v[1] - cy) for v in vals]
    r95 = float(np.percentile(dists, 95)) or 1.0
    clipped = {}
    for n, (x, y) in pos_raw.items():
        d = math.hypot(x - cx, y - cy)
        if d > r95:
            scale = r95 / d
            clipped[n] = (cx + (x - cx) * scale, cy + (y - cy) * scale)
        else:
            clipped[n] = (x, y)
    return _compress_pos(clipped, factor=0.42)


def _draw_sna_panel_refined(
    ax, nodes: dict, edges: list, pos: dict,
    degree: Counter, title: str, metrics: dict,
    hub_color: str, vis_note=None,
) -> None:
    """Publication-quality SNA panel. canvas limits are computed from the data."""
    ax.set_facecolor("#F8F8F8")
    ax.axis("off")
    ax.set_aspect("equal")

    # Derive canvas limits from 88th-percentile node distance (clips outlier components)
    pos_vals = list(pos.values())
    if pos_vals:
        dists = [math.hypot(p[0], p[1]) for p in pos_vals]
        canvas_r = float(np.percentile(dists, 60)) * 1.20
    else:
        canvas_r = 1.10
    ax.set_xlim(-canvas_r, canvas_r)
    ax.set_ylim(-canvas_r, canvas_r)

    # Only consider non-isolated nodes
    active = {n for n, d in degree.items() if d > 0}
    top3 = {n for n, _ in sorted(
        ((n, d) for n, d in degree.items() if n in active),
        key=lambda x: x[1], reverse=True)[:3]}

    # Edges: very low opacity, thin, neutral gray
    for e in edges:
        s, t = e["source"], e["target"]
        if s not in pos or t not in pos:
            continue
        w = float(e.get("weight", 1))
        ax.plot(
            [pos[s][0], pos[t][0]], [pos[s][1], pos[t][1]],
            color="#AAAAAA",
            linewidth=min(0.25 + 0.10 * w, 1.1),
            alpha=min(0.09 + 0.06 * w, 0.38),
            zorder=1, solid_capstyle="round",
        )

    # Nodes: skip isolates; sub-linear size scaling, alpha by structural role
    active_nodes = {nid: d for nid, d in nodes.items() if degree.get(nid, 0) > 0}
    max_raw = max((float(d.get("size", 1)) for d in active_nodes.values()), default=1)
    min_raw = min((float(d.get("size", 1)) for d in active_nodes.values()), default=1)
    size_span = max_raw - min_raw or 1

    for nid, data in active_nodes.items():
        if nid not in pos:
            continue
        x, y = pos[nid]
        inst = data.get("institution", "Others")
        raw_size = float(data.get("size", 1))
        t_norm = ((raw_size - min_raw) / size_span) ** 0.55
        node_s = 12 + 210 * t_norm

        is_hub = nid in top3
        color = hub_color if is_hub else _inst_color(inst)
        alpha = 0.95 if is_hub else 0.72
        ec = "#222" if is_hub else "#888"
        lw = 1.0 if is_hub else 0.25

        ax.scatter(x, y, s=node_s, c=color,
                   zorder=5 if is_hub else 3,
                   edgecolors=ec, linewidths=lw, alpha=alpha)

    # Labels: top-3 hubs only
    label_offset = canvas_r * 0.10
    for nid, _ in sorted(degree.items(), key=lambda x: x[1], reverse=True)[:3]:
        if nid not in pos:
            continue
        x, y = pos[nid]
        ax.text(x, y + label_offset, nid[:11], ha="center", va="bottom",
                fontsize=5.8, fontweight="bold", color="#111", zorder=7,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))

    ax.set_title(title, fontsize=8.5, fontweight="bold", pad=4, color="#111")

    # Compact metric strip — monospaced, bottom-center
    note = f"top-{vis_note} shown · " if vis_note else ""
    txt = (
        f"{note}N={metrics.get('n_nodes', '?')}  E={metrics.get('n_edges', '?')}  "
        f"ρ={metrics.get('density', 0):.3f}\n"
        f"Gini={metrics.get('gini_degree', 0):.3f}  "
        f"Giant={metrics.get('giant_component_ratio', 0):.2f}  "
        f"Q={metrics.get('modularity_louvain', 0):.3f}"
    )
    ax.text(0.50, 0.01, txt, transform=ax.transAxes,
            fontsize=5.8, va="bottom", ha="center", color="#555",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="#CCC", lw=0.4))


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

    G_erc_full = _build_nx_graph_from_csv(nodes_erc, edges_erc)
    G_a2a = _build_nx_graph_from_csv(nodes_a2a, edges_a2a)

    # ERC: keep only the giant component
    gcc_erc = max(nx.connected_components(G_erc_full), key=len)
    G_erc = G_erc_full.subgraph(gcc_erc).copy()
    nodes_erc = {nid: d for nid, d in nodes_erc.items() if nid in gcc_erc}
    edges_erc = [e for e in edges_erc
                 if e["source"] in gcc_erc and e["target"] in gcc_erc]

    _, deg_erc = _sna_adj(nodes_erc, edges_erc)
    _, deg_a2a = _sna_adj(nodes_a2a, edges_a2a)

    print("  Computing layouts…")
    # ERC giant component: direct spring layout, no extra normalization
    pos_erc = nx.spring_layout(G_erc, k=0.20, seed=SEED, iterations=500,
                               weight="weight")
    pos_a2a = _compact_dense_layout(G_a2a)

    # Vertical diptych — portrait orientation for single-column placement
    fig = plt.figure(figsize=(5.5, 9.0), facecolor="white")
    ax_erc = fig.add_axes([0.05, 0.51, 0.90, 0.44])
    ax_a2a = fig.add_axes([0.05, 0.04, 0.90, 0.44])

    _draw_sna_panel_refined(
        ax_erc, nodes_erc, edges_erc, pos_erc, deg_erc,
        "ERC-8004  ·  Permissionless DAO",
        m_erc, hub_color="#8B4513",
    )
    _draw_sna_panel_refined(
        ax_a2a, nodes_a2a, edges_a2a, pos_a2a, deg_a2a,
        "Google A2A  ·  Corporate Hierarchy",
        m_a2a, hub_color="#5B2C8D",
        vis_note=50,
    )

    # Thin horizontal divider between panels
    fig.add_artist(
        plt.Line2D([0.05, 0.95], [0.500, 0.500],
                   transform=fig.transFigure,
                   color="#DDDDDD", linewidth=0.8, zorder=10)
    )

    fig.text(0.50, 0.993, "Co-participation Governance Networks",
             ha="center", va="top", fontsize=9.5, fontweight="bold", color="#111")

    _save(fig, "network-sna")
    plt.close(fig)


# ── Figure: SNA — two-column cinematic dark-theme variant ────────────────────

def _draw_sna_dark(
    ax, nodes: dict, edges: list, pos: dict,
    degree: Counter, title: str, metrics: dict,
    hub_color: str, vis_note=None,
) -> None:
    """Cinematic dark-theme SNA panel with node glow and white label outlines."""
    import matplotlib.patheffects as pe

    ax.set_facecolor(DARK_PANEL)
    ax.axis("off")
    ax.set_aspect("equal")

    pos_vals = list(pos.values())
    if not pos_vals:
        return
    dists = [math.hypot(p[0], p[1]) for p in pos_vals]
    canvas_r = float(np.percentile(dists, 60)) * 1.22
    ax.set_xlim(-canvas_r, canvas_r)
    ax.set_ylim(-canvas_r, canvas_r)

    active = {n for n, d in degree.items() if d > 0}
    top3 = {n for n, _ in sorted(
        ((n, d) for n, d in degree.items() if n in active),
        key=lambda x: x[1], reverse=True)[:3]}

    # Edges — hub edges brighter, others ghosted
    for e in edges:
        s, t = e["source"], e["target"]
        if s not in pos or t not in pos:
            continue
        w = float(e.get("weight", 1))
        is_hub_edge = s in top3 or t in top3
        col = "#FFFFFF" if is_hub_edge else "#8899BB"
        alpha = min(0.18 + 0.12 * w, 0.55) if is_hub_edge else min(0.05 + 0.03 * w, 0.18)
        lw = min(0.5 + 0.18 * w, 1.8) if is_hub_edge else min(0.2 + 0.07 * w, 0.7)
        ax.plot([pos[s][0], pos[t][0]], [pos[s][1], pos[t][1]],
                color=col, linewidth=lw, alpha=alpha, zorder=1,
                solid_capstyle="round")

    # Nodes — multi-layer glow for hubs, soft halo for regular nodes
    active_nodes = {nid: d for nid, d in nodes.items() if degree.get(nid, 0) > 0}
    max_raw = max((float(d.get("size", 1)) for d in active_nodes.values()), default=1)
    min_raw = min((float(d.get("size", 1)) for d in active_nodes.values()), default=1)
    size_span = max_raw - min_raw or 1

    # Draw regular nodes first (lower z-order)
    for nid, data in active_nodes.items():
        if nid not in pos or nid in top3:
            continue
        x, y = pos[nid]
        inst = data.get("institution", "Others")
        raw_size = float(data.get("size", 1))
        t_norm = ((raw_size - min_raw) / size_span) ** 0.5
        node_s = 14 + 240 * t_norm
        color = INST_PALETTE_DARK.get(inst if inst in INST_PALETTE_DARK else "Others",
                                      "#6B7280")
        ax.scatter(x, y, s=node_s * 2.2, c=color, alpha=0.07, zorder=2, linewidths=0)
        ax.scatter(x, y, s=node_s, c=color, alpha=0.80, zorder=3,
                   edgecolors="#1E2535", linewidths=0.35)

    # Draw hub nodes last (highest z-order) with layered glow
    for nid, data in active_nodes.items():
        if nid not in pos or nid not in top3:
            continue
        x, y = pos[nid]
        raw_size = float(data.get("size", 1))
        t_norm = ((raw_size - min_raw) / size_span) ** 0.5
        node_s = 14 + 240 * t_norm
        col = hub_color
        ax.scatter(x, y, s=node_s * 7.0, c=col, alpha=0.04, zorder=4, linewidths=0)
        ax.scatter(x, y, s=node_s * 3.5, c=col, alpha=0.10, zorder=4, linewidths=0)
        ax.scatter(x, y, s=node_s * 1.8, c=col, alpha=0.22, zorder=4, linewidths=0)
        ax.scatter(x, y, s=node_s, c=col, alpha=0.96, zorder=5,
                   edgecolors="white", linewidths=0.8)

    # Labels — white bold with dark stroke outline
    label_offset = canvas_r * 0.10
    for nid, _ in sorted(degree.items(), key=lambda x: x[1], reverse=True)[:3]:
        if nid not in pos:
            continue
        x, y = pos[nid]
        t = ax.text(x, y + label_offset, nid[:13],
                    ha="center", va="bottom",
                    fontsize=7.0, fontweight="bold", color="white", zorder=8)
        t.set_path_effects([
            pe.withStroke(linewidth=2.8, foreground=DARK_BG)
        ])

    # Panel title (white)
    ax.set_title(title, fontsize=9.5, fontweight="bold", pad=5,
                 color="white", loc="center")

    # Compact metric annotation
    note = f"top-{vis_note} · " if vis_note else ""
    txt = (f"{note}N={metrics.get('n_nodes','?')}  "
           f"ρ={metrics.get('density', 0):.3f}  "
           f"Gini={metrics.get('gini_degree', 0):.3f}  "
           f"Giant={metrics.get('giant_component_ratio', 0):.2f}")
    ax.text(0.50, 0.01, txt, transform=ax.transAxes,
            fontsize=5.5, va="bottom", ha="center", color="#8899BB",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.22", fc="#1E2535", ec="#2E3D55", lw=0.5))


def _draw_sna_twocol_panel(
    ax, nodes: dict, edges: list, pos: dict,
    degree: Counter, isolates: set,
    title: str, metrics: dict, hub_color: str, vis_note=None,
) -> None:
    """Two-col panel: isolates as faint background ring + full connected foreground."""
    ax.set_facecolor("#F8F8F8")
    ax.axis("off")
    ax.set_aspect("equal")

    if not pos:
        return
    # Canvas: sized by all nodes (connected + isolate ring) at 92nd percentile
    all_dists = [math.hypot(p[0], p[1]) for p in pos.values()]
    canvas_r = float(np.percentile(all_dists, 92)) * 1.18
    ax.set_xlim(-canvas_r, canvas_r)
    ax.set_ylim(-canvas_r, canvas_r)

    top3 = {n for n, _ in sorted(
        ((n, d) for n, d in degree.items() if d > 0),
        key=lambda x: x[1], reverse=True)[:3]}

    # Draw isolate dots first (background layer, very faint)
    for nid in isolates:
        if nid not in pos:
            continue
        x, y = pos[nid]
        ax.scatter(x, y, s=7, c="#BBBBCC", alpha=0.22, zorder=1, linewidths=0)

    # Draw edges
    for e in edges:
        s, t = e["source"], e["target"]
        if s not in pos or t not in pos:
            continue
        w = float(e.get("weight", 1))
        ax.plot([pos[s][0], pos[t][0]], [pos[s][1], pos[t][1]],
                color="#AAAAAA",
                linewidth=min(0.25 + 0.10 * w, 1.1),
                alpha=min(0.09 + 0.06 * w, 0.38),
                zorder=2, solid_capstyle="round")

    # Draw connected nodes
    active_nodes = {nid: d for nid, d in nodes.items()
                    if degree.get(nid, 0) > 0}
    max_raw = max((float(d.get("size", 1)) for d in active_nodes.values()), default=1)
    min_raw = min((float(d.get("size", 1)) for d in active_nodes.values()), default=1)
    size_span = max_raw - min_raw or 1

    for nid, data in active_nodes.items():
        if nid not in pos:
            continue
        x, y = pos[nid]
        inst = data.get("institution", "Others")
        raw_size = float(data.get("size", 1))
        t_norm = ((raw_size - min_raw) / size_span) ** 0.55
        node_s = 12 + 210 * t_norm
        is_hub = nid in top3
        color = hub_color if is_hub else _inst_color(inst)
        alpha = 0.95 if is_hub else 0.72
        ec = "#222" if is_hub else "#888"
        lw = 1.0 if is_hub else 0.25
        ax.scatter(x, y, s=node_s, c=color,
                   zorder=5 if is_hub else 3,
                   edgecolors=ec, linewidths=lw, alpha=alpha)

    # Labels: top-3 only
    label_offset = canvas_r * 0.09
    for nid, _ in sorted(degree.items(), key=lambda x: x[1], reverse=True)[:3]:
        if nid not in pos:
            continue
        x, y = pos[nid]
        ax.text(x, y + label_offset, nid[:12], ha="center", va="bottom",
                fontsize=6.2, fontweight="bold", color="#111", zorder=7,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))

    ax.set_title(title, fontsize=9, fontweight="bold", pad=4, color="#111")

    note = f"top-{vis_note} · " if vis_note else ""
    txt = (f"{note}N={metrics.get('n_nodes','?')}  E={metrics.get('n_edges','?')}  "
           f"ρ={metrics.get('density',0):.3f}\n"
           f"Gini={metrics.get('gini_degree',0):.3f}  "
           f"Giant={metrics.get('giant_component_ratio',0):.2f}  "
           f"Q={metrics.get('modularity_louvain',0):.3f}")
    ax.text(0.50, 0.01, txt, transform=ax.transAxes,
            fontsize=5.8, va="bottom", ha="center", color="#555",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="#CCC", lw=0.4))


def fig_network_sna_twocol() -> None:
    """Horizontal diptych for two-column placement — full ERC (all 67 nodes)."""
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

    G_erc = _build_nx_graph_from_csv(nodes_erc, edges_erc)
    G_a2a = _build_nx_graph_from_csv(nodes_a2a, edges_a2a)

    isolates_erc = set(nx.isolates(G_erc))

    _, deg_erc = _sna_adj(nodes_erc, edges_erc)
    _, deg_a2a = _sna_adj(nodes_a2a, edges_a2a)

    print("  Computing two-col layouts…")
    # ERC: spring layout on giant component only; everything else → outer ring
    gcc_erc = max(nx.connected_components(G_erc), key=len)
    peripheral_erc = {n for n in G_erc.nodes() if n not in gcc_erc}  # isolates + small components
    sub_gcc = G_erc.subgraph(gcc_erc)
    pos_sub = nx.spring_layout(sub_gcc, k=0.40, seed=SEED, iterations=400,
                               weight="weight")
    # Normalize: 80th-percentile distance → 0.60
    vals = list(pos_sub.values())
    xs, ys = [v[0] for v in vals], [v[1] for v in vals]
    cx, cy = float(np.mean(xs)), float(np.mean(ys))
    raw = {n: (p[0] - cx, p[1] - cy) for n, p in pos_sub.items()}
    p80 = float(np.percentile([math.hypot(p[0], p[1]) for p in raw.values()], 80)) or 1.0
    scale = 0.60 / p80
    pos_erc = {n: (p[0] * scale, p[1] * scale) for n, p in raw.items()}
    # All peripheral nodes (isolates + small components) in outer ring r=0.88–1.08
    n_peri = len(peripheral_erc)
    if n_peri > 0:
        rng = np.random.default_rng(SEED)
        for i, nid in enumerate(sorted(peripheral_erc)):
            theta = 2 * math.pi * i / n_peri + rng.uniform(-0.10, 0.10)
            r = 0.88 + rng.uniform(0.0, 0.20)
            pos_erc[nid] = (r * math.cos(theta), r * math.sin(theta))
    isolates_erc = peripheral_erc  # treat all peripheral as "isolates" for drawing

    pos_a2a = _compact_dense_layout(G_a2a)

    # Horizontal diptych
    fig = plt.figure(figsize=(11.0, 5.0), facecolor="white")
    ax_erc = fig.add_axes([0.02, 0.10, 0.45, 0.84])
    ax_a2a = fig.add_axes([0.53, 0.10, 0.45, 0.84])

    _draw_sna_twocol_panel(
        ax_erc, nodes_erc, edges_erc, pos_erc, deg_erc, isolates_erc,
        "ERC-8004  ·  Permissionless DAO",
        m_erc, hub_color="#8B4513",
    )
    _draw_sna_panel_refined(
        ax_a2a, nodes_a2a, edges_a2a, pos_a2a, deg_a2a,
        "Google A2A  ·  Corporate Hierarchy",
        m_a2a, hub_color="#5B2C8D", vis_note=50,
    )

    # Thin vertical divider
    fig.add_artist(
        plt.Line2D([0.498, 0.498], [0.08, 0.97],
                   transform=fig.transFigure,
                   color="#DDDDDD", linewidth=0.8, zorder=10)
    )

    from matplotlib.patches import Patch
    handles = [Patch(color=c, label=lbl) for lbl, c in INST_PALETTE.items()]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles),
               fontsize=7, frameon=False, bbox_to_anchor=(0.5, 0.005))

    fig.text(0.50, 0.990, "Co-participation Governance Networks",
             ha="center", va="top", fontsize=10, fontweight="bold", color="#111")

    _save(fig, "network-sna-2col")
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUTPUT_FIGS.mkdir(parents=True, exist_ok=True)
    print("• BERTopic + CryptoBERT integrated dashboard…")
    fig_bertopic_cryptobert_integrated()
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
    print("• Combined pie + lifecycle (topic-pie-erc)…")
    fig_topic_pie_erc()
    print("• SNA network comparison — single-col (network-sna)…")
    fig_network_sna()
    print("• SNA network comparison — two-col (network-sna-2col)…")
    fig_network_sna_twocol()
    print(f"\nDone — output/figures/  +  paper-acm/")
