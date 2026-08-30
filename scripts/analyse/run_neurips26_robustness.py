"""Non-visual robustness analyses for the NeurIPS 2026 revision.

The script deliberately separates four issues that were previously conflated:

1. the frozen 4,323-record paper corpus versus the larger annotation archive;
2. uncertainty induced by the 142-versus-4,181 case imbalance;
3. platform/channel and calendar-time composition;
4. sensitivity of reported co-participation networks to tie-strength thresholds.

It does not claim that these descriptive checks identify a causal effect of
governance form.  Outputs are tables and machine-readable summaries only; no
figures are generated.

Usage:
    uv run python scripts/analyse/run_neurips26_robustness.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANNOTATED = ROOT / "data" / "annotated" / "r1" / "annotated_records.json"
MANIFEST_SUMMARY = ROOT / "data" / "manifests" / "r1_paper_v1_summary.json"
MANIFEST_ROWS = ROOT / "data" / "manifests" / "r1_paper_v1.jsonl"
NETWORK_DIR = ROOT / "analysis" / "metrics" / "r1"
OUT = ROOT / "analysis" / "metrics" / "neurips26"

SEED = 20260826
BOOTSTRAP_REPS = 2_000
MIN_TEXT_LENGTH = 20
BOT_AUTHORS = {
    "codecov[bot]",
    "dependabot[bot]",
    "gemini-code-assist[bot]",
    "git-vote[bot]",
    "github-actions[bot]",
    "google-cla[bot]",
}
ARGUMENT_TYPES = ["Technical", "Governance-Principle", "Economic", "Process", "Off-topic"]


def retained(record: dict) -> bool:
    """Apply the frozen R1 paper filter recorded by the row-level manifest."""
    text = str(record.get("raw_text") or "").strip()
    author = str(record.get("author") or "")
    return (
        len(text) >= MIN_TEXT_LENGTH
        and author not in BOT_AUTHORS
        and not author.endswith("[bot]")
    )


def channel(record: dict) -> str:
    source = str(record.get("source") or "unknown")
    if record.get("_case") == "ERC-8004":
        return "forum" if source == "forum" else "github_review"
    if source.startswith("discussion"):
        return "github_discussion"
    if source.startswith("pr") or source in {"review", "review_comment"}:
        return "github_pr"
    return "github_issue"


def load_frame() -> tuple[pd.DataFrame, list[dict]]:
    records = json.loads(ANNOTATED.read_text(encoding="utf-8"))
    manifest_keys = Counter()
    for line in MANIFEST_ROWS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        manifest_keys[(row["case"], row.get("date"), row.get("author"), row["raw_text_sha256"])] += 1

    filtered = []
    for record in records:
        text = str(record.get("raw_text") or "").strip()
        key = (
            record.get("_case"),
            record.get("date"),
            record.get("author"),
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )
        if manifest_keys[key] > 0:
            filtered.append(record)
            manifest_keys[key] -= 1
    unresolved = sum(manifest_keys.values())
    if unresolved:
        raise RuntimeError(f"Could not map {unresolved} frozen manifest rows to the annotation archive")
    rows = []
    for record in filtered:
        annotation = record.get("annotation") or {}
        rows.append(
            {
                "case": record.get("_case"),
                "source": record.get("source"),
                "channel": channel(record),
                "date": record.get("date"),
                "author": record.get("author"),
                "argument_type": annotation.get("argument_type", "Unknown"),
                "stance": annotation.get("stance", "Unknown"),
                "consensus_signal": annotation.get("consensus_signal", "Unknown"),
            }
        )
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="coerce", format="mixed")
    frame["quarter"] = frame["date"].dt.tz_localize(None).dt.to_period("Q").astype(str)
    return frame, records


def write_stage_counts(frame: pd.DataFrame, archive: list[dict]) -> pd.DataFrame:
    summary = json.loads(MANIFEST_SUMMARY.read_text(encoding="utf-8"))
    archive_counts = Counter(record.get("_case") for record in archive)
    refiltered_counts = Counter(record.get("_case") for record in archive if retained(record))
    retained_counts = frame["case"].value_counts().to_dict()
    rows = []
    for case in ("ERC-8004", "Google-A2A"):
        rows.extend(
            [
                {"case": case, "stage": "annotation_archive", "records": archive_counts[case],
                 "interpretation": "Stored LLM annotation archive; not the paper denominator."},
                {"case": case, "stage": "archive_refiltered", "records": refiltered_counts[case],
                 "interpretation": "Later analysis subset obtained by reapplying the visible filter; not the frozen paper manifest."},
                {"case": case, "stage": "frozen_paper_manifest", "records": retained_counts[case],
                 "interpretation": "Exact R1 paper subset after the frozen text and bot filter."},
            ]
        )
    result = pd.DataFrame(rows)
    expected = summary["retained_by_case"]
    assert retained_counts == expected, (retained_counts, expected)
    result.to_csv(OUT / "corpus_stage_counts.csv", index=False)
    return result


def bootstrap_argument_differences(frame: pd.DataFrame) -> pd.DataFrame:
    """Equal-size bootstrap: A2A share minus ERC share, n=142 per draw."""
    rng = np.random.default_rng(SEED)
    by_case = {
        case: frame.loc[frame["case"] == case, "argument_type"].to_numpy()
        for case in ("ERC-8004", "Google-A2A")
    }
    sample_n = min(len(values) for values in by_case.values())
    draws: dict[str, list[float]] = defaultdict(list)
    for _ in range(BOOTSTRAP_REPS):
        erc = rng.choice(by_case["ERC-8004"], size=sample_n, replace=True)
        a2a = rng.choice(by_case["Google-A2A"], size=sample_n, replace=True)
        for label in ARGUMENT_TYPES:
            draws[label].append(float(np.mean(a2a == label) - np.mean(erc == label)))

    rows = []
    for label in ARGUMENT_TYPES:
        values = np.asarray(draws[label])
        rows.append(
            {
                "argument_type": label,
                "sample_per_case": sample_n,
                "bootstrap_repetitions": BOOTSTRAP_REPS,
                "mean_difference_a2a_minus_erc": values.mean(),
                "ci95_low": np.quantile(values, 0.025),
                "ci95_high": np.quantile(values, 0.975),
                "probability_difference_above_zero": np.mean(values > 0),
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(OUT / "bootstrap_argument_differences.csv", index=False, float_format="%.6f")
    return result


def grouped_distribution(frame: pd.DataFrame, groups: list[str], output: str) -> pd.DataFrame:
    counts = (
        frame.groupby(groups + ["argument_type"], dropna=False)
        .size()
        .rename("records")
        .reset_index()
    )
    counts["group_total"] = counts.groupby(groups)["records"].transform("sum")
    counts["share"] = counts["records"] / counts["group_total"]
    counts.to_csv(OUT / output, index=False, float_format="%.6f")
    return counts


def gini(values: list[int]) -> float:
    array = np.asarray(sorted(values), dtype=float)
    if len(array) == 0 or array.sum() == 0:
        return 0.0
    index = np.arange(1, len(array) + 1)
    return float(np.sum((2 * index - len(array) - 1) * array) / (len(array) * array.sum()))


def graph_metrics(path: Path, threshold: float) -> dict:
    graph = nx.Graph()
    edge_type_counts: Counter[str] = Counter()
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            weight = float(row.get("weight") or 1)
            if weight < threshold:
                continue
            graph.add_edge(row["source"], row["target"], weight=weight)
            edge_type_counts[row.get("type", "unknown")] += 1
    if graph.number_of_nodes() == 0:
        return {
            "nodes": 0,
            "edges": 0,
            "density": 0.0,
            "giant_component_ratio": 0.0,
            "degree_gini": 0.0,
            "edge_types": "",
        }
    giant = max(nx.connected_components(graph), key=len)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "giant_component_ratio": len(giant) / graph.number_of_nodes(),
        "degree_gini": gini([degree for _, degree in graph.degree()]),
        "edge_types": ";".join(f"{key}:{value}" for key, value in sorted(edge_type_counts.items())),
    }


def network_sensitivity() -> pd.DataFrame:
    paths = {
        "ERC-8004": NETWORK_DIR / "network_edges_erc8004.csv",
        "Google-A2A": NETWORK_DIR / "network_edges_a2a.csv",
    }
    rows = []
    for case, path in paths.items():
        for threshold in (1.0, 1.5, 2.0, 3.0):
            metrics = graph_metrics(path, threshold)
            rows.append({"case": case, "minimum_tie_weight": threshold, **metrics})
    result = pd.DataFrame(rows)
    result.to_csv(OUT / "network_tie_threshold_sensitivity.csv", index=False, float_format="%.6f")
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    frame, archive = load_frame()
    stages = write_stage_counts(frame, archive)
    bootstrap = bootstrap_argument_differences(frame)
    channels = grouped_distribution(frame, ["case", "channel"], "channel_argument_distributions.csv")
    temporal = grouped_distribution(frame, ["case", "quarter"], "temporal_argument_distributions.csv")
    networks = network_sensitivity()

    summary = {
        "schema_version": "1.0.0",
        "generated_by": "scripts/analyse/run_neurips26_robustness.py",
        "seed": SEED,
        "bootstrap_repetitions": BOOTSTRAP_REPS,
        "paper_corpus": frame["case"].value_counts().sort_index().to_dict(),
        "date_range": {
            "minimum": frame["date"].min().isoformat(),
            "maximum": frame["date"].max().isoformat(),
        },
        "outputs": [
            "corpus_stage_counts.csv",
            "bootstrap_argument_differences.csv",
            "channel_argument_distributions.csv",
            "temporal_argument_distributions.csv",
            "network_tie_threshold_sensitivity.csv",
        ],
        "validity_boundary": (
            "All checks are descriptive. Equal-size resampling addresses denominator imbalance but "
            "does not balance case maturity, platform affordances, or organizational resources. "
            "The network inputs use platform-specific edge semantics, so threshold sensitivity is "
            "not a harmonized edge-definition test."
        ),
        "row_counts": {
            "stage_rows": len(stages),
            "bootstrap_rows": len(bootstrap),
            "channel_rows": len(channels),
            "temporal_rows": len(temporal),
            "network_rows": len(networks),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
