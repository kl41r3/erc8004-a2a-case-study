"""
annotate_a2a_r2.py — Multi-model governance annotation for Google A2A data.

Re-annotates the 5,272 A2A records from data/annotated/annotated_records.json
using the same 3-model pipeline as R2 ERC data, enabling cross-model ICR
validation and majority-vote consensus for the new comparative paper.

Backends: deepseek, glm, kimi (same as annotate_r2.py)
Output:   data/annotated/r2/a2a/{model}/annotations.json

Usage:
  uv run python scripts/process/annotate_a2a_r2.py --model deepseek
  uv run python scripts/process/annotate_a2a_r2.py --model glm
  uv run python scripts/process/annotate_a2a_r2.py --model kimi
  uv run python scripts/process/annotate_a2a_r2.py --model deepseek --limit 10
"""

import argparse
import json
import os
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

SRC_FILE = ROOT / "data" / "annotated" / "annotated_records.json"
OUT_DIR = ROOT / "data" / "annotated" / "r2" / "a2a"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_TEXT_LEN = 50

BACKENDS = {
    "deepseek": {
        "name": "DeepSeek-V4-Flash",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "api_key_env": "DEEPSEEK_API_KEY",
        "max_tokens": 1024,
        "temperature": 0.0,
        "sleep": 0.1,
    },
    "glm": {
        "name": "GLM-4-Plus",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-plus",
        "api_key_env": "GLM_API_KEY",
        "max_tokens": 1024,
        "temperature": 0.0,
        "sleep": 0.2,
    },
    "kimi": {
        "name": "Moonshot-v1-Auto",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-auto",
        "api_key_env": "KIMI_API_KEY",
        "max_tokens": 1024,
        "temperature": 0.0,
        "sleep": 0.15,
    },
}

ANNOTATION_PROMPT = """\
You are a governance researcher annotating discussion records from a technology standardization process.
For each record, output ONLY a JSON object with these fields:

{
  "stakeholder_institution": "<one of: Google | Microsoft | Salesforce | Atlassian | Cisco | Independent | Unknown>",
  "argument_type": "<one of: Technical | Economic | Governance-Principle | Process | Off-topic>",
  "stance": "<one of: Support | Oppose | Modify | Neutral | Off-topic>",
  "consensus_signal": "<one of: Adopted | Rejected | Pending | N/A>",
  "key_point": "<one sentence summary, ≤20 words>"
}

Rules:
- stakeholder_institution: infer from author handle, email domain, text, or employer clue. Default Independent if unclear.
  Common A2A contributors: Google engineers, Microsoft, Salesforce, Atlassian, Cisco, or community members.
- argument_type: Technical=spec design/implementation/API design; Economic=cost/incentive; Governance-Principle=voting/process/rights/committee; Process=procedural/admin; Off-topic=unrelated.
- stance: toward the proposal/PR/issue as written.
- consensus_signal: Adopted/Rejected only if an explicit decision exists (merged PR, closed issue). Otherwise Pending or N/A.
- Output ONLY the JSON, no explanation."""


def load_a2a_records() -> list[dict]:
    """Load all Google A2A records from annotated_records.json, filter by text length."""
    all_records = json.loads(SRC_FILE.read_text())
    a2a = []
    for r in all_records:
        if r.get("_case") != "Google-A2A":
            continue
        text = (r.get("raw_text") or "").strip()
        if len(text) < MIN_TEXT_LEN:
            continue
        a2a.append(r)
    return a2a


def _record_id(r: dict) -> str:
    """Stable composite key for dedup/resume."""
    url = r.get("url", "")
    if url:
        return f"a2a__{url}"
    cid = r.get("issue_number") or r.get("pr_number") or ""
    return f"a2a__{r.get('source')}_{cid}_{r.get('date')}"


def strip_reasoning(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


def parse_json_response(raw: str) -> dict | None:
    raw = strip_reasoning(raw)
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
        raw = raw.split("```")[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{[^{}]*"stakeholder_institution"[^{}]*\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return None


def annotate(client: OpenAI, model: str, max_tokens: int, temperature: float, record: dict) -> dict:
    text = (record.get("raw_text") or "").strip()
    title = record.get("title", "")
    context = f"Title: {title}\n\n" if title else ""

    user_msg = (
        f"Author: {record.get('author', 'unknown')}\n"
        f"Date: {record.get('date', 'unknown')}\n"
        f"Platform: GitHub A2A ({record.get('source', 'unknown')})\n"
        f"Case: Google A2A protocol governance\n\n"
        f"{context}Text:\n{text[:3000]}"
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
                if attempt < 4:
                    wait = 3 * (2 ** attempt)
                    print(f"      empty response, retry {attempt+1}/5 in {wait}s…", flush=True)
                    time.sleep(wait)
                    continue
                return {**record, "annotation": None,
                        "annotation_error": "empty_response_5_retries_exhausted"}
            annotation = parse_json_response(raw)
            if annotation is not None:
                return {**record, "annotation": annotation, "annotation_error": None}
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
            print(f"      api error ({es[:60]}), retry {attempt+1}/5 in {wait}s…", flush=True)
            time.sleep(wait)
    return {**record, "annotation": None, "annotation_error": "5_retries_exhausted"}


def main():
    parser = argparse.ArgumentParser(description="A2A multi-model annotation for paper-acm")
    parser.add_argument("--model", required=True, choices=list(BACKENDS))
    parser.add_argument("--limit", type=int, default=0, help="Test: annotate first N records")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--workers", type=int, default=10,
                        help="Concurrent API workers (default 10, 0=sequential)")
    args = parser.parse_args()

    backend = BACKENDS[args.model]
    key = os.environ.get(backend["api_key_env"], "")
    if not key:
        raise SystemExit(f"{backend['api_key_env']} not set in .env")

    client = OpenAI(api_key=key, base_url=backend["base_url"])
    model_name = backend["model"]

    model_out_dir = OUT_DIR / args.model
    model_out_dir.mkdir(parents=True, exist_ok=True)
    out_json = model_out_dir / "annotations.json"
    out_manifest = model_out_dir / "manifest.json"

    print(f"Backend: {backend['name']}  |  model: {model_name}")
    print(f"Output:  {out_json}\n")

    records = load_a2a_records()
    print(f"Loaded {len(records)} A2A records (text ≥ {MIN_TEXT_LEN} chars)")

    if args.limit:
        records = records[:args.limit]
        print(f"LIMITED to {args.limit} records (test mode)")

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

    print(f"Annotating {len(to_do)} new records"
          f"{' (concurrent, workers=' + str(args.workers) + ')' if args.workers > 0 else ' (sequential)'}…\n")

    # Shared state for concurrent mode
    write_lock = threading.Lock()
    completed_count = [0]  # mutable counter
    error_count = [0]

    def save_checkpoint():
        """Thread-safe checkpoint write."""
        with write_lock:
            try:
                raw = json.dumps(annotated, indent=2, ensure_ascii=False)
                with open(str(out_json), "w", encoding="utf-8") as _f:
                    _f.write(raw)
                    _f.flush()
                    os.fsync(_f.fileno())
            except Exception as e:
                print(f"    [SAVE FAILED: {e}]", flush=True)

    t0 = time.time()

    def process_one(record: dict) -> dict | None:
        result = annotate(client, model_name, backend["max_tokens"], backend["temperature"], record)
        with write_lock:
            annotated.append(result)
            completed_count[0] += 1
            if result["annotation"] is None:
                error_count[0] += 1
            i = completed_count[0]
            done = len(annotated)
            total = len(records)

            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(to_do) - i) / rate / 60 if rate > 0 else float("inf")
            status = "OK" if result["annotation"] is not None else "SKIP"

            if i % 5 == 0:
                print(f"  [{done}/{total}] "
                      f"{str(record.get('author','?'))[:14]:<14} {status}  "
                      f"({rate:.1f}/s  ETA {eta:.0f}m)", flush=True)

            if done % args.batch_size == 0 or done == total:
                save_checkpoint()
                if done % 50 == 0:
                    print(f"    [checkpoint {done}/{total} records]", flush=True)

        if backend.get("sleep", 0) > 0:
            time.sleep(backend["sleep"] / max(args.workers, 1))
        return result

    if args.workers > 0:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process_one, r): r for r in to_do}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"    [worker error: {e}]", flush=True)
    else:
        for record in to_do:
            process_one(record)

    save_checkpoint()
    print(f"    [final checkpoint — {len(annotated)} records]", flush=True)

    n_ok = sum(1 for r in annotated if r["annotation"] is not None)
    manifest = {
        "backend": backend["name"],
        "model": model_name,
        "base_url": backend["base_url"],
        "annotated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(SRC_FILE),
        "total_loaded": len(records),
        "total_annotated": len(annotated),
        "successful": n_ok,
        "errors": len(annotated) - n_ok,
        "error_rate": f"{(len(annotated) - n_ok) / len(annotated) * 100:.1f}%" if annotated else "N/A",
        "runtime_s": round(time.time() - t0),
    }
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    print(f"\nDone. {n_ok}/{len(annotated)} successful "
          f"({manifest['error_rate']} error rate)  →  {out_json}")


if __name__ == "__main__":
    main()
