# scripts/

All scripts run from the workspace root with `uv run python scripts/<subdir>/<name>.py`.

## scrape/ — Data collection

| Script | Output |
|--------|--------|
| `scrape_erc8004_forum.py` | `data/raw/forum_posts.json` — 113 ERC-8004 forum posts via Discourse JSON API |
| `scrape_erc8004_prs.py` | `data/raw/github_comments_filtered.json` — 36 records from 9 core lifecycle PRs |
| `scrape_a2a.py` | `data/raw/a2a_commits.json`, `a2a_issues.json`, `a2a_prs.json` |
| `scrape_a2a_discussions.py` | `data/raw/a2a_discussions.json` — GitHub Discussions via GraphQL |
| `scrape_gitvote_prs.py` | `data/raw/a2a_gitvote_prs.json` — TSC-voted PRs #831, #1206 |
| `patch_a2a_missing_pages.py` | Re-fetches any paginated A2A data that timed out |

## process/ — Filtering, annotation, enrichment

| Script | Output |
|--------|--------|
| `filter_github.py` | Legacy — whitelisted the 9 ERC-8004 core PRs (superseded by `scrape_erc8004_prs.py`) |
| `annotate_llm.py` | `data/annotated/annotated_records.json` — LLM annotation (MiniMax/OpenAI/Anthropic) |
| `annotate_gitvote.py` | Appends git-vote records to `annotated_records.json` |
| `enrich_profiles.py` | `data/raw/profiles_forum.json`, `profiles_github.json` |
| `enrich_institutions.py` | `data/annotated/author_profiles.json` — per-author profiles with LLM-inferred institutions |
| `extract_manual_institutions.py` | `data/raw/manual_institutions.json` — parses R07 manual investigation report |
| `merge_manual_institutions.py` | Updates `author_profiles.json` with R07 ground-truth institutions (3-tier provenance) |

## analyse/ — Metrics and analysis

| Script | Output |
|--------|--------|
| `compute_metrics.py` | `analysis/structural_metrics.csv` — governance indicators |
| `compute_kappa.py` | Inter-rater reliability (Cohen's κ) for LLM annotation |
| `compute_chi2.py` | χ² tests on institution × argument-type distributions |
| `identify_core_contributors.py` | `analysis/core_contributors.csv`, `cross_case_overlap.csv` |
| `sample_for_verification.py` | Random sample for human verification |
| `verify_annotation_coverage.py` | Coverage and gap report |

## visualise/ — Visualization builders

| Script | Output |
|--------|--------|
| `build_network.py` | `output/network_erc8004.html`, `network_a2a.html`, `network_compare.html` |
| `build_timeline.py` | `output/timeline_erc8004.html` |
| `build_bipartite.py` | `output/bipartite_erc8004.html`, `bipartite_a2a.html` |
