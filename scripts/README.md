# scripts/

All scripts run from the workspace root with `uv run python scripts/<subdir>/<name>.py`.

```
scripts/
├── README.md                ← This file
├── lib/                     Shared library (paths, models, colours, I/O, figure utils)
│   ├── paths.py             All ROOT-relative path constants — single source of truth
│   ├── models.py            BACKENDS dicts, canonical model IDs, bot list, institution patterns
│   ├── colors.py            Institution colour palettes + colour-blind safe fallback
│   ├── io.py                load_json / save_json / load_csv / save_csv / ensure_dir
│   └── figure_utils.py      save_figure (PNG+PDF → output/figures/ + paper-acm/fig/)
├── scrape/                  Data collection (raw JSON → data/raw/)
├── process/                 Filtering, annotation, institution enrichment
├── analyse/                 Metrics, topic discovery, network analysis
│   ├── topic_discovery/
│   │   ├── thematic_lm/         Method 1 — LLM-based open coding pipeline
│   │   ├── comparative_discourse/  Method 2 — BERTopic comparison (no API needed)
│   │   └── crypto_bert/         Method 2b — CryptoBERT robustness check
│   └── network_discourse/
│       ├── dna/                 Method 1 — Discourse Network Analysis
│       └── sociosemantic/       Method 2 — Socio-semantic bipartite network
├── visualise/               Interactive HTML graphs and paper figures
├── publish/                 Pinned Hugging Face download and local release staging
└── pipeline/                Orchestration scripts (chain multiple phases)
```

All scripts import path constants from `scripts/lib/paths.py`. Running `grep "data/annotated/r2/consensus" scripts/` should return nothing — every path comes from the library.

---

## lib/ — Shared library

Single source of truth for constants and utilities. Every script in the pipeline imports from here — no more duplicated bot lists, colour maps, or hardcoded paths.

| Module | What it provides |
|--------|-----------------|
| `lib.paths` | `ROOT`, `DATA_RAW`, `DATA_ANNOTATED_R1`, `DATA_ANNOTATED_R2_CONSENSUS`, `ANALYSIS_METRICS_R1`, `ANALYSIS_TD_R1_THEMATIC`, `OUTPUT_FIGURES`, etc. |
| `lib.models` | `BACKENDS_ANNOTATION`, `BACKENDS_CROSS_ROUND`, `BACKENDS_THEMATIC`, `CANONICAL_MODELS`, `LEGACY_KEYS`, `BOTS`, `is_bot()`, `INSTITUTION_PATTERNS`, `ERC8004_CORE_PRS` |
| `lib.colors` | `ERC_COLORS`, `A2A_COLORS`, `INST_PALETTE`, `CB_PALETTE`, `COLOR_CARD`, `BERT_SEMANTIC`, `CRYPTO_SEMANTIC` |
| `lib.io` | `load_json()`, `save_json()`, `load_csv()`, `save_csv()`, `ensure_dir()` |
| `lib.figure_utils` | `save_figure(fig, name, paper=True)` — writes PNG+PDF to `output/figures/` and copies to `paper-acm/fig/` |

---

## scrape/

| Script | Output |
|--------|--------|
| `scrape_erc8004_forum.py` | `data/raw/forum_posts.json` — ERC-8004 Discourse posts via JSON API |
| `scrape_erc8004_prs.py` | `data/raw/github_comments_filtered.json` — 36 records from 9 core lifecycle PRs |
| `scrape_a2a.py` | `data/raw/a2a_commits.json`, `a2a_issues.json`, `a2a_prs.json` |
| `scrape_a2a_discussions.py` | `data/raw/a2a_discussions.json` — GitHub Discussions via GraphQL |
| `scrape_gitvote_prs.py` | `data/raw/a2a_gitvote_prs.json` — TSC-voted PRs #831, #1206 |
| `scrape_r2_forum.py` | `data/raw/r2/tier1/` and `tier2/` — 34-ERC cluster forum posts |
| `scrape_r2_github.py` | `data/raw/r2/tier1/` and `tier2/` — GitHub PRs for cluster ERCs |
| `patch_a2a_missing_pages.py` | Re-fetches any paginated A2A data that timed out |
| `patch_r2_tier2_github.py` | Deduplicates R2 tier-2 GitHub data + fixes drift PR mapping |

---

## process/

| Script | Description |
|--------|-------------|
| `annotate_llm.py` | R1 LLM annotation (MiniMax / OpenAI / Anthropic) → `data/annotated/r1/annotated_records.json` |
| `annotate_r2.py` | R2 multi-model annotation (ERC-8004 cluster) → `data/annotated/r2/cross-model/erc/{model}/` |
| `annotate_r3.py` | Cross-round annotation (3 models × 3 rounds) → `data/annotated/r2/cross-round/` |
| `annotate_a2a_r2.py` | R2 multi-model annotation (A2A) → `data/annotated/r2/cross-model/a2a/{model}/` |
| `annotate_gitvote.py` | Git-vote record annotation, appends to `annotated_records.json` |
| `annotate_thematic.py` | Thematic open-coding (ERC, 3 models) → `data/annotated/r2/cross-model/thematic/` |
| `annotate_thematic_a2a.py` | Thematic open-coding (A2A, 3 models) → `data/annotated/r2/cross-model/thematic/a2a/` |
| `build_consensus.py` | 2-of-3 majority-vote cross-model consensus → `data/annotated/r2/cross-model/consensus/` |
| `build_r3_consensus.py` | Cross-round consensus → `data/annotated/r2/cross-round/` |
| `build_croissant_release.py` | Versioned Croissant 1.1 metadata + Parquet RecordSets → `data/croissant/v1/` |
| `complete_a2a_deepseek.py` | Gap-fill: adds missing DeepSeek A2A records from GLM/Moonshot sources |
| `enrich_profiles.py` | Fetch Discourse + GitHub author profiles → `data/raw/profiles_*.json` |
| `enrich_institutions.py` | Merge profiles into per-author institution records → `data/annotated/r1/author_profiles.json` |
| `extract_manual_institutions.py` | Parse an explicitly supplied private investigation report → `data/raw/manual_institutions.json` |
| `merge_manual_institutions.py` | Merge R07 ground-truth institutions into `author_profiles.json` |

---

## analyse/

### Flat scripts (metrics + verification)

| Script | Key outputs |
|--------|-------------|
| `compute_metrics.py` | `analysis/metrics/r1/structural_metrics.csv` — R1 governance indicators |
| `compute_metrics_r2.py` | `analysis/metrics/r2/structural_metrics.csv` — R2 governance indicators |
| `compute_cross_round_icr.py` | `analysis/metrics/r2/icr_cross_round.csv` — per-model test-retest ICR across three rounds |
| `compute_cross_model_kappa_4models.py` | `analysis/metrics/r2/kappa_4models.json` — four-model reliability on the shared R1/R2 subset |
| `identify_core_contributors.py` | `analysis/metrics/r1/core_contributors.csv`, `cross_case_overlap.csv` |
| `build_network_r2.py` | `analysis/metrics/r2/network_erc_nodes.csv`, `network_a2a_nodes.csv`, etc. |
| `rebuild_a2a_network_full.py` | `analysis/metrics/r1/network_nodes_a2a.csv`, `network_edges_a2a.csv` |
| `export_top_nodes.py` | `analysis/metrics/institution_verification_checklist.csv` |
| `analyze_network.py` | `output/figures/network_sna_comparison.png`, `network_degree_dist.png` |
| `analyze_topic.py` | `output/figures/topic_argtype_comparison.png`, `topic_stance_heatmap.png` |
| `analyze_voting_mechanism.py` | `output/figures/voting_mechanism_comparison.png` |
| `validate_multimodel.py` | `data/annotated/r2/cross-model/validation/` — pairwise κ, Fleiss' κ, report |
| `validate_thematic.py` | `data/annotated/r2/cross-model/thematic/validation/` — cross-model theme convergence |
| `sample_for_verification.py` | `verification/sample_50.csv`, `sample_50.json` |
| `verify_annotation_coverage.py` | stdout only (CI pass/fail) |

### topic_discovery/

| Entry point | Method | Outputs |
|-------------|--------|---------|
| `thematic_lm/run.py` | Thematic-LM (R1) | `analysis/topic_discovery/r1/thematic_lm/` — codes, clusters, codebook, themes |
| `thematic_lm/run_r2.py` | Thematic-LM (R2) | `analysis/topic_discovery/r2/cross-model/thematic_lm/{model}/` |
| `comparative_discourse/run.py` | BERTopic (R1) | `analysis/topic_discovery/r1/comparative_discourse/` |
| `comparative_discourse/run_r2.py` | BERTopic (R2) | `analysis/topic_discovery/r2/cross-model/comparative_discourse/` |
| `crypto_bert/run.py` | CryptoBERT validation (R1) | `analysis/topic_discovery/r1/crypto_bert/` |

### network_discourse/

| Entry point | Method | Outputs |
|-------------|--------|---------|
| `dna/run.py` | DNA (R1) | `analysis/network_discourse/r1/dna/` — congruence/conflict networks, metrics |
| `dna/run_r2.py` | DNA (R2) | `analysis/network_discourse/r2/dna/` |
| `sociosemantic/run.py` | Socio-semantic (R1) | `analysis/network_discourse/r1/sociosemantic/` — bipartite, entropy, gatekeepers |
| `sociosemantic/run_r2.py` | Socio-semantic (R2) | `analysis/network_discourse/r2/sociosemantic/` |

---

## visualise/

| Script | Output |
|--------|--------|
| `build_network.py` | `output/interactive/network_erc8004.html`, `network_a2a.html`, `network_compare.html` |
| `build_bipartite.py` | `output/interactive/bipartite_erc8004.html`, `bipartite_a2a.html` |
| `build_timeline.py` | `output/interactive/timeline_erc8004.html` |
| `build_figure_network_compare.py` | `output/figures/network_compare_r2.{png,pdf,html}` |
| `build_paper_figures.py` | `output/figures/` — all R1 paper figures (PNG+PDF) + copies to `paper-acm/fig/` |
| `build_paper_figures_r2.py` | `output/figures/` — all R2 paper figures (PNG+PDF) + copies to `paper-acm/fig/` |
| `extract_vis_positions.py` | Extracts stabilized node positions from vis.js HTML → `output/figures/vis_positions_*.json` |
| `render_network_white.py` | Screenshots white-background network HTML → `output/figures/network_compare_white.{png,pdf}` |

---

## pipeline/

| Script | Description |
|--------|-------------|
| `run_r2.py` | R2 full pipeline orchestrator — runs 10 phases in order with resume capability |

---

## repository verification and publication staging

```bash
uv run python scripts/verify_repository.py
uv run python scripts/publish/download_hf_dataset.py
uv run python scripts/verify_repository.py --with-data
uv run python scripts/publish/prepare_hf_dataset.py --output /private/tmp/rq1-hf-release
```

The first command validates the code-only GitHub boundary. The downloader restores the frozen
R1/R2 Hugging Face payloads. Rebuild the release with `make reproduce`; the third command can
then verify the frozen data and rebuilt `neurips26/` checksums and row counts. The final command
creates a complete data-only v1.1.1 staging directory and never uploads it.

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
uv run python scripts/process/extract_manual_institutions.py --input /path/to/private-report.md
uv run python scripts/process/merge_manual_institutions.py

# 3. Core metrics
uv run python scripts/analyse/compute_metrics.py
uv run python scripts/analyse/identify_core_contributors.py

# 4. Topic and network analysis
uv run python scripts/analyse/topic_discovery/thematic_lm/run.py --backend minimax
uv run python scripts/analyse/network_discourse/dna/run.py
uv run python scripts/analyse/network_discourse/sociosemantic/run.py

# 5. Visualisations and paper figures
uv run python scripts/visualise/build_network.py
uv run python scripts/visualise/build_paper_figures.py

# 6. R2 pipeline (automates R2 phases)
uv run python scripts/pipeline/run_r2.py
```

## Model naming convention

Canonical model IDs (used in all filesystem paths):
- `deepseek-v4-flash` — DeepSeek via api.deepseek.com
- `glm-4-plus` — GLM via open.bigmodel.cn
- `moonshot-v1-auto` — Moonshot (Kimi platform) via api.moonshot.cn

Legacy keys (`deepseek`, `kimi`, `glm`) are accepted in CLI `--model` arguments and resolved to canonical IDs via `lib.models.LEGACY_KEYS`.

## Archived scripts

Deprecated scripts moved to `_trash/scripts/`:
- `filter_github.py` — superseded by `scrape_erc8004_prs.py`
- `compute_kappa.py` — superseded by `validate_multimodel.py`
- `compute_chi2.py` — merged into `analyze_topic.py`
