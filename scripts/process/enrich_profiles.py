"""enrich_profiles.py — Fetch public profile metadata for all ERC-8004 and A2A authors.

Sources:
  - Discourse: https://ethereum-magicians.org/u/{username}.json  (no auth, public)
  - GitHub:    https://api.github.com/users/{username}           (PAT from .env)

Outputs:
  data/raw/profiles_forum.json    — Discourse profile data per forum handle
  data/raw/profiles_github.json   — GitHub profile data per GitHub handle
"""

import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent.parent
DATA_RAW = ROOT / "data" / "raw"
ANNOTATED = ROOT / "data" / "annotated"

FORUM_PROFILES_OUT = DATA_RAW / "profiles_forum.json"
GITHUB_PROFILES_OUT = DATA_RAW / "profiles_github.json"

# ---------------------------------------------------------------------------
# Known bots — excluded from profile fetching
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
# HTTP helpers (curl, same pattern as rest of pipeline)
# ---------------------------------------------------------------------------

def _curl(url: str, headers: list[str] | None = None, timeout: int = 15) -> tuple[int, str]:
    """Run curl, return (http_status_code, body_text)."""
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-w", "\n__STATUS__:%{http_code}"]
    if headers:
        for h in headers:
            cmd += ["-H", h]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    raw = result.stdout
    if "__STATUS__:" in raw:
        body, status_part = raw.rsplit("__STATUS__:", 1)
        try:
            status = int(status_part.strip())
        except ValueError:
            status = 0
    else:
        body = raw
        status = 0
    return status, body.strip()


def fetch_json(url: str, headers: list[str] | None = None) -> dict | None:
    status, body = _curl(url, headers)
    if status != 200:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Load annotated records → collect author sets
# ---------------------------------------------------------------------------

def load_authors() -> tuple[set[str], set[str]]:
    """Return (forum_handles, github_handles) for human authors."""
    records_path = ANNOTATED / "annotated_records.json"
    with open(records_path) as f:
        records = json.load(f)

    forum_handles: set[str] = set()
    github_handles: set[str] = set()

    for r in records:
        author = r.get("author", "")
        if not author or is_bot(author):
            continue
        case = r.get("_case", "")
        platform = r.get("platform", "")
        source = r.get("source", "")

        if case == "ERC-8004":
            if platform == "ethereum-magicians" or source == "forum":
                forum_handles.add(author)
            else:
                # GitHub author on ERC-8004 case
                github_handles.add(author)
        # A2A is always GitHub

    # Also load GitHub handles from A2A top contributors (top 30 humans)
    a2a_counts: Counter = Counter(
        r["author"] for r in records
        if r.get("_case") == "Google-A2A" and not is_bot(r.get("author", ""))
    )
    top_a2a = [author for author, _ in a2a_counts.most_common(30)]
    github_handles.update(top_a2a)

    return forum_handles, github_handles


# ---------------------------------------------------------------------------
# Step 1 — Discourse profiles
# ---------------------------------------------------------------------------

def fetch_discourse_profiles(handles: set[str]) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    base = "https://ethereum-magicians.org/u"
    total = len(handles)
    print(f"\n[forum] Fetching {total} Discourse profiles...")

    for i, handle in enumerate(sorted(handles), 1):
        url = f"{base}/{handle}.json"
        data = fetch_json(url)
        if data is None:
            print(f"  [{i}/{total}] {handle}: NOT FOUND")
            profiles[handle] = {"handle": handle, "found": False}
            time.sleep(0.3)
            continue

        user = data.get("user", {})
        profile = {
            "handle": handle,
            "found": True,
            "name": user.get("name", ""),
            "bio_raw": user.get("bio_raw", ""),
            "website": user.get("website", ""),
            "user_title": user.get("title", ""),
            "groups": [g.get("name", "") for g in user.get("groups", [])],
            "location": user.get("location", ""),
        }
        profiles[handle] = profile
        has_bio = bool(profile["bio_raw"] or profile["user_title"])
        print(f"  [{i}/{total}] {handle}: OK  bio={'yes' if has_bio else 'no'}")
        time.sleep(0.5)  # be polite to the forum

    return profiles


# ---------------------------------------------------------------------------
# Step 2 — GitHub profiles
# ---------------------------------------------------------------------------

def load_github_token() -> str | None:
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("GITHUB_PERSONAL_ACCESS_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                return token
    return os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")


def fetch_github_profiles(handles: set[str], token: str | None) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    headers = ["Accept: application/vnd.github+json"]
    if token:
        headers.append(f"Authorization: Bearer {token}")

    total = len(handles)
    print(f"\n[github] Fetching {total} GitHub profiles...")

    for i, handle in enumerate(sorted(handles), 1):
        url = f"https://api.github.com/users/{handle}"
        data = fetch_json(url, headers)
        if data is None or "login" not in data:
            print(f"  [{i}/{total}] {handle}: NOT FOUND")
            profiles[handle] = {"handle": handle, "found": False}
            time.sleep(0.2)
            continue

        profile = {
            "handle": handle,
            "found": True,
            "login": data.get("login", ""),
            "name": data.get("name", ""),
            "company": (data.get("company") or "").strip().lstrip("@"),
            "bio": data.get("bio", "") or "",
            "blog": data.get("blog", "") or "",
            "twitter_username": data.get("twitter_username", "") or "",
            "location": data.get("location", "") or "",
            "public_repos": data.get("public_repos", 0),
            "followers": data.get("followers", 0),
        }
        profiles[handle] = profile
        has_affil = bool(profile["company"] or profile["bio"])
        print(f"  [{i}/{total}] {handle}: OK  company='{profile['company']}'  bio={'yes' if profile['bio'] else 'no'}")
        time.sleep(0.3)

    return profiles


# ---------------------------------------------------------------------------
# Step 3 — Identity normalization (cross-platform same-person detection)
# ---------------------------------------------------------------------------

def normalize_identities(
    forum_profiles: dict[str, dict],
    github_profiles: dict[str, dict],
) -> list[dict]:
    """
    Try to match forum handles to GitHub handles using display name comparison.
    Returns list of cross-platform matches.
    """
    matches = []

    # Build name → github_handle index
    name_to_github: dict[str, str] = {}
    for gh_handle, gp in github_profiles.items():
        name = (gp.get("name") or "").strip().lower()
        if name and len(name) > 3:
            name_to_github[name] = gh_handle

    for forum_handle, fp in forum_profiles.items():
        if not fp.get("found"):
            continue
        forum_name = (fp.get("name") or "").strip().lower()
        if not forum_name:
            continue
        gh_handle = name_to_github.get(forum_name)
        if gh_handle and gh_handle != forum_handle:
            matches.append({
                "forum_handle": forum_handle,
                "github_handle": gh_handle,
                "matched_on": "display_name",
                "name": fp.get("name", ""),
            })
            print(f"  [identity] {forum_handle} (forum) ↔ {gh_handle} (github)  name='{fp.get('name')}'")

    # Hard-coded known aliases from our exploration
    known_aliases = [
        {"forum_handle": "Marco-MetaMask", "github_handle": "MarcoMetaMask",
         "matched_on": "manual", "name": "Marco"},
        {"forum_handle": "davidecrapis.eth", "github_handle": "dcrapis",
         "matched_on": "manual", "name": "Davide Crapis"},
    ]
    existing_pairs = {(m["forum_handle"], m["github_handle"]) for m in matches}
    for alias in known_aliases:
        pair = (alias["forum_handle"], alias["github_handle"])
        if pair not in existing_pairs:
            matches.append(alias)
            print(f"  [identity] {alias['forum_handle']} (forum) ↔ {alias['github_handle']} (github)  [manual]")

    return matches


# ---------------------------------------------------------------------------
# Stats report
# ---------------------------------------------------------------------------

def print_hit_rates(forum_profiles: dict, github_profiles: dict) -> None:
    forum_found = sum(1 for p in forum_profiles.values() if p.get("found"))
    forum_bio = sum(
        1 for p in forum_profiles.values()
        if p.get("found") and (p.get("bio_raw") or p.get("user_title"))
    )
    gh_found = sum(1 for p in github_profiles.values() if p.get("found"))
    gh_company = sum(
        1 for p in github_profiles.values()
        if p.get("found") and p.get("company")
    )
    gh_bio = sum(
        1 for p in github_profiles.values()
        if p.get("found") and p.get("bio")
    )

    print("\n--- Hit rates ---")
    print(f"Forum:  {forum_found}/{len(forum_profiles)} found  |  {forum_bio} with bio/title")
    if forum_found:
        print(f"        bio hit rate: {forum_bio/forum_found:.0%}")
    print(f"GitHub: {gh_found}/{len(github_profiles)} found  |  {gh_company} with company  |  {gh_bio} with bio")
    if gh_found:
        print(f"        company hit rate: {gh_company/gh_found:.0%}")
        print(f"        bio hit rate:     {gh_bio/gh_found:.0%}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== enrich_profiles.py ===")

    forum_handles, github_handles = load_authors()
    print(f"Authors: {len(forum_handles)} forum handles, {len(github_handles)} GitHub handles")

    # --- Forum ---
    forum_profiles = fetch_discourse_profiles(forum_handles)

    # --- GitHub ---
    token = load_github_token()
    if not token:
        print("[warn] No GITHUB_PERSONAL_ACCESS_TOKEN — GitHub rate limit applies (60 req/hr)")
    github_profiles = fetch_github_profiles(github_handles, token)

    # --- Identity normalization ---
    print("\n[identity] Cross-platform matching...")
    identity_map = normalize_identities(forum_profiles, github_profiles)

    # --- Save ---
    output = {
        "forum_profiles": forum_profiles,
        "identity_map": identity_map,
    }
    FORUM_PROFILES_OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    GITHUB_PROFILES_OUT.write_text(json.dumps(github_profiles, indent=2, ensure_ascii=False))

    print(f"\nSaved: {FORUM_PROFILES_OUT}")
    print(f"Saved: {GITHUB_PROFILES_OUT}")
    print(f"Identity pairs found: {len(identity_map)}")

    print_hit_rates(forum_profiles, github_profiles)
    print("\nDone.")


if __name__ == "__main__":
    main()
