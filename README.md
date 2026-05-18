# Agentic Analysis for Agentic Infrastructure: An LLM-Powered Pipeline for Comparative Governance of DAO and Corporate AI Protocols

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
MINIMAX_API_KEY=...      # Or any API keys for annotation
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

## Key Findings

1. **Opposite decision architectures.** ERC-8004 advances by rough consensus with permissionless deployment; A2A vests binding authority in an 8-seat corporate TSC (transitioned to Linux Foundation governance in June 2025). Both produce comparable participation inequality (degree Gini 0.804 vs 0.779) and structurally fragmented co-participation networks with no statistically significant core-periphery structure.

2. **Governance form shapes discourse composition.** A2A devotes nearly twice the share to Process arguments (25.4% vs 13.9%, χ²(3)=52.88, p<.001, Cramér's V=.103), reflecting heavier coordination overhead in corporate governance. Within ERC-8004, Process discussion surges to 53% in Phase 3 as deliberation shifts from design to editorial ratification. Topic divergence is moderate but meaningful: JSD=0.288 (BERTopic) and JSD=0.216 (Thematic-LM).

3. **DAO concentrates on trust; corporate governance spreads across engineering execution.** ERC-8004 is dominated by T08 Trust & Security Mechanisms (34.5% of records; 34.5% actor participation rate vs A2A's 4.0%). A2A spreads deliberation across Documentation (T06), Community Contributions (T07), and Protocol Specification (T01), plus three engineering-execution themes (Transport, Streaming, Project Governance) entirely absent from the EIP forum.

4. **Denser discourse congruence in the permissionless setting.** Congruence density is 0.148 (ERC-8004) vs 0.082 (A2A). Within the tighter EIP community, participants more often share positions on contested topics, consistent with groupthink in a small reputation-based elite.

5. **Both elites are small; their composition differs.** Median actor Shannon entropy H=0 in both cases — the majority of contributors engage a single theme. ERC-8004's top-3 degree holders span MetaMask, Hats Protocol, and The Graph; A2A's top-3 include two Google employees and one from Microsoft. Betweenness Gini is 0.931 (ERC-8004) and 0.979 (A2A) in the co-participation network.

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

