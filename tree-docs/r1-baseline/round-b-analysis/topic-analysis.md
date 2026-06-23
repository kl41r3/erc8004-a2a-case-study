# Round B — Topic Analysis

**Status:** DONE
**Reference:** literature/5 (Chen et al. 2025, arXiv:2409.00843 — spatiotemporal DeFi tweet analysis; LDA + temporal evolution + cross-group comparison)

## Goal

Produce 1 figure and 1 statistic result: argument-type distribution and temporal evolution comparing ERC-8004 and A2A deliberation.

## Method

Paper [5] uses LDA on 150M tweets and visualises topic probability per cluster per year (Fig. 8). We adapt the **temporal evolution + cross-case comparison** output format rather than the unsupervised LDA method — our LLM annotation already provides structured topic labels (`argument_type`). This is appropriate given ERC-8004's small N (144), which makes unsupervised topic modeling unreliable.

Analyses:
1. Argument_type distribution by case (bar chart comparison) — cross-case
2. Stance × argument_type cross-tabulation — heatmap
3. Temporal evolution: two-panel stacked 100% bar chart (ERC-8004 2-week bins + A2A monthly bins)
4. Chi-square test of independence — cross-case and within ERC-8004 lifecycle

Statistical method: χ² contingency test (scipy.stats.chi2_contingency) + Cramér's V effect size.

## Data

`data/annotated/annotated_records.json` — 5,416 records with `argument_type`, `stance`, `stakeholder_institution`, `date`

- ERC-8004: N=144 (Aug 2025 – Jan 2026)
- Google A2A: N=5,272 (Mar 2025 – present)

## Results

**Figures** (`output/figures/`):
- `topic_argtype_comparison.png` — argument type distribution by case
- `topic_stance_heatmap.png` — stance × argument_type cross-tabulation (two-panel)
- `topic_temporal_erc8004.png` — ERC-8004 only, 2-week bins (legacy)
- `topic_temporal_comparison.png` — two-panel: ERC-8004 (2-week bins) + A2A (monthly bins)

**Statistics** (`output/stats/topic_stats.json`):

Cross-case χ²:
> χ²(3) = 52.876, p < .001, Cramér's V = .103 (small–medium effect)

ERC-8004 lifecycle χ² (2-month bins: Aug–Oct / Oct–Dec / Dec–Feb):
> χ²(6) = 25.322, p < .001, Cramér's V = .315 (medium effect)

**Key findings:**
- ERC-8004: Technical 74.3%, Process 13.9%, Governance-Principle 4.9%
- A2A: Technical 64.7%, Process 25.4% (nearly double ERC-8004's Process share)
- Cross-case difference is significant but modest (V=.103): both cases are Technical-dominant; the distinction is in Process overhead
- ERC-8004 lifecycle effect is stronger (V=.315): argument composition shifts meaningfully across the 5.5-month proposal window

## Limitations

- ERC-8004 N=144 limits statistical power; cell counts in lifecycle phases are small (some cells <5)
- Argument_type labels are LLM-generated; no inter-coder reliability computed yet
- "Off-topic" excluded from chi-square contingency tables to avoid conflating annotation noise with governance signal
- A2A temporal analysis lacks a defined endpoint (ongoing project), so lifecycle comparison is asymmetric by design
