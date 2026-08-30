# NeurIPS 2026 non-visual robustness outputs

These tables support the NeurIPS 2026 robustness revision without generating
figures. No manuscript is distributed with this release.

Run from the repository root:

```bash
uv run python scripts/analyse/run_neurips26_robustness.py
```

The script uses the frozen 142-record ERC-8004 and 4,181-record A2A manifest. It
separates that primary denominator from the later 4,230-record filtered archive.
Outputs cover corpus-stage reconciliation, equal-size bootstrap intervals,
channel and quarterly composition, and tie-threshold sensitivity. All results
are descriptive. The cross-platform network edges remain platform-specific and
are not treated as a harmonized relation.

`summary.json` records the seed, repetition count, denominators, and output
inventory. No file in this directory is a human gold-standard validation result.
