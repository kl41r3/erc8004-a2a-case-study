"""
Thematic-LM — entry point.

Usage:
    uv run python scripts/analyse/topic_discovery/thematic_lm/run.py [--backend minimax] [--limit 20]

Stages:
  1. Coder:       open-code each record (batches of --batch-size)
  2. Aggregator:  group codes into raw theme clusters
  3. Reviewer:    refine clusters into a clean codebook
  4. Theme coder: assign a codebook theme to each record

Checkpoints are saved after every 10 batches — safe to interrupt and resume.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from scripts.analyse.topic_discovery.thematic_lm.pipeline import run_pipeline

BACKENDS = {
    "minimax": {
        "base_url": "https://api.minimaxi.com/v1",
        "model": "MiniMax-M2.5",
        "api_key_env": "MINIMAX_API_KEY",
    },
    "openai": {
        "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key_env": "OPENAI_API_KEY",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Thematic-LM pipeline")
    parser.add_argument("--backend", default="minimax", choices=list(BACKENDS))
    parser.add_argument("--batch-size", type=int, default=15)
    parser.add_argument("--limit", type=int, default=0, help="0 = all records")
    args = parser.parse_args()

    cfg = BACKENDS[args.backend]
    api_key = os.environ.get(cfg["api_key_env"], "")
    if not api_key:
        sys.exit(f"Error: {cfg['api_key_env']} not set in .env")

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=cfg["base_url"])

    data_path = ROOT / "data" / "annotated" / "annotated_records.json"
    if not data_path.exists():
        sys.exit(f"Error: {data_path} not found")

    print(f"Backend: {args.backend} / {cfg['model']}")
    print(f"Batch size: {args.batch_size}  Limit: {args.limit or 'all'}")
    print()

    run_pipeline(
        client=client,
        model=cfg["model"],
        data_path=data_path,
        batch_size=args.batch_size,
        limit=args.limit,
    )


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    main()
