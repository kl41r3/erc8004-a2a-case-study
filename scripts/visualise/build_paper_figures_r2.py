"""Generate all R2 paper figures for paper-acm/.

Reads from:
  data/annotated/r2/consensus/{erc,a2a}_annotations.json
  data/annotated/r2/validation/validation_report.json
  output/topic_discovery/r2/
  output/network_discourse/r2/
  analysis/r2_*.csv

Output dirs:
  output/figures/r2/      (primary)
  paper-acm/            (copy for LaTeX)

Run:
    uv run python scripts/visualise/build_paper_figures_r2.py
"""
from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import networkx as nx
import numpy as np
import pandas as pd
from dateutil import parser as dateparser
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "paper-acm"
OUTPUT_FIGS = ROOT / "output" / "figures" / "r2"
TD = ROOT / "output" / "topic_discovery" / "r2"
ND = ROOT / "output" / "network_discourse" / "r2"
ANALYSIS = ROOT / "analysis"
CONSENSUS = ROOT / "data" / "annotated" / "r2" / "consensus"
VALIDATION = ROOT / "data" / "annotated" / "r2" / "validation"

# ── Colour palette ────────────────────────────────────────────────────────────
P1 = "#a30543"
P6 = "#4965b0"
ERC_COLOR = P6
A2A_COLOR = P1
SEED = 42

ARG_ORDER = ["Technical", "Process", "Governance-Principle", "Economic", "Off-topic"]
ARG_COLORS = {
    "Technical":            "#4965b0",
    "Process":              "#80cba4",
    "Governance-Principle": "#fbda83",
    "Economic":             "#f36f43",
    "Off-topic":            "#cccccc",
}

EIP_STAGES = [
    ("2025-08-13", "Submission"),
    ("2025-12-01", "Last Call"),
    ("2026-01-29", "Mainnet"),
]


def _save(fig, stem: str) -> None:
    OUTPUT_FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        path = OUTPUT_FIGS / f"{stem}.{ext}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
    # copy to paper dir
    for ext in ("pdf", "png"):
        src = OUTPUT_FIGS / f"{stem}.{ext}"
        dst = PAPER_DIR / f"{stem}.{ext}"
        shutil.copy2(src, dst)
    print(f"  Saved: {stem}")


def _load_consensus(case: str) -> list[dict]:
    """Load consensus annotations for 'erc' or 'a2a'."""
    p = CONSENSUS / f"{case}_annotations.json"
    if not p.exists():
        print(f"  WARNING: {p} not found — skipping")
        return []
    return json.loads(p.read_text())


def _get_field(r: dict, field: str) -> str:
    ann = r.get("annotation") or {}
    return ann.get(field) or r.get(field) or ""


def _case_label(r: dict) -> str:
    """Normalize _case field to canonical label."""
    case = r.get("_case", "")
    if "A2A" in case or "a2a" in case.lower() or "Google" in case:
        return "Google-A2A"
    return "ERC-cluster"


# ── Figure: ICR heatmap ───────────────────────────────────────────────────────

def fig_icr_heatmap() -> None:
    report_path = VALIDATION / "validation_report.json"
    if not report_path.exists():
        print("  ICR report not found — skipping heatmap")
        return

    erc_report = json.loads(report_path.read_text())

    a2a_report_path = ROOT / "data" / "annotated" / "r2" / "a2a" / "validation" / "validation_report.json"
    a2a_report = json.loads(a2a_report_path.read_text()) if a2a_report_path.exists() else None

    fields = ["argument_type", "stance", "consensus_signal", "stakeholder_institution"]
    field_labels = ["Argument\nType", "Stance", "Consensus\nSignal", "Institution"]
    pairs = ["DS↔GLM", "DS↔KM", "GLM↔KM", "Fleiss' κ"]
    pair_keys = ["deepseek↔glm", "deepseek↔kimi", "glm↔kimi"]

    def extract_matrix(report) -> np.ndarray:
        pw = report.get("pairwise_kappa", {})
        fk = report.get("fleiss_kappa", {})
        mat = np.zeros((4, 4))
        for j, f in enumerate(fields):
            for i, pk in enumerate(pair_keys):
                mat[i, j] = pw.get(f, {}).get(pk, {}).get("κ", 0.0)
            mat[3, j] = fk.get(f, 0.0)
        return mat

    erc_mat = extract_matrix(erc_report)
    n_cases = 2 if a2a_report else 1
    fig, axes = plt.subplots(1, n_cases, figsize=(6 * n_cases, 3.6))
    if n_cases == 1:
        axes = [axes]

    for ax, mat, title in zip(axes,
                               [erc_mat] + ([extract_matrix(a2a_report)] if a2a_report else []),
                               ["ERC Agent Cluster\n($N=1{,}664$)", "Google A2A\n($N=?$)"]):
        im = ax.imshow(mat, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
        ax.set_xticks(range(4))
        ax.set_xticklabels(field_labels, fontsize=8)
        ax.set_yticks(range(4))
        ax.set_yticklabels(pairs, fontsize=8)
        ax.set_title(title, fontsize=9, fontweight="bold")
        for i in range(4):
            for j in range(4):
                v = mat[i, j]
                text_color = "white" if (v < 0.25 or v > 0.7) else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=9, color=text_color, fontweight="bold")
        for i in range(3):
            ax.axhline(2.5, color="white", lw=1.5)

    plt.colorbar(im, ax=axes[-1], label="κ value", shrink=0.85)

    # Landis-Koch band annotations
    for ax in axes:
        ax.text(1.02, 0.9, "≥0.80 Almost Perfect", transform=ax.transAxes,
                fontsize=6.5, color="#2d7a2d")
        ax.text(1.02, 0.76, "0.60–0.80 Substantial", transform=ax.transAxes,
                fontsize=6.5, color="#5a9e2f")
        ax.text(1.02, 0.62, "0.40–0.60 Moderate", transform=ax.transAxes,
                fontsize=6.5, color="#b8a020")
        ax.text(1.02, 0.48, "0.20–0.40 Fair", transform=ax.transAxes,
                fontsize=6.5, color="#c87020")
        ax.text(1.02, 0.34, "<0.20 Slight", transform=ax.transAxes,
                fontsize=6.5, color="#c83020")

    plt.suptitle("Pairwise Cohen's κ and Fleiss' κ — Inter-Coder Reliability",
                 fontsize=10, fontweight="bold", y=1.02)
    plt.tight_layout()
    _save(fig, "r2-fig-icr-heatmap")
    plt.close(fig)


# ── Figure: argument-type pie + ERC lifecycle ─────────────────────────────────

def fig_topic_pie_erc() -> None:
    erc_recs = _load_consensus("erc")
    a2a_recs = _load_consensus("a2a")
    if not erc_recs:
        print("  No ERC consensus data — skipping pie figure")
        return

    def pct_counts(recs):
        total = len(recs) or 1
        counts = Counter(_get_field(r, "argument_type") for r in recs)
        return [100.0 * counts.get(t, 0) / total for t in ARG_ORDER]

    erc_pct = pct_counts(erc_recs)
    a2a_pct = pct_counts(a2a_recs) if a2a_recs else [0] * len(ARG_ORDER)
    pie_colors = [ARG_COLORS.get(t, "#aaa") for t in ARG_ORDER]

    # Lifecycle bins
    dated = []
    for r in erc_recs:
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
    min_dt = dated[0][0] if dated else None
    if min_dt:
        for dt, atype in dated:
            idx = (dt - min_dt).days // bin_days
            bins[idx][atype] += 1

    indices = sorted(bins.keys())
    bin_dates = [min_dt + timedelta(days=i * bin_days) for i in indices] if min_dt else []

    fig = plt.figure(figsize=(12, 5))
    gs = gridspec.GridSpec(2, 2, width_ratios=[1, 2.2], hspace=0.5, wspace=0.08)

    def draw_pie(ax, pcts, colors, title, n_total):
        wedges, texts, autotexts = ax.pie(
            pcts, colors=colors, autopct=lambda p: f"{p:.1f}%" if p >= 4 else "",
            startangle=90, pctdistance=0.72,
            wedgeprops=dict(linewidth=0.6, edgecolor="white"),
        )
        for at in autotexts:
            at.set_fontsize(7.5)
        ax.set_title(f"{title}\n$N={n_total}$", fontsize=9, pad=4)

    draw_pie(fig.add_subplot(gs[0, 0]), erc_pct, pie_colors, "ERC Cluster", len(erc_recs))
    draw_pie(fig.add_subplot(gs[1, 0]), a2a_pct, pie_colors, "Google A2A", len(a2a_recs))

    ax_bar = fig.add_subplot(gs[:, 1])
    if indices:
        bottoms = np.zeros(len(indices))
        for atype in ARG_ORDER:
            heights = [bins[i].get(atype, 0) for i in indices]
            ax_bar.bar(range(len(indices)), heights, bottom=bottoms,
                       color=ARG_COLORS.get(atype, "#ccc"), label=atype,
                       edgecolor="white", linewidth=0.5)
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

        tick_pos, tick_lbl, last_month = [], [], None
        for i, bd in enumerate(bin_dates):
            if bd.month != last_month:
                tick_pos.append(i)
                tick_lbl.append(bd.strftime("%b '%y"))
                last_month = bd.month
        ax_bar.set_xticks(tick_pos)
        ax_bar.set_xticklabels(tick_lbl, rotation=40, ha="right")
        ax_bar.set_ylabel("Records per 2-week bin")
        ax_bar.set_title("ERC Cluster: Argument Type over Lifecycle (2-week bins)", fontsize=10)
        ax_bar.spines[["top", "right"]].set_visible(False)
        ax_bar.legend(loc="upper right", frameon=False, ncol=2, fontsize=8)

    # legend for pies
    from matplotlib.patches import Patch
    handles = [Patch(color=ARG_COLORS[t], label=t) for t in ARG_ORDER]
    fig.legend(handles=handles, loc="lower left", ncol=3, fontsize=8,
               bbox_to_anchor=(0.0, -0.02), frameon=False)

    fig.tight_layout()
    _save(fig, "r2-topic-pie-erc")
    plt.close(fig)


# ── Figure: stance × argument-type heatmap ───────────────────────────────────

def fig_stance_heatmap() -> None:
    erc_recs = _load_consensus("erc")
    a2a_recs = _load_consensus("a2a")
    if not erc_recs:
        return

    stances = ["Support", "Modify", "Neutral", "Oppose", "Off-topic"]

    def cross_tab(recs):
        mat = np.zeros((len(stances), len(ARG_ORDER)))
        for r in recs:
            s = _get_field(r, "stance")
            a = _get_field(r, "argument_type")
            if s in stances and a in ARG_ORDER:
                mat[stances.index(s), ARG_ORDER.index(a)] += 1
        row_sums = mat.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        return mat / row_sums * 100

    erc_mat = cross_tab(erc_recs)
    a2a_mat = cross_tab(a2a_recs) if a2a_recs else np.zeros_like(erc_mat)

    n_cols = 2 if a2a_recs else 1
    fig, axes = plt.subplots(1, n_cols, figsize=(5.5 * n_cols, 4.2), sharey=True)
    if n_cols == 1:
        axes = [axes]

    for ax, mat, title in zip(axes,
                               [erc_mat, a2a_mat],
                               ["ERC Agent Cluster", "Google A2A"]):
        im = ax.imshow(mat, cmap="YlOrRd", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(len(ARG_ORDER)))
        ax.set_xticklabels([a.replace("-", "-\n") for a in ARG_ORDER], fontsize=8)
        ax.set_yticks(range(len(stances)))
        ax.set_yticklabels(stances, fontsize=8)
        ax.set_title(title, fontsize=10, fontweight="bold")
        for i in range(len(stances)):
            for j in range(len(ARG_ORDER)):
                v = mat[i, j]
                if v > 5:
                    ax.text(j, i, f"{v:.0f}%", ha="center", va="center",
                            fontsize=7.5, color="white" if v > 60 else "black")

    plt.colorbar(im, ax=axes[-1], label="% within stance row", shrink=0.85)
    plt.suptitle("Stance × Argument-Type Cross-tabulation", fontsize=11, fontweight="bold")
    plt.tight_layout()
    _save(fig, "r2-topic-stance-heatmap")
    plt.close(fig)


# ── Figure: BERTopic divergence ───────────────────────────────────────────────

def fig_bertopic_divergence() -> None:
    p = TD / "comparative_discourse" / "divergence_table.csv"
    if not p.exists():
        print("  BERTopic divergence_table.csv not found — skipping")
        return
    df = pd.read_csv(p)
    df = df.sort_values("abs_diff", ascending=True)
    df["signed"] = df["erc8004_pct"] - df["a2a_pct"]
    df["short"] = df.apply(
        lambda r: f"T{int(r.topic_id)}: "
                  + ", ".join(str(r.keywords).split(", ")[:3]),
        axis=1,
    )

    # Load JSD from summary
    summary_p = TD / "comparative_discourse" / "comparison_summary.json"
    jsd_val = "?"
    if summary_p.exists():
        summary = json.loads(summary_p.read_text())
        jsd_val = f"{summary.get('global_jsd', 0):.3f}"

    fig, ax = plt.subplots(figsize=(7.0, 5.6))
    colors = [ERC_COLOR if v > 0 else A2A_COLOR for v in df["signed"]]
    ax.barh(df["short"], df["signed"], color=colors, edgecolor="white", linewidth=0.5)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("ERC Cluster share − A2A share (pp)")
    ax.set_title(f"BERTopic cross-case divergence (JSD = {jsd_val})")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=ERC_COLOR, label="ERC Cluster dominant"),
        Patch(color=A2A_COLOR, label="A2A dominant"),
    ], loc="lower right", frameon=False)

    _save(fig, "r2-fig-bertopic-divergence")
    plt.close(fig)


# ── Figure: Thematic-LM combined butterfly chart ─────────────────────────────

def fig_combined_themes() -> None:
    coded_p = TD / "thematic_lm" / "coded_records.json"
    themes_p = TD / "thematic_lm" / "themes.json"
    compare_p = ND / "sociosemantic" / "theme_actor_comparison.csv"

    if not coded_p.exists() or not themes_p.exists():
        print("  Thematic-LM output not found — skipping")
        return

    coded = json.loads(coded_p.read_text())
    themes = json.loads(themes_p.read_text())
    label_map = {t["theme_id"]: t["label"] for t in themes}

    rec_df = pd.DataFrame(coded)
    rec_df = rec_df[rec_df["theme_id"].notna()]

    def case_of(rid: str) -> str:
        rid_lower = (rid or "").lower()
        if (rid_lower.startswith("erc") or "forum" in rid_lower
                or "ethereum" in rid_lower or "github.com/ethereum" in rid_lower):
            return "ERC-cluster"
        return "Google-A2A"

    rec_df["case"] = rec_df["record_id"].map(case_of)
    total = rec_df.groupby("case").size()
    if total.empty:
        print("  No coded records found — skipping")
        return
    counts = rec_df.groupby(["case", "theme_id"]).size().unstack(fill_value=0)
    pct_heat = (counts.divide(total, axis=0) * 100.0).T

    erc_col = next((c for c in pct_heat.columns if "ERC" in c), None)
    a2a_col = next((c for c in pct_heat.columns if c != erc_col), None)
    if not erc_col or not a2a_col:
        print(f"  Could not identify case columns: {list(pct_heat.columns)} — skipping")
        return

    pct_heat["delta"] = pct_heat[erc_col] - pct_heat[a2a_col]
    pct_heat = pct_heat.sort_values("delta", ascending=False)
    theme_order = pct_heat.index.tolist()
    n_themes = len(theme_order)

    def _wrap(tid):
        base = f"{tid}: {label_map.get(tid, tid)}"
        if len(base) <= 36:
            return base
        if " & " in base:
            return base.replace(" & ", " &\n", 1)
        parts = base.split(": ", 1)
        if len(parts) == 2 and len(parts[1]) > 28:
            mid = len(parts[1]) // 2
            for off in range(10):
                for d in (1, -1):
                    idx = mid + off * d
                    if 0 < idx < len(parts[1]) and parts[1][idx] == " ":
                        parts[1] = parts[1][:idx] + "\n" + parts[1][idx + 1:]
                        return ": ".join(parts)
        return base

    theme_labels = [_wrap(tid) for tid in theme_order]
    erc_share = [float(pct_heat.loc[tid, erc_col]) for tid in theme_order]
    a2a_share = [float(pct_heat.loc[tid, a2a_col]) for tid in theme_order]

    erc_but, a2a_but = [0.0] * n_themes, [0.0] * n_themes
    if compare_p.exists():
        df_but = pd.read_csv(compare_p).set_index("theme_id")
        erc_but = [float(df_but.loc[tid, "erc8004_pct"]) if tid in df_but.index else 0.0
                   for tid in theme_order]
        a2a_but = [float(df_but.loc[tid, "a2a_pct"]) if tid in df_but.index else 0.0
                   for tid in theme_order]

    fig, ax = plt.subplots(figsize=(7.2, max(4.2, n_themes * 0.38)))
    y = np.arange(n_themes)
    bh = 0.50
    ax.barh(y, erc_share, bh, color=ERC_COLOR, alpha=0.55, lw=0.3, label="ERC record share")
    ax.barh(y, [-v for v in a2a_share], bh, color=A2A_COLOR, alpha=0.55, lw=0.3, label="A2A record share")
    ax.plot(erc_but, y, color=ERC_COLOR, lw=2.5, marker='D', ms=4.5,
            markerfacecolor='white', markeredgecolor=ERC_COLOR, markeredgewidth=1.2,
            label="ERC actor participation")
    ax.plot([-v for v in a2a_but], y, color=A2A_COLOR, lw=2.5, marker='s', ms=4.5,
            markerfacecolor='white', markeredgecolor=A2A_COLOR, markeredgewidth=1.2,
            label="A2A actor participation")

    for i in range(n_themes):
        if erc_but[i] > 5:
            ax.text(erc_but[i] + 1.2, i, f"{erc_but[i]:.0f}%",
                    va="center", fontsize=6, color=ERC_COLOR, fontweight="bold")
        if a2a_but[i] > 5:
            ax.text(-a2a_but[i] - 1.2, i, f"{a2a_but[i]:.0f}%",
                    va="center", ha="right", fontsize=6, color=A2A_COLOR, fontweight="bold")

    ax.axvline(0, color="#333", lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(theme_labels, fontsize=6.5, linespacing=0.92)
    ax.invert_yaxis()

    max_val = max(max(erc_share + erc_but), max(a2a_share + a2a_but), 1)
    x_max = max(max_val * 1.45, 40)
    ax.set_xlim(-40, x_max)
    ticks = sorted(set(list(range(-40, int(x_max) + 20, 20)) + [0]))
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{abs(t):.0f}" for t in ticks])
    ax.set_xlabel("Record share / Actor participation rate (%)", fontsize=7)
    ax.set_title("Thematic-LM (R2): record share (bar) & actor participation (line)",
                 fontsize=8, fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=6, loc="lower right", ncol=1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.grid(True, alpha=0.12, lw=0.3)

    # JSD from summary
    ss_p = ND / "sociosemantic" / "ss_metrics.json"
    if ss_p.exists():
        pass  # JSD comes from thematic, not sociosemantic
    stage1_p = TD / "thematic_lm" / "stage2_clusters.json"
    # Try to compute JSD from coded records
    try:
        ec = Counter(rec_df[rec_df["case"] == erc_col]["theme_id"])
        ac = Counter(rec_df[rec_df["case"] == a2a_col]["theme_id"])
        all_themes = set(ec) | set(ac)
        e_tot = sum(ec.values()) or 1
        a_tot = sum(ac.values()) or 1
        p_e = np.array([ec.get(t, 0) / e_tot for t in all_themes])
        p_a = np.array([ac.get(t, 0) / a_tot for t in all_themes])
        m = 0.5 * (p_e + p_a)
        with np.errstate(divide="ignore", invalid="ignore"):
            kl_e = np.where(p_e > 0, p_e * np.log2(p_e / np.where(m > 0, m, 1e-10)), 0)
            kl_a = np.where(p_a > 0, p_a * np.log2(p_a / np.where(m > 0, m, 1e-10)), 0)
        jsd = 0.5 * kl_e.sum() + 0.5 * kl_a.sum()
        ax.text(0.97, 0.97, f"JSD = {jsd:.3f}", transform=ax.transAxes,
                fontsize=7, ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.25", fc="#F8F9FA", ec="#CCCCCC", lw=0.5))
    except Exception:
        pass

    fig.tight_layout()
    _save(fig, "r2-fig-combined-themes")
    plt.close(fig)


# ── Figure: SNA two-column network ───────────────────────────────────────────

def fig_network_sna() -> None:
    erc_nodes_p = ANALYSIS / "r2_network_erc_nodes.csv"
    erc_edges_p = ANALYSIS / "r2_network_erc_edges.csv"
    a2a_nodes_p = ANALYSIS / "r2_network_a2a_nodes.csv"
    a2a_edges_p = ANALYSIS / "r2_network_a2a_edges.csv"

    if not erc_nodes_p.exists():
        print("  SNA CSV files not found — skipping")
        return

    def load_graph(nodes_p, edges_p, top_n=None):
        nodes_df = pd.read_csv(nodes_p)
        edges_df = pd.read_csv(edges_p)
        G = nx.Graph()
        for _, row in nodes_df.iterrows():
            G.add_node(row["id"], institution=row.get("stakeholder_institution", "Unknown"),
                       n_records=row.get("weight", 1))
        for _, row in edges_df.iterrows():
            G.add_edge(row["source"], row["target"], weight=row.get("weight", 1))
        if top_n and len(G.nodes) > top_n:
            top = sorted(G.degree(), key=lambda x: -x[1])[:top_n]
            G = G.subgraph([n for n, _ in top]).copy()
        return G

    INST_COLOR = {
        "Google": "#FF5252", "Microsoft": "#FFD93D",
        "MetaMask": "#FF9F43", "Ethereum Foundation": "#748EFF",
        "Coinbase": "#26D9C7", "Salesforce": "#00A1E0",
        "Atlassian": "#0052CC", "Cisco": "#6FAE8C",
        "Independent": "#82EDB2", "Unknown": "#6B7280",
    }

    G_erc = load_graph(erc_nodes_p, erc_edges_p)
    G_a2a = load_graph(a2a_nodes_p, a2a_edges_p, top_n=50)

    fig, axes = plt.subplots(1, 2, figsize=(16, 8), facecolor="#0D1117")
    for ax, G, title in [(axes[0], G_erc, "ERC Agent Cluster"),
                          (axes[1], G_a2a, "Google A2A (top-50)")]:
        ax.set_facecolor("#161B22")
        if len(G.nodes) == 0:
            ax.set_title(title, color="white")
            ax.axis("off")
            continue
        pos = nx.spring_layout(G, weight="weight", seed=SEED, k=1.5)
        degrees = dict(G.degree(weight="weight"))
        max_d = max(degrees.values()) if degrees else 1
        node_colors = [INST_COLOR.get(
            G.nodes[n].get("institution", "Unknown"), "#6B7280") for n in G.nodes()]
        node_sizes = [80 + 400 * degrees.get(n, 0) / max_d for n in G.nodes()]
        weights = [d.get("weight", 1) for _, _, d in G.edges(data=True)]
        max_w = max(weights) if weights else 1
        edge_widths = [0.3 + 1.5 * w / max_w for w in weights]
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.2, width=edge_widths, edge_color="#aaa")
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                               node_size=node_sizes, alpha=0.9)
        top5 = sorted(degrees, key=lambda n: -degrees[n])[:5]
        nx.draw_networkx_labels(G, pos, labels={n: n for n in top5}, ax=ax,
                                font_size=6, font_color="white")
        ax.set_title(f"{title}\n(N={G.number_of_nodes()}, E={G.number_of_edges()})",
                     color="white", fontsize=11)
        ax.axis("off")

    plt.tight_layout(pad=0.5)
    _save(fig, "r2-network-sna-2col")
    plt.close(fig)


# ── Figure: per-actor Shannon entropy ────────────────────────────────────────

def fig_ss_entropy() -> None:
    erc_p = ND / "sociosemantic" / "actor_diversity_erc8004.csv"
    a2a_p = ND / "sociosemantic" / "actor_diversity_googlea2a.csv"

    if not erc_p.exists():
        print("  Socio-semantic actor diversity CSVs not found — skipping")
        return

    erc_h = pd.read_csv(erc_p)["entropy"].dropna().values
    a2a_h = pd.read_csv(a2a_p)["entropy"].dropna().values if a2a_p.exists() else np.array([])

    x_max = max(erc_h.max(), a2a_h.max() if len(a2a_h) else 0) + 0.3
    x_all = np.linspace(0, x_max, 600)

    kde_erc = gaussian_kde(np.concatenate([-erc_h, erc_h]), bw_method=0.3)
    y_erc = kde_erc(x_all) * 2
    y_top = y_erc.max()

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.axvspan(0, 1, alpha=0.08, color="#888888", zorder=0)
    ax.axvline(1, color="#888888", lw=0.9, linestyle="--", alpha=0.55, zorder=1)
    ax.text(0.5, y_top * 1.02, "0–1 zone", ha="center", fontsize=9,
            color="#555555", style="italic")

    ax.fill_between(x_all, y_erc, alpha=0.38, color=ERC_COLOR, zorder=2)
    ax.plot(x_all, y_erc, color=ERC_COLOR, lw=2.0, zorder=3,
            label=f"ERC Cluster (N={len(erc_h)}, μ={erc_h.mean():.2f})")

    if len(a2a_h) > 1:
        kde_a2a = gaussian_kde(np.concatenate([-a2a_h, a2a_h]), bw_method=0.3)
        y_a2a = kde_a2a(x_all) * 2
        ax.fill_between(x_all, y_a2a, alpha=0.38, color=A2A_COLOR, zorder=2)
        ax.plot(x_all, y_a2a, color=A2A_COLOR, lw=2.0, zorder=3,
                label=f"Google A2A (N={len(a2a_h)}, μ={a2a_h.mean():.2f})")

    ax.set_xlim(0, x_max)
    ax.set_ylim(0)
    ax.set_xlabel("Actor topic-diversity entropy H (bits)")
    ax.set_ylabel("Density")
    ax.set_title("Per-actor Shannon entropy over Thematic-LM themes (R2)")
    ax.legend(frameon=False, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)

    _save(fig, "r2-fig-ss-entropy")
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUTPUT_FIGS.mkdir(parents=True, exist_ok=True)
    print("• ICR heatmap…")
    fig_icr_heatmap()
    print("• Argument-type pie + ERC lifecycle…")
    fig_topic_pie_erc()
    print("• Stance × Argument-type heatmap…")
    fig_stance_heatmap()
    print("• BERTopic divergence…")
    fig_bertopic_divergence()
    print("• Thematic-LM combined butterfly…")
    fig_combined_themes()
    print("• SNA two-column network…")
    fig_network_sna()
    print("• Socio-semantic entropy…")
    fig_ss_entropy()
    print(f"\nDone — {OUTPUT_FIGS}  +  paper-acm/")
