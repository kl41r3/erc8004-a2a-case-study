# Data Collection — Filtering

**Status:** DONE
**Script:** `scripts/filter_github.py`

## What was done

Whitelisted only the 9 GitHub PRs that directly modify `ERCS/erc-8004.md` or change its lifecycle status. All other PRs mentioning ERC-8004 (ecosystem ERCs with `Requires: ERC-8004`) were excluded.

Core lifecycle PRs retained: `#1170, #1244, #1248, #1458, #1462, #1470, #1472, #1477, #1488`

## Results

- Raw GitHub search results: 149 PRs → filtered to 36 records across 9 PRs
- Filter log: `data/raw/filter_log.json`
- Filtered output: `data/raw/github_comments_filtered.json`

## Limitations

- `#1470` and `#1488` contain only bot activity (no human participants)
- The 9-PR whitelist is manually curated; any missed PRs would not be recovered automatically
