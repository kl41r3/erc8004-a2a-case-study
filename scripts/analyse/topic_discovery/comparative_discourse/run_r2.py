"""
R2 Comparative Discourse Analysis — BERTopic on consensus annotations.

Loads from R2 consensus files (ERC + A2A) and fits BERTopic on the combined
corpus, then compares topic distributions using Jensen-Shannon divergence.

Output: output/topic_discovery/r2/comparative_discourse/

Usage:
    uv run python scripts/analyse/topic_discovery/comparative_discourse/run_r2.py
    uv run python scripts/analyse/topic_discovery/comparative_discourse/run_r2.py --n-topics 20
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT))

from scripts.analyse.topic_discovery.comparative_discourse.model import fit_bertopic
from scripts.analyse.topic_discovery.comparative_discourse.compare import (
    build_comparison_table,
    plot_comparison,
    save_results,
)

CONSENSUS_DIR = ROOT / "data" / "annotated" / "r2" / "consensus"
OUT_DIR = ROOT / "output" / "topic_discovery" / "r2" / "comparative_discourse"

BOT_AUTHORS = {"github-actions[bot]", "eip-review-bot", "dependabot[bot]"}

# Map R2 case labels to the canonical keys BERTopic compare expects
CASE_MAP = {
    "ERC-8004": "ERC-8004",
    "ERC-cluster": "ERC-8004",  # Tier 2 merges with Tier 1 as "ERC" case
    "Google-A2A": "Google-A2A",
    "Google A2A": "Google-A2A",
}


def load_r2_corpus() -> tuple[list[str], list[str], list[str]]:
    """Load R2 consensus corpus from both ERC and A2A consensus files."""
    texts, ids, cases = [], [], []

    erc_path = CONSENSUS_DIR / "erc_annotations.json"
    if erc_path.exists():
        records = json.loads(erc_path.read_text())
        for r in records:
            author = r.get("author", "")
            if author in BOT_AUTHORS or author.endswith("[bot]"):
                continue
            text = (r.get("raw_text") or "").strip()
            if len(text) < 20:
                continue
            ann = r.get("annotation") or {}
            if ann.get("argument_type") == "Off-topic":
                continue
            case_raw = r.get("_case", "ERC-8004")
            case = CASE_MAP.get(case_raw, "ERC-8004")
            cid = (r.get("post_id") or r.get("comment_id") or
                   r.get("pr_number") or r.get("issue_number") or "")
            rid = f"{case}_{r.get('source','?')}_{cid}"
            texts.append(text[:1000])
            ids.append(rid)
            cases.append(case)

    a2a_path = CONSENSUS_DIR / "a2a_annotations.json"
    if a2a_path.exists():
        records = json.loads(a2a_path.read_text())
        for r in records:
            author = r.get("author", "")
            if author in BOT_AUTHORS or author.endswith("[bot]"):
                continue
            text = (r.get("raw_text") or "").strip()
            if len(text) < 20:
                continue
            ann = r.get("annotation") or {}
            if ann.get("argument_type") == "Off-topic":
                continue
            cid = r.get("issue_number") or r.get("pr_number") or ""
            rid = f"Google-A2A_{r.get('source','?')}_{cid}"
            texts.append(text[:1000])
            ids.append(rid)
            cases.append("Google-A2A")

    return texts, ids, cases


def main() -> None:
    parser = argparse.ArgumentParser(description="R2 BERTopic comparative discourse")
    parser.add_argument("--n-topics", type=int, default=20)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading R2 corpus from consensus annotations…")
    texts, ids, cases = load_r2_corpus()
    print(f"  {Counter(cases)}")
    print(f"  Total: {len(texts)} records\n")

    if not texts:
        print("ERROR: No records found. Run build_consensus.py first.")
        return

    print("Fitting BERTopic…")
    topic_model, topics, probs = fit_bertopic(texts, n_topics=args.n_topics)

    print("\nBuilding comparison table…")
    df, global_js = build_comparison_table(topic_model, topics, cases)

    print("\nTop 10 most divergent topics:")
    print(df[["label", "erc8004_pct", "a2a_pct", "abs_diff"]].head(10).to_string(index=False))

    save_results(df, global_js, OUT_DIR)
    plot_comparison(df, OUT_DIR, top_n=20)

    print(f"\nR2 BERTopic complete. JSD={global_js:.3f}. Outputs: {OUT_DIR}")


if __name__ == "__main__":
    main()
