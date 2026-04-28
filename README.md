# Decentralized Paradox: DAO Governance vs. Corporate Governance

Comparative case study of two AI protocol governance processes:

- **ERC-8004** ("Trustless Agents", Ethereum Improvement Proposal, 2025–2026) — permissionless DAO governance
- **Google A2A** (Agent-to-Agent protocol, 2025–present) — corporate-led governance

---

## Project Structure

```
workspace/
├── scripts/
│   ├── scrape/       # Data collection
│   ├── process/      # Filtering, annotation, enrichment
│   ├── analyse/      # Metrics and statistical analysis
│   └── visualise/    # Visualization builders
├── data/
│   ├── raw/          # Original scraped data (do not edit manually)
│   └── annotated/    # LLM-annotated records and author profiles
├── output/
│   ├── network_discourse/   # DNA + socio-semantic results
│   └── topic_discovery/     # Thematic-LM + comparative-discourse results
└── paper.pdf         # Latest compiled manuscript
```

---

## Environment

Create a local `.env` (ignored by git) with:

```
GITHUB_PERSONAL_ACCESS_TOKEN=...
MINIMAX_API_KEY=...
```
