# Agentic Analysis for Agentic Infrastructure: An LLM-Powered Pipeline for Comparative Governance of DAO and Corporate AI Protocols

> **🎉 Paper accepted at KDD 2026** (ACM workshop).
>
> **📊 Data:** [See on Hugging Face](https://huggingface.co/datasets/kl41r3/erc8004-vs-a2a-governance) — full raw + annotated dataset, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
>
> **Public computational package:** This repository contains the reproducible code, released data,
> analysis artifacts, and figures. Private person-level investigation notes and reviewer materials
> are intentionally excluded. SHA-256 checksums protect data provenance.

---

## Research Context

**Research Question:** Compared to corporations, how does the governance structure of permissionless DAOs shape participation patterns, discourse composition, and network topology in AI agent protocol standardization?

**Case A — ERC-8004** ("Trustless Agents"): Ethereum Improvement Proposal for permissionless AI agent infrastructure. Governed via EIP rough consensus — open deliberation on the Ethereum Magicians forum and GitHub, with no binding authority structure.

**Case B — Google A2A** (Agent-to-Agent protocol): Corporate-initiated AI agent protocol under Linux Foundation governance with an 8-seat Technical Steering Committee that vests binding decision authority.

The paper reports results at two scopes:

| Pipeline | Scope | Records | Annotators | 
|---|---|---|---|
| **Main-text (R1)** | Single ERC-8004 vs. A2A | Paper reports ERC 142 / A2A 4,181; stored annotation archive has 5,421 rows | MiniMax-M2.5 |
| **Appendix (R2)** | 34-ERC cluster + cross-model + cross-round consensus | Cross-model ERC 1,664 / A2A 4,058; current cross-round ERC 1,664 / A2A 4,187 | 3 models × 3 rounds |

---

## Repository Structure

```
workspace/
├── README.md                       ← This file
├── pyproject.toml                  ← Dependency specification (uv)
├── uv.lock                         ← Locked dependency versions (exact)
├── .env.example                    ← Environment variable template
├── data/
│   ├── README.md                   ← Dataset card + directory map
│   ├── croissant/v1/               ← Croissant 1.1 release with Parquet RecordSets
│   ├── raw/                        ← Original scraped records (R1 + R2 tier1/tier2)
│   │   └── CHECKSUMS.json          ← SHA-256 of all raw data files
│   └── annotated/                  ← LLM annotations + consensus (R1 + R2 cross-model + cross-round)
│       └── CHECKSUMS.json          ← SHA-256 of all annotated data files
├── scripts/
│   ├── scrape/                     ← Data collection (curl-based scrapers)
│   ├── process/                    ← LLM annotation, consensus, enrichment
│   ├── analyse/                    ← Analysis: metrics, topics, networks
│   │   ├── topic_discovery/        ← BERTopic, Thematic-LM, CryptoBERT
│   │   └── network_discourse/      ← DNA, Socio-semantic bipartite
│   ├── visualise/                  ← Figure generation, interactive HTML
│   ├── pipeline/                   ← Full-pipeline orchestrators
│   └── lib/                        ← Shared utilities (paths, models, I/O)
└──analysis/                       ← Analysis outputs (metrics, CSVs, reports)
```

**Key distinction:**

- **Main-text pipeline** (R1) uses `data/raw/` files and `data/annotated/r1/`. Scripts without `_r2` suffix.
- **Appendix pipeline** (R2) uses `data/raw/r2/` and `data/annotated/r2/`. Scripts with `_r2` suffix or in `scripts/pipeline/run_r2.py`.

### Croissant 1.1 Release

The versioned machine-readable release separates the R1 annotation archive, R2 cross-model
consensus, R2 cross-round consensus, and their normalized vote tables. This prevents counts
from different pipeline stages from being interpreted as one mutable corpus.

```bash
uv run python scripts/process/build_croissant_release.py
uvx --from mlcroissant mlcroissant validate --jsonld data/croissant/v1/croissant.json
```

Outputs live in `data/croissant/v1/`. `release_manifest.json` records source hashes, exact
counts, and the R1/R2 alignment policy.

Verify the repository and prepare a data-only Hugging Face staging directory locally:

```bash
uv run python scripts/verify_repository.py
uv run python scripts/publish/prepare_hf_dataset.py --output /private/tmp/rq1-hf-release
```

The staging command does not access the network. It excludes code, paper sources, private
research notes, reviewer materials, and local Agent files.

---

## Part I — Main-Text Pipeline (R1 Baseline)

Reproduce the single-case ERC-8004 vs. A2A comparison from the paper's main body.

### Prerequisites & Environment

**System requirements:**

- **Python ≥ 3.14** (the project depends on Python 3.14+ features)
- **uv** (Python package manager) — [install guide](https://docs.astral.sh/uv/getting-started/installation/)
- **curl** (system command; required for all API scraping)
- **GitHub Personal Access Token** (only for A2A data collection; ERC-8004 data is fully public)
- **MiniMax API key** (for LLM annotation; obtain from https://platform.minimaxi.com)

**Exact dependency versions** (locked in `uv.lock`):

| Package | Version | Purpose |
|---|---|---|
| `anthropic` | 0.84.0 | Optional: Claude API backend |
| `beautifulsoup4` | 4.14.3 | HTML parsing for Discourse scraping |
| `bertopic` | 0.17.4 | BERTopic topic modeling (main-text) |
| `cpnet` | 0.0.21 | Core-periphery network analysis |
| `hdbscan` | 0.8.42 | HDBSCAN clustering (BERTopic dependency) |
| `httpx` | 0.28.1 | HTTP client (GitHub API) |
| `matplotlib` | 3.10.8 | All figure generation |
| `networkx` | 3.6.1 | All network analysis (SNA, DNA, socio-semantic) |
| `openai` | 2.26.0 | OpenAI SDK (used for MiniMax, GLM, DeepSeek, Moonshot) |
| `pandas` | 3.0.1 | Tabular data, metrics, CSV I/O |
| `playwright` | 1.61.0 | Headless browser (A2A Discourse pages) |
| `python-dateutil` | 2.9.0.post0 | Robust date parsing (Pandas 3.0 workaround) |
| `python-dotenv` | 1.2.2 | `.env` file loading |
| `python-louvain` | 0.16 | Louvain community detection |
| `requests` | 2.32.5 | HTTP client (profiles, fallback) |
| `scipy` | 1.17.1 | Statistical tests (χ², Cramér's V, JS divergence) |
| `sentence-transformers` | 5.4.0 | Text embeddings (BERTopic) |
| `umap-learn` | 0.5.12 | Dimensionality reduction (BERTopic) |

**Setup:**

```bash
git clone <this-repo> && cd <this-repo>
uv sync                         # creates .venv with exact locked versions
cp .env.example .env            # edit .env with your API keys
```

Edit `.env`:

```
MINIMAX_API_KEY="sk-cp-..."            # Required: MiniMax-M2.5 for R1 annotation
GITHUB_PERSONAL_ACCESS_TOKEN="github_pat_..."  # Required: A2A data collection (ERC-8004 scrapes without it)
# Optional for alternative annotation backends:
# ANTHROPIC_API_KEY="sk-ant-..."
# OPENAI_API_KEY="sk-..."
# OPENAI_BASE_URL="https://api.openai.com/v1"
```

All scripts are run via `uv run python scripts/...`. The `uv run` prefix ensures the exact locked dependencies are used.

---

### Step 1 — Data Collection (Scraping)

Collect raw governance discussion records from public platforms.

```bash
# === ERC-8004 (no API key needed) ===

# Ethereum Magicians forum posts (Discourse API)
uv run python scripts/scrape/scrape_erc8004_forum.py

# GitHub PR comments (filtered to 9 core lifecycle PRs)
uv run python scripts/scrape/scrape_erc8004_prs.py
# Note: scrape_erc8004_prs.py internally filters to the 9 PRs that directly
# modify ERCS/erc-8004.md or change lifecycle status:
#   #1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488
# Other PRs that merely mention "ERC-8004" are excluded.

# === Google A2A (GitHub token required) ===

# Issues + issue comments
uv run python scripts/scrape/scrape_a2a.py --github-token $GITHUB_PERSONAL_ACCESS_TOKEN

# GitHub Discussions (GraphQL API)
uv run python scripts/scrape/scrape_a2a_discussions.py --github-token $GITHUB_PERSONAL_ACCESS_TOKEN

# GitVote PRs (TSC-voted PRs #831 and #1206)
uv run python scripts/scrape/scrape_gitvote_prs.py --github-token $GITHUB_PERSONAL_ACCESS_TOKEN

# Recover any timed-out pages (idempotent; safe to run multiple times)
uv run python scripts/scrape/patch_a2a_missing_pages.py
```

**Expected output:** ~6,030 raw records in `data/raw/`. After filtering: 4,323 records (ERC-8004: 142; A2A: 4,181).

---

### Step 2 — LLM Annotation

Each governance record is annotated with five structured fields using MiniMax-M2.5, a reasoning model. The annotation is idempotent — safe to interrupt and restart (deduplicates by composite `record_id`).

```bash
# Full annotation with MiniMax-M2.5 (default backend)
uv run python scripts/process/annotate_llm.py --backend minimax

# Test run — first 5 records only
uv run python scripts/process/annotate_llm.py --backend minimax --limit 5

# Alternative backends (optional):
uv run python scripts/process/annotate_llm.py --backend anthropic
uv run python scripts/process/annotate_llm.py --backend openai
```

**Annotation prompt template** (the exact `system` prompt sent to the LLM):

```
You are a governance researcher annotating discussion records from a technology
standardization process. For each record, output ONLY a JSON object with these fields:

{
  "stakeholder_institution": "<one of: Google | Coinbase | MetaMask | Ethereum Foundation | Independent | Unknown>",
  "argument_type": "<one of: Technical | Economic | Governance-Principle | Process | Off-topic>",
  "stance": "<one of: Support | Oppose | Modify | Neutral | Off-topic>",
  "consensus_signal": "<one of: Adopted | Rejected | Pending | N/A>",
  "key_point": "<one sentence summary, ≤20 words>"
}

Rules:
- stakeholder_institution: infer from author handle, text, or any employer clue.
  Default Independent if unclear.
- argument_type: Technical=spec design/implementation; Economic=cost/incentive;
  Governance-Principle=voting/process/rights; Process=procedural; Off-topic=unrelated.
- stance: toward the proposal's adoption as written.
- consensus_signal: Adopted/Rejected only if an explicit editorial decision exists
  (merged, closed). Otherwise Pending or N/A.
- Output ONLY the JSON, no explanation.
```

The `user` message is constructed as:

```
Author: {author_handle}
Date: {record_date}
Platform: {forum | github}
Case: {ERC-8004 | Google-A2A}

Text:
{raw_text[:3000]}
```

MiniMax-M2.5 is a reasoning model — its response contains a `<think>...</think>` block before the JSON output. The script strips this block with regex before parsing.

**Expected output:** `data/annotated/r1/annotated_records.json` (5,421 records, 99.9% annotation rate).

---

### Step 3 — Structural Metrics & Governance Comparison

```bash
# Core governance metrics (participation, decision, temporal)
uv run python scripts/analyse/compute_metrics.py

# Chi-square / Cramér's V for argument type and stance distributions
uv run python scripts/analyse/analyze_topic.py

# Decision mechanism comparison (ERC rough consensus vs. A2A TSC voting)
uv run python scripts/analyse/analyze_voting_mechanism.py
```

**Expected outputs:** `analysis/metrics/r1/structural_metrics.csv`, `output/figures/topic_*.png`, `output/figures/voting_mechanism_comparison.png`.

---

### Step 4 — Topic Discovery

Two complementary unsupervised methods for discovering emergent themes from raw governance text.

#### Method 1: Thematic-LM (multi-agent LLM thematic analysis)

A 4-stage multi-agent pipeline: (1) open-ended thematic coding with MiniMax-M2.5, (2) codebook consolidation via merge + dedup, (3) closed coding (assign themes to all records), (4) cross-model validation.

```bash
# Requires MiniMax API key
uv run python scripts/analyse/topic_discovery/thematic_lm/run.py --backend minimax
```

**Expected output:** 19-theme codebook (`analysis/topic_discovery/r1/thematic_lm/themes.json`), per-record theme assignments, Jensen-Shannon divergence tables.

#### Method 2: Comparative Discourse (BERTopic + JS divergence)

Fully unsupervised — no API key needed. Uses BERTopic (all-MiniLM-L6-v2 embeddings + HDBSCAN clustering) to discover topics separately for ERC-8004 and A2A, then computes Jensen-Shannon divergence between the two topic distributions.

```bash
# No API key needed
uv run python scripts/analyse/topic_discovery/comparative_discourse/run.py

# CryptoBERT validation (ERC-8004 only, domain-specific transformer)
uv run python scripts/analyse/topic_discovery/crypto_bert/run.py
```

**Expected outputs:** `analysis/topic_discovery/r1/comparative_discourse/{divergence_table.csv,topics_per_case.json,topic_comparison.png}` and `analysis/topic_discovery/r1/crypto_bert/{topics.json,comparison_summary.md}`. Paper-ready figures are generated later by `build_paper_figures.py`.

---

### Step 5 — Network Analysis

Three complementary network methods examine the relational structure of governance participation.

#### Method 1: Structural Network Analysis (SNA)

Co-participation networks where nodes are authors and weighted edges count shared discussion threads. Computes 13 metrics: degree/betweenness Gini, graph centralization ratio (GCR), density, average clustering, modularity, core-periphery structure (CP-Score), and more.

```bash
uv run python scripts/analyse/analyze_network.py
uv run python scripts/visualise/build_network.py
```

**Expected outputs:** `analysis/metrics/r1/network_metrics_table.csv`, `output/figures/network_sna_comparison.png` (side-by-side network visualization), `output/figures/network_degree_dist.png` (degree distribution by rank), `output/interactive/network_erc8004.html` and `network_a2a.html` (vis.js interactive graphs).

#### Method 2: Discourse Network Analysis (DNA)

Congruence/conflict networks where nodes are still authors but edges are weighted by agreement or disagreement on specific themes. Combines Thematic-LM topic assignments with LLM stance labels.

```bash
uv run python scripts/analyse/network_discourse/dna/run.py
```

**Expected outputs:** `analysis/network_discourse/r1/dna/{congruence_erc8004.csv,congruence_googlea2a.csv,conflict_erc8004.csv,conflict_googlea2a.csv,dna_metrics.json,dna_comparison.png}`.

#### Method 3: Socio-semantic Bipartite Network

Actor × Theme bipartite network where edges connect authors to the themes they discuss. Measures actor specialization (Shannon entropy H over themes), theme concentration, and network bipartivity.

```bash
uv run python scripts/analyse/network_discourse/sociosemantic/run.py
```

**Expected outputs:** `analysis/network_discourse/r1/sociosemantic/{ss_metrics.json,specialization_compare.png,theme_actor_comparison.png}` plus the actor and theme CSV tables in the same directory.

---

### Step 6 — Stakeholder Enrichment

Enrich author profiles with institutional affiliations from Discourse bios, GitHub profiles, and manual investigation.

```bash
uv run python scripts/process/enrich_profiles.py          # fetch Discourse + GitHub profiles
uv run python scripts/process/extract_manual_institutions.py --input /path/to/private-report.md
uv run python scripts/process/enrich_institutions.py       # merge profiles → author_profiles.json
uv run python scripts/analyse/identify_core_contributors.py  # core contributor analysis
```

The person-level investigation report is private research material and is not distributed.
The extractor requires an explicit `--input` path and never searches local note directories.

**Expected outputs:** `data/annotated/r1/author_profiles.json`, `analysis/metrics/r1/core_contributors.csv`, `analysis/metrics/r1/cross_case_overlap.csv`, `output/interactive/network_erc8004.html` (updated with institution metadata).

---

### Step 7 — Verification (Inter-Coder Reliability)

```bash
# Generate N=50 stratified verification sample
uv run python scripts/analyse/sample_for_verification.py
# The coding guide and completed person-level coding notes are private research materials.
# After an authorized manual coding file has been supplied locally:
uv run python scripts/analyse/validate_multimodel.py --dataset erc
```

The public repository can regenerate the sample but does not distribute private coding notes.
Consequently, the human-coding step is not fully reproducible from GitHub alone. The released
multi-model validation reports remain available under `data/annotated/r2/cross-model/`.

---

### Main-Text Pipeline Summary

| Step | Script(s) | Output | API needed |
|---|---|---|---|
| 1. Data collection | `scrape/*.py` | `data/raw/*.json` | GitHub PAT (A2A only) |
| 2. LLM annotation | `process/annotate_llm.py` | `data/annotated/r1/annotated_records.json` | MiniMax |
| 3. Structural metrics | `analyse/compute_metrics.py`, `analyze_topic.py`, `analyze_voting_mechanism.py` | `analysis/metrics/r1/*.csv` | None |
| 4. Topic discovery | `analyse/topic_discovery/thematic_lm/run.py`, `comparative_discourse/run.py`, `crypto_bert/run.py` | `analysis/topic_discovery/r1/` | MiniMax (Thematic-LM only) |
| 5. Network analysis | `analyse/analyze_network.py`, `network_discourse/dna/run.py`, `network_discourse/sociosemantic/run.py` | `analysis/metrics/r1/`, `analysis/network_discourse/r1/` | None |
| 6. Stakeholder enrichment | `process/enrich_profiles.py`, `enrich_institutions.py`, `analyse/identify_core_contributors.py` | `data/annotated/r1/author_profiles.json` | GitHub PAT |
| 7. Verification | `analyse/sample_for_verification.py`, `validate_multimodel.py` | κ report | None |

---

## Part II — Appendix Pipeline (R2 Multi-Model Robustness)

The appendix reports a multi-model × multi-round robustness check that re-annotates an expanded 34-ERC cluster with three independent LLM vendors (DeepSeek-V4-Flash, GLM-4-Plus, Moonshot-v1-auto), then measures both cross-model agreement (Fleiss' κ) and test-retest self-consistency (3 rounds per model). The appendix also replicates all network analyses at this expanded scope.

### Additional Environment Variables

```
DEEPSEEK_API_KEY="sk-..."     # DeepSeek API (https://platform.deepseek.com)
GLM_API_KEY="..."             # Zhipu GLM API (https://open.bigmodel.cn)
KIMI_API_KEY="sk-..."         # Moonshot/Kimi API (https://platform.moonshot.cn)
```

---

### Step A1 — R2 Data Collection (34-ERC Cluster)

Expand the ERC case from a single standard to a 34-standard cluster, re-scraping both forum (Ethereum Magicians) and GitHub (ethereum/ERCs) data.

```bash
# Tier 1: re-scrape ERC-8004 with broader query (forum + GitHub)
uv run python scripts/scrape/scrape_r2_forum.py
uv run python scripts/scrape/scrape_r2_github.py

# Tier 2: scrape 34-ERC cluster (forum + GitHub)
uv run python scripts/scrape/scrape_r2_forum.py --tier tier2
uv run python scripts/scrape/scrape_r2_github.py --tier tier2

# Recover any timed-out pages
uv run python scripts/scrape/patch_r2_tier2_github.py
```

**Expected output:** `data/raw/r2/tier1/` (ERC-8004 expanded, ~803 KB forum + 23 KB GitHub) and `data/raw/r2/tier2/` (34-ERC cluster, ~2.8 MB forum + 502 KB GitHub).

---

### Step A2 — Cross-Model Annotation (3 Models × 2 Cases)

Each of three independent LLM vendors annotates the full expanded corpus using the **same 5-field prompt** as the main-text pipeline (see Step 2 above). Temperature is set to 0.0 for all models.

```bash
# ERC annotations (1,664 records from 34 standards)
uv run python scripts/process/annotate_r2.py --model deepseek
uv run python scripts/process/annotate_r2.py --model glm
uv run python scripts/process/annotate_r2.py --model kimi

# A2A annotations (4,059 records)
uv run python scripts/process/annotate_a2a_r2.py --model deepseek
uv run python scripts/process/annotate_a2a_r2.py --model glm
uv run python scripts/process/annotate_a2a_r2.py --model kimi

# If DeepSeek A2A annotation times out, resume with:
uv run python scripts/process/complete_a2a_deepseek.py
```

Model-to-vendor mapping (`scripts/lib/models.py`):

| CLI argument | Canonical model ID | Vendor | API endpoint |
|---|---|---|---|
| `--model deepseek` | `deepseek-v4-flash` | DeepSeek | `https://api.deepseek.com/v1` |
| `--model glm` | `glm-4-plus` | Zhipu | `https://open.bigmodel.cn/api/paas/v4` |
| `--model kimi` | `moonshot-v1-auto` | Moonshot | `https://api.moonshot.cn/v1` |

**Annotation prompt** — identical to the main-text prompt (Step 2), with temperature=0.0 and max_tokens=1024 for reproducible outputs. See `scripts/process/annotate_r2.py:46` for the exact system prompt.

---

### Step A3 — Cross-Round Test-Retest (3 Models × 3 Rounds)

Each model annotates the same records three times independently to measure self-consistency (Fleiss' κ across rounds). Uses a reduced 3-field schema (`argument_type`, `stance`, `consensus_signal` only) with lower max_tokens.

```bash
# Run all 3 rounds for all 3 models (9 annotation jobs total)
uv run python scripts/process/annotate_r3.py --model deepseek-v4-flash --round 1
uv run python scripts/process/annotate_r3.py --model deepseek-v4-flash --round 2
uv run python scripts/process/annotate_r3.py --model deepseek-v4-flash --round 3
# ... repeat for glm-4-plus and moonshot-v1-auto
```

---

### Step A4 — Build Consensus

Majority-vote consensus (2 of 3 models agree) across the three independent annotations:

```bash
uv run python scripts/process/build_consensus.py
uv run python scripts/process/build_r3_consensus.py
```

**Expected outputs:**
- `data/annotated/r2/cross-model/consensus/erc_annotations.json` (1,664 records)
- `data/annotated/r2/cross-model/consensus/a2a_annotations.json` (4,058 records)
- `data/annotated/r2/cross-round/erc_cross_consensus.json`
- `data/annotated/r2/cross-round/a2a_cross_consensus.json`

---

### Step A5 — Appendix Analysis (Full Pipeline)

The appendix replicates all analyses (structural metrics, BERTopic, Thematic-LM, SNA, DNA, socio-semantic) on the expanded consensus data. All scripts use the `_r2` suffix:

```bash
# Individual scripts:
uv run python scripts/analyse/compute_metrics_r2.py           # governance metrics
uv run python scripts/analyse/topic_discovery/comparative_discourse/run_r2.py  # BERTopic
uv run python scripts/analyse/topic_discovery/thematic_lm/run_r2.py           # Thematic-LM
uv run python scripts/analyse/build_network_r2.py             # SNA co-participation
uv run python scripts/analyse/network_discourse/dna/run_r2.py          # DNA
uv run python scripts/analyse/network_discourse/sociosemantic/run_r2.py  # Socio-semantic
uv run python scripts/analyse/validate_multimodel.py --dataset a2a  # ICR
uv run python scripts/visualise/build_paper_figures_r2.py     # appendix figures

# Or run the entire pipeline sequentially:
uv run python scripts/pipeline/run_r2.py
# Options:
#   --from-phase N    resume from phase N (1-10)
#   --skip-thematic   skip A2A thematic open-coding (Phase 5)
#   --skip-figures    skip final figure generation (Phase 10)
```

The R2 pipeline has 10 phases: (1) A2A ICR validation, (2) consensus building, (3) structural metrics, (4) BERTopic, (5) A2A thematic open-coding, (6) Thematic-LM, (7) SNA, (8) DNA, (9) socio-semantic, (10) paper figures.

---

### Appendix Pipeline Summary

| Step | Script(s) | Output | API needed |
|---|---|---|---|
| A1. Data expansion | `scrape/scrape_r2_*.py` | `data/raw/r2/tier1/`, `tier2/` | GitHub PAT |
| A2. Cross-model annotation | `process/annotate_r2.py`, `annotate_a2a_r2.py` | `data/annotated/r2/cross-model/` | DeepSeek + GLM + Kimi |
| A3. Cross-round test-retest | `process/annotate_r3.py` | `data/annotated/r2/cross-round/` | DeepSeek + GLM + Kimi |
| A4. Consensus | `process/build_consensus.py`, `build_r3_consensus.py` | Consensus JSON files | None |
| A5. Extended analysis | `pipeline/run_r2.py` (or individual `*_r2.py` scripts) | `analysis/metrics/r2/`, `analysis/topic_discovery/r2/`, `analysis/network_discourse/r2/` | MiniMax (Thematic-LM) |

---

## Robustness Results (from the Paper Appendix)

| Experiment | Models | Rounds | Records | Key result |
|---|---|---|---|---|
| Cross-model (R2) | 3 vendors | 1 | ERC 1,664 / A2A 4,045 | argument_type Fleiss' κ = 0.683 (ERC Substantial) / 0.619 (A2A Substantial) |
| Cross-round | 3 models | 3 | Paper snapshot: ERC 1,664 / A2A 3,844; current artifact: ERC 1,664 / A2A 4,187 | GLM-4-Plus κ = 0.86–0.93 (most stable); DeepSeek κ = 0.49–0.63 |
| 4-model (R1 + cross-round) | +MiniMax-M2.5 | 1 | Paper snapshot: ERC 144 / A2A 3,844 | 4-way Fleiss' κ ≈ 0.46–0.51 (Moderate); model choice dominates stochastic noise |

**What replicates** (3 of 4 findings): (i) discourse remains technically dominated across models; (ii) participation inequality persists (Gini ≈ 0.8); (iii) DAO attains denser within-community consensus.

**What reverses** (1 of 4): network connectivity ranking inverts at ecosystem scale — the permissionless DAO becomes the *more* connected and observable regime (GCR 0.917 vs. A2A 0.285), because corporate coordination moves off the public record.

---

## Data Integrity

All data files are protected by SHA-256 checksums. The checksum manifests are:

| Manifest | Coverage |
|---|---|
| `data/raw/CHECKSUMS.json` | All R1 raw data (15 files) + R2 tier1/tier2 (4 + 4 files) |
| `data/annotated/CHECKSUMS.json` | All annotated data: R1 (2 files), R2 cross-model (25 files), R2 cross-round (23 files) |
| `data/annotated/r2/cross-model/CHECKSUMS.json` | Per-directory checksums for R2 cross-model |
| `data/annotated/r2/cross-round/CHECKSUMS.json` | Per-directory checksums for R2 cross-round |

### Raw Data SHA-256 (Main-Text Pipeline)

```
forum_posts.json                b414e8b7153df6d89a2885a702f72ed5ead1cfa21cdb6b455ae86677cad3e66d
github_comments_filtered.json   41a65aa867db3e6441024854604ba951e3987e0776c32b02a84027ef2a28c8ba
a2a_commits.json                d80a78d2f79443cdff863d8400895371fc9e6a988ae312a2ac4c09e315d67a35
a2a_issues.json                 e48ebc63933380b4a68c42ea30c98168e64710640b269849d9066eeadf79cbbb
a2a_prs.json                    a7043491cc4ace44bc01eb0fbe681e659c284765493d046e7a22adc942a67747
a2a_discussions.json            1f060770b539c79761b6d12d929db4d996536398b9da9c31124f861897730049
a2a_gitvote_prs.json            2a8177162d53d048502e42a451ae82d8daac1e888d0a336be989c028cab349b1
```

### Raw Data SHA-256 (Appendix Pipeline — R2 Expansion)

```
r2/tier1/erc8004_forum.json     434c79afd82418185b1f09cc2e22e8ed46f3ea08f83ac5bb0e29db7f42aba626
r2/tier1/erc8004_github.json    a64406b0f9ddc198e453dc2cf39ef75c860e733962d78e7292d545195111f09b
r2/tier2/cluster_forum.json     fec74d15db5932d058a23be9e9444200959352487e1f5934e27d633c2d8d9639
r2/tier2/cluster_github.json    c8b9dd19352dc3c595f1d6c6c09b7030ada95476106a6ef3879f2cb4fb66f390
```

Full manifest: `data/raw/CHECKSUMS.json`. Regenerate after any data update:

```bash
python3 -c "
import json, hashlib
from pathlib import Path
raw = Path('data/raw')
m = {str(f.relative_to(raw)): {'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
     for f in sorted(raw.rglob('*.json')) if f.name != 'CHECKSUMS.json'}
(raw / 'CHECKSUMS.json').write_text(json.dumps(m, indent=2, ensure_ascii=False))
"
```

---

## Key Findings

1. **Participation is oligarchic across both governance forms, despite opposite decision architectures.** ERC-8004 advances by rough consensus with permissionless deployment; A2A vests binding authority in an 8-seat corporate TSC (transitioned to Linux Foundation governance in June 2025). Yet both produce comparable participation inequality (degree Gini 0.804 vs 0.779; betweenness Gini 0.931 vs 0.979), and the majority of contributors in both cases engage only a single theme (median actor Shannon entropy H=0). ERC-8004's top-3 degree holders span MetaMask, Hats Protocol, and The Graph; A2A's top-3 include two Google employees and one from Microsoft.

2. **Discourse is technically dominated in both cases, but governance form shapes composition.** A2A devotes nearly twice the share to Process arguments (25.4% vs 13.9%, χ²(3)=52.88, p<.001, Cramér's V=.103), reflecting heavier coordination overhead in corporate governance. Within ERC-8004, Process discussion surges to 53% in Phase 3 as deliberation shifts from design to editorial ratification. Topic divergence is moderate but meaningful: JSD=0.288 (BERTopic) and JSD=0.216 (Thematic-LM).

3. **DAO concentrates on trust; corporate governance spreads across engineering execution.** ERC-8004 is dominated by T08 Trust & Security Mechanisms (34.5% of records; 34.5% actor participation rate vs A2A's 4.0%). A2A spreads deliberation across Documentation (T06), Community Contributions (T07), and Protocol Specification (T01), plus three engineering-execution themes (Transport, Streaming, Project Governance) entirely absent from the EIP forum.

4. **Network connectivity reverses with scope.** At single-case level, the DAO attains denser discourse congruence (0.148 vs 0.082, congruence density), consistent with groupthink in a small reputation-based elite. However, expanding to a 34-ERC agent cluster overturns this finding: the DAO network coalesces at ecosystem scale (GCR 0.328 → 0.917), while the re-annotated A2A network remains fragmented (GCR 0.534 → 0.285). The permissionless DAO is the *more* connected and observable regime at ecosystem scale — coordination in the corporate case moves off the public record. See paper Appendix "Multi-Model and Multi-Round Robustness Check."

Full results: `analysis/metrics/r1/network_metrics_table.csv`, `analysis/topic_discovery/r1/`, `analysis/network_discourse/r1/`.

---

## Implementation Notes

**curl over requests:** Python 3.14's `requests` has SSL EOF errors against `ethereum-magicians.org`. All Discourse scraping uses `subprocess` + system `curl`.

**Discourse pagination:** Must use numeric topic ID only — `/t/25098/posts.json?post_ids[]=...`. The slug+ID form returns HTTP 404.

**Pandas 3.0 date parsing:** `pd.to_datetime(utc=True)` infers format from row 0 and coerces mismatches to NaT. All date parsing uses `python-dateutil.parser.parse()` per-record instead.

**MiniMax-M2.5 reasoning block:** The model wraps its JSON output in `<think>...</think>` tags. The annotation script strips these with regex before parsing.

**Annotation resume:** All annotation scripts deduplicate by a composite `record_id` (case + source + id + date). Safe to Ctrl+C and restart — already-annotated records are skipped.

**Bot exclusion:** Known bot accounts (github-actions[bot], eip-review-bot, dependabot[bot], etc.) are filtered out before annotation. See `scripts/lib/models.py:BOTS`.

---

## License

**Code:** MIT License.

**Data:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — attribution required, non-commercial use only. To be hosted on Hugging Face.
