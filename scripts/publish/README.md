# Data publication staging

This directory contains local packaging tools only. They never upload data or call a
remote API.

Prepare the Hugging Face dataset repository in a new or empty directory:

```bash
uv run python scripts/publish/prepare_hf_dataset.py --output /private/tmp/rq1-hf-release
```

The staging package contains only the dataset card, `raw/`, `annotated/`, `croissant/`,
and a generated `PUBLISH_MANIFEST.json`. Review that manifest before any separately
approved upload.
