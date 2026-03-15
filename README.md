# RQ1: DAO Governance vs. Corporate Governance in Technology Standardization

Comparative case study of two AI protocol governance processes:

- **ERC-8004** ("Trustless Agents", Ethereum Improvement Proposal, 2025–2026) — permissionless DAO governance
- **Google A2A** (Agent-to-Agent protocol, 2025–present) — corporate-led governance

Target output: AOM/SMS conference paper (TIM track).

---

## Project Structure

```
workspace/
├── scripts/
│   ├── scrape/       # Data collection
│   ├── process/      # Filtering, annotation, enrichment
│   ├── analyse/      # Metrics and statistical analysis
│   └── visualise/    # Visualization builders
├── data/
│   ├── raw/          # Original scraped data (do not edit manually)
│   └── annotated/    # LLM-annotated records and author profiles
├── analysis/         # Derived metrics and network export files
├── output/           # Final visualizations and summary reports
└── paper/            # LaTeX draft
```

Each folder has its own `README.md` listing files and their purpose.

---

## Pipeline

Run from workspace root with `uv run python scripts/<subdir>/<name>.py`.

```bash
# 1. Scrape
uv run python scripts/scrape/scrape_erc8004_forum.py
uv run python scripts/scrape/scrape_erc8004_prs.py
uv run python scripts/scrape/scrape_a2a.py --github-token $TOKEN
uv run python scripts/scrape/scrape_a2a_discussions.py
uv run python scripts/scrape/scrape_gitvote_prs.py

# 2. Annotate
uv run python scripts/process/annotate_llm.py --backend minimax
uv run python scripts/process/annotate_gitvote.py

# 3. Enrich institutions (run in order)
uv run python scripts/process/enrich_profiles.py
uv run python scripts/process/enrich_institutions.py
uv run python scripts/process/extract_manual_institutions.py
uv run python scripts/process/merge_manual_institutions.py

# 4. Analyse
uv run python scripts/analyse/compute_metrics.py
uv run python scripts/analyse/identify_core_contributors.py

# 5. Visualise
uv run python scripts/visualise/build_network.py
uv run python scripts/visualise/build_timeline.py
uv run python scripts/visualise/build_bipartite.py
```

---

## Environment

```
GITHUB_PERSONAL_ACCESS_TOKEN=...
MINIMAX_API_KEY=...
```