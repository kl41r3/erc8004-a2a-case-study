# Round B — Network Analysis

**Status:** DONE
**References:** literature/6 (SoK Blockchain Interoperability), literature/7 (Aave SNA — core-periphery, modularity)

## Goal

Produce Figure 2 and Statistic Result 2: social network analysis comparing governance network structure between ERC-8004 and A2A.

## Method

Paper [7] applies SNA to Aave token transaction networks. We adapt to collaboration/interaction networks (reply chains + PR reviews). Planned metrics:
- Degree centrality (in/out) — identifies dominant actors
- Core-periphery structure (Borgatti-Everett algorithm) — tests concentration of governance power
- Modularity — tests whether institutions cluster separately
- Giant component ratio — tests overall connectivity

## Data

Already built:
- `analysis/network_edges_erc8004.csv`, `analysis/network_edges_a2a.csv`
- `analysis/network_nodes_erc8004.csv`, `analysis/network_nodes_a2a.csv`
- `output/network_erc8004.html`, `output/network_a2a.html` (vis.js, dark background — needs white-background version for paper)

Node attributes available: author, institution, record count
Edge attributes: interaction count (weight)

## Results

- `output/network_sna_comparison.png` — Figure 2: side-by-side network (spring layout, white background)
- `output/network_degree_dist.png` — degree distribution by rank
- `output/network_metrics.json` — all computed metrics
- `analysis/network_metrics_table.csv` — metrics table for paper
- `human-notes/draft/dft.tex` — new Table (SNA metrics) + Figure (static network) + 4-finding narrative

Key metrics:

| Metric | ERC-8004 | Google A2A (top-50) |
|--------|----------|---------------------|
| Density | 0.029 | 0.177 |
| Gini(degree) | 0.804 | 0.481 |
| Giant component ratio | 0.328 | 0.880 |
| # Components | 43 | 7 |
| Modularity (institution) | −0.059 | −0.039 |
| Top-3 degree share | 32.3% (3 institutions) | 21.0% (2/3 Google) |

Key finding: ERC-8004 has higher degree inequality (Gini) but lower network density — consistent with many peripheral single-post contributors. A2A has denser core dominated by Google/Microsoft.

## Open questions

- Need to find a more current network analysis paper as reference (noted in `human-notes/new.md`)
- Paper [6] (blockchain interoperability SoK) does not directly contribute a network method

## Limitations

- ERC-8004 network is sparse (71 nodes); A2A is dense (826 nodes) — direct metric comparison needs normalization
- Reply chains may miss DMs, Discord, and TSC calls (known off-platform activity for A2A)
- Edge direction: "A replied to B" vs. "A reviewed B's PR" are semantically different but currently merged
