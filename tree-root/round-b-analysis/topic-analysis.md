# Round B — Topic Analysis

**Status:** DONE
**Reference:** literature/5 (Spatiotemporal DeFi Tweet Analysis — BERTopic method)

## Goal

Produce Figure 1 and Statistic Result 1: argument-type distribution analysis comparing ERC-8004 and A2A deliberation.

## Method

Paper [5] uses BERTopic on 150M tweets. We adapt the output format (topic distribution by group) rather than the unsupervised modeling method — our LLM annotation already provides structured topic labels (`argument_type`). This is appropriate given ERC-8004's small sample (N=149), which makes unsupervised topic modeling unreliable.

Planned analyses:
1. Argument_type distribution by case (bar chart comparison)
2. Stance × argument_type cross-tabulation
3. Temporal evolution of argument types across ERC-8004 lifecycle stages

## Data

`data/annotated/annotated_records.json` — 5,416 records with `argument_type`, `stance`, `stakeholder_institution`, `date`

## Results

- `output/topic_argtype_comparison.png` — Figure 1: argument type distribution (ERC-8004 vs A2A)
- `output/topic_stance_heatmap.png` — stance × argument_type cross-tabulation (two-panel)
- `output/topic_temporal_erc8004.png` — ERC-8004 argument type over lifecycle (2-week bins)
- `output/topic_stats.json` — full counts and percentages
- `human-notes/draft/dft.tex` — updated with figures and corrected A2A percentages

Key findings:
- ERC-8004: Technical 74.3%, Process 13.9%, Governance-Principle 4.9%
- A2A: Technical 64.7%, Process 25.4% (nearly double ERC-8004)
- Support/Modify in ERC-8004: 77–95% Technical → deliberation grounded in engineering substance
- A2A Neutral: 47% Technical / 44% Process → high coordination overhead

## Limitations

- ERC-8004 N=149 limits statistical power for cross-tabulation; percentages more meaningful than counts
- Argument_type labels are LLM-generated; no inter-coder reliability computed yet
- "Off-topic" (409 records) accounts for 7.6% of total — mostly bot-adjacent or short acknowledgments
