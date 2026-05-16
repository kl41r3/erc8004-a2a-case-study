# Decentralized Paradox: DAO Governance vs. Corporate Governance in AI Protocol Standardization

Comparative case study of two AI agent protocol governance processes:

- **ERC-8004** ("Trustless Agents", Ethereum Improvement Proposal, 2025–2026) — permissionless DAO governance via EIP rough consensus
- **Google A2A** (Agent-to-Agent protocol, 2025–present) — corporate-led governance under Linux Foundation

**Research Question:** Compared to corporations, how does the governance structure of permissionless DAOs shape participation patterns, discourse composition, and network topology in AI agent protocol standardization?

---

## Quickstart (Reproduce All Results)

### Prerequisites

- **Python ≥ 3.14** + **uv** (package manager)
- **curl** (system, for API scraping)
- **GitHub Personal Access Token** (only for A2A data collection; ERC-8004 data is public)
- **MiniMax API key** (for LLM annotation; optional if using `--backend anthropic` or `--backend openai`)

### 1. Clone & Install

```bash
git clone <this-repo> && cd <this-repo>
uv sync
cp .env.example .env   # then edit .env with your keys
```

The `.env` file needs:
```
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
MINIMAX_API_KEY=...
# Optional:
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
```

### 2. Data Collection (Scraping)

```bash
# ERC-8004: forum posts + GitHub PRs (no token needed)
uv run python scripts/scrape_erc8004_forum.py
uv run python scripts/scrape_erc8004_prs.py

# Filter to core lifecycle PRs (9 PRs that directly modify erc-8004.md)
uv run python scripts/filter_github.py

# Google A2A: issues, PRs, discussions (GitHub token required)
uv run python scripts/scrape_a2a.py --github-token $GITHUB_PERSONAL_ACCESS_TOKEN
uv run python scripts/scrape_a2a_discussions.py --github-token $GITHUB_PERSONAL_ACCESS_TOKEN
uv run python scripts/scrape_gitvote_prs.py --github-token $GITHUB_PERSONAL_ACCESS_TOKEN

# Recover any timed-out pages (idempotent)
uv run python scripts/patch_a2a_missing_pages.py
```

**Expected output:** ~6,030 raw records in `data/raw/`. After filtering: 4,323 records (ERC-8004: 142; A2A: 4,181).

### 3. LLM Annotation

```bash
# Full annotation with MiniMax-M2.5 (safe to interrupt/restart — deduplicates by record_id)
uv run python scripts/annotate_llm.py --backend minimax

# Alternatives:
uv run python scripts/annotate_llm.py --backend anthropic   # needs ANTHROPIC_API_KEY
uv run python scripts/annotate_llm.py --backend openai      # needs OPENAI_API_KEY + OPENAI_BASE_URL

# Test run on first 5 records:
uv run python scripts/annotate_llm.py --limit 5
```

Each record receives: `stakeholder_institution`, `argument_type`, `stance`, `consensus_signal`, `key_point`.

**Expected output:** `data/annotated/annotated_records.json` (5,416 / 5,421 annotated, 99.9%).

### 4. Stakeholder Enrichment

```bash
uv run python scripts/enrich_profiles.py          # fetch Discourse + GitHub profiles
uv run python scripts/enrich_institutions.py       # merge profiles → author_profiles.json
uv run python scripts/identify_core_contributors.py  # core contributor analysis
```

**Expected outputs:** `data/annotated/author_profiles.json`, `analysis/core_contributors.csv`, `analysis/cross_case_overlap.csv`.

### 5. Preliminary Analysis (Structural Metrics + Networks)

```bash
uv run python scripts/compute_metrics.py           # governance metrics + comparison table
uv run python scripts/analyze_network.py           # full SNA: 13 metrics + 2 figures
uv run python scripts/analyze_topic.py             # argument type distribution + χ² + temporal
uv run python scripts/analyze_voting_mechanism.py  # decision mechanism comparison
uv run python scripts/compute_chi2.py              # chi-square / Cramér's V
uv run python scripts/compute_kappa.py             # inter-coder reliability (Cohen's κ)
uv run python scripts/build_network.py             # interactive vis.js HTML networks
```

**Expected outputs:**
- `analysis/structural_metrics.csv` — governance metrics table
- `analysis/network_metrics_table.csv` — SNA comparison table
- `output/network_sna_comparison.png` — Figure 3: side-by-side network visualization
- `output/network_degree_dist.png` — degree distribution by rank
- `output/figures/topic_argtype_comparison.png` — argument type bar chart
- `output/figures/topic_stance_heatmap.png` — stance × argument heatmap
- `output/figures/topic_temporal_comparison.png` — temporal evolution (2-panel)
- `output/voting_mechanism_comparison.png` — governance decision flow diagrams
- `output/interactive/` — vis.js HTML networks (4 files)

### 6. Extended Analysis: Topic Discovery

Two complementary methods for unsupervised topic discovery from raw text:

```bash
# Method 1: Thematic-LM — multi-agent LLM thematic analysis (needs MiniMax API)
uv run python scripts/analyse/topic_discovery/thematic_lm/run.py --backend minimax

# Method 2: Comparative Discourse — BERTopic + Jensen-Shannon divergence (no API)
uv run python scripts/analyse/topic_discovery/comparative_discourse/run.py

# Method 2b: CryptoBERT validation (no API, ERC-8004 only)
uv run python scripts/analyse/topic_discovery/crypto_bert/run.py
```

**Expected outputs:** 19-theme codebook (`output/topic_discovery/thematic_lm/themes.json`), per-record theme assignments, JS divergence table, comparison figures.

### 7. Extended Analysis: Network Discourse

Combines Thematic-LM topics + LLM stance labels to build discourse networks:

```bash
# Method 1: Discourse Network Analysis (DNA) — congruence/conflict networks
uv run python scripts/analyse/network_discourse/dna/run.py

# Method 2: Socio-semantic Bipartite Network — actor × theme specialization
uv run python scripts/analyse/network_discourse/sociosemantic/run.py
```

**Expected outputs:** congruence/conflict edge tables, actor diversity metrics, theme concentration metrics, DNA comparison figure, specialization histograms.

### 8. Verification (Inter-coder Reliability)

```bash
uv run python scripts/sample_for_verification.py    # generate N=50 stratified sample
# Then follow verification/INTER_RATER_GUIDE.md for manual coding
uv run python scripts/compute_kappa.py              # compute Cohen's κ
```

---

## Repository Structure

```
workspace/
├── scripts/
│   ├── scrape_erc8004_forum.py         # Discourse forum scraper
│   ├── scrape_erc8004_prs.py           # GitHub PRs for ERC-8004
│   ├── scrape_a2a.py                   # GitHub REST + GraphQL (issues + PRs)
│   ├── scrape_a2a_discussions.py       # GitHub Discussions (GraphQL)
│   ├── scrape_gitvote_prs.py           # TSC GitVote PRs (#831, #1206)
│   ├── patch_a2a_missing_pages.py     # Recover timed-out pages
│   ├── filter_github.py               # Whitelist 9 core lifecycle PRs
│   ├── annotate_llm.py                # LLM annotation (MiniMax/Anthropic/OpenAI)
│   ├── annotate_gitvote.py            # Manual GitVote PR annotation
│   ├── enrich_profiles.py             # Discourse + GitHub profile fetcher
│   ├── enrich_institutions.py         # Profile → institution merge
│   ├── extract_manual_institutions.py # R07 manual institution labels
│   ├── merge_manual_institutions.py   # Merge manual + LLM institutions
│   ├── compute_metrics.py             # Governance structural metrics
│   ├── compute_chi2.py                # Chi-square / Cramér's V tests
│   ├── compute_kappa.py               # Inter-coder reliability (Cohen's κ)
│   ├── analyze_network.py             # Full SNA (13 metrics + figures)
│   ├── analyze_topic.py               # Argument type + temporal + χ²
│   ├── analyze_voting_mechanism.py    # Decision mechanism comparison
│   ├── identify_core_contributors.py  # Core contributor analysis
│   ├── rebuild_a2a_network_full.py    # Rebuild A2A network without top-N cutoff
│   ├── build_network.py               # Interactive vis.js HTML networks
│   ├── sample_for_verification.py     # Stratified N=50 sample for IRR
│   ├── verify_annotation_coverage.py  # Annotation completeness check
│   └── analyse/
│       ├── topic_discovery/
│       │   ├── thematic_lm/           # Method 1: multi-agent LLM analysis
│       │   ├── comparative_discourse/ # Method 2: BERTopic + JS divergence
│       │   └── crypto_bert/           # Method 2b: CryptoBERT validation
│       └── network_discourse/
│           ├── dna/                   # Method 1: Discourse Network Analysis
│           └── sociosemantic/         # Method 2: Socio-semantic bipartite
├── data/
│   ├── raw/                           # Original scraped data (do not edit manually)
│   │   ├── forum_posts.json           # 113 ERC-8004 forum posts
│   │   ├── github_comments_filtered.json # 36 filtered ERC-8004 GitHub records
│   │   ├── a2a_issues.json            # ~500 A2A issues + comments
│   │   ├── a2a_prs.json               # 1,955 A2A PRs + reviews
│   │   ├── a2a_discussions.json       # 234 A2A discussions
│   │   ├── a2a_gitvote_prs.json       # 2 TSC-voted PRs
│   │   ├── a2a_manifest.json          # A2A data collection manifest
│   │   ├── erc-8004_manifest.json     # ERC-8004 manifest
│   │   └── CHECKSUMS.json             # SHA-256 integrity hashes
│   └── annotated/
│       ├── annotated_records.json      # 5,416 LLM-annotated records
│       └── author_profiles.json        # Per-author institution labels
├── analysis/                           # Derived metrics + CSV exports
│   ├── structural_metrics.csv
│   ├── network_metrics_table.csv
│   ├── network_nodes_*.csv / network_edges_*.csv
│   ├── core_contributors.csv
│   └── cross_case_overlap.csv
├── output/
│   ├── figures/                        # Paper-ready figures (PNG + PDF)
│   ├── stats/                          # JSON stat bundles
│   ├── interactive/                    # vis.js HTML visualizations
│   ├── topic_discovery/                # Thematic-LM + BERTopic outputs
│   ├── network_discourse/              # DNA + socio-semantic outputs
│   └── voting_mechanism_comparison.png
├── paper/                              # LaTeX manuscript + figures
├── tree-root/                          # Project journal (tree-docs)
│   ├── data-collection/                # scraping, filtering, annotation records
│   ├── preliminary-analysis/           # structural metrics records
│   ├── round-b-analysis/               # network, topic, voting mechanism records
│   ├── topic-discovery/                # thematic-LM + BERTopic records
│   ├── network-discourse/              # DNA + socio-semantic records
│   └── paper/                          # draft status + literature table
├── verification/                       # Inter-coder reliability materials
├── human-notes/                        # Manual annotations + draft fragments
├── literature/                         # Reference papers (6 dimensions × 19 papers)
├── pyproject.toml                      # uv project config (Python ≥ 3.14)
└── CLAUDE.md                           # Detailed internal docs for AI assistants
```

---

## Key Findings

1. **Opposite architectures, same structural outcome.** ERC-8004 uses rough consensus with no formal vote; A2A vests binding authority in an 8-seat corporate TSC. Both produce oligarchic participation (Gini 0.804 vs 0.779).

2. **Process overhead asymmetry.** A2A devotes ~2× the share of records to Process arguments (25.4% vs 13.9%, χ²(3)=52.88, p<.001). ERC-8004 shifts to process only when participation collapses mid-lifecycle.

3. **Comparable participation inequality, different elite composition.** Permissionless entry shifts the *identity* of the governing elite (reputation-holders: MetaMask, Hats Protocol, The Graph vs corporate delegates: Google, Microsoft) but not the *magnitude* of concentration.

4. **Discourse specialization.** Both cases show extreme discourse labor division (median actor entropy = 0). ERC-8004 discourse is dominated by Trust & Security (45.5% actor participation rate vs A2A's 10.0%).

5. **Corporate capture of brokerage in A2A.** Betweenness Gini 0.979 (A2A) — 4/5 top brokers are Google employees. ERC-8004's top-5 brokers span 5 different institutions.

Full results: see `output/network_metrics.json`, `output/stats/topic_stats.json`, `analysis/network_metrics_table.csv`.

---

## Data Integrity

`data/raw/CHECKSUMS.json` stores SHA-256 for every raw file. Regenerate after any data update:

```bash
python3 -c "
import json, hashlib
from pathlib import Path
raw = Path('data/raw')
m = {f.name: {'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(raw.glob('*.json')) if f.name != 'CHECKSUMS.json'}
(raw / 'CHECKSUMS.json').write_text(json.dumps(m, indent=2))
"
```

---

## Environment Variables

| Variable | Required For |
|----------|-------------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | A2A scraping (issues, PRs, discussions, GitVote) |
| `MINIMAX_API_KEY` | LLM annotation + Thematic-LM method 1 |
| `ANTHROPIC_API_KEY` | Alternative: LLM annotation with Anthropic backend |
| `OPENAI_API_KEY` | Alternative: LLM annotation with OpenAI-compat backend |
| `OPENAI_BASE_URL` | Custom endpoint for OpenAI-compat backend |

---

## Citation

This repository accompanies the manuscript *"Decentralized Paradox: DAO Governance vs. Corporate Governance in AI Protocol Standardization"* (in preparation). If you use the data or methods, please cite the paper and this repository.
