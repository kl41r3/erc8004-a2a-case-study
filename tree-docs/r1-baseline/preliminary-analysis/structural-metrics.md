# Preliminary Analysis — Structural Metrics

**Status:** DONE
**Scripts:** `scripts/compute_metrics.py`, `scripts/identify_core_contributors.py`, `scripts/build_network.py`

## What was done

Computed governance metrics for both cases and built interactive network visualizations.

## Results

Key metrics (`analysis/structural_metrics.csv`):

| Metric | ERC-8004 | Google A2A |
|--------|----------|------------|
| Governance type | Permissionless DAO | Corporate Hierarchy |
| Days to consensus | 169 | N/A (ongoing) |
| Total records | 149 | 5,272 |
| Unique contributors | 71 | 826 |
| Top institution share | MetaMask 12.6% | Google ~25% |
| Independent share | 44.4% | 44.1% |
| Formal votes | None (EIP editor) | 38 /vote commands (TSC git-vote) |

Key contributor findings (`analysis/core_contributors.csv`):
- ERC-8004: `pcarranzav` (The Graph) highest Modify+Oppose rate — most active critic with no organizational power
- Google A2A: `holtskinner` (Google) ~10% of all records; `darrelmiller` (Microsoft) 286+ records, simultaneously IETF HTTPAPI WG Chair + LF A2A TSC member
- Cross-case overlap: 1 confirmed human (`voidcenter` / Sparsity.ai)
- Google and Coinbase are ERC-8004 formal co-authors with **zero** public discussion records

Network visualizations (interactive, `output/`):
- `network_erc8004.html`, `network_a2a.html`, `network_compare.html`
- `bipartite_erc8004.html`, `bipartite_a2a.html`
- `timeline_erc8004.html`

Full summary: `human-notes/preparation/findings_summary.md`

## Limitations

- Network edges built from reply chains and PR reviews; edge weight = interaction count (not normalized)
- No SNA metrics computed yet (degree centrality, modularity, core-periphery) — this is Round B work
- A2A `openness_index` = 0.969 but based on LLM-inferred institution labels for majority of contributors
