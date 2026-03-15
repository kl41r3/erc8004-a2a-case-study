# Paper Vocabulary & Phrases

Reference sheet for writing the paper. Organized by paper section. Focus on domain-specific "language" that signals you belong to the conversation.

---

## Theory Section — Transaction Cost Economics

**Key terms (use exactly as literature uses them):**
- *asset specificity* — the degree to which an investment loses value outside a particular relationship
- *bounded rationality* — cognitive limits on information processing (Simon 1955; Williamson's starting point)
- *opportunism* — self-interest seeking with guile (not just self-interest)
- *incomplete contracting* — contracts cannot specify all contingencies ex ante
- *hold-up problem* — ex post renegotiation after specific investments are made
- *remediableness* — "an outcome for which no feasible superior alternative can be described" (Williamson 1996)
- *hybrid governance* — between market and hierarchy (alliances, joint ventures, open standards bodies)
- *governance mode* — preferred to "governance mechanism" in Williamson's vocabulary
- *credible commitment* — a promise made binding through structure, not words

**Phrases for framing the puzzle:**
- "Transaction cost economics predicts that…"
- "High asset specificity and behavioral uncertainty jointly favor hierarchical governance (Williamson 1985)."
- "The conditions under which DAO governance operated closely approximate those Williamson identified as hierarchy-inducing."
- "We document an empirical regularity that the conventional TCE prediction struggles to accommodate."
- "Rather than posit that TCE is wrong, we identify the mechanisms that substitute for hierarchical authority."

---

## Theory Section — Governance & Open Source

**Key terms:**
- *commons governance* — Ostrom-style management of shared resources
- *lazy consensus* — Apache Foundation term: silence implies consent
- *rough consensus* — IETF term: "consensus is not unanimity" (RFC 7282)
- *meritocracy* — contribution-based authority (contested term; use carefully or qualify)
- *permissionless* — anyone can participate without prior approval (Ethereum community term)
- *fork threat* — the credible option to create a competing standard
- *legitimate peripheral participation* — Lave & Wenger; newcomers joining community practice
- *boundary object* — a shared artifact that coordinates heterogeneous groups (star & griesemer 1989)

**Phrases:**
- "Unlike standards setting organizations (SSOs) with formal membership structures, the EIP process is permissionless — any contributor can propose or critique."
- "The fork threat disciplines incumbents even if never exercised (West 2003)."
- "The EIP process instantiates what Simcoe (2012) calls consensus governance, but without the SSO's formal membership gate."
- "Governance legitimacy derives from technical quality of contributions, not organizational affiliation."

---

## Theory Section — Blockchain/DAO

**Key terms:**
- *decentralized autonomous organization (DAO)* — first use: Buterin (2014)
- *smart contract* — self-executing code on the blockchain; "lex cryptographia" (De Filippi & Wright 2018)
- *on-chain governance* — governance through smart contract execution
- *off-chain governance* — governance through social/deliberative processes (ERC-8004 uses this)
- *token voting* — weighted voting by token holdings (NOT used in ERC-8004)
- *signaling* — non-binding preference expression (used in EIP process)
- *trustless* — requiring no trust in counterparties (trust in code/math instead)
- *immutability* — blockchain records cannot be altered post-confirmation
- *pseudonymous identity* — known only by public key/handle, not legal name
- *credible commitment device* — smart contracts as self-enforcing agreements

**Phrases:**
- "ERC-8004 operates through off-chain governance: deliberation occurs on Ethereum Magicians and GitHub, while the binding commitment is enforced through on-chain immutability once adopted."
- "The blockchain provides what Williamson (1983) termed a credible commitment device: the cost of post-adoption defection is technical incompatibility, not legal sanction."
- "Unlike token-weighted voting systems, the EIP process weights contributions by technical quality rather than stake size."
- "Lumineau et al. (2021) identify blockchain governance as a novel form of organizing; our evidence elaborates the conditions under which it outperforms hierarchy."

---

## Methods Section

**Key terms:**
- *process tracing* — qualitative method for causal mechanism identification
- *comparative case study* — (Eisenhardt 1989; Yin 2018) — justify two-case design
- *archival data* — trace data from GitHub/forum; unobtrusive measure
- *unit of analysis* — the governance *record* (post/comment/review); supplemented by *case* for structural metrics
- *theoretical sampling* — cases selected for theoretical contrast, not statistical representation
- *LLM annotation* — machine-assisted qualitative coding; requires reliability check
- *inter-rater reliability* — should calculate Cohen's Kappa for subsample
- *manifest content* — surface-level categorization (argument type, stance)
- *latent content* — underlying meaning/mechanism (requires interpretive reading)

**Phrases:**
- "We adopt a comparative case study design (Eisenhardt 1989; Yin 2018), selecting ERC-8004 and Google A2A for theoretical contrast: both are AI protocol governance processes, differing systematically in governance mode."
- "Our primary data consists of N = 5,700 governance records archivally scraped from Ethereum Magicians forum and the GitHub repositories for both cases."
- "We employ LLM-assisted annotation using the MiniMax-M2.5 model to code each record on four dimensions: stakeholder institution, argument type, stance, and consensus signal."
- "To address validity concerns, we validate a subsample of N = 50 records against human codes, reporting Cohen's Kappa ≥ 0.7 as acceptable reliability (Landis & Koch 1977)."
- "The scraping protocols, annotation codebook, and data files are available at [repository URL] for replication."

---

## Results Section

**Structural metrics vocabulary:**
- *openness index* — proportion of non-initiating-institution contributors
- *discussion records* — total archival records of deliberation
- *unique contributors* — unduplicated author count
- *days to consensus* — proposal date to ratification date
- *argument type distribution* — proportion breakdown by coded argument type
- *stance distribution* — proportion breakdown by coded stance
- *Gini coefficient of participation* — measure of contribution concentration (optional, adds rigor)
- *reply rate* — fraction of forum posts that directly reply to another post

**Phrases for results:**
- "ERC-8004 reached ratified consensus in 169 days, compared to Google A2A's ongoing iteration with no terminus."
- "Technical arguments constitute 74.3% of ERC-8004 deliberation, significantly higher than the A2A proportion of 62.7% (χ² test, p < 0.01)."
- "The Modify-plus-Oppose stance rate of 36.1% in ERC-8004 indicates genuine adversarial review, inconsistent with rubber-stamp dynamics."
- "Google's 22.6% record share despite representing only 7.3% of unique authors reveals disproportionate contribution intensity by institutional actors."
- "The two TSC-voted pull requests constitute governance escalation events — instances where ordinary consensus mechanisms were insufficient."

---

## Discussion Section — Mechanism Language

**The three mechanisms (from data_interpretation.md):**

**M1: Smart contract as credible commitment device**
- "Immutable commitment" / "ex ante commitment technology"
- "The EVM enforces the standard, removing the need for hierarchical authority to police compliance."
- "Post-adoption defection is technically infeasible rather than merely contractually prohibited."

**M2: Pseudonymous reputation as governance currency**
- "Reputation externalization" / "portable reputation" / "identity-anchored contribution history"
- "The permanent auditability of blockchain-based contribution records disciplines participant behavior without employment authority."
- "Technical credibility, not organizational position, determines influence in the EIP process."

**M3: Permissionless entry as anti-capture mechanism**
- "Unlimited threat of competitive entry" / "fork discipline" / "contestability of the standard"
- "The EIP process is epistemically open: any party may introduce a competing standard, which disciplines incumbent actors."
- "The absence of membership gates distinguishes EIP governance from both corporate hierarchy and SSO governance."

**Theoretical framing phrases:**
- "These three mechanisms jointly substitute for the hierarchical authority that TCE theory identifies as necessary under conditions of high asset specificity and uncertainty."
- "We term this configuration *trustless coordination*: governance without hierarchy, sustained by code-enforced commitments, reputational bonding, and competitive contestability."
- "Our findings extend Lumineau et al. (2021) by specifying the operational mechanisms through which blockchain governance achieves coordination."
- "The comparison with Google A2A reveals that corporate openness (high openness index of 0.956) is compatible with informal hierarchy: institutional actors can dominate deliberation without formal authority."

---

## Limitations Language

- "Our inference rests on observational data; we cannot rule out selection effects."
- "Both cases are successful protocols; governance failures are not represented in our sample."
- "The LLM annotation approach introduces classification error; we report a reliability coefficient of κ = [X] for the validated subsample."
- "Off-platform governance (Discord, synchronous TSC calls) is systematically unobservable in A2A data, which may undercount governance activity."
- "ERC-8004 operates at smaller scale than A2A; scale differences may confound governance-mode differences."

---

## AOM/SMS-Specific Language Signals

For the TIM (Technology and Innovation Management) track, reviewers expect:
- "governance mode" not "governance mechanism"
- "organizational form" for describing DAO structure
- "new forms of organizing" (invoke Puranam et al. 2014 explicitly)
- "process" vs. "outcome" distinction — both matter; address both
- "boundary conditions" — explicitly state when your findings generalize / don't
- "mid-range theory" — appropriate ambition for a 2-case empirical paper
- "contribution to theory X" statement in abstract and introduction

**Abstract framing template:**
> "Drawing on transaction cost economics and open-source governance theory, we examine two AI protocol governance processes — ERC-8004 (DAO) and Google A2A (corporate hierarchy) — to investigate how permissionless governance achieves coordination under conditions that TCE theory predicts require hierarchy. Analysis of [N] archival governance records reveals [key finding]. We identify three mechanisms — [M1], [M2], [M3] — that substitute for hierarchical authority. Our findings contribute to [theory X] by [specific contribution]."
