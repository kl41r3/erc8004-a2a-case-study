# data/

## raw/ — Original scraped data (do not edit manually)

| File | Description | Records |
|------|-------------|---------|
| `forum_posts.json` | ERC-8004 Ethereum Magicians forum posts. Includes `own_text` (quote-stripped), `quoted_post_numbers`, `reply_to_post_number`. | 113 |
| `github_comments_filtered.json` | ERC-8004 PR bodies, issue comments, review comments, reviews for 9 core lifecycle PRs (#1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488). | 36 |
| `a2a_commits.json` | Google A2A repository commits. | 522 |
| `a2a_issues.json` | A2A GitHub issues and issue comments. | 3,104 |
| `a2a_prs.json` | A2A GitHub PRs and PR review comments. | 1,955 |
| `a2a_discussions.json` | A2A GitHub Discussions (GraphQL). | 822 |
| `a2a_gitvote_prs.json` | Full data for TSC-voted PRs #831 (passed) and #1206 (superseded). | 142 |
| `profiles_forum.json` | Discourse profile data for ERC-8004 forum authors (bio, title, groups). | 60 accounts |
| `profiles_github.json` | GitHub profile data for ERC-8004 and top-30 A2A authors (company, bio, location). | 39 accounts |
| `manual_institutions.json` | Structured output of R07 manual institution investigation. 116 entries with provenance fields (`institution_source`, `confidence`, `evidence_url`). | 116 |
| `erc-8004_manifest.json` | Scrape metadata for ERC-8004 data. | — |
| `a2a_manifest.json` | Scrape metadata for A2A data. | — |
| `filter_log.json` | Log of PR keep/discard decisions in ERC-8004 filtering step. | — |
| `CHECKSUMS.json` | SHA-256 checksums for all raw files. | — |

## annotated/ — LLM-annotated and manually enriched

| File | Description | Records |
|------|-------------|---------|
| `annotated_records.json` | All records with LLM annotations: `stakeholder_institution`, `argument_type`, `stance`, `consensus_signal`, `key_point`. | 5,421 |
| `author_profiles.json` | One entry per unique canonical author (626 total). Institution provenance fields: `institution_final`, `institution_source`, `institution_confidence`, `institution_lm`, `institution_evidence`. 107 authors enriched from R07 manual data; 2 from EIP header email. | 626 |
| `CHECKSUMS.json` | SHA-256 checksums for annotated files. | — |

### Institution data provenance (author_profiles.json)

| Source | Authors | Confidence |
|--------|---------|------------|
| `eip_header_email` | 2 | Confirmed |
| `manual_R07` | 107 | Confirmed/Strong/Probable |
| `lm_inferred` | 517 | LM_inferred |
