# network_discourse/ — Discourse Network Analysis outputs

Combines Thematic-LM topic assignments + LLM stance labels to build two types of
governance discourse networks.

## Method overview

- **DNA (Discourse Network Analysis)**: Actor–actor congruence/conflict networks
  based on shared stances toward themes. Higher congruence density = more within-community
  agreement. Outputs: edge CSVs, `dna_metrics.json`.
- **Socio-semantic bipartite network**: Actor ↔ theme bipartite graph. Measures
  actor specialization (entropy H), theme concentration, and thematic overlap
  between cases. Outputs: actor diversity CSVs, theme concentration CSVs, `ss_metrics.json`.

## r1/ — Baseline (ERC-8004 vs A2A, single model)

### DNA
| File | Description |
|------|-------------|
| `dna/congruence_erc8004.csv` | ERC-8004 congruence edges (actor pairs sharing stance toward a theme). |
| `dna/congruence_googlea2a.csv` | A2A congruence edges. |
| `dna/conflict_erc8004.csv` | ERC-8004 conflict edges (opposing stances on same theme). |
| `dna/conflict_googlea2a.csv` | A2A conflict edges. |
| `dna/dna_metrics.json` | DNA summary metrics: actor count, edge counts, congruence density. |
| `dna/dna_comparison.png` | DNA comparison figure (congruence/conflict density bar chart). |

### Socio-semantic
| File | Description |
|------|-------------|
| `sociosemantic/actor_diversity_erc8004.csv` | Per-actor Shannon entropy H (theme specialization) — ERC. |
| `sociosemantic/actor_diversity_googlea2a.csv` | Per-actor entropy — A2A. |
| `sociosemantic/actor_topic_matrix_erc8004.csv` | Actor × Theme matrix (counts) — ERC. |
| `sociosemantic/actor_topic_matrix_googlea2a.csv` | Actor × Theme matrix — A2A. |
| `sociosemantic/theme_concentration_erc8004.csv` | Per-theme actor concentration (Gini) — ERC. |
| `sociosemantic/theme_concentration_googlea2a.csv` | Per-theme actor concentration — A2A. |
| `sociosemantic/theme_actor_comparison.{csv,png}` | Cross-case theme × actor comparison. |
| `sociosemantic/specialization_compare.png` | Actor entropy histogram comparison. |
| `sociosemantic/ss_metrics.json` | Socio-semantic summary metrics (mean H, H Gini, thematic overlap Ω). |

### Other
| File | Description |
|------|-------------|
| `network_metrics.json` | R1 SNA summary metrics (density, Gini, modularity, GCR). |

## r2/ — Expanded data (34-ERC cluster, 3-model consensus)

### DNA
| File | Description |
|------|-------------|
| `dna/congruence_erc8004.csv` | ERC cluster congruence edges (R2 consensus). |
| `dna/congruence_googlea2a.csv` | A2A congruence edges (R2 consensus). |
| `dna/conflict_erc8004.csv` | ERC cluster conflict edges. |
| `dna/conflict_googlea2a.csv` | A2A conflict edges. |
| `dna/dna_metrics.json` | R2 DNA summary metrics (cross-model consensus). |
| `dna/dna_metrics_cross_round.json` | R2 DNA metrics from cross-round consensus. |
| `dna/dna_comparison.png` | R2 DNA comparison figure. |

### Socio-semantic
| File | Description |
|------|-------------|
| `sociosemantic/actor_diversity_erc8004.csv` | Per-actor entropy — ERC cluster (R2). |
| `sociosemantic/actor_diversity_googlea2a.csv` | Per-actor entropy — A2A (R2). |
| `sociosemantic/actor_topic_matrix_erc8004.csv` | Actor × Theme matrix — ERC (R2). |
| `sociosemantic/actor_topic_matrix_googlea2a.csv` | Actor × Theme matrix — A2A (R2). |
| `sociosemantic/theme_concentration_erc8004.csv` | Per-theme concentration — ERC (R2). |
| `sociosemantic/theme_concentration_googlea2a.csv` | Per-theme concentration — A2A (R2). |
| `sociosemantic/theme_actor_comparison.{csv,png}` | Cross-case comparison (R2). |
| `sociosemantic/specialization_compare.png` | Actor entropy histogram (R2). |
| `sociosemantic/ss_metrics.json` | R2 socio-semantic summary (cross-model consensus). |
| `sociosemantic/ss_metrics_cross_round.json` | R2 socio-semantic summary (cross-round consensus). |

### Other
| File | Description |
|------|-------------|
| `vis_positions_a2a.json` | A2A network node positions (for vis.js layout reproducibility). |
| `vis_positions_erc.json` | ERC network node positions. |
