"""
Comparative Discourse Analysis — entry point.

Fits BERTopic on the combined ERC-8004 + Google-A2A corpus, then compares
topic distributions across the two cases using Jensen-Shannon divergence.

No LLM API required — runs entirely on local sentence-transformers embeddings.

Usage:
    uv run python scripts/analyse/topic_discovery/comparative_discourse/run.py [--n-topics 20]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT))

from scripts.analyse.topic_discovery.comparative_discourse.model import (
    fit_bertopic,
    load_corpus,
)
from scripts.analyse.topic_discovery.comparative_discourse.compare import (
    build_comparison_table,
    plot_comparison,
    save_results,
)

OUT_DIR = ROOT / "output" / "topic_discovery" / "comparative_discourse"


def main() -> None:
    parser = argparse.ArgumentParser(description="Comparative Discourse Analysis (BERTopic)")
    parser.add_argument("--n-topics", type=int, default=20, help="Target number of topics (default: 20)")
    args = parser.parse_args()

    data_path = ROOT / "data" / "annotated" / "annotated_records.json"
    if not data_path.exists():
        sys.exit(f"Error: {data_path} not found")

    print("Loading corpus …")
    texts, ids, cases = load_corpus(data_path)
    from collections import Counter
    print(f"  {Counter(cases)}")

    print("\nFitting BERTopic …")
    topic_model, topics, probs = fit_bertopic(texts, n_topics=args.n_topics)

    print("\nBuilding comparison table …")
    df, global_js = build_comparison_table(topic_model, topics, cases)

    print("\nTop 10 most divergent topics:")
    print(df[["label", "erc8004_pct", "a2a_pct", "abs_diff"]].head(10).to_string(index=False))

    save_results(df, global_js, OUT_DIR)
    plot_comparison(df, OUT_DIR, top_n=20)

    print("\nDone.")


if __name__ == "__main__":
    main()
