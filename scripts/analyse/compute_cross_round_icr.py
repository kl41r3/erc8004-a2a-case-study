"""Compute test-retest reliability for each canonical model across three rounds.

The output contains three pairwise Cohen kappa values and one three-rater
Fleiss kappa value for every case, model, and categorical annotation field.
Only records present with a non-null annotation in all three rounds are used.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.models import CANONICAL_MODELS
from lib.paths import DATA_ANNOTATED_R2_CROSS_ROUND, METRICS_R2_ICR_CROSS_ROUND

CASES = ("erc", "a2a")
FIELDS = ("argument_type", "stance", "consensus_signal")
ROUNDS = (1, 2, 3)


def record_id(case: str, record: dict) -> str:
    if case == "a2a":
        url = record.get("url", "")
        if url:
            return url
        return (
            f"a2a_{record.get('source', '')}_{record.get('issue_number', '')}_"
            f"{record.get('date', '')}"
        )
    identifier = (
        record.get("post_id")
        or record.get("comment_id")
        or record.get("sha")
        or record.get("issue_number")
        or record.get("pr_number")
    )
    return (
        f"{record.get('_case', '')}_{record.get('source', '')}_{identifier}_"
        f"{record.get('date', '')}"
    )


def load_round(case: str, model: str, round_number: int) -> dict[str, dict]:
    path = (
        DATA_ANNOTATED_R2_CROSS_ROUND
        / case
        / model
        / f"round_{round_number}"
        / "annotations.json"
    )
    records = json.loads(path.read_text())
    return {
        record_id(case, record): record["annotation"]
        for record in records
        if record.get("annotation") is not None
    }


def cohens_kappa(left: list[str], right: list[str]) -> float:
    if not left or len(left) != len(right):
        raise ValueError("Cohen kappa requires aligned, non-empty ratings")
    total = len(left)
    observed = sum(a == b for a, b in zip(left, right)) / total
    left_counts = Counter(left)
    right_counts = Counter(right)
    labels = set(left_counts) | set(right_counts)
    expected = sum(
        (left_counts[label] / total) * (right_counts[label] / total)
        for label in labels
    )
    return 1.0 if expected == 1.0 else (observed - expected) / (1.0 - expected)


def fleiss_kappa(ratings: list[list[str]]) -> float:
    if not ratings or len(ratings[0]) < 2:
        raise ValueError("Fleiss kappa requires items rated by at least two raters")
    raters = len(ratings[0])
    if any(len(item) != raters for item in ratings):
        raise ValueError("Fleiss kappa requires a fixed number of raters")
    item_agreements = []
    overall = Counter()
    for item in ratings:
        counts = Counter(item)
        overall.update(counts)
        item_agreements.append(
            (sum(count * count for count in counts.values()) - raters)
            / (raters * (raters - 1))
        )
    observed = sum(item_agreements) / len(item_agreements)
    total_ratings = len(ratings) * raters
    expected = sum((count / total_ratings) ** 2 for count in overall.values())
    return 1.0 if expected == 1.0 else (observed - expected) / (1.0 - expected)


def compute_rows() -> list[dict]:
    output = []
    for case in CASES:
        for model in CANONICAL_MODELS:
            rounds = {number: load_round(case, model, number) for number in ROUNDS}
            common_ids = set.intersection(*(set(rounds[number]) for number in ROUNDS))
            if not common_ids:
                raise ValueError(f"No common records for {case}/{model}")
            ordered_ids = sorted(common_ids)
            for field in FIELDS:
                values = {
                    number: [rounds[number][key].get(field) for key in ordered_ids]
                    for number in ROUNDS
                }
                if any(value is None for number in ROUNDS for value in values[number]):
                    raise ValueError(f"Missing {field} value for {case}/{model}")
                for left, right in ((1, 2), (1, 3), (2, 3)):
                    output.append(
                        {
                            "case": case,
                            "model": model,
                            "field": field,
                            "round_pair": f"R{left}-R{right}",
                            "kappa": round(cohens_kappa(values[left], values[right]), 4),
                            "n": len(ordered_ids),
                        }
                    )
                output.append(
                    {
                        "case": case,
                        "model": model,
                        "field": field,
                        "round_pair": "Fleiss-3R",
                        "kappa": round(
                            fleiss_kappa(
                                [[values[number][index] for number in ROUNDS]
                                 for index in range(len(ordered_ids))]
                            ),
                            4,
                        ),
                        "n": len(ordered_ids),
                    }
                )
    return output


def main() -> None:
    rows = compute_rows()
    METRICS_R2_ICR_CROSS_ROUND.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_R2_ICR_CROSS_ROUND.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("case", "model", "field", "round_pair", "kappa", "n"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {METRICS_R2_ICR_CROSS_ROUND}")


if __name__ == "__main__":
    main()
