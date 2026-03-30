# Round B — Network Analysis

**Status:** DONE
**References:** literature/7 (Ao, Cong, Horvath, Zhang — "Is DeFi Actually Decentralized?" arXiv:2206.08401 — Borgatti-Everett core-periphery, modularity, Gini, giant component ratio)

## Goal

Produce Figure 3 and Statistic Result 3: social network analysis comparing governance interaction network structure between ERC-8004 and Google A2A.

## Method

Paper [7] applies SNA to Aave token transaction networks (nodes=wallet addresses, edges=token transfers, daily snapshots). We adapt to governance **interaction networks**:

- **ERC-8004** — Nodes: forum/GitHub authors. Edges: reply chains + quote references + PR co-participation (directed reply, undirected co-PR).
- **Google A2A** — Nodes: all non-bot GitHub contributors. Edges: co-participation in same PR/issue thread (undirected, weight = number of shared threads).

**Full-population comparison** (no elbow cutoff): ERC-8004 uses all 67 nodes with interactions; A2A uses all 771 contributors. A separate top-50 visualization subset is retained for figure readability.

**Metrics computed** (all from `scripts/analyze_network.py`):

| Metric | Method |
|--------|--------|
| Density | m / [n(n-1)/2] |
| DCstd (normalized) | std(degree) / (n-1) |
| Gini(degree) | Lorenz-based Gini coefficient on degree sequence |
| Top-3 degree share | Σdeg(top3) / 2m |
| Components | DFS connected components count |
| Giant component ratio | max_component_size / n |
| Modularity — institution | Newman Q with institution-label partition |
| Modularity — Louvain | NetworkX Louvain community detection |
| CP p-value / significance | Borgatti-Everett (cpnet.BE) + qstest (100 rand for n≤200, 20 rand for n>200) |
| Core count / avg core degree | cpnet.BE coreness=1 nodes |

## Data

- `analysis/network_nodes_erc8004.csv` — 67 nodes
- `analysis/network_edges_erc8004.csv` — 65 edges
- `analysis/network_nodes_a2a.csv` — 771 nodes (full, no cutoff)
- `analysis/network_edges_a2a.csv` — 1,230 edges
- `analysis/network_nodes_a2a_top50.csv` — 50 nodes (visualization subset, retained)
- `analysis/network_edges_a2a_top50.csv` — 217 edges (visualization subset, retained)

## Results

**Figures** (`output/`):
- `network_sna_comparison.png` — Figure 3: side-by-side spring layout (ERC-8004 full / A2A top-50 for readability); metrics inset shows full-population values
- `network_degree_dist.png` — degree distribution by rank (both cases)

**Statistics** (`output/stats/network_metrics.json`):

| Metric | ERC-8004 | Google A2A |
|--------|----------|------------|
| Nodes | 67 | 771 |
| Edges | 65 | 1,230 |
| Density | 0.029 | 0.004 |
| DCstd (normalized) | 0.051 | 0.013 |
| Gini(degree) | 0.804 | 0.779 |
| Top-3 degree share | 32.3% | 14.9% |
| \# Components | 43 | 346 |
| Giant component ratio | 0.328 | 0.534 |
| Modularity (institution) | −0.059 | −0.034 |
| Modularity (Louvain) | 0.425 | 0.473 |
| \# Louvain communities | 46 | 358 |
| CP p-value | 0.095 | 1.000 |
| CP significant (p<.05) | No | No |
| Core count | 3 | 769/771 |
| Avg core degree | 8.0 | 3.196 |

**Top-3 contributors:**
- ERC-8004: MarcoMetaMask (deg=19), spengrah (13), pcarranzav (10) — all Independent
- A2A: holtskinner/Google (deg=170), darrelmiller/Microsoft (110), pstephengoogle/Google (87)

**Key findings:**

1. **High degree inequality in both cases**: Gini 0.804 (ERC-8004) vs 0.779 (A2A) — both governance communities concentrate interaction around a small elite, regardless of formal governance structure.

2. **Scale asymmetry is substantive**: 67 vs 771 participants. A2A has 333 complete isolates (43% of all participants had no co-participation with anyone). ERC-8004's smaller scale reflects its bounded, specialist community.

3. **Institution labels do not predict interaction patterns**: Negative modularity in both cases means cross-institutional interaction exceeds within-institution interaction — even in A2A, whose TSC is corporate.

4. **No significant core-periphery structure in either case**: ERC-8004 p=0.095 (fragmented, sparse); A2A p=1.0 (BE assigns 769/771 as core — artifact of 346-component fragmentation, not centralization).

5. **Both are thread-organized, not community-organized**: Louvain finds 46 (ERC) and 358 (A2A) communities, closely matching component counts. Governance discussion is parallel-threaded, not community-deliberative.

## Methodological note

The original visualization used a `find_elbow_cutoff()` filter (top-50 A2A) for both visualization and metrics — an inconsistency (ERC-8004 used all nodes). Corrected in Round B: metrics now use full population; top-50 data retained separately for visualization readability.

## Scripts

- `scripts/analyze_network.py` — main SNA metrics + figures
- `scripts/rebuild_a2a_network_full.py` — rebuilds A2A CSVs without top-N cutoff
- `scripts/visualise/build_network.py` — builds network CSVs + interactive HTML (top-50 for A2A)

## Limitations

- Edge types differ between cases: ERC-8004 uses reply/quote/PR-coparticipation; A2A uses PR/issue co-participation only. Direct degree comparison assumes both edge types proxy "governance interaction."
- 333 A2A isolates may reflect data coverage gaps (off-platform discussion in Discord/Zoom not captured) rather than genuine non-participation.
- BE core-periphery is designed for connected graphs; results for fragmented networks (especially A2A) should be interpreted cautiously.
- Institution labels for A2A: 463/771 tagged "Independent," 248 "Unknown" — precision limited by LLM inference on 17k+ contributors.
