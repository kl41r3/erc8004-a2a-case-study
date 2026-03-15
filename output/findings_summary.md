# Findings Summary: DAO vs. Corporate Governance in AI Protocol Standardization

*Last updated: 2026-03-15. Based on 5,421 annotated records across two cases.*

---

## The Puzzle

Transaction cost economics predicts that high asset specificity and behavioral uncertainty favor hierarchy. ERC-8004 (a trustless AI agent protocol) was developed under exactly these conditions — yet contributors from competing organizations reached binding consensus in **169 days** through a permissionless DAO process, without contracts or authority.

Google A2A addressed the same problem via a corporate-led Technical Steering Committee. After one year of open development, it remains in ongoing iteration with no binding consensus date.

---

## Key Comparisons

| | ERC-8004 (DAO) | Google A2A (Corporate) |
|---|---|---|
| Governance | Permissionless EIP process | Corporate TSC + open-source |
| First public | 2025-08-13 | 2025-04-09 |
| Consensus | **2026-01-29 (169 days)** | Ongoing |
| Discussion records | 149 | 5,272 |
| Unique contributors | 69 | 771 |
| Top institution share | MetaMask: 12.6% of records | Google: 25.0% of records |
| Independent share | 44.4% of records | 44.1% of records |

---

## Participation Structure

**ERC-8004** — distributed, multi-institutional:
- 69 active discussion contributors; no single actor exceeds 13% of records
- Named institutions confirmed (R07): MetaMask (12.6%), Ethereum Foundation (10.4%), The Graph (5.9%), Hats Protocol (3.7%), Nethermind (3.0%)
- Formal EIP co-authors (per EIP header): MetaMask, Ethereum Foundation, **Google** (`jordanellis@google.com`), **Coinbase** (`erik.reppel@coinbase.com`)
- **Critical finding:** Google and Coinbase are institutional co-authors but have **zero public discussion records** — they endorsed the standard without dominating its deliberation
- Most active critic: `pcarranzav` (The Graph, 16 records) — highest Modify+Oppose rate, no organizational power within the EIP process

**Google A2A** — hierarchically concentrated:
- 771 unique contributors, but power-law concentrated: `holtskinner` (Google) alone = ~10% of all records
- Top 5 contributors all organizationally affiliated: Google ×3, Microsoft, Cisco
- `darrelmiller` (Microsoft, 286+ records) simultaneously: IETF HTTPAPI WG Chair + LF A2A TSC member — a single institutional bridge between corporate and formal standards infrastructure
- Independent contributors appear only at positions 6+ in contribution ranking

---

## Argument Type Analysis

**ERC-8004:** Technical debate dominates (74.3%). Governance-Principle arguments (4.9%) are present but not the primary mode. Process arguments (13.9%) reflect EIP lifecycle management.

**A2A:** Broader argument distribution across Technical, Process, and Economic types — consistent with an ongoing product development process rather than a finite standardization event.

**Cross-case pattern:** Both cases show ~44% independent contributor records, but ERC-8004 independents engage in substantive technical critique (high Modify+Oppose rates), while A2A independents primarily contribute feature requests and implementation questions.

---

## Three Enabling Mechanisms (Proposed)

1. **Smart-contract-enforced commitment** — blockchain finality substitutes for contractual safeguards; no party can unilaterally reverse ratified EIPs
2. **Pseudonymous reputation externalization** — on-chain identity creates reputational stakes across organizational boundaries, reducing free-rider risk
3. **Permissionless competitive entry** — any actor can fork, implement, or critique the specification; this threat disciplines incumbent contributors

These jointly substitute for hierarchical authority, resolving the Williamson puzzle.

---

## Data Quality

- 5,421 total annotated records (ERC-8004 annotation quality verified against manual sample)
- Institution attribution: 109 of 628 discussion authors enriched via R07 manual investigation; 517 remain LLM-inferred
- ERC-8004 formal co-authors: 4 (MetaMask, EF, Google, Coinbase) — all confirmed via EIP header email; Google and Coinbase have 0 public discussion records
- ERC-8004 GitHub data: 7 of 9 core PRs have human participants; #1470 and #1488 contain only bot activity
- Cross-case overlap: 1 confirmed human (voidcenter / Sparsity.ai) appears in both cases
