"""
compute_metrics_r2.py — Governance metrics from R2 consensus annotations.

Uses majority-vote consensus annotations for both cases:
  Case A (DAO/ERC cluster): data/annotated/r2/consensus/erc_annotations.json
  Case B (Google A2A):      data/annotated/r2/consensus/a2a_annotations.json

Also pulls structural counts from raw data (R2 ERC) and original A2A raw data.

Output:
  analysis/r2_structural_metrics.csv
  output/stats/r2_findings_summary.md
  output/stats/r2_chi2_results.json

Usage:
  uv run python scripts/analyse/compute_metrics_r2.py
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dateutil import parser as dateutil_parser
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
CONSENSUS_DIR = ROOT / "data" / "annotated" / "r2" / "consensus"
R2_RAW_DIR = ROOT / "data" / "raw" / "r2"
RAW_DIR = ROOT / "data" / "raw"
ANALYSIS_DIR = ROOT / "analysis"
STATS_DIR = ROOT / "output" / "stats"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
STATS_DIR.mkdir(parents=True, exist_ok=True)

FIELDS = ["argument_type", "stance", "consensus_signal", "stakeholder_institution"]

# Key governance dates
ERC8004_PROPOSAL = datetime(2025, 8, 13, tzinfo=timezone.utc)
ERC8004_MAINNET = datetime(2026, 1, 29, tzinfo=timezone.utc)
A2A_FIRST_COMMIT = datetime(2025, 3, 25, tzinfo=timezone.utc)
A2A_PUBLIC_ANNOUNCE = datetime(2025, 4, 9, tzinfo=timezone.utc)


def _parse_date(s):
    if not s:
        return pd.NaT
    try:
        dt = dateutil_parser.parse(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return pd.Timestamp(dt)
    except Exception:
        return pd.NaT


def load_consensus(dataset: str) -> list[dict]:
    path = CONSENSUS_DIR / f"{dataset}_annotations.json"
    if not path.exists():
        print(f"  WARNING: Consensus file not found: {path}  (skipping {dataset})")
        return []
    return json.loads(path.read_text())


def label_distribution(records: list[dict], field: str) -> dict:
    vals = [r["annotation"].get(field, "Unknown") for r in records if r.get("annotation")]
    c = Counter(vals)
    total = sum(c.values()) or 1
    return {k: {"n": v, "pct": round(v / total * 100, 1)} for k, v in c.most_common()}


def chi2_test(records_a: list[dict], records_b: list[dict], field: str) -> dict:
    """Compute χ² test and Cramér's V for field distribution across two cases."""
    import math
    vals_a = Counter(r["annotation"].get(field, "") for r in records_a if r.get("annotation"))
    vals_b = Counter(r["annotation"].get(field, "") for r in records_b if r.get("annotation"))
    all_cats = sorted(set(vals_a) | set(vals_b))
    n_a = sum(vals_a.values())
    n_b = sum(vals_b.values())
    n_total = n_a + n_b

    chi2 = 0.0
    for cat in all_cats:
        o_a = vals_a.get(cat, 0)
        o_b = vals_b.get(cat, 0)
        e_a = (o_a + o_b) * n_a / n_total
        e_b = (o_a + o_b) * n_b / n_total
        if e_a > 0:
            chi2 += (o_a - e_a) ** 2 / e_a
        if e_b > 0:
            chi2 += (o_b - e_b) ** 2 / e_b

    df = len(all_cats) - 1
    n_min = min(n_a, n_b)
    cramers_v = math.sqrt(chi2 / (n_total * min(df, 1))) if n_total > 0 and df > 0 else 0.0

    # Approximate p-value via chi2 CDF (scipy not required — rough estimate)
    # Use scipy if available, else report chi2 statistic only
    p_value = None
    try:
        from scipy.stats import chi2 as scipy_chi2
        p_value = float(1.0 - scipy_chi2.cdf(chi2, df))
    except ImportError:
        pass

    return {
        "field": field,
        "chi2": round(chi2, 3),
        "df": df,
        "cramers_v": round(cramers_v, 3),
        "p_value": round(p_value, 4) if p_value is not None else "scipy_not_installed",
        "n_erc": n_a,
        "n_a2a": n_b,
        "categories": {cat: {"erc_n": vals_a.get(cat, 0), "a2a_n": vals_b.get(cat, 0)} for cat in all_cats},
    }


def erc_raw_stats() -> dict:
    """Structural counts from R2 raw ERC data."""
    records = []
    for tier_dir in [R2_RAW_DIR / "tier1", R2_RAW_DIR / "tier2"]:
        if not tier_dir.exists():
            continue
        for fname in sorted(tier_dir.glob("*.json")):
            if "manifest" in fname.name:
                continue
            data = json.loads(fname.read_text())
            for r in data:
                if (r.get("raw_text") or "").strip():
                    records.append(r)

    dates = [_parse_date(r.get("date")) for r in records]
    dates = [d for d in dates if pd.notna(d)]
    unique_authors = len({r.get("author", "") for r in records if r.get("author")})

    ercs = set()
    for r in records:
        if r.get("erc"):
            ercs.add(r["erc"])

    tiers = Counter(r.get("_case", r.get("tier", "")) for r in records)
    forum_n = sum(1 for r in records if r.get("source") == "forum")
    github_n = sum(1 for r in records if r.get("source") != "forum")

    return {
        "total_raw_records": len(records),
        "forum_records": forum_n,
        "github_records": github_n,
        "unique_ercs": len(ercs),
        "unique_authors_raw": unique_authors,
        "date_range_start": min(dates).isoformat() if dates else None,
        "date_range_end": max(dates).isoformat() if dates else None,
    }


def a2a_raw_stats() -> dict:
    """Structural counts from original A2A raw data."""
    raw_files = {
        "issues": RAW_DIR / "a2a_issues.json",
        "prs": RAW_DIR / "a2a_prs.json",
        "commits": RAW_DIR / "a2a_commits.json",
        "discussions": RAW_DIR / "a2a_discussions.json",
    }
    counts = {}
    for name, path in raw_files.items():
        if path.exists():
            data = json.loads(path.read_text())
            counts[name] = len(data)
        else:
            counts[name] = 0

    all_disc = []
    for key in ("issues", "prs", "discussions"):
        p = raw_files[key]
        if p.exists():
            all_disc.extend(json.loads(p.read_text()))

    unique_authors = len({r.get("author") for r in all_disc if r.get("author")})
    return {**counts, "unique_authors_raw": unique_authors}


def stance_argtype_matrix(records: list[dict]) -> dict:
    """Stance × argument_type counts for heatmap."""
    matrix: dict[str, dict[str, int]] = {}
    for r in records:
        if not r.get("annotation"):
            continue
        a = r["annotation"]
        stance = a.get("stance", "")
        argtype = a.get("argument_type", "")
        if stance and argtype:
            matrix.setdefault(stance, {})
            matrix[stance][argtype] = matrix[stance].get(argtype, 0) + 1
    return matrix


def main():
    print("=== R2 Governance Metrics ===\n")

    # Load consensus annotations
    print("Loading consensus annotations…")
    erc_records = load_consensus("erc")
    a2a_records = load_consensus("a2a")
    print(f"  ERC: {len(erc_records)} records")
    print(f"  A2A: {len(a2a_records)} records")

    # Annotation distributions
    print("\nAnnotation distributions:")
    erc_dist = {f: label_distribution(erc_records, f) for f in FIELDS}
    a2a_dist = {f: label_distribution(a2a_records, f) for f in FIELDS}

    for field in ["argument_type", "stance"]:
        print(f"\n  {field}:")
        erc_items = [f'{k}={v["pct"]}%' for k, v in list(erc_dist[field].items())[:5]]
        a2a_items = [f'{k}={v["pct"]}%' for k, v in list(a2a_dist[field].items())[:5]]
        print(f"    ERC: {' | '.join(erc_items)}")
        print(f"    ERC: {' | '.join(erc_items)}")
        if a2a_records:
            print(f"    A2A: {' | '.join(a2a_items)}")

    # Chi-square tests (only if both datasets present)
    chi2_results = {}
    if erc_records and a2a_records:
        print("\nChi-square tests (ERC vs A2A):")
        for field in FIELDS:
            result = chi2_test(erc_records, a2a_records, field)
            chi2_results[field] = result
            p_str = f"p={result['p_value']}" if isinstance(result['p_value'], float) else result['p_value']
            print(f"  {field:<30} χ²={result['chi2']:.2f}  V={result['cramers_v']:.3f}  {p_str}")

    (STATS_DIR / "r2_chi2_results.json").write_text(
        json.dumps(chi2_results, indent=2, ensure_ascii=False)
    )

    # Stance × argument_type matrices
    erc_matrix = stance_argtype_matrix(erc_records)
    a2a_matrix = stance_argtype_matrix(a2a_records)

    # Structural metrics (raw data counts + consensus annotation counts)
    print("\nComputing structural metrics…")
    erc_raw = erc_raw_stats()
    a2a_raw = a2a_raw_stats()

    erc_dates = [_parse_date(r.get("date")) for r in erc_records]
    erc_dates = [d for d in erc_dates if pd.notna(d)]
    a2a_dates = [_parse_date(r.get("date")) for r in a2a_records]
    a2a_dates = [d for d in a2a_dates if pd.notna(d)]

    erc_unique = len({r.get("author", "") for r in erc_records if r.get("author")})
    a2a_unique = len({r.get("author", "") for r in a2a_records if r.get("author")})

    erc_row = {
        "case": "ERC Agent Cluster (Tier 1+2)",
        "governance_type": "Permissionless DAO",
        "proposal_date": ERC8004_PROPOSAL.strftime("%Y-%m-%d"),
        "mainnet_date": ERC8004_MAINNET.strftime("%Y-%m-%d"),
        "days_to_consensus": (ERC8004_MAINNET - ERC8004_PROPOSAL).days,
        "n_consensus_records": len(erc_records),
        "n_unique_ercs": erc_raw.get("unique_ercs", 0),
        "n_unique_contributors": erc_unique,
        "n_forum_records": erc_raw.get("forum_records", 0),
        "n_github_records": erc_raw.get("github_records", 0),
        "date_start": min(erc_dates).date().isoformat() if erc_dates else "",
        "date_end": max(erc_dates).date().isoformat() if erc_dates else "",
        "arg_technical_pct": erc_dist["argument_type"].get("Technical", {}).get("pct", 0),
        "arg_process_pct": erc_dist["argument_type"].get("Process", {}).get("pct", 0),
        "arg_governance_pct": erc_dist["argument_type"].get("Governance-Principle", {}).get("pct", 0),
        "stance_support_pct": erc_dist["stance"].get("Support", {}).get("pct", 0),
        "stance_oppose_pct": erc_dist["stance"].get("Oppose", {}).get("pct", 0),
        "stance_modify_pct": erc_dist["stance"].get("Modify", {}).get("pct", 0),
        "stance_neutral_pct": erc_dist["stance"].get("Neutral", {}).get("pct", 0),
    }

    a2a_row = {
        "case": "Google A2A",
        "governance_type": "Corporate Hierarchy",
        "proposal_date": A2A_PUBLIC_ANNOUNCE.strftime("%Y-%m-%d"),
        "mainnet_date": "N/A (ongoing)",
        "days_to_consensus": "N/A",
        "n_consensus_records": len(a2a_records),
        "n_unique_ercs": "N/A",
        "n_unique_contributors": a2a_unique,
        "n_forum_records": 0,
        "n_github_records": a2a_raw.get("issues", 0) + a2a_raw.get("prs", 0),
        "date_start": min(a2a_dates).date().isoformat() if a2a_dates else "",
        "date_end": max(a2a_dates).date().isoformat() if a2a_dates else "",
        "arg_technical_pct": a2a_dist["argument_type"].get("Technical", {}).get("pct", 0),
        "arg_process_pct": a2a_dist["argument_type"].get("Process", {}).get("pct", 0),
        "arg_governance_pct": a2a_dist["argument_type"].get("Governance-Principle", {}).get("pct", 0),
        "stance_support_pct": a2a_dist["stance"].get("Support", {}).get("pct", 0),
        "stance_oppose_pct": a2a_dist["stance"].get("Oppose", {}).get("pct", 0),
        "stance_modify_pct": a2a_dist["stance"].get("Modify", {}).get("pct", 0),
        "stance_neutral_pct": a2a_dist["stance"].get("Neutral", {}).get("pct", 0),
    }

    df = pd.DataFrame([erc_row, a2a_row])
    out_csv = ANALYSIS_DIR / "r2_structural_metrics.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n  → {out_csv}")

    # Findings summary
    summary_lines = [
        "# R2 Governance Findings Summary",
        f"\nGenerated: {datetime.now(timezone.utc).isoformat()}",
        f"\n## Data Counts",
        f"- ERC Agent Cluster: {len(erc_records)} consensus records ({erc_raw.get('unique_ercs', '?')} ERCs)",
        f"- Google A2A: {len(a2a_records)} consensus records",
        f"\n## Annotation Distributions",
    ]
    for field in ["argument_type", "stance"]:
        summary_lines.append(f"\n### {field}")
        for case_name, dist in [("ERC", erc_dist[field]), ("A2A", a2a_dist[field])]:
            row = "  " + case_name + ": " + " | ".join(f"{k} {v['pct']}%" for k, v in list(dist.items())[:5])
            summary_lines.append(row)
    summary_lines.append("\n## Chi-square Results")
    for field, result in chi2_results.items():
        p_str = f"p={result['p_value']:.4f}" if isinstance(result['p_value'], float) else "p=N/A"
        summary_lines.append(f"- {field}: χ²={result['chi2']:.2f}, V={result['cramers_v']:.3f}, {p_str}")

    summary_path = STATS_DIR / "r2_findings_summary.md"
    summary_path.write_text("\n".join(summary_lines))
    print(f"  → {summary_path}")

    # Save full distributions for figures
    full_stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "erc": {"distributions": erc_dist, "stance_argtype_matrix": erc_matrix},
        "a2a": {"distributions": a2a_dist, "stance_argtype_matrix": a2a_matrix},
        "chi2": chi2_results,
    }
    (STATS_DIR / "r2_annotation_stats.json").write_text(
        json.dumps(full_stats, indent=2, ensure_ascii=False)
    )
    print(f"  → {STATS_DIR / 'r2_annotation_stats.json'}")
    print("\nDone.")


if __name__ == "__main__":
    main()
