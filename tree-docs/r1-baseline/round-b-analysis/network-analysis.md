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
| **Betweenness centrality** | nx.betweenness_centrality (normalized, full graph). Chosenover closeness because both networks are highly fragmented; betweenness = 0 for isolates naturally. Identifies governance brokers — actors who mediate between otherwise disconnected groups. |
| **Betweenness Gini / top-3 share** | Concentration of brokerage power. Complement to degree Gini: captures structural influence, not just participation volume. |
| **Network efficiency** | Mean normalized harmonic centrality across all nodes: Σ(1/d_ij)/(n−1) averaged over i, where d_ij = ∞ gives 0 contribution. Harmonic variant chosen over raw closeness because it is well-defined on disconnected graphs (standard closeness is undefined for unreachable pairs). |
| **Eigenvector centrality (giant component)** | nx.eigenvector_centrality on G_giant only. Captures prestige — being connected to high-degree actors. Computed on giant component only because convergence requires a connected subgraph. Reports Gini + top-5 with institution label. |

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

**Statistics** (`output/network_metrics.json`, `analysis/network_metrics_table.csv`):

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
| CP p-value | 0.139 | 1.000 |
| CP significant (p<.05) | No | No |
| Core count | 3 | 769/771 |
| Avg core degree | 8.0 | 3.196 |
| **Betweenness mean** | 0.00248 | 0.000675 |
| **Betweenness max** | 0.069 (MarcoMetaMask) | 0.136 (holtskinner/Google) |
| **Betweenness Gini** | **0.931** | **0.979** |
| **Top-3 betweenness share** | **70.8%** | **48.5%** |
| **Network efficiency** | **0.050** | **0.110** |
| Harmonic centrality max | 0.242 | 0.374 |
| Eigenvec Gini (giant comp.) | 0.377 (n=22) | 0.507 (n=412) |
| Eigenvec max (giant comp.) | 0.546 (MarcoMetaMask) | 0.357 (holtskinner/Google) |

**Top-3 contributors by degree:**
- ERC-8004: MarcoMetaMask (deg=19, MetaMask), spengrah (13, Hats Protocol), pcarranzav (10, Edge and Node / The Graph Protocol)
- A2A: holtskinner/Google (deg=170), darrelmiller/Microsoft (110), pstephengoogle/Google (87)

**Top-5 brokers by betweenness:**
- ERC-8004: MarcoMetaMask/MetaMask (0.069), dcrapis/Ethereum Foundation (0.027), spengrah/Hats Protocol (0.022), felixnorden/Mure (0.012), pcarranzav/Edge and Node (0.011)
- A2A: holtskinner/Google (0.136), darrelmiller/Microsoft (0.067), pstephengoogle/Google (0.049), kthota-g/Google (0.040), mikeas1/Google (0.021)

**Top-5 prestige by eigenvector (giant component):**
- ERC-8004 (n=22): MarcoMetaMask/MetaMask (0.546), spengrah/Hats Protocol (0.364), pcarranzav/Edge and Node (0.335), mlegls/Independent (0.280), SumeetChougule/Nethermind (0.255) — 4 different institutions
- A2A (n=412): holtskinner/Google (0.357), pstephengoogle/Google (0.289), darrelmiller/Microsoft (0.281), kthota-g/Google (0.202), mikeas1/Google (0.184) — 4/5 are Google employees

**Key findings:**

1. **High degree inequality in both cases**: Gini 0.804 (ERC-8004) vs 0.779 (A2A) — both governance communities concentrate interaction around a small elite, regardless of formal governance structure.

2. **Scale asymmetry is substantive**: 67 vs 771 participants. A2A has 333 complete isolates (43% of all participants had no co-participation with anyone). ERC-8004's smaller scale reflects its bounded, specialist community.

3. **Institution labels do not predict interaction patterns**: Negative modularity in both cases means cross-institutional interaction exceeds within-institution interaction — even in A2A, whose TSC is corporate.

4. **No significant core-periphery structure in either case**: ERC-8004 p=0.139 (fragmented, sparse); A2A p=1.0 (BE assigns 769/771 as core — artifact of 346-component fragmentation, not centralization).

5. **Both are thread-organized, not community-organized**: Louvain finds 46 (ERC) and 358 (A2A) communities, closely matching component counts. Governance discussion is parallel-threaded, not community-deliberative.

6. **Corporate capture of brokerage in A2A**: Betweenness Gini 0.979 (A2A) vs 0.931 (ERC-8004) — brokerage is extremely concentrated in both, but the composition differs fundamentally. In A2A, 4/5 top brokers are Google employees (plus 1 Microsoft); the single actor holtskinner/Google controls 13.6% of all shortest paths. In ERC-8004, brokers come from 5 different institutions (MetaMask, Ethereum Foundation, Hats Protocol, Mure, Edge and Node) — no institution monopolizes brokerage.

7. **Network efficiency gap**: ERC-8004 (0.050) vs A2A (0.110) — A2A's larger giant component (53% of nodes) enables more than 2× better information accessibility across the network. ERC-8004's extreme fragmentation (43 components, 33% giant ratio) creates a structurally isolated governance process.

8. **Prestige concentration institutionally captured in A2A**: Eigenvector Gini 0.507 (A2A giant, n=412) vs 0.377 (ERC-8004 giant, n=22). In A2A's giant component, Google employees dominate the prestige hierarchy — being connected to Google actors is what confers structural influence. ERC-8004's prestige is distributed across heterogeneous institutions.

## Methodological note

The original visualization used a `find_elbow_cutoff()` filter (top-50 A2A) for both visualization and metrics — an inconsistency (ERC-8004 used all nodes). Corrected in Round B: metrics now use full population; top-50 data retained separately for visualization readability.

## Scripts

- `scripts/analyze_network.py` — main SNA metrics + figures; now includes `compute_centrality_metrics()` (betweenness, harmonic, eigenvector on giant component)
- `scripts/rebuild_a2a_network_full.py` — rebuilds A2A CSVs without top-N cutoff
- `scripts/visualise/build_network.py` — builds network CSVs + interactive HTML (top-50 for A2A)

## Limitations

- Edge types differ between cases: ERC-8004 uses reply/quote/PR-coparticipation; A2A uses PR/issue co-participation only. Direct degree comparison assumes both edge types proxy "governance interaction."
- 333 A2A isolates may reflect data coverage gaps (off-platform discussion in Discord/Zoom not captured) rather than genuine non-participation.
- BE core-periphery is designed for connected graphs; results for fragmented networks (especially A2A) should be interpreted cautiously.
- Institution labels for A2A: 463/771 tagged "Independent," 248 "Unknown" — precision limited by LLM inference on 17k+ contributors.
