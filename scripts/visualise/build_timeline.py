"""build_timeline.py — Diagram 1: Temporal participation timeline for ERC-8004.

Output: output/timeline_erc8004.html   (self-contained D3.js v7)

Encoding:
  X-axis:  date (chronological)
  Y-axis:  one row per author + one separator row per institution group
  Named institution authors: label = "author (Institution)"
  Independent / Unknown authors: plain author name; one separator "Independent / Unknown"
  Dot color: stance
  Row background bands: institution group (subtle color tint)
  Hover tooltip: date, author, institution, stance, argument_type, key_point
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
ANNOTATED_RECORDS_FILE = ROOT / "data" / "annotated" / "annotated_records.json"
AUTHOR_PROFILES_FILE = ROOT / "data" / "annotated" / "author_profiles.json"
OUTPUT_PATH = ROOT / "output" / "timeline_erc8004.html"

BOTS = {"eip-review-bot", "gemini-code-assist[bot]", "git-vote[bot]",
        "google-cla[bot]", "actions-user", "github-actions",
        "dependabot", "dependabot[bot]"}


def is_bot(u: str) -> bool:
    return u in BOTS or u.endswith("[bot]") or u.endswith("-bot")


STANCE_COLORS = {
    "Support":   "#22c55e",
    "Oppose":    "#ef4444",
    "Modify":    "#f97316",
    "Neutral":   "#94a3b8",
    "Off-topic": "#64748b",
}

INST_BAND_COLORS = {
    "MetaMask":                     "#1c1000",
    "Ethereum Foundation":          "#0d1225",
    "OpenZeppelin":                 "#0e0e22",
    "Hats Protocol":                "#001a12",
    "Edge and Node / The Graph Protocol": "#120a1f",
    "Nethermind":                   "#1a0005",
    "Peeramid Labs":                "#001218",
    "RnDAO":                        "#1a0d00",
    "Carrefour":                    "#00061a",
    "Mure":                         "#0e0019",
    "Prophetic":                    "#1a0010",
    "Sparsity.ai":                  "#001618",
    "Independent":                  "#111111",
    "Unknown":                      "#0d0d0d",
}
DEFAULT_BAND = "#0d0d0d"

INST_LABEL_COLORS = {
    "MetaMask":                     "#F6851B",
    "Ethereum Foundation":          "#627EEA",
    "OpenZeppelin":                 "#7c86f5",
    "Hats Protocol":                "#5FE3A1",
    "Edge and Node / The Graph Protocol": "#a78bfa",
    "Nethermind":                   "#f87171",
    "Peeramid Labs":                "#38bdf8",
    "RnDAO":                        "#fb923c",
    "Carrefour":                    "#60a5fa",
    "Mure":                         "#c084fc",
    "Prophetic":                    "#f472b6",
    "Sparsity.ai":                  "#22d3ee",
    "Independent":                  "#475569",
    "Unknown":                      "#475569",
}

ANONYMOUS_INSTS = {"Independent", "Unknown"}

# Short labels for institutions whose full names are too long for the row label
INST_SHORT: dict[str, str] = {
    "Ethereum Foundation":          "EF",
    "Edge and Node / The Graph Protocol": "The Graph",
    "Brothers of DeFi Consortium":  "BoDeFi Consortium",
    "World Foundation":             "Worldcoin/World",
    "Wivity Inc. / OMA3 DAO":      "Wivity/OMA3",
    "Basement Enterprises":         "Basement Ent.",
    "CNCF / Linux Foundation":      "CNCF/LF",
    "Apoco / IBM Research":         "Apoco/IBM",
}


def short_inst(name: str) -> str:
    return INST_SHORT.get(name, name)


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


def main():
    print("=== build_timeline.py ===")
    records, profiles = load_data()
    profile_idx = build_profile_index(profiles)

    # Filter ERC-8004 records with valid dates
    erc_records = []
    for r in records:
        if r.get("_case") != "ERC-8004":
            continue
        if is_bot(r.get("author", "")):
            continue
        date_str = r.get("date", "")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str.rstrip("Z")).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        au = canon(r["author"], profile_idx)
        ann = r.get("annotation") or {}
        erc_records.append({
            "author": au,
            "date_ts": int(dt.timestamp() * 1000),
            "stance": ann.get("stance", "Neutral"),
            "argument_type": ann.get("argument_type", ""),
            "key_point": ann.get("key_point", ""),
        })

    print(f"  ERC-8004 records for timeline: {len(erc_records)}")

    # Per-author first date
    author_first: dict[str, int] = {}
    for r in erc_records:
        au = r["author"]
        if au not in author_first or r["date_ts"] < author_first[au]:
            author_first[au] = r["date_ts"]

    INST_ORDER = [
        "MetaMask", "Ethereum Foundation", "OpenZeppelin", "Hats Protocol",
        "Edge and Node / The Graph Protocol", "Nethermind", "Peeramid Labs",
        "RnDAO", "Carrefour", "Mure", "Prophetic", "Sparsity.ai",
        "Google", "Coinbase",
        # Small named orgs — grouped together, well above Independent/Unknown
        "Brothers of DeFi Consortium", "Self-Employed",
        "Treza Labs", "Ten.IO", "Unruggable Labs", "Ethereal.news",
        "Oasis Network", "Basement Enterprises", "World Foundation",
        "Wivity Inc. / OMA3 DAO",
        # Anonymous block — must be unbroken at the bottom
        "Independent", "Unknown",
    ]

    def inst_rank(inst):
        try:
            return INST_ORDER.index(inst)
        except ValueError:
            return len(INST_ORDER) - 2  # just before Independent/Unknown

    all_authors = sorted(author_first.keys(),
                         key=lambda a: (
                             inst_rank(profile_idx.get(a, {}).get("institution_final", "Unknown")),
                             author_first[a]
                         ))

    # -------------------------------------------------------------------------
    # Build row list: interleave separator rows at institution group boundaries
    # Independent / Unknown share ONE separator at the start of their block
    # -------------------------------------------------------------------------
    rows = []          # full list including separators
    author_row: dict[str, int] = {}   # author → row index in `rows`

    prev_group = None   # tracks current institution group key

    for au in all_authors:
        p = profile_idx.get(au, {})
        inst = p.get("institution_final", "Unknown") if p else "Unknown"
        is_anon = inst in ANONYMOUS_INSTS

        # Group key: merge Independent + Unknown
        group_key = "Independent / Unknown" if is_anon else inst

        if group_key != prev_group:
            # Only add separator for the Independent / Unknown block
            if group_key == "Independent / Unknown":
                rows.append({
                    "is_separator": True,
                    "author": None,
                    "label": group_key,
                    "institution": group_key,
                    "band_color": INST_BAND_COLORS.get(inst, DEFAULT_BAND),
                    "label_color": INST_LABEL_COLORS.get(inst, "#475569"),
                })
            prev_group = group_key

        # Build row label
        if is_anon:
            row_label = au   # no institution suffix for anonymous block
        else:
            si = short_inst(inst)
            # Keep label ≤ 28 chars total (author + " (inst)")
            max_au_len = max(8, 26 - len(si))
            au_display = au if len(au) <= max_au_len else au[:max_au_len - 1] + "…"
            row_label = f"{au_display} ({si})"

        idx_in_rows = len(rows)
        author_row[au] = idx_in_rows

        rows.append({
            "is_separator": False,
            "author": au,
            "label": row_label,
            "institution": inst,
            "band_color": INST_BAND_COLORS.get(inst, DEFAULT_BAND),
            "label_color": INST_LABEL_COLORS.get(inst, "#9ca3af"),
        })

    # -------------------------------------------------------------------------
    # Attach row index to each dot record
    # -------------------------------------------------------------------------
    dots = []
    for r in erc_records:
        row_idx = author_row.get(r["author"])
        if row_idx is None:
            continue
        p = profile_idx.get(r["author"], {})
        dots.append({**r, "row_idx": row_idx,
                     "institution": p.get("institution_final", "Unknown") if p else "Unknown"})

    # Prepare JSON for D3
    dots_json = json.dumps(dots, ensure_ascii=False)
    rows_json = json.dumps(rows, ensure_ascii=False)
    stance_colors_json = json.dumps(STANCE_COLORS)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ERC-8004 Participation Timeline</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  body {{ margin:0; background:#0f172a; color:#e2e8f0; font-family:sans-serif; }}
  #header {{ padding:10px 20px; background:#1e293b; display:flex;
             align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
  #header h2 {{ margin:0; font-size:15px; }}
  #legend {{ display:flex; gap:12px; font-size:11px; }}
  .leg-item {{ display:flex; align-items:center; gap:4px; }}
  .leg-dot {{ width:9px; height:9px; border-radius:50%; }}
  #tooltip {{
    position:fixed; background:rgba(15,23,42,0.95); border:1px solid #334155;
    padding:8px 10px; font-size:11px; border-radius:6px; pointer-events:none;
    display:none; max-width:300px; line-height:1.6; z-index:999;
  }}
  #chart-container {{ overflow-y:auto; overflow-x:hidden; }}
  svg {{ display:block; }}
</style>
</head>
<body>
<div id="header">
  <h2>ERC-8004 — Temporal Participation Timeline</h2>
  <div id="legend">
    <span class="leg-item"><span class="leg-dot" style="background:#22c55e"></span>Support</span>
    <span class="leg-item"><span class="leg-dot" style="background:#ef4444"></span>Oppose</span>
    <span class="leg-item"><span class="leg-dot" style="background:#f97316"></span>Modify</span>
    <span class="leg-item"><span class="leg-dot" style="background:#94a3b8"></span>Neutral</span>
    <span class="leg-item"><span class="leg-dot" style="background:#64748b"></span>Off-topic</span>
  </div>
</div>
<div id="tooltip"></div>
<div id="chart-container"></div>

<script>
const dots = {dots_json};
const rows = {rows_json};
const STANCE_COLORS = {stance_colors_json};

const ROW_H = 20;        // uniform height for all rows including separators
const SEP_H = 16;        // separator rows are shorter
const LEFT_MARGIN = 210;
const RIGHT_MARGIN = 24;
const TOP = 40;
const BOTTOM = 30;

// Compute cumulative y positions (separators are shorter)
const rowY = [];
let curY = 0;
rows.forEach(r => {{
  rowY.push(curY);
  curY += r.is_separator ? SEP_H : ROW_H;
}});
const totalH = curY;
const svgH = TOP + totalH + BOTTOM;

const container = document.getElementById("chart-container");
const svgW = Math.max(900, window.innerWidth);

const svg = d3.select(container)
  .append("svg")
    .attr("width", svgW)
    .attr("height", svgH);

// Time scale
const allTs = dots.map(d => d.date_ts);
const tMin = d3.min(allTs);
const tMax = d3.max(allTs);
const xScale = d3.scaleTime()
  .domain([new Date(tMin - 3*24*3600*1000), new Date(tMax + 3*24*3600*1000)])
  .range([LEFT_MARGIN, svgW - RIGHT_MARGIN]);

// Row background bands
rows.forEach((r, i) => {{
  const h = r.is_separator ? SEP_H : ROW_H;
  svg.append("rect")
    .attr("x", 0)
    .attr("y", TOP + rowY[i])
    .attr("width", svgW)
    .attr("height", h)
    .attr("fill", r.band_color)
    .attr("opacity", r.is_separator ? 0.5 : 0.85);
}});

// Row labels
rows.forEach((r, i) => {{
  const h = r.is_separator ? SEP_H : ROW_H;
  const cy = TOP + rowY[i] + h * 0.68;
  if (r.is_separator) {{
    // Separator: institution name, slightly larger, italic, left-anchored
    svg.append("text")
      .attr("x", 6)
      .attr("y", cy)
      .attr("font-size", "9.5px")
      .attr("font-style", "italic")
      .attr("fill", r.label_color)
      .attr("opacity", 0.85)
      .text(r.label);
  }} else {{
    // Regular author row
    const maxChars = 30;
    const label = r.label.length > maxChars ? r.label.slice(0, maxChars - 1) + "…" : r.label;
    svg.append("text")
      .attr("x", LEFT_MARGIN - 8)
      .attr("y", cy)
      .attr("text-anchor", "end")
      .attr("font-size", "10px")
      .attr("fill", r.label_color)
      .text(label);
  }}
}});

// X-axis gridlines (monthly)
const xAxis = d3.axisTop(xScale)
  .ticks(d3.timeMonth.every(1))
  .tickFormat(d3.timeFormat("%b %Y"));

svg.append("g")
  .attr("transform", `translate(0,${{TOP}})`)
  .call(xAxis)
  .call(g => g.selectAll("text").attr("fill", "#94a3b8").attr("font-size", "10px"))
  .call(g => g.select(".domain").attr("stroke", "#334155"))
  .call(g => g.selectAll(".tick line")
    .clone()
    .attr("y2", totalH)
    .attr("stroke", "#1e293b")
    .attr("stroke-opacity", 0.7));

// Dots
const tooltip = document.getElementById("tooltip");

svg.selectAll(".dot")
  .data(dots)
  .join("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(new Date(d.date_ts)))
    .attr("cy", d => {{
      const ri = d.row_idx;
      const h = rows[ri] ? (rows[ri].is_separator ? SEP_H : ROW_H) : ROW_H;
      return TOP + rowY[ri] + h * 0.5;
    }})
    .attr("r", 4)
    .attr("fill", d => STANCE_COLORS[d.stance] || "#94a3b8")
    .attr("opacity", 0.87)
    .attr("stroke", "#0f172a")
    .attr("stroke-width", 0.5)
  .on("mousemove", (event, d) => {{
    tooltip.style.display = "block";
    tooltip.style.left = (event.clientX + 14) + "px";
    tooltip.style.top = (event.clientY - 10) + "px";
    const dateStr = new Date(d.date_ts)
      .toLocaleDateString("en-US", {{year:"numeric", month:"short", day:"numeric"}});
    tooltip.innerHTML = `
      <strong>${{d.author}}</strong><br>
      ${{d.institution}}<br>
      ${{dateStr}}<br>
      <span style="color:${{STANCE_COLORS[d.stance]}}">● ${{d.stance}}</span>
      ${{d.argument_type ? " &nbsp;|&nbsp; " + d.argument_type : ""}}<br>
      ${{d.key_point ? "<em>" + d.key_point + "</em>" : ""}}
    `;
  }})
  .on("mouseleave", () => {{ tooltip.style.display = "none"; }});
</script>
</body>
</html>"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"  Timeline HTML → {OUTPUT_PATH}")
    print(f"  Total rows (incl. separators): {len(rows)}, dots: {len(dots)}")
    sep_count = sum(1 for r in rows if r["is_separator"])
    print(f"  Institution groups (separators): {sep_count}")
    print(f"\n  open {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
