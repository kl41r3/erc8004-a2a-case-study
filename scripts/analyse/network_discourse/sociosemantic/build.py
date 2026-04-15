"""
Socio-semantic Bipartite Network — construction.

Reference: Roth & Cointet (2010), Social Networks, 32(1):16-29.

Two-mode (bipartite) graph: Actor ↔ Theme
  - Edge(actor, theme) = number of comments actor made in that theme
  - Actor-actor projection: B @ B.T (co-participation count)
  - Theme-theme projection: B.T @ B (co-discussed by same actors)
"""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import entropy as scipy_entropy

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT / "scripts/analyse/network_discourse"))
from loader import load_joined


# ── helpers ────────────────────────────────────────────────────────────────

def _gini(values: np.ndarray) -> float:
    """Gini coefficient of a non-negative array."""
    v = np.sort(values.astype(float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * (idx * v).sum() / (n * v.sum())) - (n + 1) / n)


def _shannon_entropy(counts: np.ndarray) -> float:
    p = counts / counts.sum()
    return float(scipy_entropy(p, base=2))


# ── bipartite matrix ────────────────────────────────────────────────────────

def actor_theme_matrix(sub: pd.DataFrame) -> pd.DataFrame:
    """
    Actor × Theme count matrix.
    B[actor][theme] = number of comments actor made on theme.
    """
    return (
        sub.groupby(["author", "theme_id"])
        .size()
        .unstack(fill_value=0)
    )


# ── projections ────────────────────────────────────────────────────────────

def actor_projection(B: pd.DataFrame) -> nx.Graph:
    """
    Weighted Actor-Actor network via B @ B.T.
    Weight = number of shared theme-comment co-occurrences.
    Self-loops removed.
    """
    M = B.values.astype(float)
    W = M @ M.T
    np.fill_diagonal(W, 0)

    G = nx.Graph()
    actors = B.index.tolist()
    G.add_nodes_from(actors)
    for i, a in enumerate(actors):
        for j in range(i + 1, len(actors)):
            w = W[i, j]
            if w > 0:
                G.add_edge(a, actors[j], weight=float(w))
    return G


def theme_projection(B: pd.DataFrame) -> nx.Graph:
    """
    Weighted Theme-Theme network via B.T @ B.
    Weight = number of actors who discuss both themes.
    """
    M = B.values.astype(float)
    W = M.T @ M
    np.fill_diagonal(W, 0)

    G = nx.Graph()
    themes = B.columns.tolist()
    G.add_nodes_from(themes)
    for i, t in enumerate(themes):
        for j in range(i + 1, len(themes)):
            w = W[i, j]
            if w > 0:
                G.add_edge(t, themes[j], weight=float(w))
    return G


# ── actor diversity ─────────────────────────────────────────────────────────

def actor_diversity(B: pd.DataFrame, sub: pd.DataFrame) -> pd.DataFrame:
    """
    Per-actor metrics:
      - n_comments: total comments
      - n_themes: number of distinct themes
      - entropy: Shannon entropy of theme distribution
      - gini: Gini coefficient of theme comment counts
      - top_theme: most discussed theme
    """
    rows = []
    inst = sub.drop_duplicates("author").set_index("author")["stakeholder_institution"]
    for actor in B.index:
        counts = B.loc[actor].values
        active = counts[counts > 0]
        rows.append(
            {
                "author": actor,
                "n_comments": int(counts.sum()),
                "n_themes": int((counts > 0).sum()),
                "entropy": _shannon_entropy(active) if len(active) > 1 else 0.0,
                "gini": _gini(counts),
                "top_theme": B.columns[counts.argmax()],
                "stakeholder_institution": inst.get(actor, "Unknown"),
            }
        )
    return pd.DataFrame(rows).sort_values("n_comments", ascending=False).reset_index(drop=True)


# ── theme concentration ─────────────────────────────────────────────────────

def theme_concentration(B: pd.DataFrame) -> pd.DataFrame:
    """
    Per-theme metrics:
      - n_comments: total comments on theme
      - n_actors: number of distinct actors
      - gini_actors: Gini of per-actor comment counts → how concentrated
      - hhi: Herfindahl-Hirschman Index
    """
    rows = []
    for theme in B.columns:
        counts = B[theme].values
        active = counts[counts > 0]
        total = int(counts.sum())
        n_act = int((counts > 0).sum())
        hhi = float(np.sum((active / total) ** 2)) if total > 0 else 0.0
        rows.append(
            {
                "theme_id": theme,
                "n_comments": total,
                "n_actors": n_act,
                "gini_actors": _gini(active) if len(active) > 0 else 0.0,
                "hhi": round(hhi, 4),
            }
        )
    return pd.DataFrame(rows).sort_values("n_comments", ascending=False).reset_index(drop=True)


# ── main build ──────────────────────────────────────────────────────────────

def build() -> dict:
    df = load_joined()
    result: dict = {"df": df, "by_case": {}}

    for case in ("ERC-8004", "Google-A2A"):
        sub = df[df["case"] == case]
        B = actor_theme_matrix(sub)
        G_actor = actor_projection(B)
        G_theme = theme_projection(B)
        div = actor_diversity(B, sub)
        conc = theme_concentration(B)
        result["by_case"][case] = {
            "sub": sub,
            "B": B,
            "actor_graph": G_actor,
            "theme_graph": G_theme,
            "actor_diversity": div,
            "theme_concentration": conc,
        }

    return result
