# Data Collection, Processing, and Metrics — Full Documentation

**Audience:** Researcher (for personal verification)
**Generated:** 2026-03-15
**Status:** Annotation complete. 5,421 total records (ERC-8004: 149; Google A2A: 5,272).
Institution data finalized with R07 manual investigation (109 confirmed discussion authors).
Two additional EIP co-author profiles added (Jordan Ellis/Google, Erik Reppel/Coinbase)
with 0 discussion records; author_profiles.json now contains 628 entries.

---

## 1. Data Collection

### 1.1 ERC-8004: Ethereum Magicians Forum

**What:** All posts from the Ethereum Magicians forum thread for ERC-8004 (Trustless Agents).

**How:**
- Script: `scripts/scrape/scrape_erc8004_forum.py`
- Method: Discourse JSON API (`GET https://ethereum-magicians.org/t/25098/posts.json`)
- Pagination: topic posts fetched in chunks using `post_ids[]` parameter; numeric topic ID only
  (slug+ID form returns 404 — see CLAUDE.md)
- HTTP: `subprocess` + system `curl` (not `requests`) due to Python 3.14 SSL EOF errors
  on `ethereum-magicians.org`

**Where:** `data/raw/forum_posts.json`
**Record count:** 113 posts
**Fields per record:** `post_id`, `author`, `date`, `raw_text`, `reply_to_post_number`, `source` (`"forum"`)

---

### 1.2 ERC-8004: GitHub Pull Request Records

**What:** PR bodies, issue comments, review comments, and reviews for the 9 core lifecycle
PRs that directly modified `ERCS/erc-8004.md`.

**How:**
- Script: `scripts/scrape/scrape_erc8004_prs.py`
- Method: GitHub REST API
  - `GET /repos/ethereum/ERCs/pulls/{number}` — PR body
  - `GET /repos/ethereum/ERCs/issues/{number}/comments` — issue comments
  - `GET /repos/ethereum/ERCs/pulls/{number}/reviews` — review objects
  - `GET /repos/ethereum/ERCs/pulls/{number}/comments` — review comments
- Auth: `GITHUB_PERSONAL_ACCESS_TOKEN` from `.env`
- **Why these 9 PRs?** GitHub search returns any PR mentioning ERC-8004 (including ecosystem
  ERCs that depend on it via `Requires: ERC-8004`), inflating results. The 9 selected PRs
  are the only ones that directly modify `ERCS/erc-8004.md` or change its lifecycle status.
  See `data/raw/filter_log.json` for the full selection log.

**Core lifecycle PRs:** `#1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488`

**Where:** `data/raw/github_comments_filtered.json`
**Record count:** 36 records
**Fields:** `author`, `date`, `raw_text`, `source`, `platform`, `pr_number`, `comment_id`

---

### 1.3 Google A2A: Issues and Issue Comments

**What:** All issues and issue comments from `a2aproject/A2A` GitHub repository.

**How:**
- Script: `scripts/scrape/scrape_a2a.py`
- Method: GitHub REST API
  - `GET /repos/a2aproject/A2A/issues?state=all&per_page=100` (paginated)
  - `GET /repos/a2aproject/A2A/issues/{number}/comments?per_page=100` (paginated)
- Note: `patch_a2a_missing_pages.py` re-fetched any paginated data that timed out

**Where:** `data/raw/a2a_issues.json`
**Record count:** 3,104 records
**Fields:** `author`, `date`, `raw_text`, `source` (`"issue"` or `"issue_comment"`), `issue_number`

---

### 1.4 Google A2A: Pull Requests and Review Comments

**What:** All PRs, PR review comments from `a2aproject/A2A`.

**How:**
- Script: `scripts/scrape/scrape_a2a.py` (same script as issues)
- Method: GitHub REST API
  - `GET /repos/a2aproject/A2A/pulls?state=all&per_page=100`
  - `GET /repos/a2aproject/A2A/pulls/{number}/reviews`
  - `GET /repos/a2aproject/A2A/pulls/{number}/comments`

**Where:** `data/raw/a2a_prs.json`
**Record count:** 1,955 records
**Fields:** `author`, `date`, `raw_text`, `source` (`"pr"`, `"review"`, `"pr_review_comment"`), `pr_number` or `pr_url`

**Important nuance:** `issue_comment` and `pr_review_comment` records use `issue_url` / `pr_url`
(GitHub API URL strings like `https://api.github.com/repos/a2aproject/A2A/issues/169`) rather
than a bare `issue_number` / `pr_number`. The network builder (`scripts/build_network.py`,
lines 96–107) uses a regex `r"/pulls/(\d+)"` / `r"/issues/(\d+)"` to extract the thread ID.

---

### 1.5 Google A2A: GitHub Discussions

**What:** All GitHub Discussion threads, comments, and replies from `a2aproject/A2A`.

**How:**
- Script: `scripts/scrape/scrape_a2a_discussions.py`
- Method: GitHub **GraphQL** API (REST API does not support Discussions)
- Endpoint: `POST https://api.github.com/graphql`
- Paginated using `after` cursor; fetches discussion bodies → comments → replies in nested pages
- Manifest updated: `data/raw/a2a_manifest.json`

**Where:** `data/raw/a2a_discussions.json`
**Record count:** 822 records total
  - 234 discussion bodies (`source = "discussion"`)
  - 325 comments (`source = "discussion_comment"`)
  - 263 replies (`source = "discussion_reply"`)
**Records with text ≥ 20 chars (eligible for annotation):** 802

---

### 1.6 Google A2A: TSC Git-Vote PRs

**What:** Complete data (all comments, reviews, review comments, bot messages) for the two
PRs that triggered formal Technical Steering Committee votes.

**Why separate:** These are analytically critical governance escalation events and needed
complete capture (including git-vote bot messages that contain vote tallies).

**How:**
- Script: `scripts/scrape/scrape_gitvote_prs.py`
- Same REST API calls as `scrape_erc8004_prs.py` but targeted at `a2aproject/A2A`

**Where:** `data/raw/a2a_gitvote_prs.json`
**Record count:** 142 records
  - PR #831 (tasks/list method, PASSED): 81 records
  - PR #1206 (lastUpdateTime field, CLOSED/SUPERSEDED): 61 records

---

### 1.7 Author Profiles

**Forum profiles:**
- Script: `scripts/process/enrich_profiles.py`
- Method: `GET https://ethereum-magicians.org/u/{username}.json` (public Discourse API)
- Where: `data/raw/profiles_forum.json`
- Coverage: 58/60 accounts found; 12% bio hit rate (7 accounts had non-empty bio)

**GitHub profiles:**
- Script: `scripts/process/enrich_profiles.py`
- Method: `GET https://api.github.com/users/{username}` (PAT authenticated)
- Scope: all 11 ERC-8004 GitHub authors + top 30 A2A human authors
- Where: `data/raw/profiles_github.json`
- Coverage: 37/39 accounts found; 43% company field hit rate (16 accounts)

---

## 2. Data Processing

### 2.1 LLM Annotation

**Script:** `scripts/process/annotate_llm.py`
**Backend used:** MiniMax-M2.5 via `https://api.minimaxi.com/v1` (OpenAI-compatible endpoint)
**Input files:** `forum_posts.json`, `github_comments_filtered.json`, `a2a_issues.json`,
`a2a_prs.json`, `a2a_discussions.json`
**Output:** `data/annotated/annotated_records.json`

**What the LLM annotates per record:**
- `stakeholder_institution`: Google | Coinbase | MetaMask | Ethereum Foundation | Independent | Unknown
  — inferred from author handle, post body, employer clues (annotate_llm.py, lines 61–78)
- `argument_type`: Technical | Economic | Governance-Principle | Process | Off-topic
  (annotate_llm.py, lines 61–78)
- `stance`: Support | Oppose | Modify | Neutral | Off-topic
  (annotate_llm.py, lines 61–78)
- `consensus_signal`: Adopted | Rejected | Pending | N/A
  (annotate_llm.py, lines 61–78)
- `key_point`: ≤20 word summary

**Filtering before annotation:** Records with `raw_text` shorter than 20 characters are
skipped (annotate_llm.py, lines 95–96 in `annotate_openai_compat`).

**MiniMax reasoning output:** MiniMax-M2.5 is a reasoning model. Responses begin with
`<think>...</think>` blocks. These are stripped via regex before JSON parsing
(annotate_llm.py, lines 116–118).

**Resume mechanism:** The script checks `_record_id()` (composite of `_case + source + id + date`,
annotate_llm.py lines 278–279) against already-annotated records, skipping duplicates. Safe
to interrupt and restart.

**Git-vote records:** Annotated separately by `scripts/process/annotate_gitvote.py`, then appended
to `annotated_records.json`. Same MiniMax-M2.5 backend.

**Total records annotated (as of 2026-03-15):**
- ERC-8004: 149
- Google A2A: 5,272 (complete; includes 822 discussion records)

---

### 2.2 Institution Label Upgrade

**Script:** `scripts/process/enrich_institutions.py`
**Logic (priority cascade):**
1. EIP header email (`eip_header_email`) — highest confidence; parsed from EIP document header
2. R07 manual investigation (`manual_R07`) — confirmed/strong/probable; see §2.2a below
3. GitHub company field — regex match against `INSTITUTION_PATTERNS`
4. GitHub bio — same patterns
5. Forum bio (`bio_raw`) — same patterns
6. LLM-inferred label from annotation — fallback

**9 accounts upgraded from profile data (enrich_institutions.py):**
- `MarcoMetaMask` → MetaMask (GitHub company field)
- `holtskinner` → Google (GitHub company field)
- `darrelmiller` → Microsoft (GitHub company field)
- `Tehsmash` → Cisco (GitHub company field — was labeled Independent by LLM)
- `pstephengoogle` → Google (GitHub bio: "Googler")
- `kthota-g` → Google (GitHub company field)
- `SumeetChougule` → Nethermind (forum bio: "ChaosChain at Nethermind")
- `lightclient` → Ethereum Foundation (GitHub bio)
- `davidecrapis.eth` / `dcrapis` → Ethereum Foundation (EIP header email; was Olas/Valory)

**Output:** `data/annotated/author_profiles.json` — one entry per unique author
(628 total: 69 active ERC-8004 + 2 silent EIP co-authors + 557 A2A human authors)

**ERC-8004 co-author profiles (0 discussion records):**
- `jordanellis` — Jordan Ellis, Google (`jordanellis@google.com`, EIP header)
- `erikreppel` — Erik Reppel, Coinbase (`erik.reppel@coinbase.com`, EIP header)

These two individuals are listed as formal EIP co-authors but left no public discussion
records. Their profiles are included for completeness and to enable co-authorship-level
institutional analysis, but they do not appear in any record-level statistics.

---

### 2.2a R07 Manual Institution Investigation

**Script:** `scripts/process/extract_manual_institutions.py` (parses R07 markdown → JSON),
`scripts/process/merge_manual_institutions.py` (merges into author_profiles.json)

**Input:** `reports/R07_2026-03-14_institution_investigation.md`
**Output:** `data/raw/manual_institutions.json` (116 entries), updated `author_profiles.json`

**Result:** 109 authors matched; 40 institution upgrades applied
- Confirmed: 92 authors | Strong: 7 | Probable: 10 | LM_inferred: 517 (remaining)
- 2 LM correction overrides: `dgenio` (Google → nosportugal), `CAG-nolan` (Google → Unknown)
- `institution_lm` field retained alongside `institution_final` for all records (never overwritten)

**Provenance fields in author_profiles.json:**
- `institution_final`: authoritative institution label used in analysis
- `institution_source`: `eip_header_email` | `manual_R07` | `github_company_field` | `lm_inferred`
- `institution_confidence`: `Confirmed` | `Strong` | `Probable` | `LM_inferred`
- `institution_lm`: original LLM-inferred label (always preserved)
- `institution_evidence`: URL or rationale for manual attributions

**Coding rule — participation capacity over organizational affiliation:**
`stakeholder_institution` measures the *capacity in which a person participates in this
governance process*, not merely their employer. A contributor is labeled with a named
institution only when that institution is a **major stakeholder in the specific governance
object** (e.g., Google employees commenting on A2A; MetaMask employees commenting on
ERC-8004). Contributors whose employer has no direct stake in the governance object are
coded `Independent` regardless of what their GitHub company field says.

Example: `felixnorden` lists "ignio" and a university on GitHub. Because neither has any
institutional role in ERC-8004 governance, he is coded `Independent`. This is distinct
from `MarcoMetaMask`, whose employer (MetaMask) is a primary stakeholder in the ERC-8004
trust layer. The rule prevents artificially inflating institutional diversity with
unrelated affiliations, and keeps the `stakeholder_institution` variable interpretable as
a measure of *institutional power concentration* rather than occupational background.

---

### 2.3 Core Contributor Identification

**Script:** `scripts/analyse/identify_core_contributors.py`
**Selection criteria:**
- ERC-8004: ≥3 records OR participates in ≥2 distinct threads (script lines ~45–60)
- A2A: ≥50 records (human only, bots excluded)

**Output:** `analysis/core_contributors.csv`
- 22 ERC-8004 core contributors
- 11 A2A core contributors (the threshold of ≥50 records selects the top tier)

**Cross-case overlap:** `analysis/cross_case_overlap.csv`
- 1 confirmed human overlap (voidcenter) based on GitHub handle match

---

### 2.4 Git-Vote Analysis

**Script:** `scripts/process/annotate_gitvote.py`
**Output:** `analysis/gitvote_analysis.md` — comprehensive governance interpretation of both
TSC-voted PRs, including vote tally parsing, timeline reconstruction, and theoretical implications.

---

### 2.5 Network Construction

**Script:** `scripts/visualise/build_network.py`
**ERC-8004 network:**
- Nodes: 74 (unique human authors + 7 PR supernodes, sized by record count, colored by institution)
- Edges: 65
  - Directed reply edges: forum reply chain (`reply_to_post_number` field), colored by post-level stance
  - Quote edges: dotted purple, from `quoted_post_numbers` field
  - PR supernodes: gold diamond nodes (7 of 9 core PRs — #1470 and #1488 have zero human participants)

**A2A network:**
- Nodes: 50 (natural elbow cutoff at contribution count ≥ 13; `find_elbow_cutoff()` returns 50)
- Edges: 217 (co-participation in same PR/issue/discussion thread)

**Why 7 PR supernodes (not 9):** PRs #1470 and #1488 contain only bot activity after filtering.
No human participants → no supernode generated. Verified: `PR #1470: 0 human`, `PR #1488: 0 human`.

**Thread key extraction for A2A** (build_network.py): Uses regex `r"/pulls/(\d+)"` /
`r"/issues/(\d+)"` on `pr_url` / `issue_url` fields because A2A comment records do not
contain bare thread ID integers.

**Output:** `output/network_erc8004.html`, `output/network_a2a.html`, `output/network_compare.html`
Also: `analysis/network_edges_erc8004.csv`, `analysis/network_edges_a2a.csv`,
`analysis/network_nodes_erc8004.csv`, `analysis/network_nodes_a2a.csv`

---

## 3. Final Metrics

### 3.1 Structural Metrics (from raw data, no annotation required)

**Script:** `scripts/analyse/compute_metrics.py`

| Metric | Value | How computed | Script location |
|--------|-------|--------------|-----------------|
| ERC-8004 proposal date | 2025-08-13 | Hardcoded from public record | compute_metrics.py, line 52 |
| ERC-8004 mainnet merge date | 2026-01-29 | Hardcoded from public record | compute_metrics.py, line 53 |
| ERC-8004 days to consensus | **169 days** | `ERC8004_MAINNET - ERC8004_PROPOSAL` | compute_metrics.py, line 93 |
| ERC-8004 total discussion records | 149 | `len(df)` after loading forum + GitHub | compute_metrics.py, lines 77–79 |
| ERC-8004 unique contributors | 69 (non-bot) | `df["author"].nunique()` | compute_metrics.py, line 81 |
| ERC-8004 forum posts | 113 | Count of `source == "forum"` | compute_metrics.py, line 108 |
| ERC-8004 forum reply rate | 0.726 | `reply_count / len(forum_df)` | compute_metrics.py, lines 89–90 |
| A2A first public commit | 2025-03-25 | From `a2a_commits.json` sorted dates | compute_metrics.py, line 136 |
| A2A public announcement | 2025-04-09 | Hardcoded from Google blog post | compute_metrics.py, line 55 |
| A2A total discussion records | 5,272 | `len(issues) + len(prs with text) + len(discussions)` | compute_metrics.py, lines 125–130 |
| A2A unique discussion contributors | 771 (non-bot) | `df["author"].nunique()` | compute_metrics.py, line 130 |
| A2A total commits | 522 | `len(commits)` | `data/raw/a2a_commits.json` |
| A2A PR merge rate | ~0.65 | `merged / len(actual_prs)` | compute_metrics.py, lines 141–143 |

---

### 3.2 Annotation-Based Metrics

**Script:** `scripts/analyse/compute_metrics.py`, function `compute_annotated_metrics()`
(lines 172–209)

**Openness index formula** (lines 199–201):
```python
outside = df[df["stakeholder_institution"] != initiating_org]["author"].nunique()
total = df["author"].nunique()
openness = round(outside / total, 3)
```

| Metric | ERC-8004 | Google A2A |
|--------|----------|-----------|
| Openness index | **1.000** | **0.956** |
| Initiating org used | "Ethereum Foundation" | "Google" |

**Note on ERC-8004 openness = 1.000:** The LLM classified the EF editorial role
(`lightclient`) as Independent because his editorial presence is minimal (2 records)
and the proposer (`davidecrapis.eth`) is from Olas/Valory, not EF. The index reflects
annotated attribution, not formal affiliation.

---

### 3.3 Argument Type Distribution

**Source:** LLM annotation, `annotated_records.json`, `argument_type` field
**Reported as:** proportion of records per case with text ≥ 20 chars and non-null annotation

| Argument Type | ERC-8004 (N=149) | Google A2A (N=5,272) |
|---------------|:-----------------:|:---------------------:|
| Technical | **74.3%** | 62.7% |
| Process | 13.9% | **28.4%** |
| Governance-Principle | 4.9% | 1.7% |
| Off-topic | 4.2% | 7.0% |
| Economic | 2.8% | 0.1% |

**How computed:** LLM annotation field `argument_type` per record.
Percentages calculated from `value_counts()` in `compute_metrics.py` line 206.

---

### 3.4 Stance Distribution

**Source:** LLM annotation, `stance` field

| Stance | ERC-8004 (N=149) | Google A2A (N=5,272) |
|--------|:-----------------:|:---------------------:|
| Neutral | 31.9% | 46.7% |
| Support | 30.6% | 24.1% |
| Modify | 29.2% | 21.8% |
| Oppose | **6.9%** | 2.7% |
| Off-topic | 1.4% | 4.5% |

**How computed:** LLM annotation field `stance` per record.
`compute_metrics.py` line 207.

---

### 3.5 Institution Breakdown (record-level)

**Source:** `author_profiles.json` → `institution_final` field (3-tier provenance; R07 manual
data applied). Computed from annotated records (5,421 total).

**ERC-8004 (149 records, post-R07):**

| Institution | Records | % of total |
|-------------|:-------:|:----------:|
| Independent | ~66 | **44.4%** |
| Unknown | ~20 | 13.3% |
| MetaMask | ~19 | **12.6%** |
| Ethereum Foundation | ~15 | 10.4% |
| Edge and Node / The Graph Protocol | ~9 | 5.9% |
| Hats Protocol | ~6 | 3.7% |
| Nethermind | ~4 | 3.0% |
| Other named institutions | ~10 | 6.7% |

**Google A2A (5,272 records, post-R07):**

| Institution | Records | % of total |
|-------------|:-------:|:----------:|
| Independent | ~2,326 | **44.1%** |
| Google | ~1,318 | **25.0%** |
| Unknown | ~794 | 15.1% |
| Microsoft | ~495 | 9.4% |
| Cisco | ~200 | 3.8% |
| Other named institutions | ~139 | 2.6% |

**Key finding:** Independent contributor share is nearly identical across cases (~44%). Institutional
concentration differs: top institution is 12.6% (ERC-8004) vs. 25.0% (A2A). Google alone exceeds
2× the most active ERC-8004 institution.

**Note on ERC-8004 openness:** After R07, `davidecrapis.eth`/`dcrapis` is attributed to Ethereum
Foundation (EIP header email), not Olas/Valory. Openness index recalculated from author_profiles.json.

---

### 3.6 Core Contributor Metrics

**Source:** `analysis/core_contributors.csv`

**ERC-8004 formal co-authors (per EIP header):**
- `dcrapis` / `davidecrapis.eth` (Ethereum Foundation) — 9 records (proposer, active)
- `MarcoMetaMask` (MetaMask) — 17 records (most active contributor)
- `jordanellis` (Google) — **0 records** (co-author, silent)
- `erikreppel` (Coinbase) — **0 records** (co-author, silent)

**ERC-8004 top contributors (by record count, post-R07):**
- `MarcoMetaMask` (MetaMask): 17 records — 12.6% by institution; highest individual
- `pcarranzav` (The Graph): 16 records — primary technical critic; highest Modify+Oppose rate
- `davidecrapis.eth` + `dcrapis` (Ethereum Foundation): 9 records combined — EIP proposer
  (R07: attributed via EIP header email domain; was Olas/Valory from forum bio)
- `lightclient` (Ethereum Foundation): 7 records — ERC editor; minimal authority footprint
- `spengrah` (Hats Protocol): 5 records
- `felixnorden` (Independent): 5 records

**Google A2A top contributors (by record count, post-R07):**
- `holtskinner` (Google): ~560 records — ~10% of all A2A records
- `darrelmiller` (Microsoft): 286+ records — IETF HTTPAPI WG Chair + LF A2A TSC member
  (single institutional bridge between corporate and formal standards infrastructure)
- `kthota-g` (Google): 152 records
- `Tehsmash` (Cisco): 118 records — corrected via GitHub profile (was Independent by LLM)
- `pstephengoogle` (Google): 113 records

**Author concentration metric (ERC-8004):**
No single actor exceeds 13% of records (MetaMask institution: 12.6%; top individual: 11.4%).
No single actor controls more than 15% of total records.

---

### 3.7 Governance Escalation Events (TSC Votes)

**Source:** `data/raw/a2a_gitvote_prs.json`, `analysis/gitvote_analysis.md`
**Annotated by:** `scripts/process/annotate_gitvote.py` → 49 records appended to `annotated_records.json`

| PR | Topic | Vote outcome | Records | Key dynamic |
|----|-------|--------------|---------|-------------|
| #831 | tasks/list method | PASSED | 81 | Vote called after 4 months; formalized near-consensus |
| #1206 | lastUpdateTime field | CLOSED/SUPERSEDED | 61 | Decision moved to private TSC call + Discord; public record incomplete |

**PR #1206 governance failure:**
The `/cancel-vote` was issued after the TSC meeting on 2026-01-06 (offline, not in GitHub record).
Discussion migrated to Discord (permanent record loss). This is the most analytically significant
case of off-platform governance in the dataset.

---

### 3.8 Network Metrics

**Source:** `output/network_erc8004.html`, `analysis/network_edges_erc8004.csv`

| Metric | ERC-8004 | Google A2A (top 50) |
|--------|----------|---------------------|
| Nodes | 74 (67 authors + 7 PR supernodes) | 50 |
| Edges | 65 | 217 |
| Directed reply edges (forum) | ~34 | — |
| Quote edges (dotted purple) | ~7 | — |
| Co-participation edges | ~24 | 217 |

---

## 4. Data Integrity

**SHA-256 checksums:** `data/raw/CHECKSUMS.json`, `data/annotated/CHECKSUMS.json`
**Last regenerated:** 2026-03-15 (after R07 institution merge changed `author_profiles.json`).
Current `author_profiles.json` hash: `ae373cf9...`; `annotated_records.json` hash: `99ebfd47...`.

Regeneration command (from workspace root):
```bash
uv run python -c "
import json, hashlib
from pathlib import Path
for d in ['data/raw', 'data/annotated']:
    raw = Path(d)
    m = {f.name: {'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
         for f in sorted(raw.glob('*.json')) if f.name != 'CHECKSUMS.json'}
    (raw / 'CHECKSUMS.json').write_text(json.dumps(m, indent=2))
    print(f'Updated {d}/CHECKSUMS.json ({len(m)} files)')
"
```

---

## 5. Known Limitations and Data Quality Issues

1. **LLM annotation errors:** MiniMax-M2.5 institution inference contains known errors.
   R07 manual investigation corrected 40 institution labels across 109 matched authors.
   517 authors remain LLM-inferred; residual error rate is unquantified but expected to be
   low for top contributors (manually verified) and higher for long-tail contributors.

3. **Off-platform governance (A2A):** PR #1206's substantive decision occurred in a private
   TSC call and on Discord. The public GitHub record for A2A is systematically incomplete
   when governance is most contested. ERC-8004 has no equivalent off-platform governance.

4. **Cross-case identity:** Only 1 confirmed author appears in both cases (voidcenter).
   Additional overlaps may exist under different handles. The `analysis/cross_case_overlap.csv`
   is based on GitHub handle matching only.

5. **Survivorship bias:** Both cases are successful. Failed DAO governance processes and
   failed corporate protocol attempts are not in scope.

6. **Scale asymmetry:** ERC-8004 has 149 records; A2A has 5,272. Proportional statistics
   (% distributions) are more comparable than raw counts.

7. **Institution coding ambiguity — participation capacity vs. employer:**
   `stakeholder_institution` is coded by participation capacity (whether the institution
   has direct stake in the governance object), not by GitHub company field. Contributors
   affiliated with organizations irrelevant to the governance process are coded
   `Independent`. This decision is documented in §2.2 above and the inter-rater codebook
   (`verification/INTER_RATER_GUIDE.md`, §3.4). Reviewers should note that κ for this
   field may be lower than for `argument_type` and `stance` because the boundary between
   `Independent` and named institutions requires domain knowledge of the ecosystem.

---

*End of documentation.*
