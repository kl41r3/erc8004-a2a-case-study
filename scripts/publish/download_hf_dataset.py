"""Download the frozen R1 and R2 dataset release from Hugging Face.

GitHub contains the computational package and metadata only. Dataset payloads are
downloaded from an immutable Hugging Face revision into the repository's local
``data/`` directory, where they are ignored by Git.

Usage:
    uv run python scripts/publish/download_hf_dataset.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
HF_REPO_ID = "kl41r3/erc8004-vs-a2a-governance"
HF_REVISION = "987913bacae1a169bb39587b22dd002f74293177"
ALLOW_PATTERNS = (
    "raw/**",
    "annotated/**",
    "manifests/**",
    "croissant/v1/*.parquet",
)

REQUIRED_DOWNLOADS = (
    "raw/forum_posts.json",
    "raw/github_comments_filtered.json",
    "raw/a2a_issues.json",
    "raw/a2a_prs.json",
    "raw/a2a_discussions.json",
    "annotated/r1/annotated_records.json",
    "annotated/r2/cross-model/consensus/erc_annotations.json",
    "annotated/r2/cross-model/consensus/a2a_annotations.json",
    "annotated/r2/cross-round/erc_cross_consensus.json",
    "annotated/r2/cross-round/a2a_cross_consensus.json",
    "manifests/r1_paper_v1.jsonl",
    "manifests/r1_paper_v1_summary.json",
    "croissant/v1/r1_annotations.parquet",
    "croissant/v1/r2_cross_model_consensus.parquet",
    "croissant/v1/r2_cross_model_votes.parquet",
    "croissant/v1/r2_cross_round_consensus.parquet",
    "croissant/v1/r2_cross_round_votes.parquet",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the immutable Hugging Face dataset release used by this repository."
    )
    parser.add_argument(
        "--local-dir",
        type=Path,
        default=DATA_DIR,
        help="Dataset destination. Defaults to the repository data directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    destination = args.local_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=HF_REPO_ID,
        repo_type="dataset",
        revision=HF_REVISION,
        local_dir=destination,
        allow_patterns=list(ALLOW_PATTERNS),
    )

    missing = [relative for relative in REQUIRED_DOWNLOADS if not (destination / relative).is_file()]
    if missing:
        print("Dataset download is incomplete:")
        for relative in missing:
            print(f"  {relative}")
        return 1

    print(f"Downloaded Hugging Face dataset: {HF_REPO_ID}")
    print(f"Pinned revision: {HF_REVISION}")
    print(f"Destination: {destination}")
    print("Run `uv run python scripts/verify_repository.py --with-data` to verify checksums and rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
