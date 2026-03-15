"""merge_manual_institutions.py — Merge R07 manual institution data into author_profiles.json.

Reads:
  data/raw/manual_institutions.json        (from extract_manual_institutions.py)
  data/annotated/author_profiles.json      (existing 626-entry per-author profiles)

Writes:
  data/annotated/author_profiles.json      (in-place update with new fields)

New/updated fields per profile:
  institution_final       str    Best available institution label (may be upgraded)
  institution_source      str    Source of institution_final
  institution_confidence  str    "Confirmed" | "Strong" | "Probable" | "LM_inferred"
  institution_evidence    str    Traceable evidence string (from R07)
  institution_manual      str    Manual institution label if found in R07 (else absent)
  institution_lm          str    Original LLM inference — NEVER overwritten

Priority (high → low):
  eip_header_email > manual_R07 (any confidence) > github_company_field > lm_inferred

Special actions:
  - Jordan Ellis (Google) and Erik Reppel (Coinbase): add as new profile entries
    (EIP co-authors, not in discussion data but institutionally documented)
  - dgenio: correct lm label Google → nosportugal
  - CAG-nolan: correct lm label Google → Unknown
"""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
MANUAL_PATH = ROOT / "data" / "raw" / "manual_institutions.json"
PROFILES_PATH = ROOT / "data" / "annotated" / "author_profiles.json"

# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

SOURCE_RANK = {
    "eip_header_email":   7,
    "manual_R07":         6,   # all confidence levels beat automated sources
    "github_company_field": 3,
    "github_bio":         2,
    "forum_bio":          2,
    "lm_inferred":        1,
    "unknown":            0,
}

CONF_RANK = {
    "Confirmed":   4,
    "Strong":      3,
    "Probable":    2,
    "LM_inferred": 1,
    "Unknown_checked": 1,
}


def source_priority(source: str) -> int:
    return SOURCE_RANK.get(source, 0)


# ---------------------------------------------------------------------------
# Handle index builder
# ---------------------------------------------------------------------------

def build_manual_index(entries: list[dict]) -> dict[str, dict]:
    """Build case-insensitive handle → manual entry map.
    When a handle appears in multiple entries, keep the highest-priority one.
    """
    idx: dict[str, dict] = {}

    def _register(handle: str, entry: dict) -> None:
        if not handle:
            return
        key = handle.lower()
        existing = idx.get(key)
        if existing is None:
            idx[key] = entry
        else:
            # Keep higher priority
            if source_priority(entry["institution_source"]) > source_priority(existing["institution_source"]):
                idx[key] = entry
            elif (source_priority(entry["institution_source"]) == source_priority(existing["institution_source"])
                  and CONF_RANK.get(entry["confidence"], 0) > CONF_RANK.get(existing["confidence"], 0)):
                idx[key] = entry

    for e in entries:
        _register(e.get("primary_handle", ""), e)
        for alt in e.get("alt_handles", []):
            _register(alt, e)

    return idx


# ---------------------------------------------------------------------------
# Profile matching
# ---------------------------------------------------------------------------

def find_manual_entry(profile: dict, index: dict[str, dict]) -> dict | None:
    """Try all known handles for this profile against the manual index."""
    for field in ("canonical_handle", "github_handle", "forum_handle"):
        handle = profile.get(field, "")
        if handle:
            entry = index.get(handle.lower())
            if entry:
                return entry
    return None


# ---------------------------------------------------------------------------
# Profile update
# ---------------------------------------------------------------------------

def update_profile(profile: dict, manual: dict) -> dict:
    """Return new profile dict with manual institution data merged in.
    Never mutates the original dict.
    """
    updated = dict(profile)

    existing_source = profile.get("institution_source", "lm_inferred")
    manual_source = manual["institution_source"]

    # Always upgrade if manual entry exists (manual > all automated)
    # Preserve institution_lm regardless
    updated["institution_manual"] = manual["institution"]
    updated["institution_evidence"] = manual.get("evidence", "")
    updated["institution_evidence_url"] = manual.get("evidence_url", "")

    # Only promote institution_final if this source is higher priority
    if source_priority(manual_source) >= source_priority(existing_source):
        updated["institution_final"] = manual["institution"]
        updated["institution_source"] = manual_source
        updated["institution_confidence"] = manual["confidence"]
    else:
        # Existing source is already higher; just record manual as supplementary
        # institution_confidence reflects the CURRENT source's confidence
        updated.setdefault("institution_confidence", "LM_inferred")

    return updated


def ensure_confidence_field(profile: dict) -> dict:
    """Add institution_confidence if missing (for profiles without manual data)."""
    if "institution_confidence" in profile:
        return profile
    source = profile.get("institution_source", "lm_inferred")
    if source == "github_company_field":
        conf = "Strong"
    elif source in ("github_bio", "forum_bio"):
        conf = "Probable"
    else:
        conf = "LM_inferred"
    return {**profile, "institution_confidence": conf}


# ---------------------------------------------------------------------------
# New profile template for EIP co-authors not in discussion data
# ---------------------------------------------------------------------------

def make_eip_author_profile(entry: dict) -> dict:
    """Create a minimal author profile for EIP header co-authors not in discussions."""
    handle = entry.get("primary_handle") or entry["display_name"].replace(" ", "_")
    return {
        "canonical_handle": handle,
        "github_handle": handle,
        "forum_handle": "",
        "display_name": entry.get("display_name", ""),
        "institution_final": entry["institution"],
        "institution_source": entry["institution_source"],
        "institution_confidence": entry["confidence"],
        "institution_lm": "Unknown",      # never participated in annotated discussions
        "institution_manual": entry["institution"],
        "institution_evidence": entry.get("evidence", ""),
        "institution_evidence_url": entry.get("evidence_url", ""),
        "bio": "",
        "company_raw": "",
        "location": "",
        "cases": ["ERC-8004"],
        "total_records": 0,
        "threads_touched": [],
        "argument_types": {},
        "stances": {},
        "note": "EIP co-author (not in scraped discussion data)",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== merge_manual_institutions.py ===")

    if not MANUAL_PATH.exists():
        raise FileNotFoundError(f"Run extract_manual_institutions.py first: {MANUAL_PATH}")
    if not PROFILES_PATH.exists():
        raise FileNotFoundError(f"Author profiles not found: {PROFILES_PATH}")

    manual_entries: list[dict] = json.loads(MANUAL_PATH.read_text())
    profiles: list[dict] = json.loads(PROFILES_PATH.read_text())

    print(f"Manual entries loaded: {len(manual_entries)}")
    print(f"Author profiles loaded: {len(profiles)}")

    # Build lookup index
    manual_idx = build_manual_index(manual_entries)
    print(f"Handle index size: {len(manual_idx)} unique handles")

    # Merge manual data into existing profiles
    updated_profiles: list[dict] = []
    matches = 0
    upgrades = 0

    existing_handles = {p.get("canonical_handle", "").lower() for p in profiles}
    existing_handles |= {p.get("github_handle", "").lower() for p in profiles if p.get("github_handle")}
    existing_handles |= {p.get("forum_handle", "").lower() for p in profiles if p.get("forum_handle")}

    for profile in profiles:
        manual = find_manual_entry(profile, manual_idx)
        if manual:
            old_institution = profile.get("institution_final", "Unknown")
            old_source = profile.get("institution_source", "lm_inferred")
            new_profile = update_profile(profile, manual)
            matches += 1
            if new_profile["institution_final"] != old_institution:
                upgrades += 1
                print(f"  UPGRADE {profile['canonical_handle']:30s}"
                      f"  {old_institution} ({old_source})"
                      f"  →  {new_profile['institution_final']} ({new_profile['institution_source']})")
            updated_profiles.append(new_profile)
        else:
            updated_profiles.append(ensure_confidence_field(profile))

    # Add EIP co-authors who are not in discussion data (Jordan Ellis, Erik Reppel)
    eip_coauthors = [e for e in manual_entries
                     if e["section"] == "3"
                     and e.get("primary_handle")
                     and e["primary_handle"].lower() not in existing_handles]

    for entry in eip_coauthors:
        new_profile = make_eip_author_profile(entry)
        updated_profiles.append(new_profile)
        print(f"  NEW EIP co-author: {new_profile['canonical_handle']}"
              f" → {new_profile['institution_final']}")

    # Write back
    PROFILES_PATH.write_text(json.dumps(updated_profiles, ensure_ascii=False, indent=2))

    print(f"\nResults:")
    print(f"  Profiles matched to manual data: {matches} / {len(profiles)}")
    print(f"  Institution label upgrades:      {upgrades}")
    print(f"  New EIP co-author entries:       {len(eip_coauthors)}")
    print(f"  Total profiles written:          {len(updated_profiles)}")

    # Confidence distribution after merge
    from collections import Counter
    conf_dist = Counter(p.get("institution_confidence", "?") for p in updated_profiles)
    src_dist = Counter(p.get("institution_source", "?") for p in updated_profiles)
    print(f"\nConfidence distribution: {dict(conf_dist)}")
    print(f"Source distribution:     {dict(src_dist)}")
    print(f"\nSaved → {PROFILES_PATH}")


if __name__ == "__main__":
    main()
