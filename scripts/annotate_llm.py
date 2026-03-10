"""
LLM annotation of governance records using a configurable LLM backend.

Supported backends (set via --backend or ANNOTATION_BACKEND env var):
  minimax   MiniMax domestic API  api.minimax.chat/v1  [default]
  openai    OpenAI-compatible     any base_url
  anthropic Anthropic Claude API

For each record, extracts:
  - stakeholder_institution
  - argument_type
  - stance
  - consensus_signal
  - key_point

Input:
  data/raw/forum_posts.json
  data/raw/github_comments_filtered.json   (ERC-8004, run filter_github.py first)
  data/raw/a2a_issues.json                 (Google A2A)
  data/raw/a2a_prs.json                    (Google A2A)

Output: data/annotated/annotated_records.json
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
ANNOTATED_DIR = Path(__file__).parent.parent / "data" / "annotated"
ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Backend configuration
# ---------------------------------------------------------------------------

BACKENDS = {
    "minimax": {
        "base_url": "https://api.minimaxi.com/v1",
        "model": "MiniMax-M2.5",
        "api_key_env": "MINIMAX_API_KEY",
    },
    "openai": {
        "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        # Anthropic uses its own SDK, handled separately below
        "model": os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        "api_key_env": "ANTHROPIC_API_KEY",
    },
}

ANNOTATION_PROMPT = """\
You are a governance researcher annotating discussion records from a technology standardization process.
For each record, output ONLY a JSON object with these fields:

{
  "stakeholder_institution": "<one of: Google | Coinbase | MetaMask | Ethereum Foundation | Independent | Unknown>",
  "argument_type": "<one of: Technical | Economic | Governance-Principle | Process | Off-topic>",
  "stance": "<one of: Support | Oppose | Modify | Neutral | Off-topic>",
  "consensus_signal": "<one of: Adopted | Rejected | Pending | N/A>",
  "key_point": "<one sentence summary, ≤20 words>"
}

Rules:
- stakeholder_institution: infer from author handle, text, or any employer clue. Default Independent if unclear.
- argument_type: Technical=spec design/implementation; Economic=cost/incentive; Governance-Principle=voting/process/rights; Process=procedural; Off-topic=unrelated.
- stance: toward the proposal's adoption as written.
- consensus_signal: Adopted/Rejected only if an explicit editorial decision exists (merged, closed). Otherwise Pending or N/A.
- Output ONLY the JSON, no explanation.
"""


# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------

def _make_openai_client(backend: dict):
    from openai import OpenAI
    key = os.environ.get(backend["api_key_env"], "")
    if not key:
        raise SystemExit(f"{backend['api_key_env']} not set.")
    return OpenAI(api_key=key, base_url=backend["base_url"])


def annotate_openai_compat(client, model: str, record: dict) -> dict:
    text = record.get("raw_text", "").strip()
    if len(text) < 20:
        return {**record, "annotation": None, "annotation_error": "text_too_short"}

    user_msg = (
        f"Author: {record.get('author', 'unknown')}\n"
        f"Date: {record.get('date', 'unknown')}\n"
        f"Platform: {record.get('platform', 'unknown')}\n"
        f"Case: {record.get('_case', 'unknown')}\n\n"
        f"Text:\n{text[:3000]}"
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=256,
            messages=[
                {"role": "system", "content": ANNOTATION_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        # Strip <think>...</think> reasoning block (MiniMax-M2.5, o1-style models)
        if "<think>" in raw:
            import re
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Strip markdown code fences
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
            raw = raw.split("```")[0].strip()
        annotation = json.loads(raw)
        return {**record, "annotation": annotation, "annotation_error": None}
    except json.JSONDecodeError as e:
        return {**record, "annotation": None, "annotation_error": f"json_parse: {e}"}
    except Exception as e:
        return {**record, "annotation": None, "annotation_error": f"api_error: {type(e).__name__}: {str(e)[:120]}"}


def annotate_anthropic(record: dict, model: str) -> dict:
    import anthropic
    text = record.get("raw_text", "").strip()
    if len(text) < 20:
        return {**record, "annotation": None, "annotation_error": "text_too_short"}

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set.")
    client = anthropic.Anthropic(api_key=key)

    user_msg = (
        f"Author: {record.get('author', 'unknown')}\n"
        f"Date: {record.get('date', 'unknown')}\n"
        f"Case: {record.get('_case', 'unknown')}\n\n"
        f"Text:\n{text[:3000]}"
    )
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=256,
            system=ANNOTATION_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text.strip()
        annotation = json.loads(raw)
        return {**record, "annotation": annotation, "annotation_error": None}
    except json.JSONDecodeError as e:
        return {**record, "annotation": None, "annotation_error": f"json_parse: {e}"}
    except Exception as e:
        return {**record, "annotation": None, "annotation_error": f"api_error: {type(e).__name__}: {str(e)[:120]}"}


# ---------------------------------------------------------------------------
# Record loading
# ---------------------------------------------------------------------------

def load_records() -> list[dict]:
    records = []

    # ERC-8004: forum posts
    forum_path = RAW_DIR / "forum_posts.json"
    if forum_path.exists():
        data = json.loads(forum_path.read_text())
        for r in data:
            records.append({**r, "_case": "ERC-8004"})
        print(f"  Loaded {len(data)} forum posts (ERC-8004)")
    else:
        print(f"  MISSING: {forum_path}")

    # ERC-8004: filtered GitHub comments
    gh_filtered = RAW_DIR / "github_comments_filtered.json"
    gh_raw = RAW_DIR / "github_comments.json"
    if gh_filtered.exists():
        data = json.loads(gh_filtered.read_text())
        for r in data:
            records.append({**r, "_case": "ERC-8004"})
        print(f"  Loaded {len(data)} GitHub comments filtered (ERC-8004)")
    elif gh_raw.exists():
        print(f"  WARNING: using unfiltered github_comments.json — run filter_github.py first")
        data = json.loads(gh_raw.read_text())
        for r in data:
            records.append({**r, "_case": "ERC-8004"})

    # Google A2A: issues + PRs
    for fname, label in [("a2a_issues.json", "A2A issues"), ("a2a_prs.json", "A2A PRs")]:
        path = RAW_DIR / fname
        if path.exists():
            data = json.loads(path.read_text())
            # Only annotate records with non-trivial text
            for r in data:
                if len((r.get("raw_text") or "").strip()) >= 20:
                    records.append({**r, "_case": "Google-A2A"})
            print(f"  Loaded {len(data)} {label} (Google A2A)")
        else:
            print(f"  MISSING: {path} — run scrape_a2a.py")

    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=os.environ.get("ANNOTATION_BACKEND", "minimax"),
                        choices=list(BACKENDS.keys()),
                        help="LLM backend to use (default: minimax)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Annotate only first N records (0 = all, for testing)")
    args = parser.parse_args()

    backend_name = args.backend
    backend = BACKENDS[backend_name]
    print(f"Backend: {backend_name}  model: {backend['model']}")

    # Build annotate function
    if backend_name == "anthropic":
        def annotate(record):
            return annotate_anthropic(record, backend["model"])
    else:
        client = _make_openai_client(backend)
        def annotate(record):
            return annotate_openai_compat(client, backend["model"], record)

    # Load records
    print("\nLoading records…")
    records = load_records()
    print(f"Total: {len(records)} records")

    if args.limit:
        records = records[: args.limit]
        print(f"Limited to first {args.limit} records")

    # Resume support
    out_path = ANNOTATED_DIR / "annotated_records.json"
    done_ids: set[str] = set()
    annotated: list[dict] = []

    if out_path.exists():
        existing = json.loads(out_path.read_text())
        annotated.extend(existing)
        done_ids = {_record_id(r) for r in existing}
        print(f"Resuming — {len(done_ids)} already annotated")

    to_do = [r for r in records if _record_id(r) not in done_ids]
    print(f"Annotating {len(to_do)} new records…\n")

    errors = 0
    for i, record in enumerate(to_do, 1):
        result = annotate(record)
        annotated.append(result)

        ok = result["annotation"] is not None
        if not ok:
            errors += 1
        status = "OK" if ok else f"SKIP ({result['annotation_error']})"
        print(f"  [{i}/{len(to_do)}] [{result.get('_case','?')}] {record.get('author','?')[:20]} — {status}")

        if i % 10 == 0:
            out_path.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))

        time.sleep(0.25)

    out_path.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))
    print(f"\nDone. {len(annotated)} records saved → {out_path}")
    print(f"Errors: {errors} / {len(to_do)}")


def _record_id(r: dict) -> str:
    return f"{r.get('_case')}_{r.get('source')}_{r.get('post_id') or r.get('comment_id') or r.get('sha') or r.get('issue_number') or r.get('pr_number')}_{r.get('date')}"


if __name__ == "__main__":
    main()
