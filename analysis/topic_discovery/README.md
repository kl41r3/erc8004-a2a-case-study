# topic_discovery/ — Topic Modeling outputs

Unsupervised topic discovery from governance discourse text, using three
complementary methods. Organized by research round.

## Method summary

- **Thematic-LM**: Multi-agent LLM pipeline (Coder → Aggregator → Reviewer → Theme Coder).
  Produces a codebook of governance themes and per-record theme assignments.
  Requires LLM API. Run via `scripts/analyse/topic_discovery/thematic_lm/run.py`.
- **Comparative Discourse / BERTopic**: Embedding-based topic modeling using
  sentence-transformers + BERTopic clustering. Computes Jensen-Shannon Divergence
  between ERC and A2A topic distributions. No API needed.
  Run via `scripts/analyse/topic_discovery/comparative_discourse/run.py`.
- **CryptoBERT**: Domain-specific validation of BERTopic results using
  `ElKulako/cryptobert` (crypto-domain BERT) instead of general embeddings.
  ERC-8004 only. Run via `scripts/analyse/topic_discovery/crypto_bert/run.py`.

## r1/ — Baseline (ERC-8004 vs A2A, single model MiniMax-M2.5)

### Thematic-LM
| File | Description |
|------|-------------|
| `thematic_lm/themes.json` | Final 19-theme codebook: theme ID, label, description. |
| `thematic_lm/coded_records.json` | Per-record theme assignments (theme_id + confidence). |
| `thematic_lm/stage1_codes.json` | Stage 1: initial open codes assigned by Coder agent. |
| `thematic_lm/stage2_clusters.json` | Stage 2: code clusters produced by Aggregator agent. |
| `thematic_lm/stage3_codebook.json` | Stage 3: reviewed codebook after Reviewer agent pass. |

### Comparative Discourse (BERTopic)
| File | Description |
|------|-------------|
| `comparative_discourse/divergence_table.csv` | Per-topic distribution and JS divergence: erc8004_n, a2a_n, erc8004_pct, a2a_pct, abs_diff, js_contribution. |
| `comparative_discourse/topic_comparison.png` | Side-by-side topic distribution bar chart. |
| `comparative_discourse/topics_per_case.json` | Topic counts and proportions per case. |

### CryptoBERT (validation)
| File | Description |
|------|-------------|
| `crypto_bert/topics.json` | CryptoBERT topic assignments (n_records, n_topics, noise_rate_pct). |
| `crypto_bert/comparison_summary.md` | Comparison summary: CryptoBERT vs general BERTopic agreement. |

## r2/cross-model/ — 3-model independent annotation → consensus

Each annotator model independently ran the full Thematic-LM pipeline on the same
expanded corpus. Comparative Discourse uses cross-model consensus annotations.

### Thematic-LM per model
| Directory | Model | Description |
|-----------|-------|-------------|
| `thematic_lm/deepseek-v4-flash/` | DeepSeek-V4-Flash | coded_records, stage1_codes, stage2_clusters, stage3_codebook. |
| `thematic_lm/glm-4-plus/` | GLM-4-Plus | Same structure + `themes.json` (final codebook). |
| `thematic_lm/moonshot-v1-auto/` | Moonshot-v1-auto | Same structure + `themes.json`. |

### Comparative Discourse (BERTopic, R2 consensus)
| File | Description |
|------|-------------|
| `comparative_discourse/divergence_table.csv` | R2 BERTopic divergence (20 topics, JSD = 0.250). |
| `comparative_discourse/topic_comparison.png` | R2 topic distribution bar chart. |
| `comparative_discourse/topics_per_case.json` | R2 topic counts per case. |

## r2/cross-round/ — 3-model BERTopic on cross-round data

BERTopic run on each model's cross-round annotations to verify topic stability.

| Directory | Description |
|-----------|-------------|
| `erc/deepseek-v4-flash/` | ERC BERTopic: summary.json, topic_distribution.json, topic_info.csv. |
| `erc/glm-4-plus/` | Same structure. |
| `a2a/deepseek-v4-flash/` | A2A BERTopic: same structure. |
| `a2a/glm-4-plus/` | Same structure. |
| `coded_records.json` | Cross-round consensus coded records (theme assignments). |
| `themes.json` | Cross-round consensus theme codebook. |
