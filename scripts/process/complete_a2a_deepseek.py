"""
complete_a2a_deepseek.py — Fill the 214-record gap in DeepSeek A2A annotations.

Background:
  - GLM and Kimi each annotated 4,059 unique A2A records.
  - DeepSeek only has 3,845 (was rate-limited during R2).
  - The gap = (G ∩ K) − D = exactly 214 records.
  - This script annotates only those 214, then appends them to
    data/annotated/r2/a2a/deepseek/annotations.json → total 4,059.

Config: identical to annotate_a2a_r2.py (same prompt, model, params).
Usage:
  uv run python scripts/process/complete_a2a_deepseek.py
  uv run python scripts/process/complete_a2a_deepseek.py --workers 5
"""

import argparse
import json
import os
import sys
import time
import threading
from pathlib import Path

# Re-use all logic from the original annotator (prompt/model/params byte-identical)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from annotate_a2a_r2 import (
    BACKENDS,
    ANNOTATION_PROMPT,  # noqa: F401 – imported for documentation / identity
    annotate,
    parse_json_response,  # noqa: F401
    _record_id,
)

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(ROOT / ".env")

A2A_DIR = ROOT / "data" / "annotated" / "r2" / "a2a"
DS_FILE  = A2A_DIR / "deepseek" / "annotations.json"
GLM_FILE = A2A_DIR / "glm"      / "annotations.json"
KIMI_FILE= A2A_DIR / "kimi"     / "annotations.json"


def rid(r: dict) -> str:
    """Alias matching the spec."""
    return _record_id(r)


def build_gap_set() -> tuple[list[dict], set[str], set[str], set[str]]:
    """Return (gap_records, D, G, K) where gap_records are the 214 cleaned source records."""
    ds_recs   = json.loads(DS_FILE.read_text())
    glm_recs  = json.loads(GLM_FILE.read_text())
    kimi_recs = json.loads(KIMI_FILE.read_text())

    D = {rid(r) for r in ds_recs}
    G = {rid(r): r for r in glm_recs}   # id → full record
    K = {rid(r) for r in kimi_recs}

    gap_ids = (set(G.keys()) & K) - D
    print(f"  DeepSeek count : {len(ds_recs)}")
    print(f"  GLM count      : {len(glm_recs)}")
    print(f"  Kimi count     : {len(kimi_recs)}")
    print(f"  G ∩ K          : {len(set(G.keys()) & K)}")
    print(f"  gap (G∩K)−D   : {len(gap_ids)}")

    if len(gap_ids) != 214:
        raise ValueError(
            f"Expected exactly 214 gap records, got {len(gap_ids)}. STOPPING."
        )

    # Build clean source records from GLM (carry original fields, drop annotation)
    gap_records = []
    for gid in sorted(gap_ids):
        src = dict(G[gid])
        src.pop("annotation", None)
        src.pop("annotation_error", None)
        gap_records.append(src)

    return gap_records, D, set(G.keys()), K


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=10,
                        help="Concurrent API workers (default 10)")
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()

    print("=== complete_a2a_deepseek.py ===")
    print("Building gap set…")
    gap_records, _, _, _ = build_gap_set()

    backend = BACKENDS["deepseek"]
    api_key = os.environ.get(backend["api_key_env"], "")
    if not api_key:
        raise SystemExit(f"ERROR: {backend['api_key_env']} not set in .env — cannot proceed.")

    client = OpenAI(api_key=api_key, base_url=backend["base_url"])
    model_name  = backend["model"]
    max_tokens  = backend["max_tokens"]
    temperature = backend["temperature"]

    print(f"\nBackend : {backend['name']} ({model_name})")
    print(f"Gap     : {len(gap_records)} records to annotate")
    print(f"Workers : {args.workers}")
    print()

    # Load existing deepseek annotations (3,845 records) so we can append
    existing = json.loads(DS_FILE.read_text())
    existing_ids = {rid(r) for r in existing}

    # Filter gap to only records not yet done (supports re-runs / partial completions)
    to_do = [r for r in gap_records if rid(r) not in existing_ids]
    if not to_do:
        print("All 214 gap records already annotated. Nothing to do.")
        _verify(existing)
        return

    print(f"Still to annotate: {len(to_do)} (already done: {len(gap_records) - len(to_do)})")

    results: list[dict] = []
    write_lock = threading.Lock()
    completed_count = [0]
    t0 = time.time()

    def save_checkpoint():
        """Write combined results to file. Caller must NOT hold write_lock."""
        combined = existing + results
        DS_FILE.write_text(json.dumps(combined, indent=2, ensure_ascii=False))

    def process_one(record: dict):
        result = annotate(client, model_name, max_tokens, temperature, record)
        do_checkpoint = False
        checkpoint_i = 0
        with write_lock:
            results.append(result)
            completed_count[0] += 1
            i = completed_count[0]
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(to_do) - i) / rate / 60 if rate > 0 else float("inf")
            status = "OK" if result.get("annotation") is not None else "ERR"
            if i % 5 == 0 or i == len(to_do):
                print(
                    f"  [{i}/{len(to_do)}] {str(record.get('author','?'))[:14]:<14} "
                    f"{status}  ({rate:.1f}/s  ETA {eta:.0f}m)",
                    flush=True,
                )
            if i % args.batch_size == 0 or i == len(to_do):
                do_checkpoint = True
                checkpoint_i = i
        # Save checkpoint OUTSIDE the lock to avoid deadlock
        if do_checkpoint:
            save_checkpoint()
            if checkpoint_i % 100 == 0:
                print(f"    [checkpoint {checkpoint_i}/{len(to_do)}]", flush=True)
        if backend.get("sleep", 0) > 0:
            time.sleep(backend["sleep"] / max(args.workers, 1))
        return result

    if args.workers > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
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
    print(f"\n[final checkpoint — {len(existing) + len(results)} total records]")

    _verify(json.loads(DS_FILE.read_text()))


def _verify(recs: list[dict]):
    """Post-run sanity check."""
    n_ok = sum(1 for r in recs if r.get("annotation") is not None)
    n_err = len(recs) - n_ok
    print(f"\nVerification:")
    print(f"  Total records in deepseek/annotations.json : {len(recs)}")
    print(f"  Successful annotations                     : {n_ok}")
    print(f"  Errors (annotation=None)                   : {n_err}")
    if len(recs) == 4059 and n_ok == 4059:
        print("  ✓ PASS — 4,059 records, all annotated.")
    elif len(recs) == 4059:
        print(f"  ✗ WARNING — 4,059 records but {n_err} annotation errors remain.")
    else:
        print(f"  ✗ WARNING — expected 4,059 records, got {len(recs)}.")


if __name__ == "__main__":
    main()
