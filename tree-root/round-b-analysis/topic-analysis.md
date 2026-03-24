# Round B — Topic Analysis

**Status:** TODO
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

## Limitations

- ERC-8004 N=149 limits statistical power for cross-tabulation; percentages more meaningful than counts
- Argument_type labels are LLM-generated; no inter-coder reliability computed yet
- "Off-topic" (409 records) accounts for 7.6% of total — mostly bot-adjacent or short acknowledgments
