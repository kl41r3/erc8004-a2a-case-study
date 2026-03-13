# Data Collection, Processing, and Metrics — Full Documentation

**Audience:** Researcher (for personal verification)
**Generated:** 2026-03-13
**Status:** Discussion annotation still in progress (~120/802 records complete as of writing);
all other data is final.

---

## 1. Data Collection

### 1.1 ERC-8004: Ethereum Magicians Forum

**What:** All posts from the Ethereum Magicians forum thread for ERC-8004 (Trustless Agents).

**How:**
- Script: `scripts/scrape_erc8004_forum.py`
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
- Script: `scripts/scrape_erc8004_prs.py`
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
- Script: `scripts/scrape_a2a.py`
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
- Script: `scripts/scrape_a2a.py` (same script as issues)
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
- Script: `scripts/scrape_a2a_discussions.py`
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
- Script: `scripts/scrape_gitvote_prs.py`
- Same REST API calls as `scrape_erc8004_prs.py` but targeted at `a2aproject/A2A`

**Where:** `data/raw/a2a_gitvote_prs.json`
**Record count:** 142 records
  - PR #831 (tasks/list method, PASSED): 81 records
  - PR #1206 (lastUpdateTime field, CLOSED/SUPERSEDED): 61 records

---

### 1.7 Author Profiles

**Forum profiles:**
- Script: `scripts/enrich_profiles.py`
- Method: `GET https://ethereum-magicians.org/u/{username}.json` (public Discourse API)
- Where: `data/raw/profiles_forum.json`
- Coverage: 58/60 accounts found; 12% bio hit rate (7 accounts had non-empty bio)

**GitHub profiles:**
- Script: `scripts/enrich_profiles.py`
- Method: `GET https://api.github.com/users/{username}` (PAT authenticated)
- Scope: all 11 ERC-8004 GitHub authors + top 30 A2A human authors
- Where: `data/raw/profiles_github.json`
- Coverage: 37/39 accounts found; 43% company field hit rate (16 accounts)

---

## 2. Data Processing

### 2.1 LLM Annotation

**Script:** `scripts/annotate_llm.py`
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

**Git-vote records:** Annotated separately by `scripts/annotate_gitvote.py`, then appended
to `annotated_records.json`. Same MiniMax-M2.5 backend.

**Total records annotated (as of 2026-03-13):**
- ERC-8004: 149
- Google A2A: ~4,800 (discussion annotation still in progress; 802 eligible from discussions)

---

### 2.2 Institution Label Upgrade

**Script:** `scripts/enrich_institutions.py`
**Logic (priority cascade):**
1. GitHub company field — regex match against `INSTITUTION_PATTERNS` (lines 53–68 and 102–105)
2. GitHub bio — same patterns (lines 107–110)
3. Forum bio (`bio_raw`) — same patterns (lines 113–116)
4. LLM-inferred label from annotation — fallback (lines 247–250)

**`INSTITUTION_PATTERNS`** (enrich_institutions.py, lines 53–68):
- `\bmetamask\b` → MetaMask
- `ethereum\s+foundation` → Ethereum Foundation
- `\bgoogle\b` → Google
- `\bmicrosoft\b` → Microsoft
- (and others)

**9 accounts upgraded from profile data:**
- `MarcoMetaMask` → MetaMask (GitHub company field)
- `holtskinner` → Google (GitHub company field)
- `darrelmiller` → Microsoft (GitHub company field)
- `Tehsmash` → Cisco (GitHub company field — was labeled Independent by LLM)
- `pstephengoogle` → Google (GitHub bio: "Googler")
- `kthota-g` → Google (GitHub company field)
- `SumeetChougule` → Nethermind (forum bio: "ChaosChain at Nethermind")
- `lightclient` → Ethereum Foundation (GitHub bio)
- `davidecrapis.eth` / `dcrapis` → Olas/Valory (forum bio)

**Output:** `data/annotated/author_profiles.json` — one entry per unique author
(626 total: 71 ERC-8004 + 560+ A2A human authors)

---

### 2.3 Core Contributor Identification

**Script:** `scripts/identify_core_contributors.py`
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

**Script:** `scripts/annotate_gitvote.py`
**Output:** `analysis/gitvote_analysis.md` — comprehensive governance interpretation of both
TSC-voted PRs, including vote tally parsing, timeline reconstruction, and theoretical implications.

---

### 2.5 Network Construction

**Script:** `scripts/build_network.py`
**ERC-8004 network:**
- Nodes: 67 (unique authors, sized by record count, colored by institution)
- Edges: 42
  - Solid edges: forum reply chain (`reply_to_post_number` field, lines ~120–140)
  - Dashed edges: GitHub co-participation (both commented on same PR, lines ~140–165)

**A2A network:**
- Nodes: 50 (top 50 by record count, human only)
- Edges: 243 (all dashed — co-participation in same PR/issue/discussion thread)

**Thread key extraction for A2A** (build_network.py, lines 96–107): Uses regex
`r"/pulls/(\d+)"` / `r"/issues/(\d+)"` on `pr_url` / `issue_url` fields because A2A
comment records do not contain bare thread ID integers.

**Output:** `output/network_erc8004.html`, `output/network_a2a.html`
Also: `analysis/network_edges_erc8004.csv`, `analysis/network_edges_a2a.csv`,
`analysis/network_nodes_erc8004.csv`, `analysis/network_nodes_a2a.csv`

---

## 3. Final Metrics

### 3.1 Structural Metrics (from raw data, no annotation required)

**Script:** `scripts/compute_metrics.py`

| Metric | Value | How computed | Script location |
|--------|-------|--------------|-----------------|
| ERC-8004 proposal date | 2025-08-13 | Hardcoded from public record | compute_metrics.py, line 52 |
| ERC-8004 mainnet merge date | 2026-01-29 | Hardcoded from public record | compute_metrics.py, line 53 |
| ERC-8004 days to consensus | **169 days** | `ERC8004_MAINNET - ERC8004_PROPOSAL` | compute_metrics.py, line 93 |
| ERC-8004 total discussion records | 149 | `len(df)` after loading forum + GitHub | compute_metrics.py, lines 77–79 |
| ERC-8004 unique contributors | 71 | `df["author"].nunique()` | compute_metrics.py, line 81 |
| ERC-8004 forum posts | 113 | Count of `source == "forum"` | compute_metrics.py, line 108 |
| ERC-8004 forum reply rate | 0.726 | `reply_count / len(forum_df)` | compute_metrics.py, lines 89–90 |
| A2A first public commit | 2025-03-25 | From `a2a_commits.json` sorted dates | compute_metrics.py, line 136 |
| A2A public announcement | 2025-04-09 | Hardcoded from Google blog post | compute_metrics.py, line 55 |
| A2A total discussion records | 5,059+ | `len(issues) + len(prs with text)` | compute_metrics.py, lines 125–130 |
| A2A unique discussion contributors | 600+ | `df["author"].nunique()` | compute_metrics.py, line 130 |
| A2A total commits | 522 | `len(commits)` | `data/raw/a2a_commits.json` |
| A2A PR merge rate | ~0.65 | `merged / len(actual_prs)` | compute_metrics.py, lines 141–143 |

---

### 3.2 Annotation-Based Metrics

**Script:** `scripts/compute_metrics.py`, function `compute_annotated_metrics()`
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

| Argument Type | ERC-8004 (N=144) | Google A2A (N=4,391) |
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

| Stance | ERC-8004 (N=144) | Google A2A (N=4,391) |
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

**Source:** LLM annotation `stakeholder_institution` field, upgraded by `enrich_institutions.py`
for 9 accounts (see section 2.2).

| Institution | ERC-8004 records | % | A2A records | % |
|-------------|:----------------:|---|:-----------:|---|
| Independent | 115 | 79.9% | 2,832 | 64.5% |
| Google | 0 | — | 990 | **22.6%** |
| MetaMask | 16 | **11.1%** | 0 | — |
| Unknown | 9 | 6.3% | 552 | 12.6% |
| Ethereum Foundation | 3 | 2.1% | 0 | — |
| Microsoft | 0 | — | 11 | 0.3% |

**Computed from:** `author_profiles.json` → institution_final merged back into
annotated records. The 22.6% Google record share vs. ~7.3% Google author share
indicates disproportionate per-person contribution intensity.

---

### 3.6 Core Contributor Metrics

**Source:** `analysis/core_contributors.csv`

**ERC-8004 top contributors (by record count):**
- `MarcoMetaMask` (MetaMask): 17 records — 11.4% of total; highest activity
- `pcarranzav` (Independent): 16 records — primary technical critic; Modify/Oppose rate ~19%
- `davidecrapis.eth` + `dcrapis` (Olas/Valory): 9 records combined — proposer
- `lightclient` (Ethereum Foundation): 7 records — ERC editor; minimal authority footprint

**Google A2A top contributors (by record count):**
- `holtskinner` (Google): 439 records — ~9% of all A2A records
- `darrelmiller` (Microsoft): 308 records — IETF HTTPAPI WG Chair + LF A2A TSC member
- `kthota-g` (Google): 152 records
- `Tehsmash` (Cisco): 118 records — labeled Independent by LLM; corrected via GitHub profile

**Author concentration metric (ERC-8004):**
Top contributor share: 11.4% — below the Gini threshold for monopoly control.
No single actor controls more than 15% of total records.

---

### 3.7 Governance Escalation Events (TSC Votes)

**Source:** `data/raw/a2a_gitvote_prs.json`, `analysis/gitvote_analysis.md`
**Annotated by:** `scripts/annotate_gitvote.py` → 49 records appended to `annotated_records.json`

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
| Nodes | 67 | 50 |
| Edges | 42 | 243 |
| Solid edges (forum reply) | 34 | — |
| Dashed edges (co-participation) | 8 | 243 |

---

## 4. Data Integrity

**SHA-256 checksums:** `data/raw/CHECKSUMS.json`, `data/annotated/CHECKSUMS.json`
**Note:** These need to be refreshed after discussion annotation completes.
Regeneration command (from workspace root):
```bash
python3 -c "
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

1. **Discussion annotation incomplete:** As of writing, ~120/802 eligible discussion records
   have been annotated. The annotation process is running. All discussion-based counts will
   be final once complete.

2. **LLM annotation errors:** MiniMax-M2.5 institution inference contains known errors.
   Example: `Tehsmash` (Cisco) was labeled Independent. Corrected for 9 accounts via
   profile data; others may remain wrong.

3. **Off-platform governance (A2A):** PR #1206's substantive decision occurred in a private
   TSC call and on Discord. The public GitHub record for A2A is systematically incomplete
   when governance is most contested. ERC-8004 has no equivalent off-platform governance.

4. **Cross-case identity:** Only 1 confirmed author appears in both cases (voidcenter).
   Additional overlaps may exist under different handles. The `analysis/cross_case_overlap.csv`
   is based on GitHub handle matching only.

5. **Survivorship bias:** Both cases are successful. Failed DAO governance processes and
   failed corporate protocol attempts are not in scope.

6. **Scale asymmetry:** ERC-8004 has 149 records; A2A has 5,600+. Proportional statistics
   (% distributions) are more comparable than raw counts.

---

*End of documentation.*
