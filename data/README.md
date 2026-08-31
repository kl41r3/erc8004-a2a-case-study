---
license: cc-by-nc-4.0
language:
- en
pretty_name: ERC-8004 vs Google A2A Governance Dataset
tags:
- governance
- dao
- blockchain
- ethereum
- standardization
- ai-agents
- corporate-governance
- llm-annotation
- multi-model
- inter-coder-reliability
- mlcroissant
size_categories:
- 100K<n<1M
configs:
- config_name: r1-baseline-annotations
  data_files:
  - split: full
    path: croissant/v1/r1_annotations.parquet
- config_name: r2-consensus-cross-model
  data_files:
  - split: full
    path: croissant/v1/r2_cross_model_consensus.parquet
- config_name: r2-consensus-test-retest
  data_files:
  - split: full
    path: croissant/v1/r2_cross_round_consensus.parquet
- config_name: r2-votes-cross-model
  data_files:
  - split: full
    path: croissant/v1/r2_cross_model_votes.parquet
- config_name: r2-votes-test-retest
  data_files:
  - split: full
    path: croissant/v1/r2_cross_round_votes.parquet
- config_name: neurips26-corpus-stage-counts
  data_files:
  - split: full
    path: neurips26/corpus_stage_counts.parquet
- config_name: neurips26-bootstrap-differences
  data_files:
  - split: full
    path: neurips26/bootstrap_argument_differences.parquet
- config_name: neurips26-channel-distributions
  data_files:
  - split: full
    path: neurips26/channel_argument_distributions.parquet
- config_name: neurips26-temporal-distributions
  data_files:
  - split: full
    path: neurips26/temporal_argument_distributions.parquet
- config_name: neurips26-network-threshold-sensitivity
  data_files:
  - split: full
    path: neurips26/network_tie_threshold_sensitivity.parquet
---

# ERC-8004 vs Google A2A Governance Dataset

Full raw + annotated dataset for **RQ1: DAO governance vs. corporate governance in technology
standardization** — comparing **ERC-8004** (Trustless Agents, EIP/DAO process) against **Google A2A**
(Agent-to-Agent protocol, corporate hierarchy).

> **GitHub repository:** [kl41r3/erc8004-a2a-case-study](https://github.com/kl41r3/erc8004-a2a-case-study) — complete computational pipeline (scraping → LLM annotation → analysis → figures).

---

## Research Context

**Research Question:** Compared to corporations, how does the governance structure of
permissionless DAOs shape participation patterns, discourse composition, and network
topology in AI agent protocol standardization?

**Case A — ERC-8004** ("Trustless Agents"): Ethereum Improvement Proposal for permissionless
AI agent infrastructure. Governed via EIP rough consensus — open deliberation on the Ethereum
Magicians forum and GitHub, with no binding authority structure.

**Case B — Google A2A** (Agent-to-Agent protocol): Corporate-initiated AI agent protocol under
Linux Foundation governance with an 8-seat Technical Steering Committee that vests binding
decision authority.

The paper reports results at two scopes:

| Pipeline | Scope | Records | Annotators |
|---|---|---|---|
| **Main-text (R1)** | Single ERC-8004 vs. A2A | Paper reports ERC 142 / A2A 4,181; annotation archive has ERC 149 / A2A 5,272 | MiniMax-M2.5 |
| **Appendix (R2)** | 34-ERC cluster + cross-model + cross-round consensus | Cross-model: ERC 1,664 / A2A 4,058; current cross-round: ERC 1,664 / A2A 4,187 | 3 models × 3 rounds |

Two rounds of research:
- **R1 (baseline):** Single ERC-8004 vs A2A, single annotator model (MiniMax-M2.5).
- **R2 (data expansion):** 34-ERC cluster, 3-model cross-model triangulation +
  3-model × 3-round test-retest robustness.

Licensed **CC BY-NC 4.0** (attribution, non-commercial).

---

## Dataset Viewer subsets: which one should I load?

The Dataset Viewer shows five subsets (configs). They are five related tables, not five
copies of the same data. Three are analysis-ready consensus/annotation tables; two are
long-format vote tables that exist only for auditing agreement statistics.

| Subset | Rows | Use it for | Content |
|---|---:|---|---|
| `r1-baseline-annotations` | 5,421 | Main-text replication | R1 archive: single-model (MiniMax-M2.5) labels for ERC-8004 vs A2A, five fields including `stakeholder_institution` and `key_point` |
| `r2-consensus-cross-model` | 5,722 | Appendix analysis (analysis-ready) | R2 majority consensus across 3 independent models, four categorical fields |
| `r2-consensus-test-retest` | 5,851 | Stability analysis (analysis-ready) | R2 test-retest consensus from 3 models x 3 repeated rounds, three categorical fields |
| `r2-votes-cross-model` | 68,664 | Recomputing agreement / Fleiss' kappa (audit only) | Long-format per-model votes behind `r2-consensus-cross-model`; not an extra corpus |
| `r2-votes-test-retest` | 52,659 | Recomputing agreement / Fleiss' kappa (audit only) | Long-format per-model per-round votes behind `r2-consensus-test-retest`; not an extra corpus |

Why the two R2 consensus subsets look duplicated: 5,499 of their source records are shared
(the same public discussions), but the labels come from two different robustness
experiments. Cross-model consensus asks "do independent models agree with each other?" and
keeps `stakeholder_institution`. Test-retest consensus asks "is each model stable across
repeated runs of the same input?" and uses a later canonical A2A input, so the row counts
(5,722 vs 5,851) and part of the labels legitimately differ. Join across subsets with
`source_record_id`; `record_id` additionally encodes the pipeline layer, so the same
discussion intentionally has different `record_id`s in different subsets.

For most analyses, load the three `*-annotations` / `r2-consensus-*` subsets only. The
`r2-votes-*` subsets are needed solely to recompute agreement statistics.

The v1.1.0 release introduced five small `neurips26-*` subsets (non-visual robustness
tables). They are derived summaries, not additional corpora:

| Subset | Rows | Use it for |
|---|---:|---|
| `neurips26-corpus-stage-counts` | 6 | Corpus-stage reconciliation (archive vs. refiltered vs. frozen manifest) |
| `neurips26-bootstrap-differences` | 5 | Equal-size bootstrap intervals for argument-type differences |
| `neurips26-channel-distributions` | 27 | Argument composition by source channel |
| `neurips26-temporal-distributions` | 36 | Argument composition by calendar quarter |
| `neurips26-network-threshold-sensitivity` | 8 | Co-participation network summaries under varying tie weight |

---

## Directory map

```
data/
├── README.md                    ← This file (dataset card)
├── neurips26/                   NeurIPS 2026 robustness layer (v1.1.x)
│   ├── *.parquet                Five non-visual robustness tables
│   ├── SCHEMA.md                Schemas and validity boundary
│   ├── release_manifest.json    Version, seed, corpus, boundary statement
│   └── CHECKSUMS.json           SHA-256, byte sizes, row counts
├── manifests/                   Frozen paper-analysis membership
│   ├── r1_paper_v1.jsonl        Exact 4,323 retained R1 rows
│   └── r1_paper_v1_summary.json Input hashes, policy provenance, and manifest hash
├── croissant/v1/                Croissant 1.1 machine-readable release
│   ├── croissant.json           Versioned metadata + 5 RecordSets
│   ├── *.parquet                R1, R2 consensus, and normalized vote tables
│   ├── release_manifest.json    Source hashes, counts, and alignment decisions
│   └── CHECKSUMS.json           Release-file SHA-256 checksums
├── raw/                         Original scraped records (R1 + R2)
│   ├── (R1 files at root)
│   └── r2/                      R2 expanded scrape data (tier1 + tier2)
├── annotated/                   LLM-annotated + manually enriched
│   ├── r1/                      R1 baseline annotations
│   │   ├── annotated_records.json      All R1 records with LLM labels
│   │   └── author_profiles.json        Per-author institution profiles
│   └── r2/                      R2 data expansion + robustness
│       ├── cross-model/         3-model independent annotation → consensus
│       │   ├── consensus/             Final majority-vote consensus annotations ★
│       │   ├── validation/            ICR validation reports (Fleiss κ)
│       │   ├── erc/{model}/           Per-model ERC raw annotations
│       │   ├── a2a/{model}/           Per-model A2A raw annotations
│       │   └── thematic/              Thematic-LM codebooks (3 models)
│       └── cross-round/         3-model × 3-round test-retest reliability
│           ├── erc_cross_consensus.json    ERC cross-round final consensus ★
│           ├── a2a_cross_consensus.json    A2A cross-round final consensus ★
│           ├── erc/{model}/round_{1,2,3}/  ERC per-round raw annotations
│           └── a2a/{model}/round_{1,2,3}/  A2A per-round raw annotations
```

★ = final analysis-grade data used by the paper.

---

## croissant/v1/ — Machine-readable release

Croissant release v1.0.1 conforms to the MLCommons Croissant 1.1 metadata specification.
It deliberately preserves the pipeline layers as separate RecordSets:

The current metadata revision also includes the six minimal NeurIPS 2026 Responsible AI
fields. Validation evidence from the official NeurIPS Croissant Validator is available at
[`croissant/neurips-croissant-validator-pass.png`](croissant/neurips-croissant-validator-pass.png).

| RecordSet | Rows | Meaning |
|---|---:|---|
| `r1_annotations` | 5,421 | Complete stored MiniMax R1 annotation artifact |
| `r2_cross_model_consensus` | 5,722 | ERC 1,664 + A2A 4,058 cross-model consensus records |
| `r2_cross_model_votes` | 68,664 | Normalized per-model votes for four fields |
| `r2_cross_round_consensus` | 5,851 | ERC 1,664 + A2A 4,187 current cross-round consensus records |
| `r2_cross_round_votes` | 52,659 | Normalized per-model votes for three fields |

The R1 archive contains 30 pairs that refer to the same public GitVote comments but preserve
different annotation events. `source_record_id` identifies the shared source; `record_id`
identifies each pipeline-layer annotation event.

Rebuild locally:

```bash
uv run python scripts/process/build_croissant_release.py
```

See `croissant/v1/SCHEMA.md` for the R1/R2 alignment decision and field semantics.

---

## neurips26/ — NeurIPS 2026 robustness layer (v1.1.x)

This layer was introduced in v1.1.0 and is packaged reproducibly by v1.1.1. The layer
contains the five non-visual robustness tables of the NeurIPS 2026 study. No manuscript
is distributed in this release:

| File | Rows | Content |
|---|---:|---|
| `corpus_stage_counts.parquet` | 6 | Annotation archive vs. refiltered archive vs. frozen paper manifest (142 ERC-8004 / 4,181 A2A; the 4,230-record subset is a later archive artifact) |
| `bootstrap_argument_differences.parquet` | 5 | Equal-size bootstrap (2,000 repetitions, seed 20260826) A2A-minus-ERC differences in argument-type shares with 95% intervals; every principal interval includes zero |
| `channel_argument_distributions.parquet` | 27 | Argument-type composition by source channel |
| `temporal_argument_distributions.parquet` | 36 | Argument-type composition by calendar quarter |
| `network_tie_threshold_sensitivity.parquet` | 8 | Co-participation network summaries under varying minimum tie weight |

Regenerate deterministically in the GitHub repository with
`make robustness` (`scripts/analyse/run_neurips26_robustness.py`), then rebuild this layer
with `uv run python scripts/publish/build_neurips26_parquet.py --output <dir>`.

**Boundaries.** All results are descriptive. Equal-size resampling addresses the
142-versus-4,181 denominator imbalance but does not balance case maturity, platform
affordances, or organizational resources. The network inputs use platform-specific edge
semantics, so tie-threshold sensitivity is not a harmonized edge-definition test. No file
in this layer is a human gold-standard validation result. The nine-protocol (R3) corpus
is **not** part of this dataset layer; its public release is pending.

---

## raw/ — Original scraped records

Do not edit manually. SHA-256 checksums in `CHECKSUMS.json`.

### R1 files (root of raw/)

| File | Source | Records | Description |
|------|--------|---------|-------------|
| `forum_posts.json` | ethereum-magicians.org | 113 | ERC-8004 Discourse posts. Fields: `own_text` (quote-stripped), `quoted_post_numbers`, `reply_to_post_number`. |
| `github_comments_filtered.json` | `ethereum/ERCs` GitHub | 36 | PR bodies, issue comments, review comments for 9 core lifecycle PRs (#1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488). |
| `a2a_commits.json` | `google/A2A` GitHub | 522 | All A2A repository commits with metadata. |
| `a2a_issues.json` | `google/A2A` GitHub | 3,104 | A2A issues and issue comments. |
| `a2a_prs.json` | `google/A2A` GitHub | 1,955 | A2A PRs and PR review comments. |
| `a2a_discussions.json` | `google/A2A` GitHub | 822 | GitHub Discussions via GraphQL API. |
| `a2a_gitvote_prs.json` | `google/A2A` GitHub | 142 | Full data for TSC-voted PRs #831 (passed) and #1206 (superseded). |
| `profiles_forum.json` | ethereum-magicians.org | 60 | Discourse user profiles (bio, title, groups) for ERC-8004 forum authors. |
| `profiles_github.json` | GitHub API | 39 | GitHub user profiles (company, bio, location) for ERC-8004 and top-30 A2A authors. |
| `manual_institutions.json` | Manual investigation (R07) | 116 | Structured institution ground truth with provenance fields (`institution_source`, `confidence`, `evidence_url`). |
| `erc-8004_manifest.json` | — | — | Scrape metadata for ERC-8004 collection. |
| `a2a_manifest.json` | — | — | Scrape metadata for A2A collection. |
| `filter_log.json` | — | — | Log of PR keep/discard decisions during ERC-8004 filtering. |
| `CHECKSUMS.json` | — | — | SHA-256 of all raw files. |

### R2 expanded data (raw/r2/)

| File | Records | Description |
|------|---------|-------------|
| `tier1/erc8004_forum.json` | — | ERC-8004 forum posts (re-scraped with broader query). |
| `tier1/erc8004_github.json` | — | ERC-8004 GitHub PR comments (re-scraped). |
| `tier1/tier1_forum_manifest.json` | — | Scrape metadata for tier 1 forum. |
| `tier1/tier1_github_manifest.json` | — | Scrape metadata for tier 1 GitHub. |
| `tier2/cluster_forum.json` | — | 34-ERC cluster forum posts. |
| `tier2/cluster_github.json` | — | 34-ERC cluster GitHub PR comments. |
| `tier2/tier2_forum_manifest.json` | — | Scrape metadata for tier 2 forum. |
| `tier2/tier2_github_manifest.json` | — | Scrape metadata for tier 2 GitHub. |
| `CHECKSUMS.json` | — | SHA-256 of all R2 raw files. |

---

## annotated/r1/ — R1 baseline annotations

Single-model (MiniMax-M2.5) annotations for the original 1:1 case comparison.

| File | Records | Description |
|------|---------|-------------|
| `annotated_records.json` | 5,421 | Complete stored R1 annotation artifact with LLM labels: `stakeholder_institution`, `argument_type`, `stance`, `consensus_signal`, `key_point`. Actual archive: ERC 149 / A2A 5,272. The paper-reported retained subset is ERC 142 / A2A 4,181; exact row-level membership is frozen in `manifests/r1_paper_v1.jsonl` (4,323 rows), with input hashes and policy provenance in `manifests/r1_paper_v1_summary.json`. |
| `author_profiles.json` | 626 | One entry per unique canonical author. Fields: `institution_final`, `institution_source`, `institution_confidence`, `institution_lm`, `institution_evidence`. 107 authors enriched from manual R07 investigation; 2 from EIP header email. |

---

## annotated/r2/ — R2 data expansion + robustness

Three annotator models (deepseek-v4-flash, glm-4-plus, moonshot-v1-auto) independently
labelled the same expanded corpus (ERC: 1,664 records from 34 standards; A2A: ~4,059
records). Majority-vote consensus is the final analysis-grade data. Cross-round
test-retest with 3 rounds per model measures self-consistency.

### annotated/r2/cross-model/ — 3-model independent annotation → consensus

**Final consensus (use these for analysis):**

| File | Records | Description |
|------|---------|-------------|
| `consensus/erc_annotations.json` | 1,664 | ERC 34-cluster majority-vote consensus. Fields: `argument_type`, `stance`, `consensus_signal`, `stakeholder_institution`. |
| `consensus/a2a_annotations.json` | 4,058 | A2A majority-vote consensus. Same four fields as ERC. |
| `consensus/consensus_stats.json` | — | Agreement statistics: 3/3 vs 2/3 agreement rates per field. |

A2A count reconciliation: per-model files contain 4,059 rows each, including one
duplicated or malformed source record per file (a duplicated issue #1207 comment
in two files, one record with a missing URL in the third). The consensus table
keeps the 4,058 well-formed unique records. ICR validation reports N = 4,045,
the intersection validly annotated by all three models.

**Inter-coder reliability reports:**

| File | Description |
|------|-------------|
| `validation/validation_report.json` | ERC ICR report: pairwise Cohen's κ + Fleiss' κ for all 5 fields (N=1,664). |
| `a2a/validation/validation_report.json` | A2A ICR report: pairwise Cohen's κ + Fleiss' κ for all 5 fields (N=4,045). |

**Per-model raw annotations (3 models × 2 cases):**

| Directory | Records | Description |
|-----------|---------|-------------|
| `erc/deepseek-v4-flash/annotations.json` | 1,664 | DeepSeek-V4-Flash ERC annotations (5 fields). |
| `erc/glm-4-plus/annotations.json` | 1,664 | GLM-4-Plus ERC annotations (5 fields). |
| `erc/moonshot-v1-auto/annotations.json` | 1,664 | Moonshot-v1-auto ERC annotations (5 fields). |
| `a2a/deepseek-v4-flash/annotations.json` | 4,059 | DeepSeek-V4-Flash A2A annotations (5 fields). |
| `a2a/glm-4-plus/annotations.json` | 4,059 | GLM-4-Plus A2A full annotations (5 fields). |
| `a2a/glm-4-plus/annotations_common.json` | — | GLM-4-Plus A2A records common to all 3 models (ICR intersection subset). |
| `a2a/moonshot-v1-auto/annotations.json` | 4,059 | Moonshot-v1-auto A2A full annotations (5 fields). |
| `a2a/moonshot-v1-auto/annotations_common.json` | — | Moonshot-v1-auto A2A records common to all 3 models (ICR intersection subset). |

Each model directory also contains a `manifest.json` with annotation run metadata.

**Thematic-LM codebooks (3 models):**

| Directory | Description |
|-----------|-------------|
| `thematic/deepseek_themes.json` | DeepSeek thematic analysis codebook (ERC). |
| `thematic/glm_themes.json` | GLM-4-Plus thematic analysis codebook (ERC). |
| `thematic/kimi_themes.json` | Moonshot-v1-auto thematic analysis codebook (ERC). |
| `thematic/a2a/glm_themes.json` | GLM-4-Plus thematic analysis codebook (A2A). |
| `thematic/a2a/kimi_themes.json` | Moonshot-v1-auto thematic analysis codebook (A2A). |
| `thematic/validation/thematic_validation_report.json` | Cross-model thematic codebook validation report. |

Each themes file has an accompanying `*_manifest.json` with run metadata.

### annotated/r2/cross-round/ — 3-model × 3-round test-retest

Each model independently annotated the same records 3 times to measure self-consistency
(Fleiss' κ across rounds). Only 3 fields: `argument_type`, `stance`, `consensus_signal`.

**Final cross-round consensus:**

| File | Records | Description |
|------|---------|-------------|
| `erc_cross_consensus.json` | 1,664 | ERC cross-round consensus: per-model consensus merged across 3 rounds + cross-model agreement. |
| `a2a_cross_consensus.json` | 4,187 | Current A2A cross-round consensus after canonical ≥20-character input alignment. |

**Per-model per-round raw annotations:**

Each model has 3 round directories (`round_1/`, `round_2/`, `round_3/`) each
containing `annotations.json`. A `consensus.json` at the model level provides the
per-model cross-round consensus. A `manifest.json` (where present) records run metadata.

ERC: `erc/{deepseek-v4-flash, glm-4-plus, moonshot-v1-auto}/round_{1,2,3}/`
A2A: `a2a/{deepseek-v4-flash, glm-4-plus, moonshot-v1-auto}/round_{1,2,3}/`

---

## Annotation Schema

The schema depends on the pipeline layer. R1 uses five fields. R2 cross-model consensus
retains the first four categorical fields and does not contain `key_point`. R2 cross-round
consensus contains only `argument_type`, `stance`, and `consensus_signal`.

| Field | Values | Description |
|---|---|---|
| `stakeholder_institution` | Google \| Coinbase \| MetaMask \| Ethereum Foundation \| Independent \| Unknown | Inferred institutional affiliation |
| `argument_type` | Technical \| Economic \| Governance-Principle \| Process \| Off-topic | Type of argument made in the record |
| `stance` | Support \| Oppose \| Modify \| Neutral \| Off-topic | Stance toward the proposal's adoption as written |
| `consensus_signal` | Adopted \| Rejected \| Pending \| N/A | Editorial decision outcome (if any) |
| `key_point` | free text (≤20 words) | One-sentence summary of the record |

---

## Models

| # | Model ID | Vendor | R1 | R2 cross-model | R2 cross-round |
|---|----------|--------|-----|----------------|----------------|
| 1 | **MiniMax-M2.5** | MiniMax | ✅ (baseline) | — | — |
| 2 | **deepseek-v4-flash** | DeepSeek | — | ✅ ERC 1,664 · A2A 4,059 | ✅ current consensus ERC 1,664 · A2A 4,187 |
| 3 | **glm-4-plus** | Zhipu | — | ✅ ERC 1,664 · A2A 4,059 | ✅ current consensus ERC 1,664 · A2A 4,187 |
| 4 | **moonshot-v1-auto** | Kimi/Moonshot | — | ✅ ERC 1,664 · A2A 4,059 | ✅ current consensus ERC 1,664 · A2A 4,187 |

Failed/discarded models (data deleted): MiniMax-M3, Kimi-K2.6, deepseek-chat, glm-4.7, glm-5.1.

---

## Key Findings

1. **Participation is oligarchic across both governance forms, despite opposite decision architectures.** ERC-8004 advances by rough consensus with permissionless deployment; A2A vests binding authority in an 8-seat corporate TSC (transitioned to Linux Foundation governance in June 2025). Yet both produce comparable participation inequality (degree Gini 0.804 vs 0.779; betweenness Gini 0.931 vs 0.979), and the majority of contributors in both cases engage only a single theme (median actor Shannon entropy H=0). ERC-8004's top-3 degree holders span MetaMask, Hats Protocol, and The Graph; A2A's top-3 include two Google employees and one from Microsoft.

2. **Discourse is technically dominated in both cases, but governance form shapes composition.** A2A devotes nearly twice the share to Process arguments (25.4% vs 13.9%, χ²(3)=52.88, p<.001, Cramér's V=.103), reflecting heavier coordination overhead in corporate governance. Within ERC-8004, Process discussion surges to 53% in Phase 3 as deliberation shifts from design to editorial ratification. Topic divergence is moderate but meaningful: JSD=0.288 (BERTopic) and JSD=0.216 (Thematic-LM).

3. **DAO concentrates on trust; corporate governance spreads across engineering execution.** ERC-8004 is dominated by T08 Trust & Security Mechanisms (34.5% of records; 34.5% actor participation rate vs A2A's 4.0%). A2A spreads deliberation across Documentation (T06), Community Contributions (T07), and Protocol Specification (T01), plus three engineering-execution themes (Transport, Streaming, Project Governance) entirely absent from the EIP forum.

4. **Network connectivity reverses with scope.** At single-case level, the DAO attains denser discourse congruence (0.148 vs 0.082, congruence density), consistent with groupthink in a small reputation-based elite. However, expanding to a 34-ERC agent cluster overturns this finding: the DAO network coalesces at ecosystem scale (GCR 0.328 → 0.917), while the re-annotated A2A network remains fragmented (GCR 0.534 → 0.285). The permissionless DAO is the *more* connected and observable regime at ecosystem scale — coordination in the corporate case moves off the public record.

---

## Robustness Results (from the Paper Appendix)

| Experiment | Models | Rounds | Records | Key result |
|---|---|---|---|---|
| Cross-model (R2) | 3 vendors | 1 | ERC 1,664 / A2A 4,045 | argument_type Fleiss' κ = 0.683 (ERC Substantial) / 0.619 (A2A Substantial) |
| Cross-round | 3 models | 3 | Paper snapshot: ERC 1,664 / A2A 3,844; current artifact: ERC 1,664 / A2A 4,187 | GLM-4-Plus κ = 0.86–0.93 (most stable); DeepSeek κ = 0.49–0.63 |
| 4-model (R1 + cross-round) | +MiniMax-M2.5 | 1 | ERC 144 / A2A 3,844 | 4-way Fleiss' κ ≈ 0.46–0.51 (Moderate); model choice dominates stochastic noise |

**What replicates** (3 of 4 findings): (i) discourse remains technically dominated across models; (ii) participation inequality persists (Gini ≈ 0.8); (iii) DAO attains denser within-community consensus.

**What reverses** (1 of 4): network connectivity ranking inverts at ecosystem scale — the permissionless DAO becomes the *more* connected and observable regime (GCR 0.917 vs. A2A 0.285), because corporate coordination moves off the public record.

---

## CHECKSUMS

SHA-256 checksums live in `CHECKSUMS.json` at each tier:
- `CHECKSUMS.json` (raw, root)
- `raw/r2/CHECKSUMS.json`
- `annotated/r2/cross-model/CHECKSUMS.json`
- `annotated/r2/cross-round/CHECKSUMS.json`

Regenerate after any data change with the command in the project README.

---

## License

**Data:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — attribution required,
non-commercial use only.

**Code (GitHub):** MIT License.

---

## Citation

If you use this dataset, please cite the accompanying paper and link to the
[GitHub repository](https://github.com/kl41r3/erc8004-a2a-case-study).

```bibtex
@inproceedings{wang2026agentic,
  author    = {Wang, Yutian and Zhang, Luyao},
  title     = {Agentic Analysis for Agentic Infrastructure: An LLM-Powered Pipeline for Comparative Governance of DAO and Corporate AI Protocols},
  booktitle = {KDD 2026 Workshop on SciSoc Agents \& LLMs},
  year      = {2026}
}
```
