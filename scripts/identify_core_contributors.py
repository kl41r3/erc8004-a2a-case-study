"""identify_core_contributors.py — Identify and profile core contributors per case.

Selection criteria:
  ERC-8004:  ≥3 records  OR  participated in ≥2 PRs/threads
  A2A:       ≥50 records  AND  not a bot

Outputs:
  analysis/core_contributors.csv    — structured per-author analysis
  analysis/cross_case_overlap.csv   — authors appearing in both cases
  (stdout) manual enrichment checklist for top ERC-8004 contributors
"""

import csv
import json
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
ANNOTATED = ROOT / "data" / "annotated"
ANALYSIS = ROOT / "analysis"

AUTHOR_PROFILES_FILE = ANNOTATED / "author_profiles.json"
ANNOTATED_RECORDS_FILE = ANNOTATED / "annotated_records.json"
CORE_CONTRIBUTORS_OUT = ANALYSIS / "core_contributors.csv"
CROSS_CASE_OUT = ANALYSIS / "cross_case_overlap.csv"

ANALYSIS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Known bots
# ---------------------------------------------------------------------------
BOTS = {
    "eip-review-bot",
    "gemini-code-assist[bot]",
    "git-vote[bot]",
    "google-cla[bot]",
    "actions-user",
    "github-actions",
    "dependabot",
    "dependabot[bot]",
}


def is_bot(username: str) -> bool:
    return username in BOTS or username.endswith("[bot]") or username.endswith("-bot")


# ---------------------------------------------------------------------------
# Role inference
# ---------------------------------------------------------------------------

def infer_role(author_profile: dict, records: list[dict]) -> str:
    """
    Derive a role label from contribution pattern.
    Roles: Proposer | Core Developer | Reviewer | Community Voice | Implementer
    """
    sources = Counter(r.get("source", "") for r in records)
    arg_types = author_profile.get("argument_types", {})
    stances = author_profile.get("stances", {})
    total = author_profile.get("total_records", 0)

    is_proposer = (
        sources.get("github_pr_body", 0) > 0
        or sources.get("pr", 0) > 0
        or sources.get("forum", 0) > 3
    ) and stances.get("Support", 0) > stances.get("Oppose", 0)

    is_reviewer = (
        sources.get("github_review", 0) > 0
        or sources.get("review_comment", 0) > 0
        or arg_types.get("Process", 0) > 0
    )

    is_implementer = (
        sources.get("commit", 0) > 0
        or arg_types.get("Technical", 0) > total * 0.5
    )

    if is_proposer and total >= 3:
        return "Proposer"
    if is_implementer and total >= 5:
        return "Core Developer"
    if is_reviewer:
        return "Reviewer"
    if total >= 5:
        return "Community Voice"
    return "Occasional Contributor"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data() -> tuple[list[dict], list[dict]]:
    with open(ANNOTATED_RECORDS_FILE) as f:
        records = json.load(f)

    profiles: list[dict] = []
    if AUTHOR_PROFILES_FILE.exists():
        profiles = json.loads(AUTHOR_PROFILES_FILE.read_text())
    else:
        print("[warn] author_profiles.json not found — run enrich_institutions.py first")

    return records, profiles


# ---------------------------------------------------------------------------
# Core contributor selection
# ---------------------------------------------------------------------------

def select_core(profiles: list[dict], records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (erc_core, a2a_core) lists."""

    # Index records by canonical_handle
    records_by_handle: dict[str, list[dict]] = {}
    for r in records:
        author = r.get("author", "")
        if author and not is_bot(author):
            records_by_handle.setdefault(author, []).append(r)

    erc_core: list[dict] = []
    a2a_core: list[dict] = []

    for p in profiles:
        if is_bot(p["canonical_handle"]):
            continue

        cases = p.get("cases", [])
        total = p.get("total_records", 0)
        threads = p.get("threads_touched", [])
        n_threads = len(threads)

        # Get records for this person
        handle_recs = records_by_handle.get(p["canonical_handle"], [])
        # Also check forum handle
        if p.get("forum_handle"):
            handle_recs = handle_recs + records_by_handle.get(p["forum_handle"], [])

        role = infer_role(p, handle_recs)

        entry = {**p, "role": role}

        if "ERC-8004" in cases:
            erc_recs = [r for r in handle_recs if r.get("_case") == "ERC-8004"]
            erc_total = len(erc_recs)
            erc_threads = len({r.get("pr_number") for r in erc_recs if r.get("pr_number")})
            erc_forum = len([r for r in erc_recs if r.get("source") == "forum"])
            if erc_total >= 3 or erc_threads >= 2:
                erc_core.append({**entry, "case_records": erc_total, "case_threads": erc_threads, "forum_posts": erc_forum})

        if "Google-A2A" in cases:
            a2a_recs = [r for r in handle_recs if r.get("_case") == "Google-A2A"]
            a2a_total = len(a2a_recs)
            if a2a_total >= 50:
                a2a_core.append({**entry, "case_records": a2a_total})

    # Sort by record count desc
    erc_core.sort(key=lambda x: x["case_records"], reverse=True)
    a2a_core.sort(key=lambda x: x["case_records"], reverse=True)

    return erc_core, a2a_core


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

CORE_CSV_FIELDS = [
    "canonical_handle", "display_name", "case", "institution_final",
    "institution_source", "role", "case_records", "total_records",
    "argument_types_summary", "stances_summary",
    "threads_touched", "bio_snippet",
]


def build_csv_row(p: dict, case: str) -> dict:
    arg_types = p.get("argument_types", {})
    stances = p.get("stances", {})

    top_arg = max(arg_types, key=arg_types.get) if arg_types else ""
    top_stance = max(stances, key=stances.get) if stances else ""
    arg_str = "; ".join(f"{k}:{v}" for k, v in arg_types.items()) if arg_types else ""
    stance_str = "; ".join(f"{k}:{v}" for k, v in stances.items()) if stances else ""

    bio = p.get("bio", "") or ""
    bio_snippet = bio[:100].replace("\n", " ") if bio else ""

    threads = p.get("threads_touched", [])

    return {
        "canonical_handle": p["canonical_handle"],
        "display_name": p.get("display_name", ""),
        "case": case,
        "institution_final": p.get("institution_final", ""),
        "institution_source": p.get("institution_source", ""),
        "role": p.get("role", ""),
        "case_records": p.get("case_records", 0),
        "total_records": p.get("total_records", 0),
        "argument_types_summary": arg_str,
        "stances_summary": stance_str,
        "threads_touched": "; ".join(threads[:10]),
        "bio_snippet": bio_snippet,
    }


# ---------------------------------------------------------------------------
# Cross-case overlap
# ---------------------------------------------------------------------------

def build_cross_case_overlap(profiles: list[dict]) -> list[dict]:
    overlap = []
    for p in profiles:
        cases = p.get("cases", [])
        if "ERC-8004" in cases and "Google-A2A" in cases:
            overlap.append({
                "canonical_handle": p["canonical_handle"],
                "display_name": p.get("display_name", ""),
                "institution_final": p.get("institution_final", ""),
                "total_records": p.get("total_records", 0),
            })
    return sorted(overlap, key=lambda x: x["total_records"], reverse=True)


# ---------------------------------------------------------------------------
# Manual enrichment checklist
# ---------------------------------------------------------------------------

def print_checklist(erc_core: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("MANUAL ENRICHMENT CHECKLIST — Top ERC-8004 contributors")
    print("Edit: data/raw/manual_overrides.json  (format: {handle: {institution, notes}})")
    print("=" * 70)

    top15 = erc_core[:15]
    for i, p in enumerate(top15, 1):
        handle = p["canonical_handle"]
        gh_handle = p.get("github_handle") or handle
        name = p.get("display_name", "")
        inst = p.get("institution_final", "Unknown")
        source = p.get("institution_source", "")
        n_recs = p.get("case_records", 0)
        threads = p.get("threads_touched", [])
        role = p.get("role", "")
        arg_types = p.get("argument_types", {})
        top_arg = max(arg_types, key=arg_types.get) if arg_types else "?"

        # Key points from annotations (would need to pull from records — just show top arg for now)
        print(f"\n{i:>2}. {handle}  ({name})")
        print(f"    GitHub:   https://github.com/{gh_handle}")
        print(f"    LinkedIn: https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '+') or handle}")
        print(f"    Current institution:  {inst}  [{source}]")
        print(f"    Records: {n_recs}  |  Threads: {'; '.join(threads[:5])}  |  Role: {role}")
        print(f"    Primary argument type: {top_arg}")
        print(f"    Manual override → data/raw/manual_overrides.json: {json.dumps({handle: {'institution': inst, 'notes': ''}})}")

    print("\n" + "=" * 70)
    print("Expected manual_overrides.json format:")
    print(json.dumps({
        "MarcoMetaMask": {"institution": "MetaMask", "notes": "Core MetaMask wallet eng, confirmed via GitHub profile"},
        "pcarranzav":    {"institution": "Independent", "notes": "independent researcher, no org affiliation found"},
    }, indent=2))
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== identify_core_contributors.py ===")

    records, profiles = load_data()
    print(f"Loaded {len(profiles)} author profiles, {len(records)} annotated records")

    erc_core, a2a_core = select_core(profiles, records)
    print(f"\nERC-8004 core contributors: {len(erc_core)}")
    print(f"A2A core contributors:      {len(a2a_core)}")

    # Write CSV
    rows = [build_csv_row(p, "ERC-8004") for p in erc_core] + \
           [build_csv_row(p, "Google-A2A") for p in a2a_core]

    with open(CORE_CONTRIBUTORS_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CORE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {CORE_CONTRIBUTORS_OUT}  ({len(rows)} rows)")

    # Cross-case overlap
    overlap = build_cross_case_overlap(profiles)
    print(f"\nCross-case overlap: {len(overlap)} authors in both cases")
    if overlap:
        for o in overlap[:5]:
            print(f"  {o['canonical_handle']} ({o['display_name']}) — {o['institution_final']} — {o['total_records']} records")

    with open(CROSS_CASE_OUT, "w", newline="", encoding="utf-8") as f:
        if overlap:
            writer = csv.DictWriter(f, fieldnames=list(overlap[0].keys()))
            writer.writeheader()
            writer.writerows(overlap)
        else:
            f.write("canonical_handle,display_name,institution_final,total_records\n")
    print(f"Saved: {CROSS_CASE_OUT}")

    # Print ERC-8004 summary table
    print("\nERC-8004 Core Contributors:")
    print(f"  {'Handle':<22} {'Institution':<22} {'Role':<22} {'Recs':>4} {'Threads':>7}")
    print("  " + "-" * 80)
    for p in erc_core[:20]:
        threads_str = str(p.get("case_threads", len(p.get("threads_touched", []))))
        print(f"  {p['canonical_handle']:<22} {p['institution_final']:<22} {p['role']:<22} {p['case_records']:>4} {threads_str:>7}")

    print("\nA2A Core Contributors (≥50 records):")
    print(f"  {'Handle':<22} {'Institution':<22} {'Role':<22} {'Recs':>4}")
    print("  " + "-" * 73)
    for p in a2a_core[:15]:
        print(f"  {p['canonical_handle']:<22} {p['institution_final']:<22} {p['role']:<22} {p['case_records']:>4}")

    # Manual checklist
    print_checklist(erc_core)

    print("\nDone.")


if __name__ == "__main__":
    main()
