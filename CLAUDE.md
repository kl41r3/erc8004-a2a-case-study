# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## The Most Important Philosophy

Everything should be traceable. Provide links when you give a fact. Provides explanation when you give a conclusion, for example, location of codes, name of files, or the exact methods that you used. 

## Research Context

This is an academic research pipeline for **RQ1: DAO governance vs. corporate governance in technology standardization**. Two cases are compared:

- **Case A — ERC-8004** (Trustless Agents, proposed 2025-08-13, mainnet 2026-01-29): DAO governance via Ethereum Improvement Proposal process
- **Case B — Google A2A** (Agent-to-Agent protocol, first commit 2025-03-25): corporate hierarchy governance

Target output: AOM/SMS conference paper (TIM track).

## Commands

All scripts run inside the `uv` virtual environment. Always use `uv run`, never bare `python`.

```bash
# Full pipeline (in order)
uv run python scripts/scrape_erc8004.py                          # scrape ERC-8004 forum + GitHub
uv run python scripts/filter_github.py                           # whitelist core lifecycle PRs
uv run python scripts/scrape_a2a.py --github-token $TOKEN        # scrape Google A2A (PAT required)
uv run python scripts/patch_a2a_missing_pages.py                 # recover any timed-out pages
uv run python scripts/annotate_llm.py --backend minimax          # LLM annotation (MiniMax-M2.5)
uv run python scripts/compute_metrics.py                         # governance metrics + comparison table

# Stakeholder enrichment (run after annotation)
uv run python scripts/enrich_profiles.py                         # fetch Discourse + GitHub profiles → data/raw/profiles_*.json
uv run python scripts/enrich_institutions.py                     # merge profiles into per-author records → data/annotated/author_profiles.json
uv run python scripts/identify_core_contributors.py              # core contributor analysis + manual checklist → analysis/core_contributors.csv
uv run python scripts/build_network.py                           # interactive relationship graphs → output/network_*.html

# Annotation with other backends
uv run python scripts/annotate_llm.py --backend anthropic        # requires ANTHROPIC_API_KEY
uv run python scripts/annotate_llm.py --backend openai           # requires OPENAI_API_KEY + OPENAI_BASE_URL
uv run python scripts/annotate_llm.py --limit 5                  # test run, first 5 records only
```

## Architecture

### Data Flow

```
scrape_erc8004.py  ──►  data/raw/forum_posts.json
                         data/raw/github_comments.json
                                │
                         filter_github.py
                                │
                         data/raw/github_comments_filtered.json

scrape_a2a.py      ──►  data/raw/a2a_commits.json
patch_a2a_...py          data/raw/a2a_issues.json        (issues + issue comments)
                         data/raw/a2a_prs.json           (PRs + review comments)

annotate_llm.py    ──►  data/annotated/annotated_records.json
                                │
                         compute_metrics.py
                                │
                         analysis/structural_metrics.csv
                         output/findings_summary.md

enrich_profiles.py ──►  data/raw/profiles_forum.json    (Discourse bio/company)
                         data/raw/profiles_github.json   (GitHub bio/company)
                                │
                    enrich_institutions.py
                                │
                         data/annotated/author_profiles.json
                                │
                    identify_core_contributors.py
                                │
                         analysis/core_contributors.csv
                         analysis/cross_case_overlap.csv
                                │
                    build_network.py
                                │
                         output/network_erc8004.html     (vis.js interactive)
                         output/network_a2a.html
                         analysis/network_edges_*.csv    (Gephi-compatible)
```

### Key Design Decisions

**curl over requests**: Python 3.14's `requests` has SSL EOF errors against `ethereum-magicians.org`. All HTTP is done via `subprocess` + system `curl`. GitHub API uses `-sL` to follow redirects.

**Discourse pagination**: Must use numeric topic ID only — `/t/25098/posts.json?post_ids[]=...`. Slug+ID form returns 404.

**URL parameter concatenation**: `fetch_paginated()` checks for existing `?` before appending — use `&` if `?` already present, else `?`. A double-`?` bug caused the initial A2A data loss.

**Pandas 3.0 date parsing**: `pd.to_datetime(utc=True)` infers format from row 0 and coerces mismatches to NaT in mixed DataFrames. All date parsing uses `python-dateutil.parser.parse()` per-record instead.

**MiniMax-M2.5**: Reasoning model — response contains `<think>...</think>` block before JSON. Strip with regex before parsing. Requires `max_tokens=1024` minimum (reasoning consumes ~60–200 tokens before JSON output begins).

**Annotation resume**: `annotate_llm.py` deduplicates by `_record_id()` (composite of case + source + id + date). Safe to interrupt and restart.

### GitHub Data Filtering

`filter_github.py` whitelists only 9 PRs that directly modify `ERCS/erc-8004.md` or change its lifecycle status. The GitHub search API returns any PR mentioning ERC-8004 (including ecosystem ERCs with `Requires: ERC-8004`), which inflated raw results from 11 real records to 149.

Core lifecycle PRs: `#1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488`

### LLM Annotation Schema

Each record gets annotated with:
- `stakeholder_institution`: Google | Coinbase | MetaMask | Ethereum Foundation | Independent | Unknown
- `argument_type`: Technical | Economic | Governance-Principle | Process | Off-topic
- `stance`: Support | Oppose | Modify | Neutral | Off-topic
- `consensus_signal`: Adopted | Rejected | Pending | N/A
- `key_point`: ≤20 word summary

### Environment Variables (`.env`)

```
MINIMAX_API_KEY=...
GITHUB_PERSONAL_ACCESS_TOKEN=...
ANTHROPIC_API_KEY=...   # optional
OPENAI_API_KEY=...      # optional
OPENAI_BASE_URL=...     # optional, for any OpenAI-compat endpoint
```

## Data Integrity

`data/raw/CHECKSUMS.json` stores SHA-256 for every raw file. Regenerate after any data update:

```python
python3 -c "
import json, hashlib
from pathlib import Path
raw = Path('data/raw')
m = {f.name: {'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(raw.glob('*.json')) if f.name != 'CHECKSUMS.json'}
(raw / 'CHECKSUMS.json').write_text(json.dumps(m, indent=2))
"
```

## Git Conventions

Commit types: `feat`, `fix`, `data`, `analysis`, `docs`, `chore`

Tag milestones after significant data events (e.g., `v0.3-a2a-complete`). Progress reports live in `reports/` with naming `R{N}_{date}_{topic}.md`; `reports/INDEX.md` is the master index.


## Report and Rigor

Write a report to record your progress rigorously, with traceable links.