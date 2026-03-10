# RQ1 Governance Metrics — Findings Summary
Generated: 2026-03-10 16:31 UTC

---

## Comparative Governance Metrics

| Metric | ERC-8004 (DAO) | Google A2A (Corporate) |
|--------|---------------|------------------------|
| Governance type | Permissionless DAO | Corporate Hierarchy |
| Proposal / first public date | 2025-08-13 | 2025-04-09 |
| Consensus / launch | 2026-01-29 | N/A (ongoing) |
| Days to consensus | **169** | N/A |
| Total discussion records | 124 | 3025 |
| Unique discussion contributors | 62 | 530 (+69 review comment authors) |
| Unique institutions | TBD (annotation pending) | TBD (annotation pending) |
| Openness index | TBD | TBD |
| Total commits | N/A | 522 |
| Commit authors | N/A | 131 |
| Forum reply rate | 0.46 | N/A |

> Openness index = unique contributors from outside initiating org / total unique contributors.
> Values 0–1; closer to 1.0 = more open.

---

## ERC-8004 Participation Breakdown (LLM-annotated)

_Annotation pending — run: uv run python scripts/annotate_llm.py_

## Google A2A Participation Breakdown (LLM-annotated)

_Annotation pending — run: uv run python scripts/annotate_llm.py_

---

## Data Sources

| Case | Source | Link | Records |
|------|--------|------|---------|
| ERC-8004 | Ethereum Magicians forum | https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098 | 113 posts |
| ERC-8004 | GitHub ethereum/ERCs (core PRs only) | https://github.com/ethereum/ERCs/pulls?q=erc-8004 | 11 comments |
| Google A2A | GitHub google/A2A | https://github.com/google/A2A | 522 commits, 3025 discussion records |

---

## Theoretical Interpretation (Draft)

**Williamson puzzle**: ERC-8004 involved high asset specificity (AI agent protocol)
and high uncertainty (novel domain). TCE predicts hierarchy. Instead, competing
firms cooperated via permissionless DAO in 169 days.

**Contrast**: Google A2A was developed entirely inside Google's corporate hierarchy.
Both produced a technically similar protocol addressing the same problem.
The governance form differed radically.

**Three DAO-enabling mechanisms (proposed)**:
1. Blockchain-enforced commitment substitutes for contractual safeguards
2. On-chain reputation removes free-rider incentive
3. Permissionless participation lowers coordination costs across heterogeneous stakeholders

---

*To complete: run `uv run python scripts/annotate_llm.py` (requires MiniMax/OpenAI/Anthropic API key with balance).*
