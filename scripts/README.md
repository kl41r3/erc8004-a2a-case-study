# scripts/

All scripts run from the workspace root with `uv run python scripts/<subdir>/<name>.py`.

```
scripts/
├── scrape/          Data collection (raw JSON → data/raw/)
├── process/         Filtering, annotation, institution enrichment
├── analyse/         Metrics, topic discovery, network analysis, paper figures
│   ├── topic_discovery/
│   │   ├── thematic_lm/         Method 1 — LLM-based open coding pipeline
│   │   ├── comparative_discourse/  Method 2 — BERTopic comparison (no API needed)
│   │   └── crypto_bert/         Method 2b — CryptoBERT robustness check
│   └── network_discourse/
│       ├── dna/                 Method 1 — Discourse Network Analysis
│       └── sociosemantic/       Method 2 — Socio-semantic bipartite network
└── visualise/       Interactive HTML graphs and static paper figures
```

---

## scrape/

| Script | Output |
|--------|--------|
| `scrape_erc8004_forum.py` | `data/raw/forum_posts.json` — 113 ERC-8004 Discourse posts via JSON API |
| `scrape_erc8004_prs.py` | `data/raw/github_comments_filtered.json` — 36 records from 9 core lifecycle PRs |
| `scrape_a2a.py` | `data/raw/a2a_commits.json`, `a2a_issues.json`, `a2a_prs.json` |
| `scrape_a2a_discussions.py` | `data/raw/a2a_discussions.json` — GitHub Discussions via GraphQL |
| `scrape_gitvote_prs.py` | `data/raw/a2a_gitvote_prs.json` — TSC-voted PRs #831, #1206 |
| `patch_a2a_missing_pages.py` | Re-fetches any paginated A2A data that timed out |

---

## process/

| Script | Output |
|--------|--------|
| `annotate_llm.py` | `data/annotated/annotated_records.json` — LLM annotation (MiniMax / OpenAI / Anthropic) |
| `annotate_gitvote.py` | Appends git-vote records to `annotated_records.json` |
| `enrich_profiles.py` | `data/raw/profiles_forum.json`, `profiles_github.json` — author Discourse/GitHub profiles |
| `enrich_institutions.py` | `data/annotated/author_profiles.json` — per-author profiles with LLM-inferred institutions |
| `extract_manual_institutions.py` | `data/raw/manual_institutions.json` — parses the R07 manual investigation report |
| `merge_manual_institutions.py` | Writes R07 ground-truth institutions (3-tier provenance) back into `author_profiles.json` |
| `filter_github.py` | Legacy — whitelisted the 9 ERC-8004 core PRs; superseded by `scrape_erc8004_prs.py` |

---

## analyse/

### Metrics and verification

| Script | Output |
|--------|--------|
| `compute_metrics.py` | `analysis/structural_metrics.csv` — governance indicator table |
| `compute_kappa.py` | Cohen's κ inter-rater reliability for LLM annotation |
| `compute_chi2.py` | χ² tests on institution × argument-type distributions |
| `identify_core_contributors.py` | `analysis/core_contributors.csv`, `cross_case_overlap.csv` |
| `sample_for_verification.py` | Random sample for human spot-check |
| `verify_annotation_coverage.py` | Coverage and gap report for annotations |

### Network data preparation

| Script | Output |
|--------|--------|
| `rebuild_a2a_network_full.py` | `analysis/network_nodes_a2a.csv`, `network_edges_a2a.csv` — full contributor set, no elbow cutoff |

### Paper-ready analysis figures

| Script | Output |
|--------|--------|
| `analyze_network.py` | `output/network_metrics.json`, `output/network_sna_comparison.png`, `output/network_degree_dist.png`, `analysis/network_metrics_table.csv` |
| `analyze_topic.py` | `output/figures/topic_argtype_comparison.png`, `topic_stance_heatmap.png`, `topic_temporal_comparison.png`, `output/stats/topic_stats.json` |
| `analyze_voting_mechanism.py` | `output/voting_mechanism_comparison.png`, `output/voting_stats.json` |

### topic_discovery/

| Entry point | Method | Notes |
|-------------|--------|-------|
| `thematic_lm/run.py` | Thematic-LM | Multi-agent pipeline: Coder → Aggregator → Reviewer → Theme Coder. Requires LLM API. Checkpointed every 10 batches. |
| `comparative_discourse/run.py` | BERTopic comparative discourse | Local sentence-transformers embeddings; JSD comparison across cases. No API needed. |
| `crypto_bert/run.py` | CryptoBERT validation | Re-embeds ERC-8004 with `ElKulako/cryptobert` to verify Method 2 topic findings are embedding-agnostic. ERC-8004 only. |

### network_discourse/

| Entry point | Method | Notes |
|-------------|--------|-------|
| `dna/run.py` | Discourse Network Analysis | Actor–actor network from shared stances; Borgatti-Everett core-periphery. `--min-shared` threshold optional. |
| `sociosemantic/run.py` | Socio-semantic bipartite network | Actor ↔ topic bipartite graph; entropy comparison across cases. |

---

## visualise/

| Script | Output |
|--------|--------|
| `build_network.py` | `output/network_erc8004.html`, `network_a2a.html`, `network_compare.html` — vis.js interactive graphs |
| `build_timeline.py` | `output/timeline_erc8004.html` |
| `build_bipartite.py` | `output/bipartite_erc8004.html`, `bipartite_a2a.html` |
| `build_paper_figures.py` | All figures under `output/figures/`; copies them to `paper-acm/` for LaTeX |

---

## Typical run order

```bash
# 1. Scrape
uv run python scripts/scrape/scrape_erc8004_forum.py
uv run python scripts/scrape/scrape_erc8004_prs.py
uv run python scripts/scrape/scrape_a2a.py --github-token $GITHUB_PERSONAL_ACCESS_TOKEN
uv run python scripts/scrape/scrape_a2a_discussions.py
uv run python scripts/scrape/scrape_gitvote_prs.py

# 2. Annotate and enrich
uv run python scripts/process/annotate_llm.py --backend minimax
uv run python scripts/process/annotate_gitvote.py
uv run python scripts/process/enrich_profiles.py
uv run python scripts/process/enrich_institutions.py
uv run python scripts/process/merge_manual_institutions.py

# 3. Core metrics
uv run python scripts/analyse/compute_metrics.py
uv run python scripts/analyse/compute_kappa.py
uv run python scripts/analyse/compute_chi2.py
uv run python scripts/analyse/identify_core_contributors.py

# 4. Topic and network analysis (pick methods as needed)
uv run python scripts/analyse/topic_discovery/thematic_lm/run.py --backend minimax
uv run python scripts/analyse/network_discourse/dna/run.py
uv run python scripts/analyse/network_discourse/sociosemantic/run.py

# 5. Paper analysis figures
uv run python scripts/analyse/rebuild_a2a_network_full.py
uv run python scripts/analyse/analyze_network.py
uv run python scripts/analyse/analyze_topic.py
uv run python scripts/analyse/analyze_voting_mechanism.py

# 6. Visualisations and final paper figures
uv run python scripts/visualise/build_network.py
uv run python scripts/visualise/build_paper_figures.py
```
