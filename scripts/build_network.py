"""build_network.py — Build interactive stakeholder relationship networks.

Nodes: unique authors (sized by record count)
Edges:
  - Forum: direct reply chain (reply_to_post_number → solid edge)
  - GitHub: co-participation in same PR/issue (dashed edge)
Node color: institution

Outputs:
  output/network_erc8004.html   — self-contained vis.js interactive graph
  output/network_a2a.html       — same, top-50 A2A contributors only
  analysis/network_edges_erc8004.csv  — exportable edge list for Gephi
  analysis/network_edges_a2a.csv
"""

import json
import re
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
ANNOTATED = ROOT / "data" / "annotated"
ANALYSIS = ROOT / "analysis"
OUTPUT = ROOT / "output"

ANNOTATED_RECORDS_FILE = ANNOTATED / "annotated_records.json"
AUTHOR_PROFILES_FILE = ANNOTATED / "author_profiles.json"
FORUM_POSTS_FILE = DATA_RAW / "forum_posts.json"

OUTPUT.mkdir(exist_ok=True)
ANALYSIS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BOTS = {
    "eip-review-bot",
    "gemini-code-assist[bot]",
    "git-vote[bot]",
    "google-cla[bot]",
    "actions-user",
    "github-actions",
    "dependabot",
    "dependabot[bot]",
}


def is_bot(username: str) -> bool:
    return username in BOTS or username.endswith("[bot]") or username.endswith("-bot")


# Institution → color mapping
INSTITUTION_COLORS: dict[str, str] = {
    "MetaMask":            "#F6851B",  # MetaMask orange
    "ConsenSys":           "#3c3c3d",  # dark gray
    "Ethereum Foundation": "#627EEA",  # Ethereum purple/blue
    "Google":              "#34A853",  # Google green (distinct from blue nodes)
    "Microsoft":           "#00A4EF",  # Microsoft blue
    "Coinbase":            "#0052FF",  # Coinbase blue
    "Gnosis":              "#008C73",  # Gnosis teal
    "Safe":                "#12FF80",  # Safe green
    "Oasis":               "#0000FF",  # Oasis blue
    "Independent":         "#888888",  # gray
    "Academia":            "#9B59B6",  # purple
    "Unknown":             "#CCCCCC",  # light gray
}

DEFAULT_COLOR = "#CCCCCC"

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data() -> tuple[list[dict], list[dict], list[dict]]:
    with open(ANNOTATED_RECORDS_FILE) as f:
        records = json.load(f)

    profiles: list[dict] = []
    if AUTHOR_PROFILES_FILE.exists():
        profiles = json.loads(AUTHOR_PROFILES_FILE.read_text())

    forum_posts: list[dict] = []
    if FORUM_POSTS_FILE.exists():
        with open(FORUM_POSTS_FILE) as f:
            forum_posts = json.load(f)

    return records, profiles, forum_posts


# ---------------------------------------------------------------------------
# Build profile index
# ---------------------------------------------------------------------------

def build_profile_index(profiles: list[dict]) -> dict[str, dict]:
    """Map all known handles (github + forum) → profile."""
    idx: dict[str, dict] = {}
    for p in profiles:
        idx[p["canonical_handle"]] = p
        if p.get("github_handle"):
            idx[p["github_handle"]] = p
        if p.get("forum_handle"):
            idx[p["forum_handle"]] = p
    return idx


# ---------------------------------------------------------------------------
# ERC-8004 network construction
# ---------------------------------------------------------------------------

def build_erc_network(
    records: list[dict],
    forum_posts: list[dict],
    profile_idx: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    """
    Returns (nodes, edges) for ERC-8004.
    Edges:
      type='reply'         — forum reply chain (solid)
      type='co_comment'    — both commented on same PR (dashed)
    """
    erc_records = [r for r in records if r.get("_case") == "ERC-8004" and not is_bot(r.get("author", ""))]

    # ---- Node sizing ----
    from collections import Counter
    author_counts: Counter = Counter(r["author"] for r in erc_records)

    # Canonicalize handles
    def canon(handle: str) -> str:
        p = profile_idx.get(handle)
        return p["canonical_handle"] if p else handle

    author_counts_canon: Counter = Counter()
    for author, cnt in author_counts.items():
        author_counts_canon[canon(author)] += cnt

    # ---- Edges: forum reply chains ----
    # Build post_number → author map from forum_posts
    post_author: dict[int, str] = {}
    for post in forum_posts:
        pn = post.get("post_number")
        au = post.get("author", "")
        if pn and au:
            post_author[pn] = canon(au)

    reply_edges: list[tuple[str, str]] = []
    for post in forum_posts:
        reply_to = post.get("reply_to_post_number")
        au = canon(post.get("author", ""))
        if reply_to and reply_to in post_author:
            target = post_author[reply_to]
            if au != target and not is_bot(au) and not is_bot(target):
                reply_edges.append((au, target))

    # ---- Edges: GitHub co-participation ----
    # Group by pr_number
    pr_authors: dict[int, set[str]] = defaultdict(set)
    for r in erc_records:
        pn = r.get("pr_number")
        au = canon(r.get("author", ""))
        if pn and au:
            pr_authors[pn].add(au)

    co_edges: list[tuple[str, str, int]] = []
    for pr_num, authors in pr_authors.items():
        author_list = sorted(authors)
        for i in range(len(author_list)):
            for j in range(i + 1, len(author_list)):
                co_edges.append((author_list[i], author_list[j], pr_num))

    # ---- Build node list ----
    all_canon_authors = set(author_counts_canon.keys())
    nodes = []
    for author in sorted(all_canon_authors):
        p = profile_idx.get(author, {})
        institution = p.get("institution_final", "Unknown") if p else "Unknown"
        color = INSTITUTION_COLORS.get(institution, DEFAULT_COLOR)
        size = max(10, min(50, 8 + author_counts_canon[author] * 2))
        nodes.append({
            "id": author,
            "label": author,
            "title": f"{p.get('display_name', author)}\n{institution}\n{author_counts_canon[author]} records",
            "color": color,
            "size": size,
            "institution": institution,
        })

    # ---- Build edge list ----
    # Deduplicate reply edges by (src, dst) pair
    reply_edge_set: set[tuple[str, str]] = set()
    for src, dst in reply_edges:
        pair = tuple(sorted([src, dst]))
        reply_edge_set.add(pair)

    co_edge_set: set[tuple[str, str]] = set()
    for src, dst, _ in co_edges:
        pair = tuple(sorted([src, dst]))
        co_edge_set.add(pair)

    edges = []
    for src, dst in reply_edge_set:
        edges.append({
            "from": src, "to": dst,
            "type": "reply", "dashes": False,
            "color": "#666666", "width": 1.5,
            "title": "direct reply",
        })
    for src, dst in co_edge_set - reply_edge_set:
        edges.append({
            "from": src, "to": dst,
            "type": "co_comment", "dashes": True,
            "color": "#aaaaaa", "width": 1,
            "title": "co-participation",
        })

    return nodes, edges


# ---------------------------------------------------------------------------
# A2A network construction
# ---------------------------------------------------------------------------

def build_a2a_network(
    records: list[dict],
    profile_idx: dict[str, dict],
    top_n: int = 50,
) -> tuple[list[dict], list[dict]]:
    """
    A2A network — top_n human authors only.
    Edges: co-participation in same PR or issue (dashed).
    """
    from collections import Counter

    a2a_records = [
        r for r in records
        if r.get("_case") == "Google-A2A" and not is_bot(r.get("author", ""))
    ]

    author_counts: Counter = Counter(r["author"] for r in a2a_records)
    top_authors = {a for a, _ in author_counts.most_common(top_n)}

    def _thread_key(r: dict) -> str | None:
        """Extract a thread key from any A2A record, regardless of field naming."""
        if "pr_number" in r:
            return f"pr_{r['pr_number']}"
        if "issue_number" in r:
            return f"issue_{r['issue_number']}"
        # Comments store URLs instead of numbers
        for url_field in ("pr_url", "issue_url", "url"):
            url = r.get(url_field, "") or ""
            m = re.search(r"/pulls/(\d+)", url)
            if m:
                return f"pr_{m.group(1)}"
            m = re.search(r"/issues/(\d+)", url)
            if m:
                return f"issue_{m.group(1)}"
        return None

    # Thread co-participation
    thread_authors: dict[str, set[str]] = defaultdict(set)
    for r in a2a_records:
        au = r.get("author", "")
        if au not in top_authors:
            continue
        key = _thread_key(r)
        if key:
            thread_authors[key].add(au)

    co_edge_counts: Counter = Counter()
    for _thread, authors in thread_authors.items():
        author_list = sorted(authors)
        for i in range(len(author_list)):
            for j in range(i + 1, len(author_list)):
                pair = (author_list[i], author_list[j])
                co_edge_counts[pair] += 1

    # Nodes
    nodes = []
    for author in sorted(top_authors):
        p = profile_idx.get(author, {})
        institution = p.get("institution_final", "Unknown") if p else "Unknown"
        color = INSTITUTION_COLORS.get(institution, DEFAULT_COLOR)
        cnt = author_counts[author]
        size = max(10, min(60, 8 + cnt // 5))
        nodes.append({
            "id": author,
            "label": author,
            "title": f"{p.get('display_name', author)}\n{institution}\n{cnt} records",
            "color": color,
            "size": size,
            "institution": institution,
        })

    # Edges — include all co-participation pairs (min_weight=1 for readability)
    edges = []
    for (src, dst), weight in co_edge_counts.items():
        if weight >= 1:
            edges.append({
                "from": src, "to": dst,
                "type": "co_comment", "dashes": True,
                "color": "#aaaaaa",
                "width": min(5, 1 + weight // 3),
                "title": f"co-participation in {weight} threads",
            })

    return nodes, edges


# ---------------------------------------------------------------------------
# Export to CSV (Gephi-compatible)
# ---------------------------------------------------------------------------

def export_edge_csv(nodes: list[dict], edges: list[dict], path: Path) -> None:
    import csv
    # node attributes
    node_map = {n["id"]: n for n in nodes}
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "type", "weight"])
        for e in edges:
            weight = e.get("width", 1)
            writer.writerow([e["from"], e["to"], e.get("type", "edge"), weight])
    print(f"  Saved edge CSV: {path}")

    # Also save node CSV
    node_path = path.with_name(path.stem.replace("edges", "nodes") + ".csv")
    with open(node_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "label", "institution", "size"])
        writer.writeheader()
        for n in nodes:
            writer.writerow({"id": n["id"], "label": n["label"], "institution": n["institution"], "size": n["size"]})
    print(f"  Saved node CSV: {node_path}")


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin: 0; font-family: sans-serif; background: #1a1a2e; color: #eee; }}
  #header {{ padding: 12px 20px; background: #16213e; display: flex; align-items: center; gap: 20px; }}
  #header h2 {{ margin: 0; font-size: 16px; }}
  #legend {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .legend-item {{ display: flex; align-items: center; gap: 4px; font-size: 12px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}
  #info {{ padding: 6px 20px; background: #0f3460; font-size: 12px; color: #bbb; display: flex; gap: 24px; align-items: center; flex-wrap: wrap; }}
  .edge-legend {{ display: flex; align-items: center; gap: 6px; }}
  .edge-line {{ display: inline-block; width: 28px; height: 2px; }}
  .edge-solid {{ background: #666; }}
  .edge-dashed {{ background: none; border-top: 2px dashed #aaa; }}
  #network {{ width: 100%; height: calc(100vh - 115px); }}
</style>
</head>
<body>
<div id="header">
  <h2>{title}</h2>
  <div id="legend">
    {legend_html}
  </div>
</div>
<div id="info">
  <span>Node size = record count</span>
  <span class="edge-legend"><span class="edge-line edge-solid"></span> Solid edge: direct reply (forum reply chain)</span>
  <span class="edge-legend"><span class="edge-line edge-dashed"></span> Dashed edge: co-participation (both commented on same PR/issue)</span>
  <span>Drag to move &bull; Scroll to zoom &bull; Click to highlight</span>
</div>
<div id="network"></div>
<script>
var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});

var container = document.getElementById("network");
var options = {{
  nodes: {{
    shape: "dot",
    font: {{ color: "#ffffff", size: 11 }},
    borderWidth: 1.5,
    borderWidthSelected: 3,
  }},
  edges: {{
    smooth: {{ type: "dynamic" }},
    arrows: {{ to: false }},
  }},
  physics: {{
    solver: "forceAtlas2Based",
    forceAtlas2Based: {{ gravitationalConstant: -50, springLength: 120, damping: 0.4 }},
    stabilization: {{ iterations: 200 }},
  }},
  interaction: {{ hover: true, tooltipDelay: 100 }},
}};
var network = new vis.Network(container, {{ nodes: nodes, edges: edges }}, options);
</script>
</body>
</html>"""


def build_legend_html(nodes: list[dict]) -> str:
    institutions = sorted({n["institution"] for n in nodes})
    items = []
    for inst in institutions:
        color = INSTITUTION_COLORS.get(inst, DEFAULT_COLOR)
        items.append(
            f'<div class="legend-item">'
            f'<div class="legend-dot" style="background:{color}"></div>'
            f'<span>{inst}</span></div>'
        )
    return "\n    ".join(items)


def render_html(
    nodes: list[dict],
    edges: list[dict],
    title: str,
    out_path: Path,
) -> None:
    # Strip internal fields not needed by vis.js
    vis_nodes = [
        {k: v for k, v in n.items() if k in ("id", "label", "title", "color", "size")}
        for n in nodes
    ]
    vis_edges = [
        {k: v for k, v in e.items() if k in ("from", "to", "dashes", "color", "width", "title")}
        for e in edges
    ]

    legend_html = build_legend_html(nodes)
    html = HTML_TEMPLATE.format(
        title=title,
        legend_html=legend_html,
        nodes_json=json.dumps(vis_nodes, ensure_ascii=False),
        edges_json=json.dumps(vis_edges, ensure_ascii=False),
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"  Saved HTML: {out_path}  ({len(nodes)} nodes, {len(edges)} edges)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== build_network.py ===")

    records, profiles, forum_posts = load_data()
    profile_idx = build_profile_index(profiles)

    print(f"Loaded {len(records)} records, {len(profiles)} profiles, {len(forum_posts)} forum posts")

    # --- ERC-8004 ---
    print("\n[ERC-8004] Building network...")
    erc_nodes, erc_edges = build_erc_network(records, forum_posts, profile_idx)
    render_html(erc_nodes, erc_edges, "ERC-8004 Stakeholder Network", OUTPUT / "network_erc8004.html")
    export_edge_csv(erc_nodes, erc_edges, ANALYSIS / "network_edges_erc8004.csv")

    # --- A2A ---
    print("\n[A2A] Building network (top 50 humans)...")
    a2a_nodes, a2a_edges = build_a2a_network(records, profile_idx, top_n=50)
    render_html(a2a_nodes, a2a_edges, "Google A2A Stakeholder Network (Top 50)", OUTPUT / "network_a2a.html")
    export_edge_csv(a2a_nodes, a2a_edges, ANALYSIS / "network_edges_a2a.csv")

    print(f"\nOpen in browser:")
    print(f"  open {OUTPUT / 'network_erc8004.html'}")
    print(f"  open {OUTPUT / 'network_a2a.html'}")
    print("\nDone.")


if __name__ == "__main__":
    main()
