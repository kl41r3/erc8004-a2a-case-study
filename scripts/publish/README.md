# Data publication staging

This directory contains the boundary between the GitHub computational package and the
Hugging Face dataset release.

Download the immutable dataset revision used by the GitHub release:

```bash
uv run python scripts/publish/download_hf_dataset.py
uv run python scripts/verify_repository.py --with-data
```

The downloader writes `raw/`, `annotated/`, and the five Parquet payloads into the local
`data/` directory. These payloads are ignored by Git. The pinned Hugging Face commit prevents
an exact reproduction from silently following a changing `main` branch.

Prepare the Hugging Face dataset repository in a new or empty directory:

```bash
uv run python scripts/publish/prepare_hf_dataset.py --output /private/tmp/rq1-hf-release
```

Run the downloader first. The staging package then contains only the dataset card, `raw/`, `annotated/`, `croissant/`,
and a generated `PUBLISH_MANIFEST.json`. Review that manifest before any separately
approved upload.
