# Data publication staging

This directory contains the boundary between the GitHub computational package and the
Hugging Face dataset release.

Download the immutable dataset revision used by the GitHub release:

```bash
uv run python scripts/publish/download_hf_dataset.py
uv run python scripts/verify_repository.py --with-data
```

The downloader restores the frozen `raw/`, `annotated/`, `manifests/`, and five Croissant
Parquet payloads into the local `data/` directory. `make reproduce` then rebuilds the local
`neurips26/` layer from tracked robustness CSVs. These payloads are ignored by Git. The pinned
Hugging Face commit prevents exact R1/R2 reproduction from silently following a changing
`main` branch.

Prepare the Hugging Face dataset repository in a new or empty directory:

```bash
uv run python scripts/publish/prepare_hf_dataset.py --output /private/tmp/rq1-hf-release
```

Run `make reproduce` first. The staging package then contains only the dataset card, `raw/`,
`annotated/`, `manifests/`, `croissant/`, the rebuilt `neurips26/` layer, and a generated
`PUBLISH_MANIFEST.json`. Review that manifest before any separately approved upload.
