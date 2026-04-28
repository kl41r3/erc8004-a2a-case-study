"""
CryptoBERT Domain-Adapted Topic Discovery — entry point.

Re-embeds ERC-8004 records using ElKulako/cryptobert (BERTweet fine-tuned on
3.2M crypto social-media posts) and runs BERTopic to validate that the
Trust & Security dominance found by all-MiniLM-L6-v2 (Method 2) is robust
to domain-adapted embeddings.

Scope: ERC-8004 only (A2A is corporate/GitHub context, not crypto).
Output:
    output/topic_discovery/crypto_bert/topics.json
    output/topic_discovery/crypto_bert/comparison_summary.md

Usage:
    uv run python scripts/analyse/topic_discovery/crypto_bert/run.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT))

DATA_PATH = ROOT / "data" / "annotated" / "annotated_records.json"
OUT_DIR = ROOT / "output" / "topic_discovery" / "crypto_bert"

BOT_AUTHORS = {
    "gemini-code-assist[bot]", "google-cla[bot]", "github-actions[bot]",
    "codecov[bot]", "dependabot[bot]", "git-vote[bot]",
}

# Method 2 (all-MiniLM-L6-v2) ERC-8004 slice results for comparison
METHOD2_ERC_RESULTS = {
    "global_jsd": 0.2880,
    "erc8004_topic0_pct": 67.6,
    "description": "Topic 0 (agent, agents, for, of): 67.6% of ERC-8004 records",
}


def load_erc8004_corpus() -> tuple[list[str], list[str]]:
    raw = json.loads(DATA_PATH.read_text())
    texts, ids = [], []
    for r in raw:
        if r.get("_case") != "ERC-8004":
            continue
        author = r.get("author", "")
        if author in BOT_AUTHORS or author.endswith("[bot]"):
            continue
        text = (r.get("raw_text") or "").strip()
        if len(text) < 20:
            continue
        record_id = f"ERC-8004_{r.get('source','?')}_{r.get('post_id') or r.get('id','?')}"
        texts.append(text[:512])  # cap at 512 chars; CryptoBERT truncates at 128 tokens anyway
        ids.append(record_id)
    return texts, ids


def compute_cryptobert_embeddings(texts: list[str]) -> "np.ndarray":
    import torch
    import numpy as np
    from transformers import AutoTokenizer, AutoModel

    print("  Loading ElKulako/cryptobert …")
    tokenizer = AutoTokenizer.from_pretrained("ElKulako/cryptobert")
    model = AutoModel.from_pretrained("ElKulako/cryptobert")
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    all_embeddings = []
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        encoded = {k: v.to(device) for k, v in encoded.items()}
        with torch.no_grad():
            output = model(**encoded)

        # Mean pooling over non-padding tokens
        attention_mask = encoded["attention_mask"]
        token_embeddings = output.last_hidden_state
        mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        summed = torch.sum(token_embeddings * mask_expanded, dim=1)
        counts = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        mean_embeddings = summed / counts

        # L2-normalize
        mean_embeddings = torch.nn.functional.normalize(mean_embeddings, p=2, dim=1)
        all_embeddings.append(mean_embeddings.cpu().numpy())

        if (i // batch_size) % 5 == 0:
            print(f"    Embedded {min(i + batch_size, len(texts))}/{len(texts)} records …")

    return np.vstack(all_embeddings)


def fit_bertopic(texts: list[str], embeddings: "np.ndarray", nr_topics: int = 10):
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer

    n = len(texts)
    print(f"  Fitting BERTopic on {n} ERC-8004 records …")

    umap_model = UMAP(
        n_neighbors=min(10, n - 1),
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=5,   # smaller than Method 2 to suit n≈140
        min_samples=3,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    # Filter stop words so c-TF-IDF labels are content-bearing
    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2)

    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        nr_topics=nr_topics,
        calculate_probabilities=False,
        verbose=True,
    )

    topics, _ = topic_model.fit_transform(texts, embeddings=embeddings)
    return topic_model, topics


def build_results(topic_model, topics: list[int], texts: list[str]) -> dict:
    import numpy as np
    from collections import Counter

    topic_counts = Counter(t for t in topics if t != -1)
    noise_count = sum(1 for t in topics if t == -1)
    total_valid = len(topics) - noise_count

    topic_info = topic_model.get_topic_info()
    topic_list = []
    for _, row in topic_info.iterrows():
        tid = row["Topic"]
        if tid == -1:
            continue
        keywords = [w for w, _ in topic_model.get_topic(tid)][:8]
        count = topic_counts.get(tid, 0)
        pct = round(100.0 * count / len(topics), 1) if topics else 0.0
        topic_list.append(
            {
                "id": int(tid),
                "keywords": keywords,
                "count": int(count),
                "pct": pct,
                "label": f"{tid}_{'_'.join(keywords[:4])}",
            }
        )

    topic_list.sort(key=lambda x: -x["count"])

    return {
        "n_records": len(topics),
        "n_topics": len(topic_list),
        "noise_count": int(noise_count),
        "noise_rate_pct": round(100.0 * noise_count / len(topics), 1),
        "topics": topic_list,
    }


def build_comparison_summary(results: dict) -> str:
    topics = results["topics"]
    top3 = topics[:3]

    lines = [
        "# CryptoBERT vs. all-MiniLM-L6-v2: ERC-8004 Topic Comparison\n",
        f"- Records: {results['n_records']}",
        f"- Topics found (CryptoBERT): {results['n_topics']}",
        f"- Noise rate: {results['noise_rate_pct']}%\n",
        "## CryptoBERT Top Topics\n",
    ]
    for t in topics:
        lines.append(f"- Topic {t['id']} ({t['pct']}%): {', '.join(t['keywords'][:6])}")

    lines += [
        "",
        "## Method 2 Reference (all-MiniLM-L6-v2, ERC-8004 slice)",
        f"- Topic 0 (agent, agents): {METHOD2_ERC_RESULTS['erc8004_topic0_pct']}% of ERC-8004",
        "",
        "## Convergence Assessment",
    ]

    # Check if top topic has trust/security/verif/agent keywords
    trust_keywords = {"trust", "security", "verif", "credential", "reputa", "vouch", "agent"}
    top_topic_keywords = set(k.lower() for k in (top3[0]["keywords"] if top3 else []))
    convergent = bool(top_topic_keywords & trust_keywords)

    if convergent:
        lines.append(
            "**Convergent**: The dominant CryptoBERT topic overlaps with trust/security/agent "
            "discourse, consistent with Method 2's Topic 0 dominance in ERC-8004."
        )
    else:
        lines.append(
            "**Divergent**: CryptoBERT reveals different dominant themes — domain-adapted "
            "embeddings may capture finer-grained crypto-governance distinctions."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    if not DATA_PATH.exists():
        sys.exit(f"Error: {DATA_PATH} not found")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading ERC-8004 corpus …")
    texts, ids = load_erc8004_corpus()
    print(f"  {len(texts)} records after filtering")

    print("\nComputing CryptoBERT embeddings …")
    embeddings = compute_cryptobert_embeddings(texts)
    print(f"  Embeddings shape: {embeddings.shape}")

    print("\nFitting BERTopic …")
    topic_model, topics = fit_bertopic(texts, embeddings)

    print("\nBuilding results …")
    results = build_results(topic_model, topics, texts)

    topics_path = OUT_DIR / "topics.json"
    topics_path.write_text(json.dumps(results, indent=2))
    print(f"  Saved → {topics_path}")

    summary = build_comparison_summary(results)
    summary_path = OUT_DIR / "comparison_summary.md"
    summary_path.write_text(summary)
    print(f"  Saved → {summary_path}")

    print("\nTop topics (CryptoBERT):")
    for t in results["topics"][:5]:
        print(f"  Topic {t['id']:2d} ({t['pct']:5.1f}%): {', '.join(t['keywords'][:6])}")

    print(f"\nNoise rate: {results['noise_rate_pct']}%")
    print("\nDone.")


if __name__ == "__main__":
    main()
