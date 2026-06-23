"""
build_network_r2.py — Build SNA co-participation networks from R2 consensus annotations.

For each case (ERC cluster, Google A2A), two actors are linked if they both
participated in the same discussion thread (forum topic or GitHub issue/PR).

Output:
  analysis/r2_network_erc_{nodes,edges}.csv
  analysis/r2_network_a2a_{nodes,edges}.csv
  analysis/r2_network_a2a_top50_{nodes,edges}.csv   (top-50 subset for viz)
  analysis/r2_network_metrics_table.csv

Usage:
  uv run python scripts/analyse/build_network_r2.py
"""

import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CONSENSUS_DIR = ROOT / "data" / "annotated" / "r2" / "consensus"
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(parents=True, exist_ok=True)

BOTS = {
    "github-actions[bot]", "eip-review-bot", "dependabot[bot]",
    "gemini-code-assist[bot]", "git-vote[bot]", "google-cla[bot]",
    "actions-user", "github-actions", "dependabot",
}


def is_bot(author: str) -> bool:
    if not author:
        return True
    return author in BOTS or author.endswith("[bot]") or author.endswith("-bot")


def _thread_key_erc(r: dict) -> str | None:
    """Unique thread identifier for ERC records."""
    if r.get("source") == "forum":
        tid = r.get("topic_id")
        return f"forum_{tid}" if tid else None
    pn = r.get("pr_number")
    return f"pr_{pn}" if pn else None


def _thread_key_a2a(r: dict) -> str | None:
    """Unique thread identifier for A2A records."""
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


def build_coparticipation(records: list[dict], thread_key_fn) -> tuple[dict, list]:
    """Build co-participation edges from a list of annotated records."""
    # thread → set of authors
    threads: dict[str, set[str]] = defaultdict(set)
    # author → contribution count (weight = # records)
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

    # Build edges: within each thread, fully connect all co-participants
    edge_weights: Counter = Counter()
    for authors in threads.values():
        authors_list = sorted(authors)
        for i in range(len(authors_list)):
            for j in range(i + 1, len(authors_list)):
                edge = (authors_list[i], authors_list[j])
                edge_weights[edge] += 1

    # Nodes: all authors with ≥1 thread appearance
    nodes = {}
    for author, count in author_counts.items():
        nodes[author] = {"id": author, "weight": count,
                         "thread_count": sum(1 for a in threads.values() if author in a)}

    # Edges
    edges = []
    for (src, tgt), w in edge_weights.items():
        edges.append({"source": src, "target": tgt, "weight": w})

    return nodes, edges


def gini(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    arr = sorted(values)
    n = len(arr)
    total = sum(arr)
    if total == 0:
        return 0.0
    cumsum = 0.0
    gini_num = 0.0
    for i, v in enumerate(arr):
        cumsum += v
        gini_num += (2 * cumsum - v - total) / total
    return gini_num / n


def degree_stats(nodes: dict, edges: list) -> dict[str, int]:
    """Compute degree for each node."""
    degrees: Counter = Counter()
    for e in edges:
        degrees[e["source"]] += 1
        degrees[e["target"]] += 1
    return degrees


def compute_sna_metrics(nodes: dict, edges: list) -> dict:
    """Compute SNA metrics matching the original paper's Table tab:sna."""
    import networkx as nx

    G = nx.Graph()
    for node_id in nodes:
        G.add_node(node_id)
    for e in edges:
        G.add_edge(e["source"], e["target"], weight=e.get("weight", 1))

    n = G.number_of_nodes()
    m = G.number_of_edges()
    degrees = dict(G.degree())
    degree_vals = list(degrees.values())

    # Giant component
    components = list(nx.connected_components(G))
    giant = max(components, key=len) if components else set()
    giant_ratio = len(giant) / n if n > 0 else 0

    # Degree Gini
    degree_gini = gini(sorted(degree_vals))

    # Top-3 degree share
    top3 = sorted(degree_vals, reverse=True)[:3]
    top3_share = sum(top3) / sum(degree_vals) * 100 if sum(degree_vals) > 0 else 0

    # Density
    density = 2 * m / (n * (n - 1)) if n > 1 else 0

    # Network efficiency (avg inverse shortest path in giant component)
    G_giant = G.subgraph(giant).copy()
    efficiency = 0.0
    if len(G_giant) > 1:
        try:
            path_lengths = nx.all_pairs_shortest_path_length(G_giant)
            total_inv = 0.0
            count = 0
            for src, targets in path_lengths:
                for tgt, length in targets.items():
                    if src != tgt and length > 0:
                        total_inv += 1.0 / length
                        count += 1
            efficiency = total_inv / count if count > 0 else 0.0
        except Exception:
            pass

    # Modularity (Louvain)
    modularity = 0.0
    n_communities = 0
    try:
        from community import community_louvain
        partition = community_louvain.best_partition(G, random_state=42)
        from networkx.algorithms.community.quality import modularity as nx_modularity
        communities = {}
        for node, comm_id in partition.items():
            communities.setdefault(comm_id, set()).add(node)
        modularity = nx_modularity(G, list(communities.values()))
        n_communities = len(communities)
    except Exception:
        pass

    # Top betweenness (centrality measure of hub dominance)
    top3_betweenness = []
    betweenness_vals = []
    try:
        bc = nx.betweenness_centrality(G, normalized=True)
        top_bc = sorted(bc.items(), key=lambda x: -x[1])[:3]
        top3_betweenness = [(a, round(v, 4)) for a, v in top_bc]
        top3_bc_share = sum(v for _, v in top3_betweenness) / sum(bc.values()) * 100 if sum(bc.values()) > 0 else 0
        betweenness_vals = list(bc.values())
    except Exception:
        top3_bc_share = 0.0

    return {
        "n_actors": n,
        "n_edges": m,
        "density": round(density, 4),
        "degree_gini": round(degree_gini, 3),
        "top3_degree_share_pct": round(top3_share, 1),
        "n_components": len(components),
        "giant_component_ratio": round(giant_ratio, 3),
        "network_efficiency": round(efficiency, 4),
        "louvain_modularity": round(modularity, 3),
        "n_louvain_communities": n_communities,
        "top3_betweenness_actors": [a for a, _ in top3_betweenness],
        "top3_betweenness_share_pct": round(top3_bc_share, 1),
    }


def save_network_csv(nodes: dict, edges: list, prefix: str):
    nodes_path = ANALYSIS / f"{prefix}_nodes.csv"
    edges_path = ANALYSIS / f"{prefix}_edges.csv"

    with open(nodes_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "weight", "thread_count"])
        w.writeheader()
        w.writerows(nodes.values())

    with open(edges_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source", "target", "weight"])
        w.writeheader()
        w.writerows(edges)

    print(f"  {prefix}: {len(nodes)} nodes, {len(edges)} edges")
    return nodes_path, edges_path


def top_n_subgraph(nodes: dict, edges: list, n: int = 50) -> tuple[dict, list]:
    """Return subgraph of top-n nodes by degree."""
    degrees: Counter = Counter()
    for e in edges:
        degrees[e["source"]] += 1
        degrees[e["target"]] += 1
    top_nodes = {a for a, _ in degrees.most_common(n)}
    sub_nodes = {k: v for k, v in nodes.items() if k in top_nodes}
    sub_edges = [e for e in edges if e["source"] in top_nodes and e["target"] in top_nodes]
    return sub_nodes, sub_edges


def main():
    print("=== Building R2 Co-participation Networks ===\n")

    # ── ERC cluster ─────────────────────────────────────────────────────────
    print("Loading ERC consensus annotations…")
    erc_path = CONSENSUS_DIR / "erc_annotations.json"
    if not erc_path.exists():
        print(f"  ERROR: {erc_path} not found. Run build_consensus.py first.")
        return
    erc_records = json.loads(erc_path.read_text())
    print(f"  {len(erc_records)} ERC records")

    erc_nodes, erc_edges = build_coparticipation(erc_records, _thread_key_erc)
    save_network_csv(erc_nodes, erc_edges, "r2_network_erc")
    erc_metrics = compute_sna_metrics(erc_nodes, erc_edges)
    print(f"  ERC metrics: density={erc_metrics['density']} "
          f"Gini={erc_metrics['degree_gini']} "
          f"efficiency={erc_metrics['network_efficiency']}")

    # ── Google A2A ───────────────────────────────────────────────────────────
    print("\nLoading A2A consensus annotations…")
    a2a_path = CONSENSUS_DIR / "a2a_annotations.json"
    if not a2a_path.exists():
        print(f"  ERROR: {a2a_path} not found. Run build_consensus.py first.")
        return
    a2a_records = json.loads(a2a_path.read_text())
    print(f"  {len(a2a_records)} A2A records")

    a2a_nodes, a2a_edges = build_coparticipation(a2a_records, _thread_key_a2a)
    save_network_csv(a2a_nodes, a2a_edges, "r2_network_a2a")
    a2a_metrics = compute_sna_metrics(a2a_nodes, a2a_edges)
    print(f"  A2A metrics: density={a2a_metrics['density']} "
          f"Gini={a2a_metrics['degree_gini']} "
          f"efficiency={a2a_metrics['network_efficiency']}")

    # Top-50 subgraph for visualization
    a2a_top50_nodes, a2a_top50_edges = top_n_subgraph(a2a_nodes, a2a_edges, n=50)
    save_network_csv(a2a_top50_nodes, a2a_top50_edges, "r2_network_a2a_top50")

    # ── Metrics table ────────────────────────────────────────────────────────
    print("\nSaving metrics table…")
    metrics_rows = []
    for case_name, m in [("ERC Agent Cluster (Tier 1+2)", erc_metrics),
                          ("Google A2A", a2a_metrics)]:
        row = {"case": case_name}
        row.update(m)
        row["top3_betweenness_actors"] = "; ".join(m.get("top3_betweenness_actors", []))
        metrics_rows.append(row)

    fields = list(metrics_rows[0].keys()) if metrics_rows else []
    table_path = ANALYSIS / "r2_network_metrics_table.csv"
    with open(table_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(metrics_rows)
    print(f"  → {table_path}")

    # Save JSON for paper
    json_out = ROOT / "output" / "stats" / "r2_network_metrics.json"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "erc": erc_metrics,
        "a2a": a2a_metrics,
    }, indent=2))
    print(f"  → {json_out}")
    print("\nDone.")


if __name__ == "__main__":
    main()
