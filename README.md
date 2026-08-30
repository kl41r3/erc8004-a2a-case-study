# Agentic Analysis for Agentic Infrastructure: An LLM-Powered Pipeline for Comparative Governance of DAO and Corporate AI Protocols

> **🎉 Paper accepted at KDD 2026** (ACM workshop) — original v1.0 release.
>
> **📊 v1.1.0:** five non-visual robustness tables and an extended release verifier
> are included in `analysis/metrics/neurips26/` and `scripts/verify_neurips26.py`.
>
> **📦 Archive:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21830235.svg)](https://doi.org/10.5281/zenodo.21830235) (Zenodo, all versions)
>
> **📊 Data:** [See on Hugging Face](https://huggingface.co/datasets/kl41r3/erc8004-vs-a2a-governance) — full raw + annotated dataset, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
>
> **Public computational package:** GitHub contains the reproducible code, metadata, analysis
> artifacts, and figures. Dataset payloads are hosted only on Hugging Face and are downloaded from
> a pinned revision. Private person-level investigation notes and reviewer materials are excluded.

---

## Release versions

| Version | Contents |
|---|---|
| **v1.0** (KDD 2026 workshop, accepted) | R1 pairwise pipeline, R2 34-ERC cluster expansion, Croissant 1.1 release |
| **v1.1.0** (this release) | Everything in v1.0, plus five non-visual robustness tables (`analysis/metrics/neurips26/`), the equal-size bootstrap and tie-threshold robustness script, and the extended release verifier (`scripts/verify_neurips26.py`) |

Both versions share the same frozen R1/R2 data. v1.1.0 is a backward-compatible
addition: no v1.0 file, checksum, or Hugging Face payload is modified.

This release deliberately distributes **no manuscript**: the NeurIPS 2026 paper that
these robustness tables accompany is under anonymous review and will be published
separately after the review period.

### Scope boundary of v1.1.0

The nine-protocol (R3) analysis layer — its 7,458-record corpus, per-protocol topic fits,
and governance-index construct checks — remains in the private research tree and is **not**
part of this repository or the Hugging Face dataset. The pairwise study, the ERC-cluster
expansion, and the robustness tables **are** reproducible
from this repository. No human gold-standard validation of the LLM labels exists; none
is claimed, and no validation worksheet is distributed.

---

## Research Context

**Research Question:** Compared to corporations, how does the governance structure of permissionless DAOs shape participation patterns, discourse composition, and network topology in AI agent protocol standardization?

**Case A — ERC-8004** ("Trustless Agents"): Ethereum Improvement Proposal for permissionless AI agent infrastructure. Governed via EIP rough consensus — open deliberation on the Ethereum Magicians forum and GitHub, with no binding authority structure.

**Case B — Google A2A** (Agent-to-Agent protocol): Corporate-initiated AI agent protocol under Linux Foundation governance with an 8-seat Technical Steering Committee that vests binding decision authority.

The pipeline reports results at two scopes:

| Pipeline | Scope | Records | Annotators |
|---|---|---|---|
| **Main-text (R1)** | Single ERC-8004 vs. A2A | Paper reports ERC 142 / A2A 4,181; stored annotation archive has 5,421 rows | MiniMax-M2.5 |
| **Appendix (R2)** | 34-ERC cluster + cross-model + cross-round consensus | Cross-model ERC 1,664 / A2A 4,058; current cross-round ERC 1,664 / A2A 4,187 | 3 models × 3 rounds |

The v1.1.0 robustness layer extends this design toward a nine-protocol comparison
(A2A, ACP, AP2, ERC-8004, ERC-8183, MCP, MPP, UCP, x402); that R3 layer is pending
public release (see the scope boundary above).

---

## Repository Structure

```
workspace/
├── README.md                       ← This file
├── Makefile                        ← verify / manifest / robustness / reproduce / all
├── ASSET_LICENSES.md               ← Asset and data ledger
├── CITATION.cff / .zenodo.json     ← Citation and archival metadata
├── analysis/
│   ├── metrics/r1/                 ← R1 network tables (tracked)
│   ├── metrics/r2/                 ← R2 network tables (tracked)
│   └── metrics/neurips26/          ← Five robustness tables + summary.json (tracked)
├── scripts/
│   ├── verify_repository.py        ← v1.0 repository verifier
│   ├── verify_neurips26.py         ← v1.1.0 robustness-release verifier
│   ├── reproduce_release.py        ← Exact R1/R2 reproduction entry point
│   ├── analyse/run_neurips26_robustness.py  ← Regenerates the five robustness tables
│   ├── scrape/                     ← Data collection (curl-based scrapers)
│   ├── process/                    ← LLM annotation, consensus, enrichment
│   ├── analyse/                    ← Analysis: metrics, topics, networks
│   └── visualise/                  ← Figure generation, interactive HTML
└── data/
    ├── README.md                   ← Dataset card and Hugging Face pointer
    └── croissant/                  ← Tracked metadata, checksums, and validator evidence
```

**Key distinction:**

- **Main-text pipeline** (R1) uses `data/raw/` files and `data/annotated/r1/`. Scripts without `_r2` suffix.
- **Appendix pipeline** (R2) uses `data/raw/r2/` and `data/annotated/r2/`. Scripts with `_r2` suffix or in `scripts/pipeline/run_r2.py`.
- **v1.1.0 robustness layer** uses the frozen R1 manifest via `scripts/analyse/run_neurips26_robustness.py` and writes `analysis/metrics/neurips26/`.

### Reproducibility Contract

The repository supports two different operations that should not be conflated:

1. **Exact release reproduction**, using R1 and R2 payloads downloaded from the immutable
   Hugging Face revision pinned in `scripts/publish/download_hf_dataset.py`. This path requires
   no API keys and reconstructs the 4,323-row R1 paper manifest and Croissant release before
   validating checksums, row counts, RecordSet counts, and the GitHub distribution boundary.
   The v1.1.0 robustness tables, network tables, and model-reliability values are additionally
   checked by `scripts/verify_neurips26.py`.
2. **Provenance reruns**, using live source APIs and hosted LLMs. These commands document
   how the archived artifacts were produced, but upstream content and hosted model behavior
   can change. A later live rerun is therefore not expected to be byte-identical to the
   frozen release.

**One shortest command for the exact path** (from a fresh clone):

```bash
git clone https://github.com/kl41r3/erc8004-a2a-case-study.git
cd erc8004-a2a-case-study
uv sync --frozen
make reproduce
```

No `.env` file or paid service is required for this command. A successful run ends with
`Exact R1/R2 release reproduction passed.` The expected R1 manifest SHA-256 is
`0445428da7b67f6c7a62b5bb83014dccdd92433fc8e66819f55d4839e5ec92cb`.

**Component commands** (all runnable independently):

| Command | What it does | Needs API key |
|---|---|---|
| `make verify` | Runs `verify_repository.py` + `verify_neurips26.py` (code, tables, metadata, boundary) | No |
| `make reproduce` | Downloads the pinned Hugging Face payloads, rebuilds the manifest and Croissant release, verifies everything | No |
| `make manifest` | Rebuilds the frozen 4,323-row R1 paper manifest from the downloaded raw payloads | No |
| `make robustness` | Regenerates the five NeurIPS robustness tables (seed 20260826, 2,000 bootstrap repetitions) | No |
| `make all` | manifest + robustness + verify | No |

To download the data without rebuilding the release:

```bash
uv run python scripts/publish/download_hf_dataset.py
uv run python scripts/verify_repository.py --with-data
```

The downloader is pinned to Hugging Face commit
[`987913bacae1a169bb39587b22dd002f74293177`](https://huggingface.co/datasets/kl41r3/erc8004-vs-a2a-governance/commit/987913bacae1a169bb39587b22dd002f74293177).
Downloaded payloads are ignored by Git and are never recommitted to this repository.

### Resource requirements

The exact reproduction path was validated on a 10-core Apple M4 with 32 GB RAM running
macOS 26.6.2, Python 3.14, and `uv` 0.12.6. Measured wall-clock times on that machine:
`make verify` ≈ 4 s, `make reproduce` ≈ 19 s (including the Hugging Face download),
and `make robustness` ≈ 1 s; allow extra time for the initial dependency download (the
installed environment is ≈ 1.2 GB). Expect roughly 2 GB of free disk space for the cloned
repository, the virtual environment, and the downloaded Hugging Face payloads. No GPU and
no paid model calls are needed for the exact path. The historical hosted-annotation run
consumed 1,161,411 prompt tokens and 205,688 completion tokens; a live rerun requires the
corresponding API keys and is not expected to be byte-identical.

### Validity limits

The released artifact is observational and descriptive. Cross-model reliability is moderate
(Fleiss' κ 0.545–0.541 for argument type) and is **not** a human gold-standard validation:
no human audit of the LLM labels exists, no label accuracy, F1, or human–model agreement
is claimed, and no validation worksheet is distributed. Equal-size bootstrap intervals
quantify record-resampling uncertainty only; they do not balance case maturity, platform
affordances, or organizational resources. Network edges encode platform-specific
affordances and are not a harmonized edge definition. The analyses separate formal
authority, observed influence, and public observability, and claim no causal effect of
governance form.

---

## The NeurIPS 2026 robustness tables (v1.1.0)

`analysis/metrics/neurips26/` holds the five non-visual robustness outputs behind the
NeurIPS 2026 study — corpus-stage counts (6 rows), equal-size bootstrap intervals
(5 rows), channel composition (27 rows), quarterly composition (36 rows), and
network tie-threshold sensitivity (8 rows).

```bash
make robustness   # deterministic: seed 20260826, 2,000 bootstrap repetitions
make verify       # integrity checks over the release
```

`scripts/verify_neurips26.py` checks the robustness tables, the R1/R2 network tables,
the four-model reliability values, repository metadata, and the public distribution
boundary (including that no manuscript file is tracked in this release).

### Croissant 1.1 Release

The versioned machine-readable release separates the R1 annotation archive, R2 cross-model
consensus, R2 cross-round consensus, and their normalized vote tables. This prevents counts
from different pipeline stages from being interpreted as one mutable corpus.

```bash
uv run python scripts/publish/download_hf_dataset.py
uv run python scripts/process/build_croissant_release.py
uvx --from mlcroissant mlcroissant validate --jsonld data/croissant/v1/croissant.json
```

GitHub retains `croissant.json`, `SCHEMA.md`, `release_manifest.json`, `CHECKSUMS.json`, and
the validator screenshot. The five Parquet payloads are hosted on Hugging Face and appear
locally only after the download command.

### GitHub Education assisted publication workflow

The dataset publication workflow used GitHub Codespaces and GitHub Copilot through GitHub
Education benefits. Codespaces provided a reproducible cloud development environment for
running the repository's locked `uv` workflow, while Copilot assisted with mechanical
refactoring and documentation. All substantive schema choices, count reconciliation, and
interpretation boundaries were reviewed against the source artifacts and verified by the
repository checks.

The publication process reformats heterogeneous JSON artifacts into five homogeneous Parquet
tables before publishing them to Hugging Face. GitHub does not track raw, annotated, manifest,
or Parquet payloads. It retains the code, the immutable Hugging Face pointer, Croissant metadata,
checksums, and validation evidence. Hugging Face exposes each Parquet table as a separate Dataset
Viewer config so incompatible R1, cross-model, and cross-round scopes are not silently merged.

The checked metadata file is [`data/croissant/v1/croissant.json`](data/croissant/v1/croissant.json).
The NeurIPS Croissant Validator evidence is stored at
[`data/croissant/neurips-croissant-validator-pass.png`](data/croissant/neurips-croissant-validator-pass.png).

Verify the code-only GitHub release, or download and verify the full data release:

```bash
uv run python scripts/verify_repository.py
uv run python scripts/publish/download_hf_dataset.py
uv run python scripts/verify_repository.py --with-data
```

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
uv sync --frozen                # creates .venv from the committed lockfile
cp .env.example .env            # only needed for live scraping or LLM reruns
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

The pinned Hugging Face download provides the frozen raw records used by the release. The
following commands are provenance reruns against live public platforms and may collect newer content.

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

The archived March 2026 release contains 6,030 raw R1 records. To reconstruct the exact
paper membership from the committed frozen inputs, run:

```bash
uv run python scripts/process/build_r1_paper_manifest.py
```

The builder accepts only the five byte-identical March 2026 input files recorded in its
versioned SHA-256 allowlist. It deterministically retains 4,323 records (ERC-8004: 142;
A2A: 4,181) and writes `data/manifests/r1_paper_v1.jsonl` plus an audit summary.

---

### Step 2 — LLM Annotation

Each governance record was annotated with five structured fields using MiniMax-M2.5, a reasoning model. The annotation is idempotent — safe to interrupt and restart (deduplicates by composite `record_id`). Hosted LLM output is not guaranteed to remain byte-identical across service revisions, so exact reproduction uses the committed annotation artifacts and checksums.

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
uv run python scripts/process/enrich_profiles.py           # live provenance rerun
uv run python scripts/process/enrich_institutions.py       # uses committed manual_institutions.json
uv run python scripts/analyse/identify_core_contributors.py  # core contributor analysis
```

The exact release includes the structured audit artifact `data/raw/manual_institutions.json`
and its checksum. The longer person-level investigation notes are private research material
and are not required to reconstruct the released outputs. For provenance work on a replacement
audit, `scripts/process/extract_manual_institutions.py --input <report.md>` accepts an explicit
authorized source and never searches local note directories.

**Expected outputs:** `data/annotated/r1/author_profiles.json`, `analysis/metrics/r1/core_contributors.csv`, `analysis/metrics/r1/cross_case_overlap.csv`, `output/interactive/network_erc8004.html` (updated with institution metadata).

---

### Step 7 — Multi-Model Verification

```bash
uv run python scripts/analyse/validate_multimodel.py --dataset erc
uv run python scripts/analyse/validate_multimodel.py --dataset a2a
```

These commands reproduce the public cross-model agreement reports and deterministic stratified
verification samples under `data/annotated/r2/cross-model/`. Blank human-coding columns are an
optional extension and are not used in the released R1 or R2 findings.

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
| 7. Verification | `analyse/validate_multimodel.py` | κ reports and stratified samples | None |

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
uv run python scripts/process/annotate_r3.py --case erc --model deepseek-v4-flash --round 1
uv run python scripts/process/annotate_r3.py --case erc --model deepseek-v4-flash --round 2
uv run python scripts/process/annotate_r3.py --case erc --model deepseek-v4-flash --round 3
# Repeat for --case a2a and for glm-4-plus and moonshot-v1-auto.
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
| Cross-model (R2) | 3 vendors | 1 | Current artifact: ERC 1,664 / A2A 4,058 | argument_type Fleiss' κ = 0.683 (ERC Substantial) / 0.619 (A2A Substantial) |
| Cross-round | 3 models | 3 | Paper snapshot: ERC 1,664 / A2A 3,844; current artifact: ERC 1,664 / A2A 4,187 | GLM-4-Plus κ = 0.86–0.93 (most stable); DeepSeek κ = 0.49–0.63 |
| 4-model (R1 + cross-round) | +MiniMax-M2.5 | 1 | Paper snapshot: ERC 144 / A2A 3,844 | 4-way Fleiss' κ ≈ 0.46–0.51 (Moderate); model choice dominates stochastic noise |
| Equal-size bootstrap (v1.1.0) | — | 2,000 reps | Pairwise: 142 vs 142 per draw | Every 95% interval for the principal argument-type differences includes zero |

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

The exact R1 paper subset is separately frozen in
`data/manifests/r1_paper_v1.jsonl`. Its summary records the five input hashes, historical
filter policy, source-row locators, per-row content hashes, and manifest hash. Run
`uv run python scripts/process/build_r1_paper_manifest.py` to reproduce it and
`uv run python scripts/verify_repository.py` to validate every row locator.

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
uv run python -c "
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

**Data:** [Hugging Face dataset](https://huggingface.co/datasets/kl41r3/erc8004-vs-a2a-governance), released under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
