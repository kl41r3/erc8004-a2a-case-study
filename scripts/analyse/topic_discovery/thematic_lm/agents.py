"""
LLM agent call wrappers for each stage of the Thematic-LM pipeline.
Reuses the MiniMax/OpenAI-compatible pattern from scripts/process/annotate_llm.py.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from .prompts import (
    AGGREGATOR_SYSTEM, AGGREGATOR_USER,
    CODER_SYSTEM, CODER_USER,
    REVIEWER_SYSTEM, REVIEWER_USER,
    THEME_CODER_SYSTEM, THEME_CODER_USER,
)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_RE = re.compile(r"^```[^\n]*\n(.*?)```$", re.DOTALL)


def _clean_response(raw: str) -> str:
    """Strip <think> blocks and markdown code fences."""
    raw = _THINK_RE.sub("", raw).strip()
    m = _FENCE_RE.match(raw)
    if m:
        raw = m.group(1).strip()
    return raw


def _call(client, model: str, system: str, user: str, max_tokens: int = 4096, thinking: bool = True) -> str:
    extra: dict = {}
    if not thinking:
        # MiniMax-M2.5: budget_tokens=0 disables chain-of-thought reasoning
        extra["extra_body"] = {"think_budget_tokens": 0}
    for attempt in range(6):
        try:
            resp = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **extra,
            )
            return _clean_response(resp.choices[0].message.content)
        except Exception as e:
            if attempt == 5:
                print(f"  [give up after 6 attempts] {type(e).__name__}: {str(e)[:120]}")
                return ""   # return empty instead of crashing
            wait = min(2 ** attempt, 60)
            print(f"  [retry {attempt+1}/6] {type(e).__name__}: {str(e)[:80]} — waiting {wait}s")
            time.sleep(wait)
    return ""


def run_coder_batch(client, model: str, batch: list[dict]) -> list[dict]:
    """
    Stage 1: Open-code a batch of records.
    Returns list of {"id": original_index, "record_id": ..., "code": ...}
    """
    numbered = "\n\n".join(
        f"{i+1}. [{r['_record_id']}]\n{r['raw_text'][:800].strip()}"
        for i, r in enumerate(batch)
    )
    user = CODER_USER.format(n=len(batch), numbered_texts=numbered)
    raw = _call(client, model, CODER_SYSTEM, user, max_tokens=2048, thinking=False)
    try:
        parsed: list[dict] = json.loads(raw)
        result = []
        for item in parsed:
            idx = item.get("id", 0) - 1
            if 0 <= idx < len(batch):
                result.append({
                    "record_id": batch[idx]["_record_id"],
                    "code": item.get("code", ""),
                })
        return result
    except json.JSONDecodeError:
        # Return empty codes for this batch on parse failure
        return [{"record_id": r["_record_id"], "code": ""} for r in batch]


def run_aggregator(client, model: str, all_codes: list[str]) -> dict[str, list[str]]:
    """
    Stage 2: Group codes into themes.
    Returns {theme_label: [code1, code2, ...]}
    """
    codes_list = "\n".join(f"- {c}" for c in sorted(set(all_codes)) if c)
    user = AGGREGATOR_USER.format(n=len(set(all_codes)), codes_list=codes_list)
    raw = _call(client, model, AGGREGATOR_SYSTEM, user, max_tokens=4096)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def run_reviewer(client, model: str, raw_clusters: dict[str, list[str]]) -> list[dict]:
    """
    Stage 3: Review and refine the codebook.
    Returns list of {theme_id, label, description, codes}
    """
    raw_codebook = json.dumps(raw_clusters, indent=2, ensure_ascii=False)
    user = REVIEWER_USER.format(raw_codebook=raw_codebook)
    raw = _call(client, model, REVIEWER_SYSTEM, user, max_tokens=4096)
    try:
        codebook: list[dict] = json.loads(raw)
        # Normalise: ensure theme_id, label, description, codes
        for i, entry in enumerate(codebook):
            if "theme_id" not in entry:
                entry["theme_id"] = f"T{i+1:02d}"
        return codebook
    except json.JSONDecodeError:
        return []


def run_theme_coder_batch(
    client, model: str, codebook: list[dict], batch: list[dict]
) -> list[dict]:
    """
    Stage 4: Assign a theme from the codebook to each record in the batch.
    Returns list of {record_id, theme_id, confidence}
    """
    codebook_summary = "\n".join(
        f"{e['theme_id']}: {e['label']} — {e.get('description', '')}"
        for e in codebook
    )
    numbered = "\n\n".join(
        f"{i+1}. {r['raw_text'][:600].strip()}"
        for i, r in enumerate(batch)
    )
    user = THEME_CODER_USER.format(
        codebook_summary=codebook_summary,
        n=len(batch),
        numbered_texts=numbered,
    )
    raw = _call(client, model, THEME_CODER_SYSTEM, user, max_tokens=2048)
    try:
        parsed: list[dict] = json.loads(raw)
        result = []
        for item in parsed:
            idx = item.get("id", 0) - 1
            if 0 <= idx < len(batch):
                result.append({
                    "record_id": batch[idx]["_record_id"],
                    "theme_id": item.get("theme_id", "Unclassified"),
                    "confidence": item.get("confidence", "medium"),
                })
        return result
    except json.JSONDecodeError:
        return [
            {"record_id": r["_record_id"], "theme_id": "Unclassified", "confidence": "low"}
            for r in batch
        ]
