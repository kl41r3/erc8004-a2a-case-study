# Round B — Network Analysis

**Status:** TODO
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

## Open questions

- Need to find a more current network analysis paper as reference (noted in `human-notes/new.md`)
- Paper [6] (blockchain interoperability SoK) does not directly contribute a network method

## Limitations

- ERC-8004 network is sparse (71 nodes); A2A is dense (826 nodes) — direct metric comparison needs normalization
- Reply chains may miss DMs, Discord, and TSC calls (known off-platform activity for A2A)
- Edge direction: "A replied to B" vs. "A reviewed B's PR" are semantically different but currently merged
