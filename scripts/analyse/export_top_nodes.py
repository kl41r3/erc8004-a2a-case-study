"""
export_top_nodes.py — Export top nodes from R2 co-participation networks for manual
institution verification.

For each case (ERC cluster, Google A2A), computes degree + betweenness centrality,
finds the elbow cutoff, and exports a CSV with institution details for manual review.

Output:
  analysis/node_verification_checklist.csv

Usage:
  uv run python scripts/analyse/export_top_nodes.py
"""

import csv
import json
import sys
from pathlib import Path

import networkx as nx

from build_network_r2 import (
    build_coparticipation,
    _thread_key_erc,
    _thread_key_a2a,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, CONSENSUS_ERC, CONSENSUS_A2A, DATA_ANNOTATED_R1_PROFILES, METRICS_R1_VERIFICATION_CHECKLIST

PROFILES_PATH = DATA_ANNOTATED_R1_PROFILES


def load_profiles() -> dict[str, dict]:
    """Load author profiles indexed by canonical handle and all known handles."""
    if not PROFILES_PATH.exists():
        print("  WARNING: author_profiles.json not found, using empty index")
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


def find_elbow_cutoff(values: list[float], floor: int = 3, cap: int = 30) -> int:
    """Find natural break using largest relative drop. Returns count to include."""
    if len(values) <= floor:
        return len(values)
    sorted_vals = sorted(values, reverse=True)
    rel_diffs: list[float] = []
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
    max_idx = segment.index(max(segment))
    cutoff = search_start + max_idx + 1  # +1 to convert index to count
    return max(floor, min(cap, cutoff))


def main():
    print("=== Export Top Nodes for Manual Verification ===\n")

    profiles_idx = load_profiles()
    print(f"Loaded {len(profiles_idx)} profile handles\n")

    for case_label, path, thread_key_fn in [
        ("ERC-8004 Cluster", CONSENSUS_ERC, _thread_key_erc),
        ("Google A2A", CONSENSUS_A2A, _thread_key_a2a),
    ]:
        print(f"── {case_label} ──")
        records = json.loads(path.read_text())
        print(f"  {len(records)} records")

        nodes, edges = build_coparticipation(records, thread_key_fn)
        print(f"  {len(nodes)} nodes, {len(edges)} edges")

        # Build NetworkX graph
        G = nx.Graph()
        for node_id in nodes:
            G.add_node(node_id)
        for e in edges:
            G.add_edge(e["source"], e["target"], weight=e.get("weight", 1))

        # Compute centralities
        degree_cent = dict(G.degree())
        betweenness_cent = nx.betweenness_centrality(G, normalized=True)

        # Sort by betweenness for elbow detection
        bc_sorted = sorted(betweenness_cent.values(), reverse=True)
        cutoff = find_elbow_cutoff(bc_sorted)
        print(f"  Elbow cutoff: top {cutoff} nodes by betweenness")

        # Build ranked list
        ranked = []
        for node_id in nodes:
            deg = degree_cent.get(node_id, 0)
            bc = betweenness_cent.get(node_id, 0.0)
            ranked.append((node_id, deg, bc))

        ranked.sort(key=lambda x: -x[2])  # sort by betweenness descending
        top = ranked[:cutoff]

        # Get profile info
        print(f"\n  Top {len(top)} nodes for review:")
        print(f"  {'Author':<30s} {'Degree':>6s} {'Betw.Cent':>8s} {'Institution':<30s} {'Confidence':<18s}")
        print(f"  {'-'*30} {'-'*6} {'-'*8} {'-'*30} {'-'*18}")

        review_rows = []
        for author, deg, bc in top:
            p = profiles_idx.get(author, {})
            inst = p.get("institution_final", "Unknown")
            conf = p.get("institution_confidence", "LM_inferred")
            evidence = p.get("institution_evidence", "")
            display = p.get("display_name", author)
            source = p.get("institution_source", "")

            print(f"  {author:<30s} {deg:>6d} {bc:>8.4f} {inst:<30s} {conf:<18s}")

            review_rows.append({
                "case": "ERC-8004" if "ERC" in case_label else "Google-A2A",
                "author_handle": author,
                "display_name": display,
                "degree": deg,
                "betweenness_centrality": round(bc, 6),
                "institution_current": inst,
                "institution_confidence": conf,
                "institution_source": source,
                "institution_evidence": evidence,
                "manual_override": "",
                "verified_institution": "",
            })
        print()

        # Write CSV
        csv_path = METRICS_R1_VERIFICATION_CHECKLIST
        mode = "w" if "ERC" in case_label else "a"
        with open(csv_path, mode, newline="") as f:
            fieldnames = [
                "case", "author_handle", "display_name", "degree",
                "betweenness_centrality", "institution_current",
                "institution_confidence", "institution_source",
                "institution_evidence", "manual_override",
                "verified_institution",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if mode == "w":
                writer.writeheader()
            writer.writerows(review_rows)

    print(f"\nChecklist saved to: {csv_path}")
    print("Instructions: Fill in 'manual_override' and 'verified_institution' columns.")
    print("Then run: uv run python scripts/process/apply_verification.py (to be created)")


if __name__ == "__main__":
    main()
