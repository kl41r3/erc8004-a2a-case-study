"""
Verify annotation coverage: for each raw source file,
  eligible_raw - failed_annotations == successfully_annotated

Prints a pass/fail table and exits non-zero if any check fails.
"""

import json
import sys
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
ANN_PATH = Path(__file__).parent.parent / "data" / "annotated" / "annotated_records.json"

MIN_TEXT = 20  # same threshold as annotate_llm.py


def load_annotated():
    ann = json.loads(ANN_PATH.read_text())
    # index by (source, id) → annotation result
    by_source = {}   # source_label -> {ok: int, fail: int, fail_errors: list}
    for r in ann:
        src = r.get("source", "?")
        ok = r.get("annotation") is not None
        err = r.get("annotation_error") or ""
        if src not in by_source:
            by_source[src] = {"ok": 0, "fail": 0, "fail_short": 0, "errors": []}
        if ok:
            by_source[src]["ok"] += 1
        elif err == "text_too_short":
            by_source[src]["fail_short"] += 1
        else:
            by_source[src]["fail"] += 1
            by_source[src]["errors"].append(err[:60])
    return ann, by_source


def count_raw_eligible(path: Path, text_field="raw_text") -> tuple[int, int]:
    """Returns (total_records, eligible_records with text >= MIN_TEXT)."""
    data = json.loads(path.read_text())
    eligible = sum(1 for r in data if len((r.get(text_field) or "").strip()) >= MIN_TEXT)
    return len(data), eligible


def main():
    ann_records, by_source = load_annotated()

    # Map raw files → expected source labels in annotated file
    # (source_label_in_annotated, raw_file, text_field)
    sources = [
        # ERC-8004
        ("forum",              "forum_posts.json",              "raw_text"),
        # ERC-8004 GitHub — annotate_llm.py loads github_comments_filtered.json
        # Records get source from their own 'source' field; could be several labels
        (None,                 "github_comments_filtered.json", "raw_text"),
        # A2A
        (None,                 "a2a_issues.json",               "raw_text"),
        (None,                 "a2a_prs.json",                  "raw_text"),
        (None,                 "a2a_discussions.json",          "raw_text"),
        # Gitvote — annotated by annotate_gitvote.py, uses 'text' field
        (None,                 "a2a_gitvote_prs.json",          "text"),
    ]

    print(f"{'File':<40} {'Raw':>6} {'Eligible':>9} {'Ann-OK':>8} {'Ann-Fail':>9} {'Check':>8}")
    print("-" * 90)

    all_pass = True

    # Per-file check using _record_id or case+source matching
    # Simpler: count by loading each raw file and matching to annotated records by content

    # Build a set of annotated record IDs (same logic as annotate_llm.py _record_id)
    def record_id(r, case, text_field="raw_text"):
        return (
            f"{case}"
            f"_{r.get('source', r.get('record_type', '?'))}"
            f"_{r.get('post_id') or r.get('comment_id') or r.get('sha') or r.get('issue_number') or r.get('pr_number')}"
            f"_{r.get('date')}"
        )

    ann_ids = {}  # id -> annotation result
    for r in ann_records:
        rid = (
            f"{r.get('_case')}"
            f"_{r.get('source', '?')}"
            f"_{r.get('post_id') or r.get('comment_id') or r.get('sha') or r.get('issue_number') or r.get('pr_number')}"
            f"_{r.get('date')}"
        )
        ann_ids[rid] = r.get("annotation") is not None

    # --- Per-file verification ---
    file_specs = [
        ("forum_posts.json",             "ERC-8004",    "raw_text", "standard"),
        ("github_comments_filtered.json","ERC-8004",    "raw_text", "standard"),
        ("a2a_issues.json",              "Google-A2A",  "raw_text", "standard"),
        ("a2a_prs.json",                 "Google-A2A",  "raw_text", "standard"),
        ("a2a_discussions.json",         "Google-A2A",  "raw_text", "standard"),
        # gitvote: uses 'text' field; many records overlap with a2a_issues/prs.
        # Match by (author, date) across all annotated records.
        ("a2a_gitvote_prs.json",         "Google-A2A",  "text",     "gitvote"),
    ]

    # For gitvote matching: build (author, date) lookup from all annotated records
    ann_by_author_date = {}
    for r in ann_records:
        key = (r.get("author", ""), r.get("date", ""))
        if key not in ann_by_author_date:
            ann_by_author_date[key] = r.get("annotation") is not None

    # Bot authors to skip (consistent with annotate_llm.py and annotate_gitvote.py)
    BOT_AUTHORS = {
        "gemini-code-assist[bot]", "google-cla[bot]", "github-actions[bot]",
        "codecov[bot]", "dependabot[bot]", "git-vote[bot]",
    }

    total_eligible = 0
    total_ann_ok = 0
    total_ann_fail = 0

    for fname, case, tfield, match_mode in file_specs:
        fpath = RAW_DIR / fname
        if not fpath.exists():
            print(f"  MISSING: {fname}")
            continue

        raw = json.loads(fpath.read_text())
        n_total = len(raw)

        # Filter: non-bot, text >= MIN_TEXT
        eligible = [r for r in raw
                    if len((r.get(tfield) or "").strip()) >= MIN_TEXT
                    and r.get("author", "") not in BOT_AUTHORS
                    and not r.get("author", "").endswith("[bot]")]
        n_eligible = len(eligible)

        ann_ok = 0
        ann_fail = 0
        ann_missing = 0

        for r in eligible:
            if match_mode == "gitvote":
                # Match by (author, date) — many overlap with a2a_issues/prs
                key = (r.get("author", ""), r.get("date", ""))
                if key in ann_by_author_date:
                    if ann_by_author_date[key]:
                        ann_ok += 1
                    else:
                        ann_fail += 1
                else:
                    ann_missing += 1
            else:
                rid = (
                    f"{case}"
                    f"_{r.get('source', r.get('record_type', '?'))}"
                    f"_{r.get('post_id') or r.get('comment_id') or r.get('sha') or r.get('issue_number') or r.get('pr_number')}"
                    f"_{r.get('date')}"
                )
                if rid in ann_ids:
                    if ann_ids[rid]:
                        ann_ok += 1
                    else:
                        ann_fail += 1
                else:
                    ann_missing += 1

        total_eligible += n_eligible
        total_ann_ok += ann_ok
        total_ann_fail += ann_fail

        status = "PASS" if ann_missing == 0 and ann_fail == 0 else \
                 "WARN" if ann_missing == 0 else "FAIL"
        if status != "PASS":
            all_pass = False

        mark = "✓" if status == "PASS" else ("!" if status == "WARN" else "✗")
        print(f"  {mark} {fname:<38} {n_total:>6} {n_eligible:>9} {ann_ok:>8} {ann_fail:>9}  "
              f"missing={ann_missing}  [{status}]")

    print("-" * 90)
    print(f"  {'TOTAL':<39} {'':>6} {total_eligible:>9} {total_ann_ok:>8} {total_ann_fail:>9}")
    print()

    # Overall annotated file stats
    total_in_file = len(ann_records)
    total_ok = sum(1 for r in ann_records if r.get("annotation") is not None)
    total_short = sum(1 for r in ann_records if r.get("annotation_error") == "text_too_short")
    total_err = sum(1 for r in ann_records if r.get("annotation") is None and r.get("annotation_error") != "text_too_short")
    print(f"Annotated file: {total_in_file} records total")
    print(f"  Successfully annotated: {total_ok}")
    print(f"  text_too_short (skipped): {total_short}")
    print(f"  Other failures: {total_err}")

    if total_err > 0:
        print("\nFailed records by error type:")
        err_counts = {}
        for r in ann_records:
            if r.get("annotation") is None and r.get("annotation_error") != "text_too_short":
                e = (r.get("annotation_error") or "?").split(":")[0].strip()
                err_counts[e] = err_counts.get(e, 0) + 1
        for e, n in sorted(err_counts.items(), key=lambda x: -x[1]):
            print(f"  {e}: {n}")

    print()
    if all_pass and total_err == 0:
        print("ALL CHECKS PASSED ✓")
        return 0
    else:
        print("ISSUES FOUND — see above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
