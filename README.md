# RQ1: DAO Governance vs. Corporate Governance in Technology Standardization

Comparative case study of two AI protocol governance processes:

- **ERC-8004** ("Trustless Agents", Ethereum Improvement Proposal, 2025–2026) — permissionless DAO governance
- **Google A2A** (Agent-to-Agent protocol, open-source, 2025–present) — corporate-led governance

Research target: AOM/SMS conference paper (TIM track).

---

## Project Structure

```
workspace/
├── scripts/          # Data collection, annotation, enrichment, analysis
├── data/
│   ├── raw/          # Original scraped data (do not edit manually)
│   └── annotated/    # LLM-annotated records and author profiles
├── analysis/         # Derived metrics and network files
├── output/           # Final visualizations and summary reports
├── reports/          # Dated progress reports (R01–R05)
└── human-notes/      # Researcher notes and task lists
```

---

## Data Files

### `data/raw/`

| File | Description | Records |
|------|-------------|---------|
| `forum_posts.json` | ERC-8004 discussion posts from Ethereum Magicians forum. Scraped via Discourse JSON API. | 113 |
| `github_comments_filtered.json` | ERC-8004 GitHub PR records — bodies, issue comments, review comments, reviews — for 9 core lifecycle PRs (#1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488). | 36 |
| `a2a_commits.json` | Google A2A repository commits (author, message, date). | 522 |
| `a2a_issues.json` | Google A2A GitHub issues and issue comments. | 3,104 |
| `a2a_prs.json` | Google A2A GitHub pull requests and PR review comments. | 1,955 |
| `a2a_discussions.json` | Google A2A GitHub Discussions — discussion bodies, comments, and replies. Scraped via GraphQL API. | 822 |
| `a2a_gitvote_prs.json` | Full data for the two PRs that triggered formal TSC votes (#831: passed; #1206: superseded). Includes all comments, reviews, and git-vote bot messages. | 142 |
| `profiles_forum.json` | Public Discourse profile data for ERC-8004 forum authors (bio, title, groups). Also contains cross-platform identity map (forum handle ↔ GitHub handle). | 60 accounts |
| `profiles_github.json` | GitHub public profile data (company, bio, name, location) for ERC-8004 GitHub authors + top-30 A2A authors. | 39 accounts |
| `a2a_manifest.json` | Scrape metadata for A2A data (timestamps, record counts). | — |
| `filter_log.json` | Log of which GitHub PRs were kept/discarded in the ERC-8004 filtering step. | — |
| `CHECKSUMS.json` | SHA-256 checksums for all raw files. Regenerate after data updates. | — |

### `data/annotated/`

| File | Description | Records |
|------|-------------|---------|
| `annotated_records.json` | All records with LLM annotations. Fields: `stakeholder_institution`, `argument_type`, `stance`, `consensus_signal`, `key_point`. 4,863 total (4,814 + 49 git-vote). | 4,863 |
| `author_profiles.json` | One entry per unique canonical author across both cases. Fields: `institution_final`, `institution_source`, `argument_types`, `stances`, `threads_touched`, `bio`, `company_raw`. | 626 authors |
| `CHECKSUMS.json` | SHA-256 for annotated files. | — |

### `analysis/`

| File | Description |
|------|-------------|
| `structural_metrics.csv` | Quantitative governance indicators (openness index, contributor counts, timeline, PR merge rates). |
| `core_contributors.csv` | Core contributors per case with role, institution, argument distribution (22 ERC-8004 + 11 A2A). |
| `cross_case_overlap.csv` | Authors appearing in both cases. |
| `gitvote_analysis.md` | Detailed governance analysis of the two TSC-voted PRs (#831, #1206). |
| `network_edges_erc8004.csv` / `network_edges_a2a.csv` | Edge lists for Gephi import (source, target, type, weight). |
| `network_nodes_erc8004.csv` / `network_nodes_a2a.csv` | Node lists with institution and size for Gephi. |

### `output/`

| File | Description |
|------|-------------|
| `network_erc8004.html` | Interactive vis.js stakeholder network for ERC-8004 (67 nodes, 42 edges). Open in browser. |
| `network_a2a.html` | Interactive vis.js stakeholder network for A2A top-50 contributors (50 nodes, 243 edges). |
| `findings_summary.md` | Auto-generated summary of governance metrics from `compute_metrics.py`. |

---

## Scripts

Run all scripts with `uv run python scripts/<name>.py` from the workspace root.

### Data Collection

| Script | What it does | Output |
|--------|-------------|--------|
| `scrape_erc8004_forum.py` | Scrapes the ERC-8004 Ethereum Magicians forum thread via Discourse JSON API. Uses `curl` (not `requests`) due to Python 3.14 SSL issues. | `forum_posts.json` |
| `scrape_erc8004_prs.py` | Fetches the 9 core ERC-8004 lifecycle PRs directly by number from GitHub API. Collects PR bodies, issue comments, review comments, and reviews. | `github_comments_filtered.json` |
| `scrape_a2a.py` | Scrapes the Google A2A repository: commits, issues, PRs, and associated comments. Requires `--github-token` or `.env`. | `a2a_commits.json`, `a2a_issues.json`, `a2a_prs.json` |
| `patch_a2a_missing_pages.py` | Re-fetches any paginated data that timed out during the initial A2A scrape. | Updates `a2a_issues.json`, `a2a_prs.json` |
| `scrape_a2a_discussions.py` | Scrapes all GitHub Discussions from a2aproject/A2A via GraphQL API. | `a2a_discussions.json` |
| `scrape_gitvote_prs.py` | Fetches complete data for the two TSC-voted PRs (#831, #1206). | `a2a_gitvote_prs.json` |

### Filtering & Annotation

| Script | What it does | Output |
|--------|-------------|--------|
| `filter_github.py` | Whitelists only the 9 PRs that directly modify `ERCS/erc-8004.md`. Kept for documentation; `scrape_erc8004_prs.py` now writes filtered output directly. | `github_comments_filtered.json` |
| `annotate_llm.py` | LLM annotation of all records. Supports MiniMax (default), OpenAI-compatible, and Anthropic backends. Resumes from checkpoint. | `annotated_records.json` |
| `annotate_gitvote.py` | Annotates git-vote PR records specifically and appends to `annotated_records.json`. | Appends to `annotated_records.json`, updates `gitvote_analysis.md` |

### Enrichment & Analysis

| Script | What it does | Output |
|--------|-------------|--------|
| `enrich_profiles.py` | Fetches public profile data from Discourse and GitHub APIs. Detects cross-platform identity pairs. | `profiles_forum.json`, `profiles_github.json` |
| `enrich_institutions.py` | Merges profile data with LLM annotations to build per-author records. Upgrades institution labels using GitHub company field where available. | `author_profiles.json` |
| `identify_core_contributors.py` | Selects core contributors per case (ERC-8004: ≥3 records; A2A: ≥50 records). Infers roles and prints manual enrichment checklist. | `core_contributors.csv`, `cross_case_overlap.csv` |
| `compute_metrics.py` | Calculates structural governance metrics and comparison table. | `structural_metrics.csv`, `findings_summary.md` |
| `build_network.py` | Builds interactive stakeholder relationship graphs. ERC-8004: solid edges = forum reply chain, dashed = GitHub co-participation. A2A: dashed = co-participation only. | `network_erc8004.html`, `network_a2a.html`, edge/node CSVs |

---

## Pipeline Order

```
# ERC-8004
uv run python scripts/scrape_erc8004_forum.py
uv run python scripts/scrape_erc8004_prs.py

# Google A2A
uv run python scripts/scrape_a2a.py --github-token $TOKEN
uv run python scripts/patch_a2a_missing_pages.py
uv run python scripts/scrape_a2a_discussions.py
uv run python scripts/scrape_gitvote_prs.py

# Annotation
uv run python scripts/annotate_llm.py --backend minimax
uv run python scripts/annotate_gitvote.py

# Enrichment & analysis
uv run python scripts/enrich_profiles.py
uv run python scripts/enrich_institutions.py
uv run python scripts/identify_core_contributors.py
uv run python scripts/compute_metrics.py
uv run python scripts/build_network.py
```

---

## Environment

Requires `.env` in the workspace root:

```
GITHUB_PERSONAL_ACCESS_TOKEN=...
MINIMAX_API_KEY=...
```

Python environment managed with `uv`. Always use `uv run python`, never bare `python3`.

---

## Key Findings (summary)

| Metric | ERC-8004 (DAO) | Google A2A (Corporate) |
|--------|:--------------:|:---------------------:|
| Governance type | Permissionless DAO | Corporate hierarchy + TSC |
| Time to consensus | 169 days | Ongoing iteration |
| Total discussion records | 149 (forum + GitHub) | 5,700+ (issues, PRs, discussions) |
| Unique contributors | 71 | 600+ |
| Openness index | 1.000 | 0.956 |
| Dominant institution | Independent (82%) | Independent (64%), Google (23% of records) |
| Formal voting | None (lazy consensus) | TSC git-vote on contested PRs |
