"""annotate_gitvote.py — Annotate git-vote PR records and merge into annotated_records.json.

Reads data/raw/a2a_gitvote_prs.json, annotates non-bot substantive comments
using Anthropic Claude, then appends results to data/annotated/annotated_records.json.

Also writes a focused gitvote governance summary to analysis/gitvote_analysis.md.
"""

import json
import os
import re
import time
from pathlib import Path

import urllib.request

ROOT = Path(__file__).parent.parent.parent
DATA_RAW = ROOT / "data" / "raw"
ANNOTATED_DIR = ROOT / "data" / "annotated"
ANALYSIS = ROOT / "analysis"

GITVOTE_JSON = DATA_RAW / "a2a_gitvote_prs.json"
ANNOTATED_FILE = ANNOTATED_DIR / "annotated_records.json"
ANALYSIS_MD = ANALYSIS / "gitvote_analysis.md"


BOTS = {"git-vote[bot]", "gemini-code-assist[bot]", "google-cla[bot]", "github-actions[bot]"}


def load_minimax_key() -> str:
    env_path = ROOT / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("MINIMAX_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("MINIMAX_API_KEY", "")


ANNOTATION_PROMPT = """You are a governance researcher annotating discussion records from a technology standardization process (Google A2A open-source protocol).
Output ONLY a JSON object with these fields:

{
  "stakeholder_institution": "<one of: Google | Microsoft | Cisco | Coinbase | MetaMask | Ethereum Foundation | Independent | Unknown>",
  "argument_type": "<one of: Technical | Economic | Governance-Principle | Process | Off-topic>",
  "stance": "<one of: Support | Oppose | Modify | Neutral | Off-topic>",
  "consensus_signal": "<one of: Adopted | Rejected | Pending | N/A>",
  "key_point": "<one sentence, ≤20 words>"
}

Rules:
- stakeholder_institution: holtskinner/kthota-g/pstephengoogle/yarolegovich → Google. darrelmiller → Microsoft. Tehsmash → Cisco. Default Independent if unclear.
- argument_type: Technical=spec design; Governance-Principle=voting/rights/process fairness; Process=procedural; Off-topic=unrelated.
- stance: toward the PR proposal being adopted as-is.
- consensus_signal: Adopted only if merged; Rejected only if explicitly closed; Pending otherwise; N/A for procedural.
- Output ONLY the JSON object. No markdown, no explanation."""


def annotate_record_minimax(api_key: str, author: str, text: str) -> dict | None:
    if not text or len(text.strip()) < 20:
        return None
    user_msg = f"Author: {author}\nText: {text[:1500]}"
    payload = json.dumps({
        "model": "MiniMax-M2.5",
        "messages": [
            {"role": "system", "content": ANNOTATION_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 1024,
    }).encode()
    req = urllib.request.Request(
        "https://api.minimaxi.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        raw = data["choices"][0]["message"]["content"]
        # Strip <think>...</think> block from MiniMax-M2.5
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Strip markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        return {"_error": str(e)}


def record_id(r: dict) -> str:
    return f"gitvote|pr{r.get('pr_number')}|{r.get('record_type')}|{r.get('comment_id', r.get('review_id', 'body'))}"


def main():
    print("=== annotate_gitvote.py ===")

    api_key = load_minimax_key()
    if not api_key:
        raise SystemExit("MINIMAX_API_KEY not set in .env")

    # Load git-vote records
    raw_records = json.loads(GITVOTE_JSON.read_text())
    print(f"Loaded {len(raw_records)} raw records")

    # Load existing annotated records to check for duplicates
    existing = json.loads(ANNOTATED_FILE.read_text())
    existing_ids = {r.get("_record_id", "") for r in existing}
    print(f"Existing annotated records: {len(existing)}")

    # Filter: non-bot, substantive text, not already annotated
    to_annotate = []
    for r in raw_records:
        author = r.get("author", "")
        text = r.get("text", "")
        if author in BOTS or author.endswith("[bot]"):
            continue
        if not text or len(text.strip()) < 30:
            continue
        # Skip /vote and similar single-line commands
        if text.strip().startswith("/") and len(text.strip()) < 20:
            continue
        rid = record_id(r)
        if rid in existing_ids:
            continue
        to_annotate.append(r)

    print(f"Records to annotate: {len(to_annotate)}")

    annotated_new = []
    for i, r in enumerate(to_annotate, 1):
        author = r.get("author", "")
        text = r.get("text", "")
        print(f"  [{i}/{len(to_annotate)}] {author}: ", end="", flush=True)

        annotation = annotate_record_minimax(api_key, author, text)
        err = None
        if annotation and "_error" in annotation:
            err = annotation["_error"]
            annotation = None
            print(f"ERROR: {err}")
        else:
            kp = (annotation or {}).get("key_point", "")[:50] if annotation else ""
            print(f"OK  → {kp}")

        record_out = {
            "source": r.get("record_type", ""),
            "platform": "github",
            "pr_number": r.get("pr_number"),
            "date": r.get("date", ""),
            "author": author,
            "raw_text": text,
            "state": r.get("state", ""),
            "url": r.get("url", ""),
            "_case": "Google-A2A",
            "_note": "gitvote_pr",
            "_record_id": record_id(r),
            "annotation": annotation,
            "annotation_error": err,
        }
        annotated_new.append(record_out)
        time.sleep(0.3)

    # Merge into annotated_records.json
    merged = existing + annotated_new
    ANNOTATED_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print(f"\nMerged: {len(existing)} + {len(annotated_new)} = {len(merged)} records")
    print(f"Saved: {ANNOTATED_FILE}")

    # Write improved analysis markdown
    write_enriched_analysis(raw_records, annotated_new)
    print(f"Saved: {ANALYSIS_MD}")
    print("Done.")


def write_enriched_analysis(raw_records: list, annotated: list) -> None:
    """Rewrite gitvote_analysis.md with LLM-enriched content."""
    from collections import Counter, defaultdict

    # Group annotated by PR
    ann_by_pr: dict[int, list] = defaultdict(list)
    for r in annotated:
        ann_by_pr[r["pr_number"]].append(r)

    # Group raw by PR for vote info
    raw_by_pr: dict[int, list] = defaultdict(list)
    for r in raw_records:
        raw_by_pr[r["pr_number"]].append(r)

    PR_META = {
        831: {
            "title": "feat(spec): Add `tasks/list` method with filtering and pagination",
            "outcome": "PASSED (merged)",
            "summary": (
                "Adds a new `tasks/list` RPC method to the A2A spec, allowing clients to query tasks with "
                "filtering (by status, contextId, lastUpdatedAfter) and pagination. "
                "Vote called because the feature was a substantive spec addition requiring TSC sign-off before merge."
            ),
        },
        1206: {
            "title": "feat(spec): Add last update time to `Task`",
            "outcome": "CLOSED (superseded by #1358)",
            "summary": (
                "Proposes adding a `lastUpdateTime` field to the Task data model, needed by `tasks/list` ordering. "
                "Vote called but then `/cancel-vote` issued after TSC meeting on 2026-01-06 resolved the naming dispute: "
                "the group agreed to rename the filter parameter to `status_timestamp_after` instead, "
                "removing the need for a new field. Discussion migrated to Discord and a TSC call — key decision was offline."
            ),
        },
    }

    lines = [
        "# Git-Vote PRs: Governance Analysis",
        "",
        "Two pull requests in the Google A2A repository that triggered formal TSC votes via `git-vote[bot]`.",
        "Labels: `TSC Review` + `gitvote`. These are the only two PRs in the dataset with an explicit voting mechanism.",
        "",
        "## Background: What is git-vote?",
        "",
        "`git-vote[bot]` is a GitHub app that enables formal voting on PRs via emoji reactions on a pinned comment.",
        "A TSC (Technical Steering Committee) member types `/vote` to initiate; binding voters are pre-registered members.",
        "Threshold: a majority of binding voters must approve. The bot periodically posts vote-status updates.",
        "",
        "## Why Does This Matter Theoretically?",
        "",
        "The existence of a formal voting mechanism in an ostensibly 'open' corporate project is analytically significant:",
        "- It reveals that Google A2A has a **defined inner circle** (TSC) with binding authority, unlike the permissionless ERC process",
        "- Invoking `/vote` signals that **ordinary review consensus failed** — a governance escalation point",
        "- PR #1206's trajectory (vote → TSC call → Discord → /cancel-vote → superseding PR) shows that **key decisions happen off-platform**, reducing transparency",
        "",
    ]

    for pr_num in [831, 1206]:
        meta = PR_META[pr_num]
        raw = raw_by_pr[pr_num]
        ann = ann_by_pr[pr_num]

        # Vote info from raw
        bot_comments = [r for r in raw if r.get("author") == "git-vote[bot]"]
        vote_triggers = [r for r in raw if r.get("record_type") == "issue_comment"
                         and r.get("text", "").strip().startswith("/vote")]
        cancel_triggers = [r for r in raw if r.get("record_type") == "issue_comment"
                           and "/cancel-vote" in r.get("text", "")]

        # Human participants
        human_authors = [r.get("author", "") for r in raw
                         if r.get("author") not in BOTS and not r.get("author", "").endswith("[bot]")]
        author_counts = Counter(human_authors)

        # Annotation summary
        if ann:
            arg_types = Counter(r["annotation"]["argument_type"] for r in ann if r.get("annotation") and not r.get("annotation_error"))
            stances = Counter(r["annotation"]["stance"] for r in ann if r.get("annotation") and not r.get("annotation_error"))
            institutions = Counter(r["annotation"]["stakeholder_institution"] for r in ann if r.get("annotation") and not r.get("annotation_error"))
        else:
            arg_types = stances = institutions = Counter()

        lines += [
            "---",
            "",
            f"## PR #{pr_num}: {meta['title']}",
            "",
            f"**URL**: https://github.com/a2aproject/A2A/pull/{pr_num}",
            f"**Outcome**: {meta['outcome']}",
            "",
            "### What the PR proposes",
            "",
            meta["summary"],
            "",
            "### Vote mechanics",
            "",
            f"| | |",
            f"|---|---|",
            f"| `/vote` called by | {', '.join(r.get('author','') for r in vote_triggers) or 'N/A'} |",
            f"| `/cancel-vote` called by | {', '.join(r.get('author','') for r in cancel_triggers) or 'N/A'} |",
            f"| git-vote bot messages | {len(bot_comments)} |",
            f"| Human participants | {', '.join(a for a,_ in author_counts.most_common(10))} |",
            "",
            "### LLM annotation summary (human comments only)",
            "",
        ]

        if arg_types:
            lines.append("**Argument types:**")
            for k, v in arg_types.most_common():
                lines.append(f"- {k}: {v}")
            lines.append("")
            lines.append("**Stance distribution:**")
            for k, v in stances.most_common():
                lines.append(f"- {k}: {v}")
            lines.append("")
            lines.append("**Institutions involved:**")
            for k, v in institutions.most_common():
                lines.append(f"- {k}: {v}")
            lines.append("")
        else:
            lines.append("*(No annotation available)*")
            lines.append("")

        # Key annotated points
        lines.append("### Key annotated comments")
        lines.append("")
        shown = 0
        for r in ann:
            if not r.get("annotation") or r.get("annotation_error"):
                continue
            ann_data = r["annotation"]
            kp = ann_data.get("key_point", "")
            at = ann_data.get("argument_type", "")
            st = ann_data.get("stance", "")
            inst = ann_data.get("stakeholder_institution", "")
            author = r.get("author", "")
            text_excerpt = r.get("raw_text", "")[:200].replace("\n", " ")
            lines.append(f"**{author}** ({inst}, {at}, stance={st})")
            lines.append(f"> {text_excerpt}")
            lines.append(f"*Key point: {kp}*")
            lines.append("")
            shown += 1
            if shown >= 12:
                break

    lines += [
        "---",
        "",
        "## Comparative Governance Interpretation",
        "",
        "| Dimension | PR #831 (tasks/list) | PR #1206 (lastUpdateTime) |",
        "|-----------|---------------------|--------------------------|",
        "| Outcome | Passed and merged | Closed, superseded |",
        "| Decision venue | GitHub comments | TSC meeting + Discord |",
        "| Transparency | High (all on-platform) | Low (key decision offline) |",
        "| Vote trigger | Feature maturity, TSC sign-off | Data model design dispute |",
        "| Resolution time | ~4 months | ~2 months then cancelled |",
        "",
        "The contrast between #831 and #1206 illustrates a **dual-mode decision process** in A2A governance:",
        "technical changes with rough consensus proceed through standard review; structurally contested changes",
        "escalate to TSC voting — and sometimes further to off-platform coordination (Discord, synchronous calls).",
        "This opacity gradient is absent in the ERC-8004 process, where all deliberation occurs on Ethereum Magicians forum.",
    ]

    ANALYSIS_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
