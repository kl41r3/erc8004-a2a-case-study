"""
DNA network metrics:
  - Density
  - Modularity (Louvain, colored by stakeholder_institution)
  - Polarization index
  - Top-5 betweenness centrality actors
  - Theme participation counts
"""
from __future__ import annotations

import networkx as nx
import networkx.algorithms.community as nx_comm
import pandas as pd
import numpy as np


def _louvain_modularity(G: nx.Graph) -> float:
    if len(G.edges) == 0:
        return 0.0
    communities = nx_comm.louvain_communities(G, weight="weight", seed=42)
    return nx_comm.modularity(G, communities, weight="weight")


def _polarization_index(G: nx.Graph, sub: pd.DataFrame) -> float:
    """
    Fraction of edges that cross stakeholder_institution boundaries.
    Higher → more cross-group interaction (less polarized by institution).
    """
    if len(G.edges) == 0:
        return float("nan")
    inst = sub.drop_duplicates("author").set_index("author")["stakeholder_institution"]
    cross = 0
    total = 0
    for u, v in G.edges():
        iu = inst.get(u, "Unknown")
        iv = inst.get(v, "Unknown")
        total += 1
        if iu != iv:
            cross += 1
    return cross / total if total > 0 else float("nan")


def _gini(vals: list[float]) -> float:
    if not vals:
        return 0.0
    arr = sorted(vals)
    n = len(arr)
    total = sum(arr)
    if total == 0:
        return 0.0
    gini_num = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(arr))
    return round(gini_num / (n * total), 4)


def compute(case_data: dict, sub: pd.DataFrame) -> dict:
    """
    case_data: {"congruence": G, "conflict": G, "mat": DataFrame}
    """
    G_cong = case_data["congruence"]
    G_conf = case_data["conflict"]
    mat = case_data["mat"]

    n_actors = len(mat.index)
    n_themes = len(mat.columns)
    n_records = len(sub)

    # Congruence network stats
    cong_density = nx.density(G_cong)
    cong_edges = G_cong.number_of_edges()
    cong_mod = _louvain_modularity(G_cong)
    cong_polar = _polarization_index(G_cong, sub)

    # Conflict network stats
    conf_edges = G_conf.number_of_edges()

    # Betweenness (congruence network)
    if cong_edges > 0:
        bc = nx.betweenness_centrality(G_cong, weight="weight", normalized=True)
        bc_vals = list(bc.values())
        top_bc = sorted(bc.items(), key=lambda x: -x[1])[:5]
        bc_sum = sum(bc_vals)
        top3_bc_share = (
            sum(v for _, v in top_bc[:3]) / bc_sum if bc_sum > 0 else 0.0
        )
        bc_gini = _gini(bc_vals)
    else:
        bc_vals, top_bc = [], []
        top3_bc_share, bc_gini = 0.0, 0.0

    # Theme distribution per case
    theme_counts = sub["theme_id"].value_counts().to_dict()

    # Actor theme diversity (entropy)
    actor_themes = sub.groupby("author")["theme_id"].nunique()
    mean_theme_diversity = float(actor_themes.mean())

    return {
        "n_actors": n_actors,
        "n_themes_active": n_themes,
        "n_records": n_records,
        "congruence": {
            "edges": cong_edges,
            "density": round(cong_density, 4),
            "modularity": round(cong_mod, 4),
            "polarization_index": round(cong_polar, 4) if not np.isnan(cong_polar) else None,
            "top_betweenness": [{"actor": a, "bc": round(v, 4)} for a, v in top_bc],
            "betweenness_gini": bc_gini,
            "top3_betweenness_share": round(top3_bc_share, 4),
        },
        "conflict": {
            "edges": conf_edges,
        },
        "theme_participation": theme_counts,
        "mean_actor_theme_diversity": round(mean_theme_diversity, 3),
    }
