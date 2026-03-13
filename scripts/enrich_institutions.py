"""enrich_institutions.py — Re-annotate institution labels using profile data.

Strategy:
  1. If GitHub company field contains a recognizable org → deterministic override
  2. If bio/title contains a recognizable org → deterministic override
  3. Otherwise keep original LLM annotation

Outputs:
  data/annotated/author_profiles.json  — one entry per unique author, both cases
"""

import json
import re
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
ANNOTATED = ROOT / "data" / "annotated"

ANNOTATED_RECORDS = ANNOTATED / "annotated_records.json"
FORUM_PROFILES_FILE = DATA_RAW / "profiles_forum.json"
GITHUB_PROFILES_FILE = DATA_RAW / "profiles_github.json"
AUTHOR_PROFILES_OUT = ANNOTATED / "author_profiles.json"

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
# Institution detection rules
# ---------------------------------------------------------------------------
# Order matters — more specific patterns first.
# Each entry: (regex_pattern, canonical_institution_name)
INSTITUTION_PATTERNS: list[tuple[str, str]] = [
    (r"\bmetamask\b",              "MetaMask"),
    (r"\bconsenSys\b|\bconsensys\b", "ConsenSys"),
    (r"\bethereumfoundation\b|\bethereum foundation\b|\bef\b|\befdn\b", "Ethereum Foundation"),
    (r"\bgoogle\b",                "Google"),
    (r"\bmicrosoft\b",             "Microsoft"),
    (r"\bcoinbase\b",              "Coinbase"),
    (r"\bopenai\b",                "OpenAI"),
    (r"\banthropicl\b|\banthropic\b", "Anthropic"),
    (r"\bprotocol labs\b",         "Protocol Labs"),
    (r"\boasis\b",                 "Oasis"),
    (r"\bgnosisguild\b|\bgnosis guild\b|\bgnosis\b", "Gnosis"),
    (r"\bsafe\b",                  "Safe"),
    (r"\barkham\b",                "Arkham"),
    (r"\bzk ?sync\b|\bmatter labs\b", "Matter Labs"),
    (r"\bstarkware\b",             "StarkWare"),
    (r"\boptimism\b",              "Optimism"),
    (r"\barbitrum\b|\boffchain labs\b", "Offchain Labs"),
    (r"\bpolygon\b",               "Polygon"),
    (r"\bchainlink\b",             "Chainlink"),
    (r"\bender labs\b|\bender\b",  "Ender Labs"),
    (r"\balchemy\b",               "Alchemy"),
    (r"\binfura\b",                "Infura"),
    (r"\buniversity\b|\buniv\b|\bcollege\b|\bacademia\b|\bphd\b", "Academia"),
    (r"\bindependent\b|\bfreelance\b|\bself.?employed\b", "Independent"),
]

_compiled_patterns = [
    (re.compile(pat, re.IGNORECASE), label)
    for pat, label in INSTITUTION_PATTERNS
]


def detect_institution_from_text(text: str) -> str | None:
    """Return institution label if a pattern matches, else None."""
    if not text:
        return None
    for pattern, label in _compiled_patterns:
        if pattern.search(text):
            return label
    return None


def detect_institution(github_profile: dict | None, forum_profile: dict | None) -> tuple[str, str]:
    """
    Return (institution_label, source) where source is one of:
      'github_company_field' | 'github_bio' | 'forum_bio' | 'forum_title' | 'not_found'
    """
    if github_profile and github_profile.get("found"):
        company = github_profile.get("company", "")
        label = detect_institution_from_text(company)
        if label:
            return label, "github_company_field"

        bio = github_profile.get("bio", "")
        label = detect_institution_from_text(bio)
        if label:
            return label, "github_bio"

    if forum_profile and forum_profile.get("found"):
        bio_raw = forum_profile.get("bio_raw", "")
        label = detect_institution_from_text(bio_raw)
        if label:
            return label, "forum_bio"

        title = forum_profile.get("user_title", "")
        label = detect_institution_from_text(title)
        if label:
            return label, "forum_title"

    return "", "not_found"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data() -> tuple[list[dict], dict, dict, dict, list[dict]]:
    with open(ANNOTATED_RECORDS) as f:
        records = json.load(f)

    # Forum profiles
    forum_data: dict[str, dict] = {}
    identity_map: list[dict] = []
    if FORUM_PROFILES_FILE.exists():
        raw = json.loads(FORUM_PROFILES_FILE.read_text())
        forum_data = raw.get("forum_profiles", {})
        identity_map = raw.get("identity_map", [])
    else:
        print("[warn] profiles_forum.json not found — run enrich_profiles.py first")

    # GitHub profiles
    github_data: dict[str, dict] = {}
    if GITHUB_PROFILES_FILE.exists():
        github_data = json.loads(GITHUB_PROFILES_FILE.read_text())
    else:
        print("[warn] profiles_github.json not found — run enrich_profiles.py first")

    return records, forum_data, github_data, {}, identity_map


# ---------------------------------------------------------------------------
# Build cross-handle mapping
# ---------------------------------------------------------------------------

def build_handle_index(
    identity_map: list[dict],
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns:
      forum_to_github: dict mapping forum_handle → github_handle
      github_to_forum: dict mapping github_handle → forum_handle
    """
    f2g: dict[str, str] = {}
    g2f: dict[str, str] = {}
    for entry in identity_map:
        fh = entry.get("forum_handle", "")
        gh = entry.get("github_handle", "")
        if fh and gh:
            f2g[fh] = gh
            g2f[gh] = fh
    return f2g, g2f


# ---------------------------------------------------------------------------
# Per-author aggregation
# ---------------------------------------------------------------------------

def aggregate_authors(
    records: list[dict],
    forum_data: dict[str, dict],
    github_data: dict[str, dict],
    identity_map: list[dict],
) -> dict[str, dict]:
    """
    Build one author profile entry per unique (canonical) author.
    We canonicalize by preferring the GitHub handle when we have an identity match.
    """
    forum_to_github, github_to_forum = build_handle_index(identity_map)

    # author_key → canonical handle for deduplication
    def canonical(author: str, case: str, platform: str) -> str:
        if platform == "ethereum-magicians" or (case == "ERC-8004" and platform != "github"):
            return forum_to_github.get(author, author)
        return author

    # Collect per-canonical records
    author_records: dict[str, list[dict]] = {}
    for r in records:
        author = r.get("author", "")
        if not author or is_bot(author):
            continue
        key = canonical(author, r.get("_case", ""), r.get("platform", ""))
        author_records.setdefault(key, []).append(r)

    profiles: dict[str, dict] = {}
    for canon_handle, recs in author_records.items():
        # Determine forum/github handles
        gh_handle = canon_handle
        forum_handle = github_to_forum.get(canon_handle, "")

        # If canon is a forum handle (not matched to github), set forum_handle
        if not forum_handle and canon_handle in forum_data:
            forum_handle = canon_handle
            gh_handle = ""

        # Gather profile data
        gp = github_data.get(gh_handle) if gh_handle else None
        fp = forum_data.get(forum_handle) if forum_handle else None

        # Display name: prefer GitHub name, then forum name, then handle
        display_name = ""
        if gp and gp.get("name"):
            display_name = gp["name"]
        elif fp and fp.get("name"):
            display_name = fp["name"]
        elif gp and gp.get("login"):
            display_name = gp["login"]
        else:
            display_name = canon_handle

        # Institution from profile
        inst_profile, inst_source_profile = detect_institution(gp, fp)

        # Institution from LLM annotations (majority vote)
        lm_institutions = [
            r["annotation"]["stakeholder_institution"]
            for r in recs
            if r.get("annotation") and r["annotation"].get("stakeholder_institution")
        ]
        lm_institution = Counter(lm_institutions).most_common(1)[0][0] if lm_institutions else "Unknown"

        # Final institution: prefer profile-derived, fall back to LLM
        if inst_profile:
            institution_final = inst_profile
            institution_source = inst_source_profile
        else:
            institution_final = lm_institution
            institution_source = "lm_inferred"

        # Argument types
        arg_types = Counter(
            r["annotation"]["argument_type"]
            for r in recs
            if r.get("annotation") and r["annotation"].get("argument_type")
        )
        stances = Counter(
            r["annotation"]["stance"]
            for r in recs
            if r.get("annotation") and r["annotation"].get("stance")
        )

        # Cases
        cases = sorted({r.get("_case", "") for r in recs})

        # PRs / threads touched (ERC-8004 GitHub PRs, or A2A issue/PR numbers)
        threads: set[str] = set()
        for r in recs:
            if "pr_number" in r:
                threads.add(f"PR#{r['pr_number']}")
            elif "issue_number" in r:
                threads.add(f"I#{r['issue_number']}")

        profiles[canon_handle] = {
            "canonical_handle": canon_handle,
            "github_handle": gh_handle,
            "forum_handle": forum_handle,
            "display_name": display_name,
            "institution_final": institution_final,
            "institution_source": institution_source,
            "institution_lm": lm_institution,
            "bio": (gp or {}).get("bio", "") or (fp or {}).get("bio_raw", "") or "",
            "company_raw": (gp or {}).get("company", "") or "",
            "location": (gp or {}).get("location", "") or (fp or {}).get("location", "") or "",
            "cases": cases,
            "total_records": len(recs),
            "threads_touched": sorted(threads),
            "argument_types": dict(arg_types.most_common()),
            "stances": dict(stances.most_common()),
        }

    return profiles


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def print_stats(profiles: dict[str, dict]) -> None:
    total = len(profiles)
    profile_sourced = sum(
        1 for p in profiles.values()
        if p["institution_source"] != "lm_inferred"
    )
    company_field = sum(
        1 for p in profiles.values()
        if p["institution_source"] == "github_company_field"
    )

    print(f"\n--- Author profiles stats ---")
    print(f"Total unique canonical authors: {total}")
    print(f"Institution from profile data:  {profile_sourced} ({profile_sourced/total:.0%})")
    print(f"  of which github company:      {company_field}")
    print(f"Institution from LLM only:      {total - profile_sourced} ({(total - profile_sourced)/total:.0%})")

    # Top institution distribution
    inst_counts = Counter(p["institution_final"] for p in profiles.values())
    print("\nTop institutions (all cases):")
    for inst, count in inst_counts.most_common(10):
        print(f"  {inst:<30} {count}")

    # Known persons spot-check
    checks = [
        ("MarcoMetaMask", "MetaMask"),
        ("lightclient", "Ethereum Foundation"),
        ("holtskinner", "Google"),
    ]
    print("\nSpot-checks:")
    for handle, expected in checks:
        p = profiles.get(handle)
        if p:
            ok = "OK" if p["institution_final"] == expected else "MISMATCH"
            print(f"  [{ok}] {handle}: got '{p['institution_final']}' (expected '{expected}') source={p['institution_source']}")
        else:
            print(f"  [MISSING] {handle} not in profiles")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== enrich_institutions.py ===")

    records, forum_data, github_data, _, identity_map = load_data()
    print(f"Loaded {len(records)} records, {len(forum_data)} forum profiles, {len(github_data)} GitHub profiles")

    profiles = aggregate_authors(records, forum_data, github_data, identity_map)
    print(f"Built {len(profiles)} author profiles")

    AUTHOR_PROFILES_OUT.write_text(json.dumps(list(profiles.values()), indent=2, ensure_ascii=False))
    print(f"Saved: {AUTHOR_PROFILES_OUT}")

    print_stats(profiles)
    print("\nDone.")


if __name__ == "__main__":
    main()
