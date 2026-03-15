"""build_bipartite.py — Diagram 4: Bipartite institution × argument type network.

Shows what argument roles each institution plays in ERC-8004 and Google A2A.

Output:
  output/bipartite_erc8004.html   ERC-8004 institution × argument type
  output/bipartite_a2a.html       A2A institution × argument type

Layout:
  Left column:   institutions (sized by total record count)
  Right column:  argument types (sized by total record count)
  Edges:         weight = records from institution making that argument type
  Edge width:    proportional to log(weight)
  Node color:    institutions use case-specific palette; arg types use fixed palette

Answers the research question: Do institutionally affiliated contributors (MetaMask,
Google, Microsoft) make different argument types than independent contributors?
"""

import json
import math
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
ANNOTATED_RECORDS_FILE = ROOT / "data" / "annotated" / "annotated_records.json"
AUTHOR_PROFILES_FILE = ROOT / "data" / "annotated" / "author_profiles.json"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

BOTS = {"eip-review-bot", "gemini-code-assist[bot]", "git-vote[bot]",
        "google-cla[bot]", "actions-user", "github-actions",
        "dependabot", "dependabot[bot]"}


def is_bot(u: str) -> bool:
    return u in BOTS or u.endswith("[bot]") or u.endswith("-bot")


ARG_TYPE_COLORS = {
    "Technical":           "#3b82f6",
    "Economic":            "#f59e0b",
    "Governance-Principle":"#a855f7",
    "Process":             "#10b981",
    "Off-topic":           "#6b7280",
}

ERC_INST_COLORS = {
    "MetaMask":                     "#F6851B",
    "Ethereum Foundation":          "#627EEA",
    "OpenZeppelin":                 "#7c86f5",
    "Hats Protocol":                "#5FE3A1",
    "Edge and Node / The Graph Protocol": "#a78bfa",
    "Nethermind":                   "#f87171",
    "Peeramid Labs":                "#38bdf8",
    "RnDAO":                        "#fb923c",
    "Google":                       "#34A853",
    "Coinbase":                     "#0052FF",
    "Independent":                  "#9ca3af",
    "Unknown":                      "#6b7280",
}

A2A_INST_COLORS = {
    "Google":           "#4285F4",
    "Microsoft":        "#00A4EF",
    "Cisco":            "#1BA0D7",
    "Cisco Systems":    "#1BA0D7",
    "Red Hat":          "#EE0000",
    "IBM":              "#006699",
    "IBM Research":     "#006699",
    "CNCF":             "#0086FF",
    "Intuit":           "#365EBF",
    "Weave":            "#9B59B6",
    "Independent":      "#9ca3af",
    "Unknown":          "#6b7280",
}

DEFAULT_INST_COLOR = "#6b7280"


def inst_color(institution: str, palette: dict) -> str:
    c = palette.get(institution)
    if c:
        return c
    for k, v in palette.items():
        if k.lower() in institution.lower():
            return v
    return DEFAULT_INST_COLOR


def load_data():
    records = json.loads(ANNOTATED_RECORDS_FILE.read_text())
    profiles = json.loads(AUTHOR_PROFILES_FILE.read_text()) if AUTHOR_PROFILES_FILE.exists() else []
    return records, profiles


def build_profile_index(profiles):
    idx = {}
    for p in profiles:
        idx[p["canonical_handle"]] = p
        if p.get("github_handle"):
            idx[p["github_handle"]] = p
        if p.get("forum_handle"):
            idx[p["forum_handle"]] = p
    return idx


def canon(handle: str, idx: dict) -> str:
    p = idx.get(handle)
    return p["canonical_handle"] if p else handle


def build_bipartite_data(
    records: list[dict],
    profile_idx: dict,
    case: str,
) -> tuple[dict[str, int], dict[str, int], dict[tuple[str, str], int]]:
    """Returns (inst_counts, argtype_counts, edge_weights)."""
    inst_totals: Counter = Counter()
    argtype_totals: Counter = Counter()
    edge_weights: Counter = Counter()

    for r in records:
        if r.get("_case") != case:
            continue
        if is_bot(r.get("author", "")):
            continue
        au = canon(r["author"], profile_idx)
        p = profile_idx.get(au, {})
        inst = p.get("institution_final", "Unknown") if p else "Unknown"
        ann = r.get("annotation") or {}
        arg_type = ann.get("argument_type", "")
        if not arg_type:
            continue
        inst_totals[inst] += 1
        argtype_totals[arg_type] += 1
        edge_weights[(inst, arg_type)] += 1

    return dict(inst_totals), dict(argtype_totals), dict(edge_weights)


def render_bipartite_html(
    inst_counts: dict[str, int],
    argtype_counts: dict[str, int],
    edge_weights: dict[tuple[str, str], int],
    inst_palette: dict[str, str],
    title: str,
    out_path: Path,
) -> None:
    # Sort institutions by total records descending
    insts = sorted(inst_counts.keys(), key=lambda x: -inst_counts[x])
    argtypes = sorted(argtype_counts.keys(), key=lambda x: -argtype_counts[x])

    n_inst = len(insts)
    n_arg = len(argtypes)
    total_nodes = n_inst + n_arg

    if total_nodes == 0:
        print(f"  No data for {title}, skipping.")
        return

    # Build vis.js node and edge arrays
    vis_nodes = []
    vis_edges = []

    # Fixed layout: institutions at x=0, arg types at x=600
    # y distributed evenly within each column
    inst_y_step = max(60, 600 // max(1, n_inst))
    arg_y_step = max(60, 600 // max(1, n_arg))

    total_inst_h = n_inst * inst_y_step
    total_arg_h = n_arg * arg_y_step

    inst_y_start = -(total_inst_h // 2)
    arg_y_start = -(total_arg_h // 2)

    max_inst = max(inst_counts.values()) if inst_counts else 1
    max_arg = max(argtype_counts.values()) if argtype_counts else 1

    for i, inst in enumerate(insts):
        cnt = inst_counts[inst]
        node_size = max(20, min(80, 20 + 60 * cnt / max_inst))
        color = inst_color(inst, inst_palette)
        vis_nodes.append({
            "id": f"inst_{inst}",
            "label": inst if len(inst) <= 18 else inst[:17] + "…",
            "title": f"{inst}\n{cnt} records",
            "x": -350,
            "y": inst_y_start + i * inst_y_step,
            "size": node_size,
            "color": {"background": color, "border": "#ffffff"},
            "fixed": {"x": True, "y": True},
            "font": {"color": "#ffffff", "size": 11},
        })

    for j, arg in enumerate(argtypes):
        cnt = argtype_counts[arg]
        node_size = max(20, min(80, 20 + 60 * cnt / max_arg))
        color = ARG_TYPE_COLORS.get(arg, "#6b7280")
        vis_nodes.append({
            "id": f"arg_{arg}",
            "label": arg,
            "title": f"{arg}\n{cnt} records",
            "x": 350,
            "y": arg_y_start + j * arg_y_step,
            "size": node_size,
            "color": {"background": color, "border": "#ffffff"},
            "fixed": {"x": True, "y": True},
            "font": {"color": "#ffffff", "size": 11},
            "shape": "box",
        })

    max_weight = max(edge_weights.values()) if edge_weights else 1
    for (inst, arg), weight in sorted(edge_weights.items(), key=lambda x: -x[1]):
        if weight == 0:
            continue
        width = max(1.5, min(12, 1.5 + 10.5 * math.log2(weight + 1) / math.log2(max_weight + 1)))
        pct = round(100 * weight / inst_counts.get(inst, 1))
        vis_edges.append({
            "from": f"inst_{inst}",
            "to": f"arg_{arg}",
            "width": width,
            "color": ARG_TYPE_COLORS.get(arg, "#6b7280"),
            "title": f"{inst} → {arg}: {weight} records ({pct}%)",
            "smooth": {"type": "curvedCW", "roundness": 0.1},
        })

    nodes_json = json.dumps(vis_nodes, ensure_ascii=False)
    edges_json = json.dumps(vis_edges, ensure_ascii=False)

    # Arg type legend
    arg_legend = "\n    ".join(
        f'<span class="leg-item"><span class="leg-dot" style="background:{ARG_TYPE_COLORS.get(a,"#6b7280")}"></span>{a}</span>'
        for a in argtypes
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin:0; font-family:sans-serif; background:#0f172a; color:#e2e8f0; }}
  #header {{ padding:10px 16px; background:#1e293b; display:flex;
             align-items:center; gap:16px; flex-wrap:wrap; }}
  #header h2 {{ margin:0; font-size:14px; }}
  #legend {{ display:flex; gap:10px; flex-wrap:wrap; }}
  .leg-item {{ display:flex; align-items:center; gap:4px; font-size:11px; }}
  .leg-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
  #info {{ padding:5px 16px; background:#0c1445; font-size:11px; color:#94a3b8;
           display:flex; gap:20px; align-items:center; flex-wrap:wrap; }}
  #col-labels {{ display:flex; justify-content:space-between;
                  padding:4px 60px; font-size:12px; color:#64748b; }}
  #network {{ width:100%; height:calc(100vh - 100px); }}
</style>
</head>
<body>
<div id="header">
  <h2>{title}</h2>
  <div id="legend">
    <strong style="font-size:11px">Argument types:</strong>
    {arg_legend}
  </div>
</div>
<div id="info">
  <span>Left: institutions (size = total records)</span>
  <span>Right: argument types (size = total records)</span>
  <span>Edge width = log(record count) &bull; Hover for counts &bull; Scroll to zoom</span>
</div>
<div id="network"></div>
<script>
var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});
var opts = {{
  nodes: {{ shape:"dot", borderWidth:1.5 }},
  edges: {{ smooth:{{type:"curvedCW", roundness:0.15}}, arrows:{{to:{{enabled:true,scaleFactor:0.4}}}} }},
  physics: {{ enabled:false }},
  interaction: {{ hover:true, tooltipDelay:80, dragNodes:false }},
  layout: {{ improvedLayout:false }},
}};
new vis.Network(document.getElementById("network"), {{nodes:nodes,edges:edges}}, opts);
</script>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    print(f"  Bipartite HTML → {out_path}  ({n_inst} insts, {n_arg} argtypes, {len(vis_edges)} edges)")


def main():
    print("=== build_bipartite.py ===")
    records, profiles = load_data()
    profile_idx = build_profile_index(profiles)
    print(f"Loaded: {len(records)} records, {len(profiles)} profiles")

    # ERC-8004
    print("\n[ERC-8004] Building institution × argument type bipartite...")
    inst_c, arg_c, ew = build_bipartite_data(records, profile_idx, "ERC-8004")
    render_bipartite_html(inst_c, arg_c, ew, ERC_INST_COLORS,
                          "ERC-8004 — Institution × Argument Type",
                          OUTPUT / "bipartite_erc8004.html")

    # A2A
    print("\n[A2A] Building institution × argument type bipartite...")
    inst_c, arg_c, ew = build_bipartite_data(records, profile_idx, "Google-A2A")
    render_bipartite_html(inst_c, arg_c, ew, A2A_INST_COLORS,
                          "Google A2A — Institution × Argument Type",
                          OUTPUT / "bipartite_a2a.html")

    print(f"\nOpen in browser:")
    print(f"  open {OUTPUT / 'bipartite_erc8004.html'}")
    print(f"  open {OUTPUT / 'bipartite_a2a.html'}")
    print("Done.")


if __name__ == "__main__":
    main()
