"""R3 Annotation — 3 models, 3 fields (argument_type, stance, consensus_signal).

Usage:
  uv run python scripts/process/annotate_r3.py --model deepseek-v4-flash --case erc
  uv run python scripts/process/annotate_r3.py --model moonshot-v1-auto --case a2a --workers 20
"""
import argparse, json, os, re, time, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv; load_dotenv(ROOT / ".env")
from openai import OpenAI

PROMPT = """You are an expert governance analyst. For this record, assign THREE fields as a JSON object:

1. argument_type: {Technical, Governance-Principle, Economic, Process, Off-topic}
   - Technical: code, architecture, spec, implementation details
   - Governance-Principle: DAO structure, voting rights, policy, decentralization philosophy
   - Economic: cost, incentives, tokenomics, funding
   - Process: lifecycle, procedure, review, coordination logistics
   - Off-topic: unrelated content

2. stance: {Support, Oppose, Modify, Neutral, Off-topic}
   - Support: explicitly favors the proposal/decision
   - Oppose: explicitly opposes
   - Modify: proposes changes
   - Neutral: factual or questions without clear position
   - Off-topic: unrelated

3. consensus_signal: {Adopted, Rejected, Pending, N/A}
   - Adopted: the proposal/suggestion was accepted
   - Rejected: it was denied
   - Pending: still under discussion
   - N/A: not applicable (informational record)

OUTPUT: Only the JSON object: {"argument_type":"...","stance":"...","consensus_signal":"..."}"""

BACKENDS = {
    "deepseek-v4-flash": {
        "api_key_env": "DEEPSEEK_API_KEY", "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash", "max_tokens": 512, "temperature": 0.0,
        "sleep": 0.05, "core": True,
    },
    "glm-4-plus": {
        "api_key_env": "GLM_API_KEY", "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-plus", "max_tokens": 256, "temperature": 0.0,
        "sleep": 0.05, "core": True,
    },
    "moonshot-v1-auto": {
        "api_key_env": "KIMI_API_KEY", "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-auto", "max_tokens": 256, "temperature": 0.0,
        "sleep": 0.0, "core": True,
    },
}

OUT_DIR = ROOT / "data" / "annotated" / "r3"
FIELDS = ["argument_type", "stance", "consensus_signal"]


def parse_json(raw: str) -> dict | None:
    raw = raw.strip()
    t = re.search(r'<think>.*?</think>', raw, re.DOTALL)
    if t: raw = raw[t.end():].strip()
    for pat in [r'\{[^{}]*"argument_type"[^{}]*\}', r'\{[^{}]*"stance"[^{}]*\}',
                 r'\{[^{}]*"consensus_signal"[^{}]*\}', r'\{[^{}]*\}']:
        m = re.search(pat, raw)
        if m:
            try: return json.loads(m.group(0))
            except: pass
    try: return json.loads(raw)
    except: return None


def annotate_one(client, model, max_tokens, temperature, record, case_label):
    text = (record.get("raw_text") or "").strip()[:3000]
    title = record.get("title", "")
    user = f"Author: {record.get('author','?')}\nDate: {record.get('date','?')}\n"
    if title: user += f"Title: {title}\n"
    user += f"Platform: {record.get('source','?')}\nCase: {case_label} governance\n\nText:\n{text}"
    for attempt in range(3):
        try:
            r = client.chat.completions.create(
                model=model, max_tokens=max_tokens, temperature=temperature,
                messages=[{"role":"system","content":PROMPT},{"role":"user","content":user}])
            raw = r.choices[0].message.content
            if raw and raw.strip():
                ann = parse_json(raw)
                if ann and all(f in ann for f in FIELDS):
                    return {**record, "annotation": {f: ann[f] for f in FIELDS}, "annotation_error": None}
            time.sleep(0.3)
        except Exception:
            time.sleep(1.5 if attempt == 0 else 3.0)
    return {**record, "annotation": None, "annotation_error": "retries_exhausted"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(BACKENDS))
    ap.add_argument("--case", required=True, choices=["erc","a2a"])
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--workers", type=int, default=1,
                    help="Concurrent API workers (default: 1)")
    args = ap.parse_args()

    cfg = BACKENDS[args.model]
    key = os.environ.get(cfg["api_key_env"], "")
    if not key: sys.exit(f"ERROR: {cfg['api_key_env']} not set")

    client = OpenAI(api_key=key, base_url=cfg["base_url"])
    model_dir = OUT_DIR / args.case / args.model / f"round_{args.round}"
    model_dir.mkdir(parents=True, exist_ok=True)
    out_path = model_dir / "annotations.json"
    manifest_path = model_dir / "manifest.json"

    # Load data
    if args.case == "erc":
        recs = []
        erc_dir = ROOT / "data" / "annotated" / "r2"
        for m in ["deepseek", "glm", "kimi"]:
            p = erc_dir / m / "annotations.json"
            if p.exists():
                recs = json.loads(p.read_text())
                break
        if not recs:
            cp = ROOT / "data/annotated/r2/consensus/erc_annotations.json"
            if cp.exists():
                recs = [{**r, "_case": "ERC-cluster"} for r in json.loads(cp.read_text())]
    else:
        src = ROOT / "data" / "annotated" / "annotated_records.json"
        all_recs = json.loads(src.read_text())
        recs = [r for r in all_recs if r.get("_case") == "Google-A2A"
                and len((r.get("raw_text") or "").strip()) >= 50
                and not (r.get("author", "") or "").endswith("[bot]")]

    if args.limit:
        recs = recs[:args.limit]
        print(f"LIMITED to {len(recs)} records (test mode)")

    def rid(r):
        if args.case == "erc":
            cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
                   or r.get("issue_number") or r.get("pr_number"))
            return f"{r.get('_case','')}_{r.get('source','')}_{cid}_{r.get('date','')}"
        else:
            url = r.get("url", "")
            return url if url else f"a2a_{r.get('source','')}_{r.get('issue_number','')}_{r.get('date','')}"

    # Resume
    done = []
    done_ids = set()
    if out_path.exists():
        all_done = json.loads(out_path.read_text())
        done = [r for r in all_done if r.get("annotation") is not None]
        failed = [r for r in all_done if r.get("annotation") is None]
        done_ids = {rid(r) for r in done}
        if failed:
            print(f"Resuming: {len(done)} annotated, {len(failed)} failed (will retry)")
        else:
            print(f"Resuming: {len(done)} already annotated")

    todo = [r for r in recs if rid(r) not in done_ids]
    if not todo:
        print("All done — nothing to annotate."); return

    workers = args.workers
    print(f"Annotating {len(todo)} {args.case.upper()} records ({cfg['model']}, "
          f"{workers} worker{'s' if workers > 1 else ''})…")
    t0 = time.time()
    case_label = "ERC agent cluster" if args.case == "erc" else "Google A2A"

    if workers <= 1:
        errs = 0
        for i, rec in enumerate(todo, 1):
            result = annotate_one(client, cfg["model"], cfg["max_tokens"],
                                  cfg["temperature"], rec, case_label)
            done.append(result)
            if result["annotation"] is None: errs += 1
            if i % args.batch_size == 0 or i == len(todo):
                with open(str(out_path), "w") as f:
                    json.dump(done, f, indent=2, ensure_ascii=False)
                    f.flush(); os.fsync(f.fileno())
            if i % 20 == 0 or i == 1 or i == len(todo):
                e = time.time() - t0
                rate = i / max(e, 0.1)
                eta = (len(todo) - i) / max(rate, 0.01) / 60
                print(f"  [{i}/{len(todo)}] rate={rate:.1f}/s ETA={eta:.0f}m "
                      f"ok={result['annotation'] is not None} errs={errs}", flush=True)
            time.sleep(cfg["sleep"])
    else:
        lock = threading.Lock()
        errs = [0]
        completed = [0]

        def _worker(rec):
            c = OpenAI(api_key=key, base_url=cfg["base_url"])
            return annotate_one(c, cfg["model"], cfg["max_tokens"], cfg["temperature"],
                               rec, case_label)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_worker, rec): rec for rec in todo}
            for future in as_completed(futures):
                result = future.result()
                with lock:
                    done.append(result)
                    completed[0] += 1
                    if result["annotation"] is None:
                        errs[0] += 1
                    n = completed[0]
                    if n % args.batch_size == 0 or n == len(todo):
                        with open(str(out_path), "w") as f:
                            json.dump(done, f, indent=2, ensure_ascii=False)
                            f.flush(); os.fsync(f.fileno())
                if n % 20 == 0 or n == 1 or n == len(todo):
                    e = time.time() - t0
                    rate = n / max(e, 0.1)
                    eta = (len(todo) - n) / max(rate, 0.01) / 60
                    print(f"  [{n}/{len(todo)}] rate={rate:.1f}/s ETA={eta:.0f}m "
                          f"errs={errs[0]} w={workers}", flush=True)
        errs = errs[0]

    # Final save
    with open(str(out_path), "w") as f:
        json.dump(done, f, indent=2, ensure_ascii=False)
        f.flush(); os.fsync(f.fileno())

    n_ok = sum(1 for r in done if r["annotation"] is not None)
    elapsed = time.time() - t0
    manifest = {
        "model": cfg["model"], "case": args.case, "fields": FIELDS,
        "total": len(done), "annotated": n_ok, "errors": len(done)-n_ok,
        "runtime_s": round(elapsed), "annotated_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nDone: {n_ok}/{len(done)} annotated ({elapsed:.0f}s, "
          f"{n_ok/max(elapsed,1):.1f}/s effective)")


if __name__ == "__main__":
    main()
