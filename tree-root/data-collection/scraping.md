# Data Collection — Scraping

**Status:** DONE
**Scripts:** `scripts/scrape_erc8004.py`, `scripts/scrape_a2a.py`, `scripts/patch_a2a_missing_pages.py`

## What was done

Scraped all public governance records for both cases:

- **ERC-8004:** 113 Ethereum Magicians forum posts (topic 25098, Discourse JSON API) + GitHub records from the `ethereum/EIPs` repo
- **Google A2A:** issues, PRs, PR review comments, GitHub Discussions via GitHub REST + GraphQL APIs; GitVote PRs (#831, #1206) scraped separately via `a2a_gitvote_prs.json`

## Results

| File | Records |
|------|---------|
| `data/raw/forum_posts.json` | 113 |
| `data/raw/github_comments_filtered.json` | 36 (post-filter) |
| `data/raw/a2a_issues.json` | ~500 issues |
| `data/raw/a2a_prs.json` | 1,955 PRs |
| `data/raw/a2a_discussions.json` | 234 discussions |
| `data/raw/a2a_gitvote_prs.json` | 2 TSC-voted PRs |

## Limitations

- ERC-8004 has no on-chain or Snapshot vote records; governance is forum discussion + GitHub editor approval only
- GitHub search API initially returned 149 PR results for ERC-8004 (many false positives from `Requires: ERC-8004`); filtered down to 9 core lifecycle PRs
- Some A2A pages timed out and were recovered by `patch_a2a_missing_pages.py`
- All HTTP done via `subprocess` + `curl` due to SSL EOF errors with Python `requests` against `ethereum-magicians.org`
