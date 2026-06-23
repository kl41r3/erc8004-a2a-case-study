# Round B — Voting Mechanism

**Status:** DONE
**References:** literature/1 (SoK Blockchain Governance), literature/2 (Consensus Mechanisms Review)
**Visualization refs:** literature/3 (Event Knowledge Graphs), literature/4 (3D History Timelines)

## Goal

Produce a side-by-side comparison of the two governance decision mechanisms:
1. **Figure:** Two-panel diagram — EIP editor-approval flow vs. TSC git-vote flow
2. **Pseudocode:** Formal pseudocode blocks for each mechanism

## Evidence available

**ERC-8004 side:**
- 8 GitHub review records with APPROVE/COMMENT states (e.g., `lightclient` APPROVED "LGTM!")
- EIP stage transitions traceable through 9 core lifecycle PRs
- No formal voting — governance is editor judgment + community forum discussion

**A2A side:**
- `data/raw/a2a_gitvote_prs.json`: 2 TSC-voted PRs (#831 passed, #1206 closed/superseded)
- 38 `/vote` commands, 8 `/cancel-vote` commands across 32 threads
- TSC membership is pre-registered; non-TSC members cannot cast binding votes
- `human-notes/preparation/gitvote_analysis.md`: full annotation of PR #831 and #1206

## Key analytical point

The asymmetry is a finding: ERC-8004 has no formal vote — the "decision" is EIP editor merge judgment after public deliberation. A2A has a formal TSC vote mechanism that is invoked only when ordinary review consensus fails (governance escalation). PR #1206 illustrates off-platform migration: vote → TSC call → Discord → /cancel-vote.

## Results

- `output/voting_mechanism_comparison.png` — two-panel process diagram (white background, 180 dpi)
- `output/voting_stats.json` — key statistics
- `human-notes/draft/dft.tex` — new §Results subsection "Decision Mechanism Architecture" with Figure~\ref{fig:voting} and Algorithms 1 & 2

Key stats:
- ERC-8004: 2 human approvals (`lightclient`), 3 bot auto-merges, no formal vote mechanism
- A2A: 4 /vote commands, 1 /cancel-vote command, 66 bot messages across 2 TSC-voted PRs (13 + 6 human participants respectively)

## Limitations

- ERC-8004 vote evidence is sparse (8 review records, 2 human approvals); process relies heavily on informal norms not captured in data
- A2A GitVote only triggered on 2 of 755 PRs — mechanism exists but is rarely invoked
- LaTeX `algorithm`/`algpseudocode` packages added to dft.tex; verify compilation before submission
