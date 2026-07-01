"""
annotate_r2.py — Multi-model governance annotation for R2 data (1713 records).

Runs structured 5-field annotation with multiple LLM backends on the expanded
DAO dataset. Each model writes to its own output file with resume support.

Backends (all OpenAI-compatible):
  deepseek    DeepSeek v4 Flash    api.deepseek.com
  glm         GLM-4-Plus (Zhipu)   open.bigmodel.cn
  kimi        Moonshot v1 Auto    api.moonshot.cn  (K2.6 too slow for batch)

Standard annotation prompt = same 5-field schema as round-1:
  stakeholder_institution, argument_type, stance, consensus_signal, key_point

Data: data/raw/r2/tier{1,2}/*.json  (1713 records across forum + github)

Usage:
  uv run python scripts/process/annotate_r2.py --model deepseek
  uv run python scripts/process/annotate_r2.py --model glm
  uv run python scripts/process/annotate_r2.py --model kimi
  uv run python scripts/process/annotate_r2.py --model deepseek --limit 10  # test
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, DATA_RAW_R2, DATA_ANNOTATED_R2_CROSS_MODEL
from lib.models import BACKENDS_ANNOTATION, LEGACY_KEYS

load_dotenv(ROOT / ".env")

R2_DIR = DATA_RAW_R2
OUT_DIR = DATA_ANNOTATED_R2_CROSS_MODEL
OUT_DIR.mkdir(parents=True, exist_ok=True)

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
- Output ONLY the JSON, no explanation."""


# ── Data loading ───────────────────────────────────────────────────────────────

def load_r2_records() -> list[dict]:
    """Load all R2 Tier 1 + Tier 2 records (forum + github)."""
    records = []
    for tier, tier_label in [("tier1", "ERC-8004"), ("tier2", "ERC-cluster")]:
        tier_dir = R2_DIR / tier
        for fname in sorted(tier_dir.glob("*.json")):
            if "manifest" in fname.name:
                continue
            data = json.loads(fname.read_text())
            for r in data:
                text = (r.get("raw_text") or "").strip()
                if len(text) < 20:
                    continue
                r["_case"] = tier_label
                records.append(r)
    return records


def _record_id(r: dict) -> str:
    """Composite key for dedup/resume across forum + github records."""
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("issue_number") or r.get("pr_number"))
    return f"{r.get('_case')}_{r.get('source')}_{cid}_{r.get('date')}"


# ── Annotation ─────────────────────────────────────────────────────────────────

def strip_reasoning(raw: str) -> str:
    """Remove <think>...</think> blocks (Kimi K2.6 and other reasoning models)."""
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


def parse_json_response(raw: str, text_len: int) -> dict | None:
    """Extract JSON from an LLM response, handling markdown fences."""
    raw = strip_reasoning(raw)
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
        raw = raw.split("```")[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        m = re.search(r'\{[^{}]*"stakeholder_institution"[^{}]*\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return None


def annotate(client: OpenAI, model: str, max_tokens: int, temperature: float, record: dict) -> dict:
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
    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": ANNOTATION_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            raw = resp.choices[0].message.content.strip()
            if not raw:
                # Empty response — retry
                if attempt < 4:
                    wait = 3 * (2 ** attempt)
                    print(f"      empty response, retry {attempt+1}/5 in {wait}s…", flush=True)
                    time.sleep(wait)
                    continue
                return {**record, "annotation": None,
                        "annotation_error": "empty_response_5_retries_exhausted"}
            annotation = parse_json_response(raw, len(text))
            if annotation is not None:
                return {**record, "annotation": annotation, "annotation_error": None}
            # Parse failed — retry
            if attempt < 4:
                wait = 2 * (2 ** attempt)
                print(f"      parse failed, retry {attempt+1}/5 in {wait}s…", flush=True)
                time.sleep(wait)
                continue
            return {**record, "annotation": None,
                    "annotation_error": f"json_parse_5_retries: {raw[:120]}"}
        except Exception as e:
            es = str(e)
            if "429" not in es and "rate" not in es.lower() and attempt >= 4:
                return {**record, "annotation": None,
                        "annotation_error": f"api_error: {type(e).__name__}: {es[:120]}"}
            wait = 10 * (2 ** attempt) if ("429" in es or "rate" in es.lower()) else 3 * (2 ** attempt)
            print(f"      api error, retry {attempt+1}/5 in {wait}s…", flush=True)
            time.sleep(wait)
    return {**record, "annotation": None,
            "annotation_error": "5_retries_exhausted"}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="R2 Multi-model governance annotation")
    parser.add_argument("--model", required=True,
                        choices=sorted(set(list(LEGACY_KEYS.keys()) + list(BACKENDS_ANNOTATION.keys()))),
                        help="LLM backend to use")
    parser.add_argument("--limit", type=int, default=0,
                        help="Annotate first N records (0=all)")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Save every N records (default: 20)")
    args = parser.parse_args()

    canonical_id = LEGACY_KEYS.get(args.model, args.model)
    backend = BACKENDS_ANNOTATION[canonical_id]
    key = os.environ.get(backend["api_key_env"], "")
    if not key:
        raise SystemExit(f"{backend['api_key_env']} not set in .env")

    client = OpenAI(api_key=key, base_url=backend["base_url"])
    model_name = backend["model"]
    max_tokens = backend.get("max_tokens", 1024)
    temperature = backend.get("temperature", 0.0)
    sleep_s = backend.get("sleep", 0.15)

    # Output paths
    model_out_dir = OUT_DIR / canonical_id
    model_out_dir.mkdir(parents=True, exist_ok=True)
    out_json = model_out_dir / "annotations.json"
    out_manifest = model_out_dir / "manifest.json"

    print(f"Backend: {backend['name']}  |  model: {model_name}")
    print(f"Output:  {out_json}\n")

    # Load data
    records = load_r2_records()
    print(f"Loaded {len(records)} R2 records (tier1 + tier2)")

    if args.limit:
        records = records[:args.limit]
        print(f"LIMITED to {args.limit} records (test mode)")

    # Resume
    annotated: list[dict] = []
    done_ids: set[str] = set()
    if out_json.exists():
        annotated = json.loads(out_json.read_text())
        done_ids = {_record_id(r) for r in annotated}
        print(f"Resuming: {len(done_ids)} already annotated")

    to_do = [r for r in records if _record_id(r) not in done_ids]
    if not to_do:
        print("All records already annotated — nothing to do.")
        return

    print(f"Annotating {len(to_do)} new records…\n")
    errors = 0
    t0 = time.time()

    for i, record in enumerate(to_do, 1):
        result = annotate(client, model_name, max_tokens, temperature, record)
        annotated.append(result)

        ok = result["annotation"] is not None
        if not ok:
            errors += 1
        status = "OK" if ok else f"SKIP ({result.get('annotation_error','?')[:60]})"

        elapsed = time.time() - t0
        rate = i / elapsed if elapsed > 0 else 0
        eta = (len(to_do) - i) / rate / 60 if rate > 0 else float("inf")
        print(f"  [{i}/{len(to_do)}] {result.get('_case','?')} "
              f"{str(result.get('author','?'))[:18]:<18} {status}  "
              f"({rate:.1f}/s  ETA {eta:.0f}m)", flush=True)

        if i % args.batch_size == 0:
            out_json.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))

        time.sleep(sleep_s)

    out_json.write_text(json.dumps(annotated, indent=2, ensure_ascii=False))

    # Manifest
    n_ok = sum(1 for r in annotated if r["annotation"] is not None)
    manifest = {
        "backend": backend["name"],
        "model": model_name,
        "base_url": backend["base_url"],
        "annotated_at": datetime.now(timezone.utc).isoformat(),
        "total_loaded": len(records),
        "total_annotated": len(annotated),
        "successful": n_ok,
        "errors": len(annotated) - n_ok,
        "error_rate": f"{(len(annotated) - n_ok) / len(annotated) * 100:.1f}%" if annotated else "N/A",
        "runtime_s": round(time.time() - t0),
    }
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    print(f"\nDone. {n_ok}/{len(annotated)} successful "
          f"({manifest['error_rate']} error rate)  "
          f"→ {out_json}")


if __name__ == "__main__":
    main()
