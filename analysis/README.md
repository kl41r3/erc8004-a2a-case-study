# analysis/

All analysis outputs from the governance comparison pipeline. Three subdirectories
reflect the three analytical dimensions of the study.

```
analysis/
├── README.md                ← This file
├── metrics/                 Governance metrics, network topology, inter-coder reliability
│   ├── r1/                  R1 baseline (ERC-8004 vs A2A, single model)
│   ├── r2/                  R2 data expansion (34-ERC cluster, multi-model robustness)
│   └── institution_verification_checklist.csv   Manual institution audit trail
├── network_discourse/       Discourse Network Analysis (DNA) + Socio-semantic bipartite
│   ├── r1/                  R1 baseline results
│   └── r2/                  R2 expanded data results
└── topic_discovery/         Topic modeling (Thematic-LM, BERTopic, CryptoBERT)
    ├── r1/                  R1 baseline codebooks and distributions
    └── r2/                  R2 cross-model + cross-round results
```

Each subdirectory has its own README.md with a complete file inventory.

---

## metrics/

Quantitative outputs: governance indicators, network edge/node tables, and
inter-coder reliability results. See [`metrics/README.md`](metrics/README.md).
Key file: `institution_verification_checklist.csv` — manual audit trail of
network node institution assignments (194 ERC + 713 A2A actors).

## network_discourse/

Discourse Network Analysis (actor–actor congruence/conflict from shared stances)
and Socio-semantic bipartite network (actor × theme specialization and entropy).
See [`network_discourse/README.md`](network_discourse/README.md).

## topic_discovery/

Unsupervised topic discovery from governance text: Thematic-LM (LLM open coding),
BERTopic comparative discourse, and CryptoBERT domain validation.
See [`topic_discovery/README.md`](topic_discovery/README.md).
