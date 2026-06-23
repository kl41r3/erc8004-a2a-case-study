# Method 2b — CryptoBERT Domain-Adapted Embedding Validation

## What was done
Re-embedded ERC-8004 records using ElKulako/cryptobert (RoBERTa-based model pre-trained on 3.2M crypto social-media posts) to validate that the Trust & Security discourse concentration found by all-MiniLM-L6-v2 (Method 2) is robust to domain-adapted embeddings, not an artefact of general-purpose encoding.

## Method
- **Model**: `ElKulako/cryptobert` (BERTweet base, fine-tuned on StockTwits/Reddit/Telegram/Twitter crypto posts)
- **Embeddings**: mean pooling over non-padding hidden states, L2-normalized, 768-dim, 128-token truncation
- **Scope**: ERC-8004 only (n=142) — A2A is corporate/GitHub context, not crypto domain
- **BERTopic params**: UMAP(n_neighbors=10, n_components=5, cosine, seed=42) + HDBSCAN(min_cluster_size=5, min_samples=3) + CountVectorizer(stop_words=english, ngram_range=(1,2))
- **Script**: `scripts/analyse/topic_discovery/crypto_bert/run.py`

## Results

| Topic | Keywords | Count | % |
|-------|----------|-------|---|
| 0 | agents, agent, onchain, reputation, registry | 76 | 53.5% |
| 2 | agent, trust, feedback, reputation, agent card | 28 | 19.7% |
| 4 | merge, uint256, github, pr, reviewers approved | 13 | 9.2% |
| 3 | file, reviewers, marcometamask, abcoathup | 9 | 6.3% |
| 1 | implementation, protocol, lightweight, discover | 7 | 4.9% |

- Noise: 9 records (6.3%)
- Topics 0+2 combined: 73.2% → agent/trust/reputation/onchain discourse

## Key Results
- **Convergence confirmed**: Topics 0+2 (73.2%) replicate Method 2's ERC-8004 Topic 0 concentration (67.6%)
- **Additional granularity**: CryptoBERT separates on-chain infrastructure layer (Topic 0: onchain, registry) from trust-negotiation layer (Topic 2: trust, feedback, agent card) — collapsed into one cluster by all-MiniLM-L6-v2
- **Crypto-native evidence**: "uint256" (Solidity type) appears in governance-process topic, confirming EIP reviewers evaluate implementation implications at spec stage
- **Named participants**: MetaMask, abcoathup surface as dominant stakeholders in review topic

## Limitations
- CryptoBERT max 128 tokens (short social media origin); EIP forum posts are longer → truncation may discard late technical arguments
- Training data (StockTwits, Twitter) is not governance-forum text — vocabulary overlap partial
- ERC-8004 corpus n=142 is small → wide confidence intervals on percentage estimates

## Output Files
- `output/topic_discovery/crypto_bert/topics.json` — 5-topic result with keywords and counts
- `output/topic_discovery/crypto_bert/comparison_summary.md` — auto-generated convergence narrative
- `output/topic_discovery/paper_sections.md` — LaTeX subsubsection added
