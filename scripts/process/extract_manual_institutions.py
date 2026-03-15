"""extract_manual_institutions.py — Parse R07 manual investigation report into structured JSON.

Source: reports/R07_2026-03-14_机构归属人工调查.md
Output: data/raw/manual_institutions.json

Each entry schema:
  primary_handle    str            Main handle (forum or GitHub)
  alt_handles       list[str]      Alternative handles (e.g. forum ↔ GitHub)
  display_name      str | None
  institution       str            Canonical institution name (parentheticals stripped)
  confidence        str            "Confirmed" | "Strong" | "Probable"
  institution_source str           "manual_R07" | "eip_header_email"
  case              str            "ERC-8004" | "Google-A2A"
  evidence          str            Evidence summary text
  evidence_url      str | None     First URL found in evidence
  lm_correction     bool           True if this entry corrects an LM annotation error
  lm_wrong          str | None     The institution the LM wrongly inferred
  section           str            R07 section number ("1.1", "2.3", "3", etc.)
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
R07_PATH = ROOT / "reports" / "R07_2026-03-14_机构归属人工调查.md"
OUTPUT_PATH = ROOT / "data" / "raw" / "manual_institutions.json"

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def strip_md(text: str) -> str:
    """Remove markdown bold/italic/code formatting."""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()


def extract_url(text: str) -> str | None:
    """Return the first HTTP(S) URL found in text."""
    m = re.search(r'\[.*?\]\((https?://[^\)]+)\)', text)
    if m:
        return m.group(1)
    m = re.search(r'https?://[^\s\)）】\]]+', text)
    if m:
        return m.group(0).rstrip('）)。')
    return None


def clean_institution(raw: str) -> str:
    """Strip bold, leading @, and trailing parenthetical from institution string."""
    raw = strip_md(raw)
    raw = re.sub(r'（[^）]*）', '', raw)   # remove （...）
    raw = re.sub(r'\([^)]*\)', '', raw)    # remove (...)
    raw = raw.lstrip('@').strip()
    return raw


def clean_handle(raw: str) -> str | None:
    raw = strip_md(raw).lstrip('@').strip()
    if raw in ('未知', '—', '-', ''):
        return None
    return raw


def parse_handle_cell(cell: str) -> tuple[str | None, list[str]]:
    """Parse '**Marco-MetaMask** / MarcoMetaMask' → ('Marco-MetaMask', ['MarcoMetaMask'])."""
    cell = strip_md(cell)
    parts = [p.strip().lstrip('@') for p in cell.split('/')]
    primary = parts[0] if parts[0] not in ('未知', '—', '-', '') else None
    alts = [p for p in parts[1:] if p not in ('未知', '—', '-', '')]
    return primary, alts


def null_name(s: str) -> str | None:
    s = strip_md(s).strip()
    if s in ('（未公开姓名）', '（未公开）', '—', '-', ''):
        return None
    return s


# ---------------------------------------------------------------------------
# Table parser
# ---------------------------------------------------------------------------

def parse_table_rows(text: str) -> list[list[str]]:
    """Return all non-separator rows from the first markdown table found in text."""
    rows = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('|'):
            if in_table:
                break           # table ended
            continue
        in_table = True
        cells = [c.strip() for c in stripped.split('|')[1:-1]]
        if not cells:
            continue
        if all(re.match(r'^[-: ]+$', c) for c in cells):
            continue            # separator row
        rows.append(cells)
    return rows   # row 0 = header, rows 1+ = data


# ---------------------------------------------------------------------------
# Section splitter
# ---------------------------------------------------------------------------

def split_sections(markdown: str) -> dict[str, str]:
    """Split markdown by ## / ### headings → {heading_text: body_text}."""
    sections: dict[str, str] = {}
    current = "__preamble__"
    buf: list[str] = []
    for line in markdown.splitlines():
        if line.startswith('##'):
            if buf:
                sections[current] = '\n'.join(buf)
            current = line.strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = '\n'.join(buf)
    return sections


# ---------------------------------------------------------------------------
# Section-specific parsers
# ---------------------------------------------------------------------------

def parse_confirmed_section(section_text: str, case: str, section_id: str) -> list[dict]:
    """Sections 1.1, 1.2, 2.1, 2.2 — columns: handle | name | institution | confidence | evidence."""
    rows = parse_table_rows(section_text)
    entries = []
    for cells in rows[1:]:      # skip header
        if len(cells) < 5:
            continue
        handle_cell, name_cell, inst_cell, conf_cell, evidence_cell = cells[:5]
        primary, alts = parse_handle_cell(handle_cell)
        if primary is None and not alts:
            continue
        institution = clean_institution(inst_cell)
        confidence = conf_cell.strip()
        evidence_text = strip_md(evidence_cell)
        # Strip markdown link syntax for display
        evidence_clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', evidence_text).strip()
        evidence_url = extract_url(evidence_cell)
        entries.append({
            "primary_handle": primary,
            "alt_handles": alts,
            "display_name": null_name(name_cell),
            "institution": institution,
            "confidence": confidence,
            "institution_source": "manual_R07",
            "case": case,
            "evidence": evidence_clean,
            "evidence_url": evidence_url,
            "lm_correction": False,
            "lm_wrong": None,
            "section": section_id,
        })
    return entries


def parse_unknown_section(section_text: str, case: str, section_id: str) -> list[dict]:
    """Sections 1.3, 2.4 — columns: handle | name | count | notes.
    These authors were manually checked and confirmed as Independent/Unknown."""
    rows = parse_table_rows(section_text)
    entries = []
    for cells in rows[1:]:      # skip header
        if not cells:
            continue
        handle = clean_handle(cells[0]) if cells else None
        if not handle:
            continue
        display = null_name(cells[1]) if len(cells) > 1 else None
        notes = cells[3].strip() if len(cells) > 3 else "无公开信息"
        entries.append({
            "primary_handle": handle,
            "alt_handles": [],
            "display_name": display,
            "institution": "Independent",
            "confidence": "Confirmed",
            "institution_source": "manual_R07",
            "case": case,
            "evidence": notes if notes else "无公开信息，人工核查后归为Independent",
            "evidence_url": None,
            "lm_correction": False,
            "lm_wrong": None,
            "section": section_id,
        })
    return entries


def parse_lm_corrections(section_text: str, case: str) -> list[dict]:
    """Section 2.3 — columns: handle | LM_inferred | actual | evidence."""
    rows = parse_table_rows(section_text)
    entries = []
    for cells in rows[1:]:      # skip header
        if len(cells) < 3:
            continue
        handle = clean_handle(cells[0])
        if not handle:
            continue
        lm_wrong = strip_md(cells[1]).strip()
        actual = clean_institution(cells[2])
        if actual == '':
            actual = "Unknown"
        evidence_cell = cells[3] if len(cells) > 3 else ''
        evidence_text = strip_md(evidence_cell)
        entries.append({
            "primary_handle": handle,
            "alt_handles": [],
            "display_name": None,
            "institution": actual,
            "confidence": "Confirmed",
            "institution_source": "manual_R07",
            "case": case,
            "evidence": evidence_text,
            "evidence_url": extract_url(evidence_cell),
            "lm_correction": True,
            "lm_wrong": lm_wrong,
            "section": "2.3",
        })
    return entries


def parse_eip_header(section_text: str) -> list[dict]:
    """Section 3 (EIP co-author header) — columns: name | github_handle | email | institution.
    Source is 'eip_header_email' — highest possible confidence."""
    EIP_URL = "https://github.com/ethereum/ERCs/blob/master/ERCS/erc-8004.md"
    rows = parse_table_rows(section_text)
    entries = []
    for cells in rows[1:]:      # skip header
        if len(cells) < 4:
            continue
        name_cell, handle_cell, email_cell, inst_cell = cells[:4]
        handle = clean_handle(handle_cell)
        institution = clean_institution(inst_cell)
        email = email_cell.strip()
        entries.append({
            "primary_handle": handle,               # None for unknown handles
            "alt_handles": [],
            "display_name": null_name(name_cell),
            "institution": institution,
            "confidence": "Confirmed",
            "institution_source": "eip_header_email",
            "case": "ERC-8004",
            "evidence": f"EIP header email: {email}",
            "evidence_url": EIP_URL,
            "lm_correction": False,
            "lm_wrong": None,
            "section": "3",
        })
    return entries


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== extract_manual_institutions.py ===")
    if not R07_PATH.exists():
        raise FileNotFoundError(f"R07 not found: {R07_PATH}")

    markdown = R07_PATH.read_text(encoding="utf-8")
    sections = split_sections(markdown)

    all_entries: list[dict] = []

    # Map section heading substrings → parser
    for heading, body in sections.items():
        h = heading.lower()

        if '1.1' in heading:
            entries = parse_confirmed_section(body, "ERC-8004", "1.1")
            all_entries.extend(entries)
            print(f"  §1.1 ERC-8004 Confirmed/Strong: {len(entries)} entries")

        elif '1.2' in heading:
            entries = parse_confirmed_section(body, "ERC-8004", "1.2")
            all_entries.extend(entries)
            print(f"  §1.2 ERC-8004 Probable:         {len(entries)} entries")

        elif '1.3' in heading:
            entries = parse_unknown_section(body, "ERC-8004", "1.3")
            all_entries.extend(entries)
            print(f"  §1.3 ERC-8004 Unknown:          {len(entries)} entries")

        elif '2.1' in heading:
            entries = parse_confirmed_section(body, "Google-A2A", "2.1")
            all_entries.extend(entries)
            print(f"  §2.1 A2A Confirmed/Strong:      {len(entries)} entries")

        elif '2.2' in heading:
            entries = parse_confirmed_section(body, "Google-A2A", "2.2")
            all_entries.extend(entries)
            print(f"  §2.2 A2A Probable:              {len(entries)} entries")

        elif '2.3' in heading or 'lm' in h:
            entries = parse_lm_corrections(body, "Google-A2A")
            all_entries.extend(entries)
            print(f"  §2.3 LM corrections:            {len(entries)} entries")

        elif '2.4' in heading:
            entries = parse_unknown_section(body, "Google-A2A", "2.4")
            all_entries.extend(entries)
            print(f"  §2.4 A2A Unknown:               {len(entries)} entries")

        elif '三' in heading or 'eip' in h or '特别说明' in heading:
            entries = parse_eip_header(body)
            all_entries.extend(entries)
            print(f"  §3 EIP header co-authors:       {len(entries)} entries")

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(all_entries, ensure_ascii=False, indent=2))
    print(f"\nTotal entries: {len(all_entries)}")
    print(f"Saved → {OUTPUT_PATH}")

    # Quick summary
    from collections import Counter
    by_source = Counter(e["institution_source"] for e in all_entries)
    by_conf = Counter(e["confidence"] for e in all_entries)
    by_case = Counter(e["case"] for e in all_entries)
    print(f"  By source:     {dict(by_source)}")
    print(f"  By confidence: {dict(by_conf)}")
    print(f"  By case:       {dict(by_case)}")
    lm_fixes = [e for e in all_entries if e["lm_correction"]]
    print(f"  LM corrections: {len(lm_fixes)}")
    for e in lm_fixes:
        print(f"    {e['primary_handle']}: {e['lm_wrong']} → {e['institution']}")


if __name__ == "__main__":
    main()
