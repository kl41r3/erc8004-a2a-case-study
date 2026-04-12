"""
BERTopic model fitting for comparative discourse analysis.

Fits ONE BERTopic model on the combined corpus, then segments topic
distributions by case for cross-case comparison.

Reference: Comparative Discourse Analysis Using Topic Models
ACM SMSociety 2020, DOI: 10.1145/3400806.3400816
"""
from __future__ import annotations

import json
from pathlib import Path

BOT_AUTHORS = {
    "gemini-code-assist[bot]", "google-cla[bot]", "github-actions[bot]",
    "codecov[bot]", "dependabot[bot]", "git-vote[bot]",
}

VALID_CASES = {"ERC-8004", "Google-A2A"}


def load_corpus(data_path: Path) -> tuple[list[str], list[str], list[str]]:
    """
    Returns (texts, record_ids, cases) for all usable records.
    """
    raw = json.loads(data_path.read_text())
    texts, ids, cases = [], [], []
    for r in raw:
        author = r.get("author", "")
        if author in BOT_AUTHORS or author.endswith("[bot]"):
            continue
        text = (r.get("raw_text") or "").strip()
        if len(text) < 20:
            continue
        case = r.get("_case", "")
        if case not in VALID_CASES:
            continue
        record_id = f"{case}_{r.get('source','?')}_{r.get('post_id') or r.get('id','?')}"
        texts.append(text[:1000])
        ids.append(record_id)
        cases.append(case)
    return texts, ids, cases


def fit_bertopic(texts: list[str], n_topics: int = 20):
    """
    Fit BERTopic on the full corpus.
    Returns (topic_model, topics, probs).
    """
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    from umap import UMAP
    from hdbscan import HDBSCAN

    print(f"  Fitting BERTopic on {len(texts)} documents …")

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=10,
        min_samples=5,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        nr_topics=n_topics,
        calculate_probabilities=True,
        verbose=True,
    )

    topics, probs = topic_model.fit_transform(texts)
    return topic_model, topics, probs
