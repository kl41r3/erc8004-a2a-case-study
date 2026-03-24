# Data Collection — LLM Annotation

**Status:** DONE
**Script:** `scripts/annotate_llm.py --backend minimax`

## What was done

All 5,421 records annotated with MiniMax-M2.5 reasoning model. Each record received four labels:
- `stakeholder_institution`: Google | MetaMask | Ethereum Foundation | Coinbase | Independent | Unknown
- `argument_type`: Technical | Economic | Governance-Principle | Process | Off-topic
- `stance`: Support | Oppose | Modify | Neutral | Off-topic
- `consensus_signal`: Adopted | Rejected | Pending | N/A
- `key_point`: ≤20-word summary

Institution labels follow a three-tier cascade: (1) EIP header email → (2) R07 manual investigation (109 authors) → (3) LLM inference (517 authors).

## Results

- Annotated: 5,416 / 5,421 (99.9%)
- Output: `data/annotated/annotated_records.json`

Argument type distribution:

| Type | Count |
|------|-------|
| Technical | 3,517 |
| Process | 1,359 |
| Off-topic | 409 |
| Governance-Principle | 109 |
| Economic | 13 |

## Limitations

- Inter-coder reliability (Cohen's κ) not yet computed — needed before submission
- 517 of 626 unique authors have LLM-inferred institution labels; 109 manually verified (R07 investigation corrected 40 labels)
- 5 records failed annotation (text too short or JSON parse error)
