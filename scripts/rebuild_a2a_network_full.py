"""rebuild_a2a_network_full.py — Rebuild A2A network CSVs with ALL contributors (no top-N cutoff).

Outputs:
  analysis/network_nodes_a2a.csv   — all A2A authors (no elbow cutoff)
  analysis/network_edges_a2a.csv   — co-participation edges

This overwrites the previous elbow-cutoff CSVs so that analyze_network.py
works on the complete contributor population.
"""

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
ANNOTATED = ROOT / "data" / "annotated"
ANALYSIS = ROOT / "analysis"

ANNOTATED_RECORDS_FILE = ANNOTATED / "annotated_records.json"
AUTHOR_PROFILES_FILE = ANNOTATED / "author_profiles.json"

BOTS = {
    "eip-review-bot", "gemini-code-assist[bot]", "git-vote[bot]",
    "google-cla[bot]", "actions-user", "github-actions",
    "dependabot", "dependabot[bot]",
}


def is_bot(username: str) -> bool:
    return username in BOTS or username.endswith("[bot]") or username.endswith("-bot")


def _thread_key(r: dict) -> str | None:
    """Prefer pr_number → issue_number → regex on url fields."""
    if "pr_number" in r:
        return f"pr_{r['pr_number']}"
    if "issue_number" in r:
        return f"issue_{r['issue_number']}"
    for field in ("pr_url", "issue_url", "url"):
        url = r.get(field, "") or ""
        m = re.search(r"/pulls/(\d+)", url)
        if m:
            return f"pr_{m.group(1)}"
        m = re.search(r"/issues/(\d+)", url)
        if m:
            return f"issue_{m.group(1)}"
    return None


def build_profile_index(profiles: list[dict]) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for p in profiles:
        idx[p["canonical_handle"]] = p
        if p.get("github_handle"):
            idx[p["github_handle"]] = p
        if p.get("forum_handle"):
            idx[p["forum_handle"]] = p
    return idx


def main() -> None:
    print("=== rebuild_a2a_network_full.py (no top-N cutoff) ===")

    # Load data
    records: list[dict] = json.loads(ANNOTATED_RECORDS_FILE.read_text())
    profiles: list[dict] = (
        json.loads(AUTHOR_PROFILES_FILE.read_text())
        if AUTHOR_PROFILES_FILE.exists()
        else []
    )
    profile_idx = build_profile_index(profiles)
    print(f"Loaded {len(records)} records, {len(profiles)} profiles")

    # Filter to A2A non-bot records
    a2a_records = [
        r for r in records
        if r.get("_case") == "Google-A2A" and not is_bot(r.get("author", ""))
    ]
    print(f"A2A non-bot records: {len(a2a_records)}")

    # Author contribution counts
    author_counts: Counter = Counter(r["author"] for r in a2a_records)
    all_authors: set[str] = set(author_counts.keys())
    print(f"Unique A2A authors (ALL, no cutoff): {len(all_authors)}")

    # Build thread → authors mapping
    thread_authors: dict[str, set[str]] = defaultdict(set)
    for r in a2a_records:
        au = r.get("author", "")
        if not au:
            continue
        key = _thread_key(r)
        if key:
            thread_authors[key].add(au)

    print(f"Threads found: {len(thread_authors)}")

    # Build co-participation edges (undirected, weight = shared thread count)
    co_edge_counts: Counter = Counter()
    for _thread, authors in thread_authors.items():
        author_list = sorted(authors)
        for i in range(len(author_list)):
            for j in range(i + 1, len(author_list)):
                co_edge_counts[(author_list[i], author_list[j])] += 1

    print(f"Co-participation edges: {len(co_edge_counts)}")

    # Identify nodes with at least one edge
    nodes_with_edges: set[str] = set()
    for src, dst in co_edge_counts:
        nodes_with_edges.add(src)
        nodes_with_edges.add(dst)

    isolate_count = len(all_authors) - len(nodes_with_edges)
    print(f"Isolate nodes (no edges): {isolate_count}")

    # Write network_nodes_a2a.csv
    ANALYSIS.mkdir(exist_ok=True)
    nodes_path = ANALYSIS / "network_nodes_a2a.csv"
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "label", "institution", "size"])
        writer.writeheader()
        for au in sorted(all_authors):
            p = profile_idx.get(au, {})
            institution = p.get("institution_final", "Unknown") if p else "Unknown"
            cnt = author_counts[au]
            size = max(10, min(60, 8 + cnt // 5))
            writer.writerow({"id": au, "label": au, "institution": institution, "size": size})
    print(f"  Node CSV → {nodes_path}  ({len(all_authors)} nodes)")

    # Write network_edges_a2a.csv
    edges_path = ANALYSIS / "network_edges_a2a.csv"
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "type", "weight"])
        for (src, dst), weight in sorted(co_edge_counts.items()):
            writer.writerow([src, dst, "co_comment", weight])
    print(f"  Edge CSV → {edges_path}  ({len(co_edge_counts)} edges)")

    # Summary statistics
    print("\n=== Summary ===")
    print(f"  Total nodes  : {len(all_authors)}")
    print(f"  Total edges  : {len(co_edge_counts)}")
    print(f"  Isolate nodes: {isolate_count}")
    print(f"  Threads used : {len(thread_authors)}")

    # Top-10 authors by contribution count
    print("\n  Top-10 authors by record count:")
    for au, cnt in author_counts.most_common(10):
        p = profile_idx.get(au, {})
        inst = p.get("institution_final", "Unknown") if p else "Unknown"
        print(f"    {au:<30s} {cnt:4d} records  [{inst}]")


if __name__ == "__main__":
    main()
