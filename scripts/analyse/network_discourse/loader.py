"""
Shared data loader: joins coded_records.json (theme_id) with
annotated_records.json (author, stance, stakeholder_institution).

Record-ID scheme (from thematic_lm/pipeline.py):
  - Records with url field → record_id = url
  - Otherwise → record_id = "{case}_{source}_{uid}"
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).parents[3]

BOT_AUTHORS = {"github-actions[bot]", "eip-review-bot", "dependabot[bot]"}

STANCE_SCORE = {"Support": 1.0, "Modify": 0.5, "Neutral": 0.0, "Oppose": -1.0}


def load_joined() -> pd.DataFrame:
    """
    Returns DataFrame columns:
      record_id, author, case, theme_id, confidence,
      stance, stance_val, stakeholder_institution
    Off-topic and Unclassified records are excluded.
    """
    ann_records = json.loads(
        (ROOT / "data/annotated/annotated_records.json").read_text()
    )

    url_lookup: dict[str, dict] = {}
    composite_lookup: dict[str, dict] = {}
    for r in ann_records:
        author = r.get("author", "")
        if author in BOT_AUTHORS or author.endswith("[bot]"):
            continue
        text = (r.get("raw_text") or "").strip()
        if len(text) < 20:
            continue
        case = r.get("_case", "")
        if case not in {"ERC-8004", "Google-A2A"}:
            continue
        if r.get("url"):
            url_lookup[r["url"]] = r
        else:
            uid = (
                r.get("post_id")
                or r.get("comment_id")
                or r.get("issue_number")
                or r.get("pr_number")
            )
            key = f"{case}_{r.get('source', '?')}_{uid}"
            composite_lookup[key] = r

    coded = json.loads(
        (ROOT / "output/topic_discovery/thematic_lm/coded_records.json").read_text()
    )

    rows = []
    for c in coded:
        rid = c["record_id"]
        theme_id = c["theme_id"]
        if theme_id == "Unclassified":
            continue
        ann = url_lookup.get(rid) or composite_lookup.get(rid)
        if ann is None:
            continue
        annotation = ann.get("annotation") or {}
        stance = annotation.get("stance", "Neutral")
        if stance == "Off-topic":
            continue
        rows.append(
            {
                "record_id": rid,
                "author": ann["author"],
                "case": ann["_case"],
                "theme_id": theme_id,
                "confidence": c["confidence"],
                "stance": stance,
                "stance_val": STANCE_SCORE.get(stance, 0.0),
                "stakeholder_institution": annotation.get(
                    "stakeholder_institution", "Unknown"
                ),
            }
        )

    return pd.DataFrame(rows)
