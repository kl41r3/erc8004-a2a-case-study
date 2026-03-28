# output/

Final visualizations and research outputs.

```
output/
├── figures/        PNG figures for paper (180 dpi, white background)
├── interactive/    HTML visualizations (open in browser)
└── stats/          JSON/MD data summaries
```

## figures/ — Paper-ready PNGs

| File | Description | Script |
|------|-------------|--------|
| `voting_mechanism_comparison.png` | Two-panel process diagram: EIP editor-approval vs TSC git-vote | `scripts/analyze_voting_mechanism.py` |
| `topic_argtype_comparison.png` | Argument type distribution by case (ERC-8004 vs A2A) | `scripts/analyze_topic.py` |
| `topic_stance_heatmap.png` | Stance × argument type cross-tabulation, two-panel | `scripts/analyze_topic.py` |
| `topic_temporal_erc8004.png` | ERC-8004 argument type over lifecycle (2-week bins) | `scripts/analyze_topic.py` |
| `network_sna_comparison.png` | Side-by-side SNA network (spring layout, institution colors) | `scripts/analyze_network.py` |
| `network_degree_dist.png` | Ranked degree distribution by case | `scripts/analyze_network.py` |

## interactive/ — Browser visualizations

| File | Description | Script |
|------|-------------|--------|
| `timeline_erc8004.html` | D3.js temporal participation timeline (authors by institution, dots by stance) | `scripts/visualise/build_timeline.py` |
| `network_erc8004.html` | vis.js stakeholder network for ERC-8004 | `scripts/visualise/build_network.py` |
| `network_a2a.html` | vis.js stakeholder network for A2A top contributors | `scripts/visualise/build_network.py` |
| `network_compare.html` | Side-by-side ERC-8004 vs A2A (same physics params) | `scripts/visualise/build_network.py` |
| `bipartite_erc8004.html` | Institution × Argument Type bipartite graph for ERC-8004 | `scripts/visualise/build_bipartite.py` |
| `bipartite_a2a.html` | Institution × Argument Type bipartite graph for A2A | `scripts/visualise/build_bipartite.py` |

## stats/ — Data summaries

| File | Description |
|------|-------------|
| `voting_stats.json` | Voting mechanism counts (approvals, /vote commands, bot messages) |
| `topic_stats.json` | Argument type and stance counts/percentages by case |
| `network_metrics.json` | Full SNA metrics (density, Gini, modularity, giant component ratio, etc.) |
| `findings_summary.md` | Concise findings summary |
