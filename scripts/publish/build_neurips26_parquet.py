"""Build the neurips26 Parquet tables for the Hugging Face dataset release.

Converts the five non-visual robustness tables under
``analysis/metrics/neurips26/`` into Parquet, and writes the checksum
manifest and release manifest next to them. Existing raw, R1, R2, and
Croissant payloads on Hugging Face are not modified; this release adds
only the ``neurips26/`` layer.

Usage:
    uv run python scripts/publish/build_neurips26_parquet.py --output <staging-dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "analysis" / "metrics" / "neurips26"
SCHEMA_SOURCE = ROOT / "scripts" / "publish" / "neurips26_schema.md"

RELEASE_VERSION = "neurips26-v1.1.1"

# filename -> (row count, column dtypes applied after read)
TABLES: dict[str, tuple[int, dict[str, str]]] = {
    "corpus_stage_counts.parquet": (
        6,
        {"case": "string", "stage": "string", "records": "int64", "interpretation": "string"},
    ),
    "bootstrap_argument_differences.parquet": (
        5,
        {
            "argument_type": "string",
            "sample_per_case": "int64",
            "bootstrap_repetitions": "int64",
            "mean_difference_a2a_minus_erc": "float64",
            "ci95_low": "float64",
            "ci95_high": "float64",
            "probability_difference_above_zero": "float64",
        },
    ),
    "channel_argument_distributions.parquet": (
        27,
        {
            "case": "string",
            "channel": "string",
            "argument_type": "string",
            "records": "int64",
            "group_total": "int64",
            "share": "float64",
        },
    ),
    "temporal_argument_distributions.parquet": (
        36,
        {
            "case": "string",
            "quarter": "string",
            "argument_type": "string",
            "records": "int64",
            "group_total": "int64",
            "share": "float64",
        },
    ),
    "network_tie_threshold_sensitivity.parquet": (
        8,
        {
            "case": "string",
            "minimum_tie_weight": "float64",
            "nodes": "int64",
            "edges": "int64",
            "density": "float64",
            "giant_component_ratio": "float64",
            "degree_gini": "float64",
            "edge_types": "string",
        },
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Target directory for the neurips26 release layer (created if missing).",
    )
    arguments = parser.parse_args()

    target = arguments.output / "neurips26"
    target.mkdir(parents=True, exist_ok=True)

    summary = json.loads((SOURCE_DIR / "summary.json").read_text(encoding="utf-8"))
    checksums: dict[str, dict[str, object]] = {}

    for filename, (expected_rows, dtypes) in TABLES.items():
        csv_name = filename.removesuffix(".parquet") + ".csv"
        frame = pd.read_csv(SOURCE_DIR / csv_name)
        if list(frame.columns) != list(dtypes):
            raise SystemExit(f"FAIL: unexpected columns in {csv_name}: {list(frame.columns)}")
        if len(frame) != expected_rows:
            raise SystemExit(f"FAIL: {csv_name} must have {expected_rows} rows, found {len(frame)}")
        frame = frame.astype(dtypes)
        out_path = target / filename
        frame.to_parquet(out_path, index=False, engine="pyarrow", compression="snappy")
        checksums[filename] = {"sha256": sha256(out_path), "bytes": out_path.stat().st_size, "rows": len(frame)}
        print(f"wrote {out_path.name}: {len(frame)} rows")

    (target / "CHECKSUMS.json").write_text(
        json.dumps(checksums, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    release_manifest = {
        "release": RELEASE_VERSION,
        "generated_by": "scripts/publish/build_neurips26_parquet.py",
        "source": "analysis/metrics/neurips26/ (GitHub repository v1.1.1)",
        "seed": summary["seed"],
        "bootstrap_repetitions": summary["bootstrap_repetitions"],
        "paper_corpus": summary["paper_corpus"],
        "validity_boundary": summary["validity_boundary"],
        "tables": {name: meta["rows"] for name, meta in checksums.items()},
    }
    (target / "release_manifest.json").write_text(
        json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    shutil.copy2(SCHEMA_SOURCE, target / "SCHEMA.md")

    print(f"\nneurips26 release layer written to {target}")
    print(f"version: {RELEASE_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
