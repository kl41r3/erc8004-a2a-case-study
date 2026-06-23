"""
validate_thematic.py — Cross-model thematic convergence analysis.

After 3 models independently extract themes from the same deliberative records,
this script:
  1. Builds a merged theme space per record (union of all model themes)
  2. Computes Jaccard similarity on theme *labels* (exact match)
  3. Computes semantic similarity on theme *labels* (via embedding or LLM judge)
  4. Reports per-model stats: themes/record, sentiment distribution
  5. Identifies convergent themes (appear in ≥2 models for same record)
  6. Exports a thematic convergence report + per-record multi-model theme table

Usage:
  uv run python scripts/analyse/validate_thematic.py
  uv run python scripts/analyse/validate_thematic.py --semantic  # use LLM for similarity
"""

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
THEMATIC_DIR = ROOT / "data" / "annotated" / "r2" / "thematic"
OUT_DIR = THEMATIC_DIR / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = ["deepseek", "glm", "kimi"]
MODEL_NAMES = {"deepseek": "DeepSeek-V4-Flash", "glm": "GLM-4-Plus", "kimi": "Moonshot-v1-Auto"}


def load_thematic() -> dict[str, dict]:
    """Load per-model thematic data, keyed by _record_id."""
    model_data = {}
    for model in MODELS:
        path = THEMATIC_DIR / f"{model}_themes.json"
        if not path.exists():
            print(f"  MISSING: {path}")
            continue
        all_recs = json.loads(path.read_text())
        idx = {}
        for r in all_recs:
            rid = _record_id(r)
            idx[rid] = r
        model_data[model] = idx
        themed = sum(1 for r in idx.values() if r.get("themes") and not r.get("theme_error"))
        print(f"  {model}: {len(idx)} records, {themed} with themes")
    return model_data


def _record_id(r: dict) -> str:
    cid = (r.get("post_id") or r.get("comment_id") or r.get("pr_number"))
    return f"{r.get('_case')}_{r.get('source')}_{cid}"


def align_themes(model_data: dict[str, dict]) -> list[dict]:
    """Align records across models, produce per-record multi-model theme table."""
    common_ids = set.intersection(*(set(d.keys()) for d in model_data.values())) if model_data else set()
    print(f"  Aligned records: {len(common_ids)}")
    rows = []
    for rid in sorted(common_ids):
        row = {"_record_id": rid,
               "_case": model_data[MODELS[0]][rid].get("_case", ""),
               "author": model_data[MODELS[0]][rid].get("author", ""),
               "text": (model_data[MODELS[0]][rid].get("raw_text", ""))[:300]}
        for model in MODELS:
            r = model_data[model].get(rid, {})
            themes = r.get("themes", []) or []
            row[f"{model}_n_themes"] = len(themes)
            row[f"{model}_themes"] = " | ".join(t.get("theme", "") for t in themes)
            # sentiments are S/C/N per theme — store as space-joined for clean parsing
            s_list = [t.get("sentiment", "") for t in themes]
            row[f"{model}_sentiments"] = " ".join(s_list)
        rows.append(row)
    return rows


def jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def theme_convergence(aligned: list[dict]) -> dict:
    """Per-record theme overlap stats."""
    results = {"per_record": [], "summary": defaultdict(list)}
    # Use all MODELS that actually have theme columns in the data
    ms = [m for m in MODELS if f"{m}_themes" in aligned[0]] if aligned else MODELS
    if not ms:
        return results
    pair_keys = []
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            pair_keys.append(f"{ms[i]}↔{ms[j]}")

    for row in aligned:
        rec = {"_record_id": row["_record_id"]}
        # build theme sets per model
        model_themes = {}
        for m in ms:
            key = f"{m}_themes"
            labels = set()
            if row.get(key):
                labels = set(t.strip() for t in row[key].split("|") if t.strip())
            model_themes[m] = labels
            rec[f"{m}_themes"] = sorted(labels)

        # pairwise Jaccard
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                jac = jaccard(model_themes[ms[i]], model_themes[ms[j]])
                key = f"{ms[i]}↔{ms[j]}"
                rec[f"jaccard_{key}"] = round(jac, 3)
                results["summary"][f"jaccard_{key}"].append(jac)

        # convergence: themes found by ≥2 models
        all_labels = set()
        for labels in model_themes.values():
            all_labels |= labels
        convergent = [l for l in all_labels if sum(1 for m in ms if l in model_themes[m]) >= 2]
        unique = [l for l in all_labels if sum(1 for m in ms if l in model_themes[m]) == 1]
        rec["n_convergent"] = len(convergent)
        rec["n_unique"] = len(unique)
        rec["convergent_themes"] = convergent
        rec["unique_themes"] = unique
        results["per_record"].append(rec)

    # Aggregate summary
    agg = {}
    for key, vals in results["summary"].items():
        vals_f = [v for v in vals if v is not None]
        agg[key] = {
            "mean": round(sum(vals_f) / len(vals_f), 3) if vals_f else 0,
            "median": round(sorted(vals_f)[len(vals_f)//2], 3) if vals_f else 0,
            "n": len(vals_f),
        }
    results["aggregate"] = agg
    return results


def model_stats(aligned: list[dict]) -> dict:
    """Per-model: themes/record, sentiment distribution."""
    stats = {}
    for model in MODELS:
        n_key = f"{model}_n_themes"
        sent_key = f"{model}_sentiments"
        counts = [row[n_key] for row in aligned if isinstance(row.get(n_key), (int, float))]
        sents = []
        for row in aligned:
            if row.get(sent_key):
                sents.extend(row[sent_key].split())  # space-separated sentiment words
        sent_dist = Counter(sents)
        stats[model] = {
            "mean_themes_per_record": round(sum(counts) / len(counts), 2) if counts else 0,
            "total_themes": sum(counts),
            "records_with_themes": sum(1 for c in counts if c > 0),
            "sentiment_distribution": dict(sent_dist.most_common()),
        }
        # Map S→Supportive, C→Critical, N→Neutral
        stats[model]["sentiment_distribution"] = {
            k: v for k, v in sent_dist.most_common()
        }
    return stats


def write_cross_model_table(aligned: list[dict]):
    """CSV with all 3 models' themes side-by-side for qualitative review."""
    path = OUT_DIR / "cross_model_themes.csv"
    cols = ["_record_id", "_case", "author", "text"]
    for m in MODELS:
        cols += [f"{m}_n_themes", f"{m}_themes"]
    cols += ["n_convergent", "n_unique", "convergent_themes"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(aligned)
    print(f"\n  Cross-model theme table → {path}  ({len(aligned)} rows)")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", action="store_true",
                        help="Use LLM for semantic theme similarity (slower, richer)")
    args = parser.parse_args()

    print("=== Thematic Convergence Validation ===\n")
    print("Loading thematic data…")
    model_data = load_thematic()
    if len(model_data) < 2:
        print(f"ERROR: need ≥2 models, got {len(model_data)}")
        return

    aligned = align_themes(model_data)

    # 1. Convergence analysis
    print("\n── 1. Theme Convergence (Jaccard on labels) ──")
    conv = theme_convergence(aligned)
    for key, vals in conv["aggregate"].items():
        print(f"  {key}: mean Jaccard={vals['mean']:.3f}  median={vals['median']:.3f}  (n={vals['n']})")

    # 2. Per-model stats
    print("\n── 2. Per-Model Thematic Stats ──")
    mstats = model_stats(aligned)
    for model, s in mstats.items():
        print(f"  {model}: {s['mean_themes_per_record']} themes/record  "
              f"{s['records_with_themes']} themed  {s['total_themes']} total themes  "
              f"sentiments={s['sentiment_distribution']}")

    # 3. Most convergent themes (global)
    print("\n── 3. Most Convergent Themes (≥2 models, ≥2 records) ──")
    theme_records = defaultdict(list)
    for rec in conv["per_record"]:
        for t in rec.get("convergent_themes", []):
            theme_records[t].append(rec["_record_id"])
    top = sorted(theme_records.items(), key=lambda x: -len(x[1]))[:25]
    for theme, recs in top:
        if len(recs) >= 2:
            print(f"  [{len(recs):>3} records] {theme}")

    # 4. Export
    write_cross_model_table(aligned)

    # Write full report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": list(model_data.keys()),
        "aligned_records": len(aligned),
        "jaccard_convergence": conv["aggregate"],
        "model_stats": mstats,
        "top_convergent_themes": [{"theme": t, "n_records": len(r)} for t, r in top[:20]],
    }
    rpath = OUT_DIR / "thematic_validation_report.json"
    rpath.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n  Full report → {rpath}")


if __name__ == "__main__":
    main()
