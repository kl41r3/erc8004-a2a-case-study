"""
Standard I/O helpers used across the pipeline.

Every script that reads or writes JSON/CSV should use these functions
so that encoding, error handling, and directory creation are consistent.
"""

import json
import csv
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> Path:
    """Create parent directories if they don't exist. Returns path for chaining."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path) -> Any:
    """Load and return a JSON file. Returns None if the file does not exist."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any, indent: int = 2) -> Path:
    """Save data as JSON, creating parent directories as needed."""
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
    return path


def load_csv(path: Path) -> list[dict[str, str]]:
    """Load a CSV file as a list of dicts. Returns empty list if missing."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> Path:
    """Save a list of dicts as CSV, creating parent directories as needed."""
    ensure_dir(path)
    if fieldnames is None and rows:
        fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or [])
        writer.writeheader()
        writer.writerows(rows)
    return path


def load_json_lines(path: Path) -> list[dict]:
    """Load a JSON-lines file (one JSON object per line)."""
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
