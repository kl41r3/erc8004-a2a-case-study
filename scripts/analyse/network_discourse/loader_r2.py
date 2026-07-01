"""
loader_r2.py — Data loader for R2 consensus annotations + new Thematic-LM codes.

Joins consensus annotations (majority-vote across 3 models) with the Thematic-LM
coded records from the R2 analysis pipeline.

Used by DNA and socio-semantic network scripts when running in --r2 mode.

Record-ID scheme matches the Thematic-LM pipeline output format.
"""

import sys
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.paths import DATA_ANNOTATED_R2_CONSENSUS, ANALYSIS_TD_R2_CROSS_MODEL_THEMATIC
from lib.models import is_bot

STANCE_SCORE = {"Support": 1.0, "Modify": 0.5, "Neutral": 0.0, "Oppose": -1.0}

CONSENSUS_DIR = DATA_ANNOTATED_R2_CONSENSUS
THEMATIC_LM_DIR = ANALYSIS_TD_R2_CROSS_MODEL_THEMATIC / "moonshot-v1-auto"


def _record_id_erc(r: dict) -> str:
    """Match the ID scheme used by annotate_r2.py."""
    cid = (r.get("post_id") or r.get("comment_id") or r.get("sha")
           or r.get("issue_number") or r.get("pr_number"))
    return f"{r.get('_case')}_{r.get('source')}_{cid}_{r.get('date')}"


def _record_id_a2a(r: dict) -> str:
    """Match the ID scheme used by Thematic-LM run_r2.py (bare URL, no prefix)."""
    url = r.get("url", "")
    if url:
        return url
    cid = r.get("issue_number") or r.get("pr_number") or ""
    return f"a2a__{r.get('source')}_{cid}_{r.get('date')}"


def load_joined_r2() -> pd.DataFrame:
    """
    Returns DataFrame with columns:
      record_id, author, case, theme_id, confidence,
      stance, stance_val, stakeholder_institution, consensus_confidence

    Both ERC (consensus) and A2A (consensus) records are joined with
    Thematic-LM coded records. Off-topic and Unclassified records excluded.
    """
    coded_path = THEMATIC_LM_DIR / "coded_records.json"
    if not coded_path.exists():
        raise FileNotFoundError(
            f"R2 Thematic-LM coded records not found: {coded_path}\n"
            "Run the R2 Thematic-LM pipeline first."
        )
    coded = json.loads(coded_path.read_text())

    # Build lookup tables from consensus annotations
    erc_lookup: dict[str, dict] = {}
    a2a_lookup: dict[str, dict] = {}

    erc_path = CONSENSUS_DIR / "erc_annotations.json"
    if erc_path.exists():
        for r in json.loads(erc_path.read_text()):
            if is_bot(r.get("author", "")):
                continue
            erc_lookup[_record_id_erc(r)] = r

    a2a_path = CONSENSUS_DIR / "a2a_annotations.json"
    if a2a_path.exists():
        for r in json.loads(a2a_path.read_text()):
            if is_bot(r.get("author", "")):
                continue
            a2a_lookup[_record_id_a2a(r)] = r

    all_lookup = {**erc_lookup, **a2a_lookup}

    rows = []
    for c in coded:
        rid = c["record_id"]
        theme_id = c.get("theme_id", "")
        if theme_id in ("Unclassified", "", None):
            continue
        ann = all_lookup.get(rid)
        if ann is None:
            continue
        annotation = ann.get("annotation") or {}
        stance = annotation.get("stance", "Neutral")
        if stance == "Off-topic":
            continue
        conf = ann.get("consensus_confidence", {})
        rows.append({
            "record_id": rid,
            "author": ann.get("author", ""),
            "case": ann.get("_case", ""),
            "theme_id": theme_id,
            "confidence": c.get("confidence", 1.0),
            "stance": stance,
            "stance_val": STANCE_SCORE.get(stance, 0.0),
            "stakeholder_institution": annotation.get("stakeholder_institution", "Unknown"),
            "consensus_confidence_stance": conf.get("stance", 1.0) if isinstance(conf, dict) else 1.0,
        })

    return pd.DataFrame(rows)


def load_erc_only() -> pd.DataFrame:
    """Load only ERC cluster records (for ERC-only network analysis)."""
    df = load_joined_r2()
    return df[df["case"].str.startswith("ERC")].copy()


def load_a2a_only() -> pd.DataFrame:
    """Load only Google A2A records."""
    df = load_joined_r2()
    return df[df["case"] == "Google-A2A"].copy()
