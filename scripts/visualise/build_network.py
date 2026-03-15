"""build_network.py — Build improved stakeholder relationship network visualizations.

Outputs:
  output/network_erc8004.html     Diagram 2 — Improved ERC-8004 network
  output/network_a2a.html         Diagram 2 variant — A2A network (natural elbow cutoff)
  output/network_compare.html     Diagram 3 — Side-by-side comparison
  analysis/network_edges_*.csv    Gephi-compatible edge lists

Improvements over previous version:
  - Directed arrows on forum reply edges (from replier → to target)
  - Edge color encodes replier's post-level stance (green/red/orange/gray)
  - Quote edges from quoted_post_numbers (dotted purple)
  - PR supernodes (diamond nodes) replace clique co-participation edges
  - Node border width encodes institution_confidence
  - New institution color palettes (ERC-8004 and A2A specific)
  - Natural elbow cutoff for A2A (largest relative drop in contribution counts)
"""

import json
import re
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
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
    "eip-review-bot", "gemini-code-assist[bot]", "git-vote[bot]",
    "google-cla[bot]", "actions-user", "github-actions",
    "dependabot", "dependabot[bot]",
}


def is_bot(username: str) -> bool:
    return username in BOTS or username.endswith("[bot]") or username.endswith("-bot")


# Institution → color (ERC-8004 specific palette)
ERC_COLORS: dict[str, str] = {
    "MetaMask":                     "#F6851B",
    "Ethereum Foundation":          "#627EEA",
    "OpenZeppelin":                 "#4E5EE4",
    "Hats Protocol":                "#5FE3A1",
    "Edge and Node / The Graph Protocol": "#6F4CBA",
    "The Graph Protocol":           "#6F4CBA",
    "Nethermind":                   "#D01F36",
    "Peeramid Labs":                "#00B4D8",
    "RnDAO":                        "#FB8500",
    "Carrefour":                    "#004494",
    "Mure":                         "#A855F7",
    "Prophetic":                    "#EC4899",
    "Sparsity.ai":                  "#06B6D4",
    "Ethereal.news":                "#FF6B35",
    "Unruggable Labs":              "#84CC16",
    "Ten.IO":                       "#14B8A6",
    "Treza Labs":                   "#F59E0B",
    "Brothers of DeFi Consortium":  "#92400E",
    "Self-Employed":                "#9E9E9E",
    "World Foundation":             "#F43F5E",
    "Wivity Inc. / OMA3 DAO":      "#64748B",
    "Basement Enterprises":         "#65A30D",
    "Google":                       "#34A853",
    "Coinbase":                     "#0052FF",
    "Independent":                  "#888888",
    "Unknown":                      "#CCCCCC",
}

# Institution → color (A2A specific palette)
A2A_COLORS: dict[str, str] = {
    "Google":           "#4285F4",
    "Microsoft":        "#00A4EF",
    "Cisco":            "#1BA0D7",
    "Cisco Systems":    "#1BA0D7",
    "Red Hat":          "#EE0000",
    "IBM":              "#006699",
    "IBM Research":     "#006699",
    "Apoco":            "#5F6368",
    "CNCF":             "#0086FF",
    "Intuit":           "#365EBF",
    "Weave":            "#9B59B6",
    "AGENIUM":          "#2ECC71",
    "nosportugal":      "#E74C3C",
    "@nosportugal":     "#E74C3C",
    "Independent":      "#888888",
    "Unknown":          "#CCCCCC",
}

DEFAULT_COLOR = "#CCCCCC"

# Stance → edge color
STANCE_EDGE_COLORS: dict[str, str] = {
    "Support":   "#22c55e",
    "Oppose":    "#ef4444",
    "Modify":    "#f97316",
    "Neutral":   "#6b7280",
    "Off-topic": "#9ca3af",
}

# Confidence → border width
CONF_BORDER: dict[str, float] = {
    "Confirmed":     3.5,
    "Strong":        2.5,
    "Probable":      2.0,
    "LM_inferred":   1.0,
    "Unknown_checked": 1.5,
}


def inst_color(institution: str, palette: dict[str, str]) -> str:
    """Exact match, then substring match, then default."""
    c = palette.get(institution)
    if c:
        return c
    for key, color in palette.items():
        if key.lower() in institution.lower() or institution.lower() in key.lower():
            return color
    return DEFAULT_COLOR


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> tuple[list[dict], list[dict], list[dict]]:
    records = json.loads(ANNOTATED_RECORDS_FILE.read_text())
    profiles = json.loads(AUTHOR_PROFILES_FILE.read_text()) if AUTHOR_PROFILES_FILE.exists() else []
    forum_posts = json.loads(FORUM_POSTS_FILE.read_text()) if FORUM_POSTS_FILE.exists() else []
    return records, profiles, forum_posts


def build_profile_index(profiles: list[dict]) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for p in profiles:
        idx[p["canonical_handle"]] = p
        if p.get("github_handle"):
            idx[p["github_handle"]] = p
        if p.get("forum_handle"):
            idx[p["forum_handle"]] = p
    return idx


def canon(handle: str, profile_idx: dict[str, dict]) -> str:
    p = profile_idx.get(handle)
    return p["canonical_handle"] if p else handle


# ---------------------------------------------------------------------------
# Natural elbow cutoff for A2A
# ---------------------------------------------------------------------------

def find_elbow_cutoff(counts: list[int], floor: int = 20, cap: int = 80) -> int:
    """Find natural break in contribution distribution using largest relative drop.

    Returns number of authors to include (those at or above the break).
    The search range is [floor, cap] to exclude trivially large or small results.
    """
    if len(counts) <= floor:
        return len(counts)
    sorted_counts = sorted(counts, reverse=True)
    # Compute relative drops: (count[i] - count[i+1]) / count[i]
    rel_diffs: list[float] = []
    for i in range(len(sorted_counts) - 1):
        if sorted_counts[i] > 0:
            rel_diffs.append((sorted_counts[i] - sorted_counts[i + 1]) / sorted_counts[i])
        else:
            rel_diffs.append(0.0)

    # Search within [floor-1 .. cap-1] indices (0-indexed)
    search = rel_diffs[floor - 1: cap]
    if not search:
        return min(cap, len(sorted_counts))
    max_idx = search.index(max(search))
    cutoff = floor + max_idx       # index 0-based → count of authors to include
    return max(floor, min(cap, cutoff))


# ---------------------------------------------------------------------------
# ERC-8004 network builder
# ---------------------------------------------------------------------------

def build_erc_network(
    records: list[dict],
    forum_posts: list[dict],
    profile_idx: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    """
    Nodes: ERC-8004 authors + PR supernodes.
    Edges:
      type='reply'      — directed forum reply chain (arrow, colored by stance)
      type='quote'      — quoted post reference (dotted purple, no arrow)
      type='pr_edge'    — commenter → PR supernode (dashed gold)
    """
    erc_records = [r for r in records
                   if r.get("_case") == "ERC-8004" and not is_bot(r.get("author", ""))]

    # Author record counts (canonicalized)
    author_counts: Counter = Counter()
    for r in erc_records:
        author_counts[canon(r["author"], profile_idx)] += 1

    # Post-number → (canonical_author, stance) index from annotated records
    post_num_to_author: dict[int, str] = {}
    post_num_to_stance: dict[int, str] = {}
    for r in erc_records:
        if r.get("source") == "forum" and r.get("post_number"):
            pn = r["post_number"]
            au = canon(r["author"], profile_idx)
            post_num_to_author[pn] = au
            post_num_to_stance[pn] = (r.get("annotation") or {}).get("stance", "Neutral")

    # Also build from forum_posts (in case records don't cover all posts)
    for post in forum_posts:
        pn = post.get("post_number")
        au_raw = post.get("author", "")
        if pn and au_raw and pn not in post_num_to_author:
            post_num_to_author[pn] = canon(au_raw, profile_idx)

    # ---- Reply edges (directed: replier → replied-to) ----
    reply_edges: list[dict] = []
    seen_reply: set[tuple[str, str]] = set()
    for post in forum_posts:
        reply_to = post.get("reply_to_post_number")
        pn = post.get("post_number")
        au_src = canon(post.get("author", ""), profile_idx)
        if reply_to and reply_to in post_num_to_author and pn:
            au_dst = post_num_to_author[reply_to]
            if au_src != au_dst and not is_bot(au_src) and not is_bot(au_dst):
                stance = post_num_to_stance.get(pn, "Neutral")
                key = (au_src, au_dst)
                if key not in seen_reply:
                    seen_reply.add(key)
                    reply_edges.append({
                        "from": au_src, "to": au_dst,
                        "type": "reply",
                        "dashes": False,
                        "color": STANCE_EDGE_COLORS.get(stance, "#6b7280"),
                        "width": 1.5,
                        "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
                        "title": f"reply ({stance})",
                    })

    # ---- Quote edges (undirected: quoting post → quoted author) ----
    quote_edges: list[dict] = []
    seen_quote: set[frozenset] = set()
    for post in forum_posts:
        au_src = canon(post.get("author", ""), profile_idx)
        quoted_pns = post.get("quoted_post_numbers") or []
        for qpn in quoted_pns:
            au_dst = post_num_to_author.get(qpn)
            if au_dst and au_src != au_dst and not is_bot(au_src) and not is_bot(au_dst):
                pair = frozenset({au_src, au_dst})
                if pair not in seen_quote:
                    seen_quote.add(pair)
                    quote_edges.append({
                        "from": au_src, "to": au_dst,
                        "type": "quote",
                        "dashes": [4, 4],
                        "color": "#8B5CF6",
                        "width": 1,
                        "arrows": {"to": {"enabled": False}},
                        "title": "quote reference",
                    })

    # ---- PR supernode edges ----
    pr_participants: dict[int, set[str]] = defaultdict(set)
    for r in erc_records:
        pn = r.get("pr_number")
        au = canon(r.get("author", ""), profile_idx)
        if pn and au:
            pr_participants[pn].add(au)

    pr_nodes: list[dict] = []
    pr_edges: list[dict] = []
    for pr_num, participants in pr_participants.items():
        pr_id = f"PR_{pr_num}"
        pr_nodes.append({
            "id": pr_id,
            "label": f"PR #{pr_num}",
            "title": f"GitHub PR #{pr_num}\n{len(participants)} commenters",
            "color": "#FFD700",
            "shape": "diamond",
            "size": 14,
            "institution": "__pr__",
        })
        for au in participants:
            pr_edges.append({
                "from": au, "to": pr_id,
                "type": "pr_edge",
                "dashes": True,
                "color": "#aaaaaa",
                "width": 1,
                "arrows": {"to": {"enabled": False}},
                "title": f"commented on PR #{pr_num}",
            })

    # ---- Author nodes ----
    author_nodes: list[dict] = []
    for au in sorted(author_counts.keys()):
        p = profile_idx.get(au, {})
        institution = p.get("institution_final", "Unknown") if p else "Unknown"
        color = inst_color(institution, ERC_COLORS)
        conf = p.get("institution_confidence", "LM_inferred") if p else "LM_inferred"
        border = CONF_BORDER.get(conf, 1.0)
        cnt = author_counts[au]
        size = max(10, min(50, 8 + cnt * 2))
        arg_types = p.get("argument_types", {}) if p else {}
        stances = p.get("stances", {}) if p else {}
        tooltip = (f"{p.get('display_name', au)} ({au})\n"
                   f"Institution: {institution} [{conf}]\n"
                   f"Records: {cnt}\n"
                   f"Arguments: {arg_types}\n"
                   f"Stances: {stances}")
        author_nodes.append({
            "id": au, "label": au,
            "title": tooltip,
            "color": {"background": color, "border": "#ffffff" if border > 2.5 else "#888888"},
            "borderWidth": border,
            "size": size,
            "institution": institution,
            "institution_confidence": conf,
        })

    nodes = author_nodes + pr_nodes
    edges = reply_edges + quote_edges + pr_edges
    return nodes, edges


# ---------------------------------------------------------------------------
# A2A network builder
# ---------------------------------------------------------------------------

def build_a2a_network(
    records: list[dict],
    profile_idx: dict[str, dict],
) -> tuple[list[dict], list[dict], int]:
    """
    A2A network with natural elbow cutoff.
    Returns (nodes, edges, cutoff_n).
    Edges: co-participation in same PR/issue (dashed, width=log(weight)).
    """
    a2a_records = [r for r in records
                   if r.get("_case") == "Google-A2A" and not is_bot(r.get("author", ""))]

    author_counts: Counter = Counter(r["author"] for r in a2a_records)
    sorted_counts = sorted(author_counts.values(), reverse=True)
    top_n = find_elbow_cutoff(sorted_counts)
    top_authors = {a for a, _ in author_counts.most_common(top_n)}

    print(f"  A2A: natural elbow cutoff = {top_n} authors "
          f"(contributions: {sorted_counts[top_n-1] if top_n <= len(sorted_counts) else 0}+ records)")

    def _thread_key(r: dict) -> str | None:
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
                co_edge_counts[(author_list[i], author_list[j])] += 1

    # Nodes
    nodes: list[dict] = []
    for au in sorted(top_authors):
        p = profile_idx.get(au, {})
        institution = p.get("institution_final", "Unknown") if p else "Unknown"
        color = inst_color(institution, A2A_COLORS)
        conf = p.get("institution_confidence", "LM_inferred") if p else "LM_inferred"
        border = CONF_BORDER.get(conf, 1.0)
        cnt = author_counts[au]
        size = max(10, min(60, 8 + cnt // 5))
        stances = p.get("stances", {}) if p else {}
        tooltip = (f"{p.get('display_name', au)} ({au})\n"
                   f"Institution: {institution} [{conf}]\n"
                   f"Records: {cnt}\n"
                   f"Stances: {stances}")
        nodes.append({
            "id": au, "label": au,
            "title": tooltip,
            "color": {"background": color, "border": "#ffffff" if border > 2.5 else "#888888"},
            "borderWidth": border,
            "size": size,
            "institution": institution,
            "institution_confidence": conf,
        })

    # Edges
    edges: list[dict] = []
    for (src, dst), weight in co_edge_counts.items():
        import math
        width = max(1, min(8, 1 + math.log2(weight + 1)))
        edges.append({
            "from": src, "to": dst,
            "type": "co_comment", "dashes": True,
            "color": "#aaaaaa",
            "width": width,
            "title": f"co-participation in {weight} threads",
        })

    return nodes, edges, top_n


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_edge_csv(nodes: list[dict], edges: list[dict], path: Path) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "type", "weight"])
        for e in edges:
            writer.writerow([e["from"], e["to"], e.get("type", "edge"), e.get("width", 1)])
    print(f"  Edge CSV → {path}")

    node_path = path.with_name(path.stem.replace("edges", "nodes") + ".csv")
    with open(node_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "label", "institution", "size"])
        writer.writeheader()
        for n in nodes:
            if n.get("institution", "__pr__") != "__pr__":
                writer.writerow({"id": n["id"], "label": n["label"],
                                 "institution": n["institution"], "size": n["size"]})
    print(f"  Node CSV → {node_path}")


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

def _vis_node(n: dict) -> dict:
    """Strip internal fields not needed by vis.js."""
    keep = ("id", "label", "title", "color", "size", "shape", "borderWidth")
    return {k: v for k, v in n.items() if k in keep}


def _vis_edge(e: dict) -> dict:
    keep = ("from", "to", "dashes", "color", "width", "title", "arrows")
    return {k: v for k, v in e.items() if k in keep}


def _legend_html(nodes: list[dict], palette: dict[str, str]) -> str:
    institutions = sorted({n["institution"] for n in nodes if n.get("institution", "__pr__") != "__pr__"})
    items = []
    for inst in institutions:
        color = inst_color(inst, palette)
        items.append(
            f'<span class="legend-item">'
            f'<span class="dot" style="background:{color}"></span>'
            f'{inst}</span>'
        )
    return "\n    ".join(items)


_CSS_BASE = """
  body { margin:0; font-family:sans-serif; background:#1a1a2e; color:#eee; }
  #header { padding:10px 16px; background:#16213e; display:flex; align-items:center;
            gap:16px; flex-wrap:wrap; }
  #header h2 { margin:0; font-size:15px; white-space:nowrap; }
  #legend { display:flex; flex-wrap:wrap; gap:6px; }
  .legend-item { display:flex; align-items:center; gap:4px; font-size:11px; }
  .dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
  #info { padding:5px 16px; background:#0f3460; font-size:11px; color:#bbb;
          display:flex; gap:20px; flex-wrap:wrap; align-items:center; }
  .edge-legend { display:flex; align-items:center; gap:5px; }
  .eline { display:inline-block; width:24px; height:2px; }
"""

_EDGE_LEGEND = """
  <span class="edge-legend">
    <svg width="24" height="10"><line x1="0" y1="5" x2="24" y2="5"
      stroke="#22c55e" stroke-width="2" marker-end="url(#arrow)"/></svg>
    Reply (Support)
  </span>
  <span class="edge-legend">
    <svg width="24" height="10"><line x1="0" y1="5" x2="24" y2="5"
      stroke="#ef4444" stroke-width="2"/></svg>
    Reply (Oppose)
  </span>
  <span class="edge-legend">
    <svg width="24" height="10"><line x1="0" y1="5" x2="24" y2="5"
      stroke="#8B5CF6" stroke-width="1.5" stroke-dasharray="4 4"/></svg>
    Quote reference
  </span>
  <span class="edge-legend">
    <svg width="24" height="10"><line x1="0" y1="5" x2="24" y2="5"
      stroke="#aaa" stroke-width="1" stroke-dasharray="4 4"/></svg>
    PR/issue co-participation
  </span>
  <span>&#9826; = GitHub PR node</span>
  <span>Border width = data confidence</span>
"""

_VIS_OPTS = """{
  nodes: { shape:"dot", font:{color:"#fff",size:10}, borderWidthSelected:4 },
  edges: { smooth:{type:"dynamic"} },
  physics: {
    solver:"forceAtlas2Based",
    forceAtlas2Based:{gravitationalConstant:-50, springLength:130, damping:0.4},
    stabilization:{iterations:250}
  },
  interaction:{hover:true, tooltipDelay:80}
}"""


def render_single_html(
    nodes: list[dict],
    edges: list[dict],
    title: str,
    palette: dict[str, str],
    out_path: Path,
) -> None:
    vis_nodes = json.dumps([_vis_node(n) for n in nodes], ensure_ascii=False)
    vis_edges = json.dumps([_vis_edge(e) for e in edges], ensure_ascii=False)
    legend = _legend_html(nodes, palette)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
{_CSS_BASE}
  #network {{ width:100%; height:calc(100vh - 118px); }}
</style>
</head>
<body>
<div id="header">
  <h2>{title}</h2>
  <div id="legend">{legend}</div>
</div>
<div id="info">
  <span>Node size = record count &bull; Drag/scroll to navigate &bull; Hover for details</span>
  {_EDGE_LEGEND}
</div>
<div id="network"></div>
<script>
var nodes = new vis.DataSet({vis_nodes});
var edges = new vis.DataSet({vis_edges});
var opts = {_VIS_OPTS};
new vis.Network(document.getElementById("network"), {{nodes:nodes,edges:edges}}, opts);
</script>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")
    print(f"  HTML → {out_path}  ({len(nodes)} nodes, {len(edges)} edges)")


def render_compare_html(
    erc_nodes: list[dict], erc_edges: list[dict],
    a2a_nodes: list[dict], a2a_edges: list[dict],
    a2a_cutoff: int,
    out_path: Path,
) -> None:
    """Side-by-side comparison HTML (Diagram 3)."""
    erc_vn = json.dumps([_vis_node(n) for n in erc_nodes], ensure_ascii=False)
    erc_ve = json.dumps([_vis_edge(e) for e in erc_edges], ensure_ascii=False)
    a2a_vn = json.dumps([_vis_node(n) for n in a2a_nodes], ensure_ascii=False)
    a2a_ve = json.dumps([_vis_edge(e) for e in a2a_edges], ensure_ascii=False)
    erc_legend = _legend_html(erc_nodes, ERC_COLORS)
    a2a_legend = _legend_html(a2a_nodes, A2A_COLORS)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DAO vs Corporate Governance — Stakeholder Networks</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
{_CSS_BASE}
  #compare {{ display:flex; height:calc(100vh - 80px); gap:2px; background:#111; }}
  .panel {{ flex:1; display:flex; flex-direction:column; background:#1a1a2e; overflow:hidden; }}
  .panel-header {{ padding:8px 14px; background:#16213e; }}
  .panel-header h3 {{ margin:0; font-size:13px; color:#7dd3fc; }}
  .panel-header .sub {{ font-size:10px; color:#94a3b8; margin-top:2px; }}
  .panel-legend {{ padding:4px 14px; background:#0f3460; display:flex;
                   flex-wrap:wrap; gap:5px; }}
  .panel-network {{ flex:1; min-height:0; height:calc(100vh - 170px); }}
  #header {{ padding:8px 16px; background:#0c1445; display:flex;
             align-items:center; justify-content:space-between; }}
  #header h2 {{ margin:0; font-size:14px; color:#e2e8f0; }}
  #header .meta {{ font-size:11px; color:#94a3b8; }}
</style>
</head>
<body>
<div id="header">
  <h2>Governance Structure Comparison — Stakeholder Interaction Networks</h2>
  <span class="meta">Node size = contribution volume &bull; Hover for details &bull; Scroll to zoom</span>
</div>
<div id="compare">
  <div class="panel">
    <div class="panel-header">
      <h3>Case A — ERC-8004 (DAO / Open Governance)</h3>
      <div class="sub">{len([n for n in erc_nodes if n.get('institution','__pr__')!='__pr__'])} participants &bull; Ethereum Magicians forum + GitHub PRs</div>
    </div>
    <div class="panel-legend" id="erc-legend">{erc_legend}</div>
    <div class="panel-network" id="net-erc"></div>
  </div>
  <div class="panel">
    <div class="panel-header">
      <h3>Case B — Google A2A (Corporate / Hierarchical Governance)</h3>
      <div class="sub">Top {a2a_cutoff} contributors (natural elbow cutoff) &bull; GitHub Issues + PRs</div>
    </div>
    <div class="panel-legend" id="a2a-legend">{a2a_legend}</div>
    <div class="panel-network" id="net-a2a"></div>
  </div>
</div>
<script>
var opts = {_VIS_OPTS};
var ercNet = new vis.Network(
  document.getElementById("net-erc"),
  {{nodes: new vis.DataSet({erc_vn}), edges: new vis.DataSet({erc_ve})}},
  opts
);
var a2aNet = new vis.Network(
  document.getElementById("net-a2a"),
  {{nodes: new vis.DataSet({a2a_vn}), edges: new vis.DataSet({a2a_ve})}},
  opts
);
</script>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")
    print(f"  Compare HTML → {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== build_network.py ===")
    records, profiles, forum_posts = load_data()
    profile_idx = build_profile_index(profiles)
    print(f"Loaded: {len(records)} records, {len(profiles)} profiles, {len(forum_posts)} forum posts")

    # ERC-8004
    print("\n[ERC-8004] Building improved network...")
    erc_nodes, erc_edges = build_erc_network(records, forum_posts, profile_idx)
    render_single_html(erc_nodes, erc_edges,
                       "ERC-8004 Stakeholder Network", ERC_COLORS,
                       OUTPUT / "network_erc8004.html")
    export_edge_csv(erc_nodes, erc_edges, ANALYSIS / "network_edges_erc8004.csv")

    # A2A
    print("\n[A2A] Building network with elbow cutoff...")
    a2a_nodes, a2a_edges, cutoff = build_a2a_network(records, profile_idx)
    render_single_html(a2a_nodes, a2a_edges,
                       f"Google A2A Stakeholder Network (Top {cutoff})", A2A_COLORS,
                       OUTPUT / "network_a2a.html")
    export_edge_csv(a2a_nodes, a2a_edges, ANALYSIS / "network_edges_a2a.csv")

    # Side-by-side comparison
    print("\n[Compare] Building side-by-side comparison...")
    render_compare_html(erc_nodes, erc_edges, a2a_nodes, a2a_edges, cutoff,
                        OUTPUT / "network_compare.html")

    print(f"\nOpen in browser:")
    for f in ["network_erc8004.html", "network_a2a.html", "network_compare.html"]:
        print(f"  open {OUTPUT / f}")
    print("Done.")


if __name__ == "__main__":
    main()
