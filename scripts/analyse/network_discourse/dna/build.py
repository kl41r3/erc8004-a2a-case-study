"""
Discourse Network Analysis — network construction.

Reference: Leifeld (2013), Policy Studies Journal, 41(1):169-198.

Two projections from the Actor × Theme affiliation matrix:
  - Congruence network: edge(a,b) if both hold same-sign stance on ≥1 theme
  - Conflict network:   edge(a,b) if they hold opposite stances on ≥1 theme
"""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT / "scripts/analyse/network_discourse"))
from loader import load_joined


def affiliation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Actor × Theme matrix; value = mean stance_val across all that actor's
    comments on that theme. NaN if the actor never touched the theme.
    """
    return (
        df.groupby(["author", "theme_id"])["stance_val"]
        .mean()
        .unstack(fill_value=np.nan)
    )


def congruence_network(mat: pd.DataFrame, min_shared: int = 1) -> nx.Graph:
    """
    Congruence (alliance) network.
    weight = # themes on which both actors hold the same-sign stance.
    """
    G = nx.Graph()
    actors = mat.index.tolist()
    G.add_nodes_from(actors)

    vals = mat.values
    idx = {a: i for i, a in enumerate(actors)}

    for i, a in enumerate(actors):
        for j in range(i + 1, len(actors)):
            b = actors[j]
            va, vb = vals[i], vals[j]
            both_known = ~(np.isnan(va) | np.isnan(vb))
            n_shared = both_known.sum()
            if n_shared < min_shared:
                continue
            congruent = int(((va[both_known] * vb[both_known]) > 0).sum())
            if congruent > 0:
                G.add_edge(a, b, weight=congruent, shared=int(n_shared))
    return G


def conflict_network(mat: pd.DataFrame, min_shared: int = 1) -> nx.Graph:
    """
    Conflict network.
    weight = # themes on which actors hold strictly opposing stances.
    """
    G = nx.Graph()
    actors = mat.index.tolist()
    G.add_nodes_from(actors)

    vals = mat.values

    for i, a in enumerate(actors):
        for j in range(i + 1, len(actors)):
            b = actors[j]
            va, vb = vals[i], vals[j]
            both_known = ~(np.isnan(va) | np.isnan(vb))
            n_shared = both_known.sum()
            if n_shared < min_shared:
                continue
            conflict = int(((va[both_known] * vb[both_known]) < 0).sum())
            if conflict > 0:
                G.add_edge(a, b, weight=conflict, shared=int(n_shared))
    return G


def graph_to_edgelist(G: nx.Graph) -> pd.DataFrame:
    rows = [
        {"actor_a": u, "actor_b": v, **d} for u, v, d in G.edges(data=True)
    ]
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["actor_a", "actor_b", "weight", "shared"]
    )


def build(min_shared: int = 1) -> dict:
    """
    Returns dict with keys: df, matrices, networks (per case).
    """
    df = load_joined()
    result: dict = {"df": df, "by_case": {}}

    for case in ("ERC-8004", "Google-A2A"):
        sub = df[df["case"] == case]
        mat = affiliation_matrix(sub)
        cong = congruence_network(mat, min_shared=min_shared)
        conf = conflict_network(mat, min_shared=min_shared)
        result["by_case"][case] = {
            "sub": sub,
            "mat": mat,
            "congruence": cong,
            "conflict": conf,
        }

    return result
