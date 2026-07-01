"""
scrape_r2_github.py — Round-2 GitHub PR scraper for ethereum/ERCs.

Mirrors the ERC-8004 "forum + PR" treatment for the whole sampling frame so both
tiers are measured on the same ruler:

  Tier 1: the 9 known ERC-8004 lifecycle PRs  → data/raw/r2/tier1/erc8004_github.json
  Tier 2: PR(s) discovered per cluster ERC     → data/raw/r2/tier2/cluster_github.json

PR discovery per ERC (precise-first, logged):
  A) GET /commits?path=ERCS/erc-N.md  → for each commit, /commits/{sha}/pulls
     (exact history of PRs that modified the spec file; catches merged drafts)
  B) GET /search/issues type:pr "ERC-N"  → confirm each candidate via /pulls/{n}/files
     touches ERCS/erc-N.md (catches still-open submission PRs)

Per-ERC provenance (PRs found, method, record counts, ERCs with 0 PRs) is written
to a manifest. Reuses the fetch_pr logic of scrape_erc8004_prs.py.

Usage:
  uv run python scripts/scrape/scrape_r2_github.py --tier both
  uv run python scripts/scrape/scrape_r2_github.py --tier tier2
"""

import argparse
import csv
import json
import os
import re
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, DATA_RAW_R2_TIER1, DATA_RAW_R2_TIER2, METRICS_R2_AGENT_ERC_UNIVERSE
from lib.models import ERC8004_CORE_PRS

UNIVERSE_CSV = METRICS_R2_AGENT_ERC_UNIVERSE
OUT_TIER1 = DATA_RAW_R2_TIER1
OUT_TIER2 = DATA_RAW_R2_TIER2
REPO = "ethereum/ERCs"
BASE_API = "https://api.github.com"


def load_token() -> str | None:
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token:
        return token
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("GITHUB_PERSONAL_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def curl_get(url: str, token: str | None, tries: int = 4):
    cmd = ["curl", "-s", "-L", "--max-time", "30",
           "-H", "Accept: application/vnd.github+json",
           "-H", "User-Agent: Mozilla/5.0 (research scraper; academic use)"]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    last = ""
    for attempt in range(tries):
        r = subprocess.run(cmd + [url], capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            try:
                parsed = json.loads(r.stdout)
            except json.JSONDecodeError as e:
                last = f"json: {e}"; time.sleep(2 + 2 * attempt); continue
            if isinstance(parsed, dict) and parsed.get("message") and "rate limit" in parsed["message"].lower():
                print(f"    rate-limited, sleeping 60s…"); time.sleep(60); continue
            return parsed
        last = f"rc={r.returncode}: {r.stderr[:120]}"
        time.sleep(2 + 2 * attempt)
    raise RuntimeError(f"curl_get failed ({url}): {last}")


def fetch_paginated(base_url: str, token: str | None, label: str) -> list[dict]:
    records, page = [], 1
    while True:
        sep = "&" if "?" in base_url else "?"
        try:
            items = curl_get(f"{base_url}{sep}per_page=100&page={page}", token)
        except Exception as e:
            print(f"    [{label}] page {page} error: {e}"); break
        if not isinstance(items, list) or not items:
            break
        records.extend(items)
        if len(items) < 100:
            break
        page += 1
        time.sleep(0.3)
    return records


def fetch_pr(pr_number: int, pr_desc: str, tier: str, erc: str, token: str | None) -> list[dict]:
    """All governance-relevant content for one PR (body + comments + reviews)."""
    records = []
    base = {"tier": tier, "erc": erc, "platform": "github",
            "pr_number": pr_number, "pr_description": pr_desc}

    try:
        pr = curl_get(f"{BASE_API}/repos/{REPO}/pulls/{pr_number}", token)
        body = (pr.get("body") or "").strip()
        if body:
            records.append({**base, "source": "github_pr_body",
                            "comment_id": f"pr_{pr_number}_body", "date": pr.get("created_at"),
                            "author": (pr.get("user") or {}).get("login"), "raw_text": body,
                            "state": pr.get("state"), "merged": pr.get("merged"),
                            "url": pr.get("html_url")})
        pr_title = pr.get("title", pr_desc)
        pr_state = pr.get("state")
    except Exception as e:
        print(f"    [pr_body] #{pr_number} error: {e}")
        pr_title, pr_state = pr_desc, None

    for item in fetch_paginated(f"{BASE_API}/repos/{REPO}/issues/{pr_number}/comments", token, "issue_comments"):
        b = (item.get("body") or "").strip()
        if b:
            records.append({**base, "source": "github_issue_comment", "comment_id": item.get("id"),
                            "date": item.get("created_at"), "author": (item.get("user") or {}).get("login"),
                            "raw_text": b, "state": None, "url": item.get("html_url")})

    for item in fetch_paginated(f"{BASE_API}/repos/{REPO}/pulls/{pr_number}/comments", token, "review_comments"):
        b = (item.get("body") or "").strip()
        if b:
            records.append({**base, "source": "github_review_comment", "comment_id": item.get("id"),
                            "date": item.get("created_at"), "author": (item.get("user") or {}).get("login"),
                            "raw_text": b, "state": None, "url": item.get("html_url")})

    for item in fetch_paginated(f"{BASE_API}/repos/{REPO}/pulls/{pr_number}/reviews", token, "reviews"):
        b = (item.get("body") or "").strip()
        if b:
            records.append({**base, "source": "github_review", "comment_id": item.get("id"),
                            "date": item.get("submitted_at"), "author": (item.get("user") or {}).get("login"),
                            "raw_text": b, "state": item.get("state"), "url": item.get("html_url")})

    # annotate records with PR title/state for context
    for r in records:
        r.setdefault("pr_title", pr_title)
    print(f"    PR #{pr_number} [{pr_state}]: {len(records)} records — {pr_title[:45]}")
    return records


def discover_prs(erc: str, token: str | None) -> dict[int, str]:
    """Return {pr_number: discovery_method} for one ERC number."""
    found: dict[int, str] = {}
    if not erc:
        return found
    # A) commits on the spec file → associated pulls
    try:
        commits = curl_get(f"{BASE_API}/repos/{REPO}/commits?path=ERCS/erc-{erc}.md&per_page=100", token)
        if isinstance(commits, list):
            for c in commits:
                msg = (c.get("commit", {}) or {}).get("message", "")
                m = re.search(r"\(#(\d+)\)", msg)
                if m:
                    found.setdefault(int(m.group(1)), "commit_msg")
                sha = c.get("sha")
                if sha:
                    try:
                        pulls = curl_get(f"{BASE_API}/repos/{REPO}/commits/{sha}/pulls", token)
                        for p in (pulls if isinstance(pulls, list) else []):
                            found.setdefault(p["number"], "commit_pulls")
                    except Exception:
                        pass
                    time.sleep(0.2)
    except Exception as e:
        print(f"    discover A (erc-{erc}) error: {e}")
    # B) search open/other PRs by phrase, confirm changed files
    try:
        res = curl_get(f"{BASE_API}/search/issues?q=repo:{REPO}+type:pr+ERC-{erc}&per_page=20", token)
        for item in (res.get("items", []) if isinstance(res, dict) else []):
            n = item["number"]
            if n in found:
                continue
            try:
                files = curl_get(f"{BASE_API}/repos/{REPO}/pulls/{n}/files?per_page=100", token)
                names = {f.get("filename") for f in (files if isinstance(files, list) else [])}
                if f"ERCS/erc-{erc}.md" in names:
                    found[n] = "search_confirmed"
            except Exception:
                pass
            time.sleep(0.2)
        time.sleep(1.0)  # search API: 30 req/min
    except Exception as e:
        print(f"    discover B (erc-{erc}) error: {e}")
    return found


def run_tier1(token):
    OUT_TIER1.mkdir(parents=True, exist_ok=True)
    print("\n=== TIER 1 GitHub: 9 ERC-8004 lifecycle PRs ===")
    records = []
    for pr, desc in sorted(ERC8004_CORE_PRS.items()):
        records.extend(fetch_pr(pr, desc, "tier1", "8004", token))
        time.sleep(0.4)
    (OUT_TIER1 / "erc8004_github.json").write_text(json.dumps(records, indent=2, ensure_ascii=False))
    manifest = {"scraped_at": datetime.now(timezone.utc).isoformat(), "tier": "tier1",
                "repo": REPO, "prs": list(ERC8004_CORE_PRS), "total_records": len(records),
                "by_source": dict(Counter(r["source"] for r in records))}
    (OUT_TIER1 / "tier1_github_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"  → {len(records)} records → {OUT_TIER1/'erc8004_github.json'}")


def run_tier2(token):
    """Incremental + resumable: saves after every ERC so an interrupt loses
    at most one ERC, and a rerun skips ERCs already completed."""
    OUT_TIER2.mkdir(parents=True, exist_ok=True)
    out_json = OUT_TIER2 / "cluster_github.json"
    out_manifest = OUT_TIER2 / "tier2_github_manifest.json"

    rows = [r for r in csv.DictReader(open(UNIVERSE_CSV))
            if r["include"] == "Y" and r["tier"] == "tier2"]

    # resume: load prior records + completed-ERC provenance
    all_records = json.loads(out_json.read_text()) if out_json.exists() else []
    prov = []
    done_ercs = set()
    if out_manifest.exists():
        prior = json.loads(out_manifest.read_text())
        prov = prior.get("per_erc", [])
        done_ercs = {p["topic_id"] for p in prov}  # key by topic_id (erc may be empty)

    def save():
        # dedup: same PR can be reached via two forum topics of one ERC
        seen, deduped = set(), []
        for r in all_records:
            k = (r["pr_number"], r.get("comment_id"))
            if k in seen:
                continue
            seen.add(k)
            deduped.append(r)
        out_json.write_text(json.dumps(deduped, indent=2, ensure_ascii=False))
        no_pr = [p["erc"] or p["topic_id"] for p in prov if not p["prs_found"]]
        out_manifest.write_text(json.dumps({
            "scraped_at": datetime.now(timezone.utc).isoformat(), "tier": "tier2",
            "repo": REPO, "ercs_processed": len(prov), "ercs_total": len(rows),
            "total_records": len(deduped), "raw_records_before_dedup": len(all_records),
            "ercs_with_no_pr": no_pr,
            "by_source": dict(Counter(r["source"] for r in deduped)),
            "per_erc": prov}, indent=2, ensure_ascii=False))

    print(f"\n=== TIER 2 GitHub: {len(rows)} ERCs ({len(done_ercs)} already done, resuming) ===",
          flush=True)
    for r in sorted(rows, key=lambda x: -int(x["posts"])):
        erc, topic_id = r["erc"], r["topic_id"]
        if topic_id in done_ercs:
            print(f"  ERC-{erc or '(none)'} (topic {topic_id}): SKIP (done)", flush=True)
            continue
        prs = discover_prs(erc, token)
        print(f"  ERC-{erc or '(none)'} (topic {topic_id}): {len(prs)} PR(s) {sorted(prs)}", flush=True)
        recs = []
        for pr_num in sorted(prs):
            recs.extend(fetch_pr(pr_num, f"ERC-{erc}", "tier2", erc, token))
            time.sleep(0.4)
        all_records.extend(recs)
        prov.append({"erc": erc, "topic_id": topic_id, "title": r["title"],
                     "prs_found": sorted(prs), "discovery": prs, "records": len(recs)})
        save()  # checkpoint after every ERC
    save()
    no_pr = [p["erc"] or p["topic_id"] for p in prov if not p["prs_found"]]
    print(f"  → {len(all_records)} records → {out_json}", flush=True)
    print(f"  → ERCs with NO PR found (forum-only): {no_pr}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["tier1", "tier2", "both"], default="both")
    args = ap.parse_args()
    token = load_token()
    print("GitHub PAT loaded" if token else "WARNING: no PAT (60 req/hr anon)")
    if args.tier in ("tier1", "both"):
        run_tier1(token)
    if args.tier in ("tier2", "both"):
        run_tier2(token)


if __name__ == "__main__":
    main()
