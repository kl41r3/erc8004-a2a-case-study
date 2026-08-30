"""Verify the NeurIPS 2026 robustness release layer (v1.1.0).

This is the public counterpart of the review-artifact verifier. It checks the
five robustness tables, the R1/R2 network tables, the four-model reliability
values, the human-validation boundary, repository metadata, and the public
boundary of tracked files — including that no manuscript file is distributed
in this release. It does not require network access; dataset payloads are
optional and verified by ``verify_repository.py --with-data`` after download.

Usage:
    uv run python scripts/verify_neurips26.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RELEASE_VERSION = "1.1.0"

# Frozen pairwise corpus (unchanged from the review artifact).
EXPECTED_MANIFEST_SHA256 = "0445428da7b67f6c7a62b5bb83014dccdd92433fc8e66819f55d4839e5ec92cb"
EXPECTED_FLEISS_KAPPA = {
    "erc": {"argument_type": 0.5451, "stance": 0.5792, "consensus_signal": 0.4853},
    "a2a": {"argument_type": 0.5409, "stance": 0.5247, "consensus_signal": 0.4947},
}

EXPECTED_ROW_COUNTS = {"stage_rows": 6, "bootstrap_rows": 5, "channel_rows": 27, "temporal_rows": 36, "network_rows": 8}

# Manuscript files must not be distributed in this release.
FORBIDDEN_TRACKED_PREFIXES = (
    "paper/",
    "paper-acm/",
)

FORBIDDEN_LOCAL_PATH_MARKERS = (
    "/Users/" + "michelangelo/",
    "C:\\Users\\" + "michelangelo\\",
)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"hf_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def verify_robustness_tables() -> None:
    base = ROOT / "analysis" / "metrics" / "neurips26"
    summary = json.loads((base / "summary.json").read_text(encoding="utf-8"))
    require(summary["seed"] == 20260826, "robustness seed drift")
    require(summary["bootstrap_repetitions"] == 2000, "bootstrap repetition count drift")
    require(summary["row_counts"] == EXPECTED_ROW_COUNTS, "summary row-count inventory drift")

    tables = {
        "stage_rows": "corpus_stage_counts.csv",
        "bootstrap_rows": "bootstrap_argument_differences.csv",
        "channel_rows": "channel_argument_distributions.csv",
        "temporal_rows": "temporal_argument_distributions.csv",
        "network_rows": "network_tie_threshold_sensitivity.csv",
    }
    for key, filename in tables.items():
        rows = list(csv.DictReader((base / filename).open()))
        require(len(rows) == EXPECTED_ROW_COUNTS[key],
                f"{filename} must contain {EXPECTED_ROW_COUNTS[key]} rows, found {len(rows)}")

    boot = list(csv.DictReader((base / "bootstrap_argument_differences.csv").open()))
    require(all(float(row["ci95_low"]) <= 0 <= float(row["ci95_high"]) for row in boot),
            "a principal bootstrap interval no longer includes zero")
    stages = list(csv.DictReader((base / "corpus_stage_counts.csv").open()))
    frozen = {row["case"]: int(row["records"]) for row in stages if row["stage"] == "frozen_paper_manifest"}
    require(frozen == {"ERC-8004": 142, "Google-A2A": 4181}, "stage-count reconciliation drift")


def verify_network_tables() -> None:
    r1 = list(csv.DictReader((ROOT / "analysis" / "metrics" / "r1" / "network_metrics_table.csv").open()))
    r2 = list(csv.DictReader((ROOT / "analysis" / "metrics" / "r2" / "network_metrics_table.csv").open()))
    require(any(row["Metric"] == "Nodes" and row["ERC-8004"] == "67" and row["Google A2A (full)"] == "771" for row in r1),
            "R1 node counts drift")
    require(any(row["case"] == "ERC Agent Cluster (Tier 1+2)" and row["n_actors"] == "204" for row in r2),
            "R2 ERC actor count drift")
    require(any(row["case"] == "Google A2A" and row["n_actors"] == "629" for row in r2),
            "R2 A2A actor count drift")


def verify_model_reliability() -> None:
    kappa = json.loads((ROOT / "analysis" / "metrics" / "r2" / "kappa_4models.json").read_text(encoding="utf-8"))
    require(kappa["erc"]["n_overlap"] == 144 and kappa["a2a"]["n_overlap"] == 4185,
            "four-model kappa overlap sizes drift")
    for case, expected in EXPECTED_FLEISS_KAPPA.items():
        actual = kappa[case]["fleiss"]
        for field, value in expected.items():
            require(abs(actual[field] - value) < 1e-9, f"Fleiss kappa drift for {case}.{field}")


def verify_human_boundary() -> None:
    rows = list(csv.DictReader((ROOT / "validation" / "sample_50.csv").open()))
    require(len(rows) == 50, "human-validation worksheet must contain 50 records")
    human_fields = [name for name in rows[0] if name.startswith("human_")]
    require(all(not str(row[field]).strip() for row in rows for field in human_fields),
            "worksheet is no longer blank; adjudicate and update the release before claiming validity")


def verify_metadata() -> None:
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    require(re.search(r"^cff-version:\s*\S+", cff, flags=re.MULTILINE) is not None,
            "CITATION.cff is missing cff-version")
    require(re.search(r"^version:\s*" + RELEASE_VERSION + r"\s*$", cff, flags=re.MULTILINE) is not None,
            f"CITATION.cff version must be {RELEASE_VERSION}")
    require("family-names:" in cff and "given-names:" in cff, "CITATION.cff authors missing")

    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    require(zenodo["version"] == f"v{RELEASE_VERSION}", f".zenodo.json version must be v{RELEASE_VERSION}")
    require(zenodo["upload_type"] == "software" and zenodo["license"] == "MIT",
            ".zenodo.json upload type or license drift")

    require((ROOT / "LICENSE").is_file(), "LICENSE is missing")
    require((ROOT / "ASSET_LICENSES.md").is_file(), "ASSET_LICENSES.md is missing")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("verify", "robustness", "reproduce", "all"):
        require(re.search(r"^" + target + r":", makefile, flags=re.MULTILINE) is not None,
                f"Makefile target missing: {target}")
    require(re.search(r"^paper:", makefile, flags=re.MULTILINE) is None,
            "Makefile must not ship a paper target in this release")


def releasable_files() -> list[str]:
    """Tracked files plus untracked files that Git does not ignore."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    return result.stdout.splitlines()


def verify_public_boundary() -> None:
    tracked = releasable_files()
    require(any(line.startswith("analysis/metrics/neurips26/") for line in tracked),
            "robustness tables are not tracked in git")
    require(any(line.startswith("validation/") for line in tracked),
            "validation worksheet is not tracked in git")

    for relative in tracked:
        require(not relative.startswith(FORBIDDEN_TRACKED_PREFIXES),
                f"manuscript path is tracked but this release distributes no manuscript: {relative}")
        path = ROOT / relative
        if not path.is_file():
            continue
        require(relative != ".env" and not relative.endswith(".env"), f"secret file is tracked: {relative}")
        if path.suffix.lower() in {".py", ".md", ".tex", ".toml", ".csv", ".json", ".jsonl", ".yml", ".yaml", ".cff"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in FORBIDDEN_LOCAL_PATH_MARKERS:
                require(marker not in text, f"local researcher path in tracked file: {relative}")
            for pattern in SECRET_PATTERNS:
                require(pattern.search(text) is None, f"secret-like token in tracked file: {relative}")


def verify_frozen_manifest_if_present() -> None:
    rows_path = ROOT / "data" / "manifests" / "r1_paper_v1.jsonl"
    if not rows_path.is_file():
        return
    summary = json.loads((ROOT / "data" / "manifests" / "r1_paper_v1_summary.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in rows_path.read_text().splitlines() if line]
    require(sha256(rows_path) == EXPECTED_MANIFEST_SHA256, "frozen manifest digest drift")
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["case"]] = counts.get(row["case"], 0) + 1
    require(counts == {"ERC-8004": 142, "Google-A2A": 4181}, f"unexpected counts: {counts}")
    require(summary["retained_rows"] == 4323, "summary retained-row count drift")


def main() -> int:
    verify_robustness_tables()
    verify_network_tables()
    verify_model_reliability()
    verify_human_boundary()
    verify_metadata()
    verify_public_boundary()
    verify_frozen_manifest_if_present()
    print("PASS: NeurIPS 2026 robustness release verification")
    print("Checked robustness tables, network tables, model reliability,")
    print("human-validation boundary, metadata, public boundary (no manuscript")
    print("distributed), and the frozen pairwise manifest when present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
