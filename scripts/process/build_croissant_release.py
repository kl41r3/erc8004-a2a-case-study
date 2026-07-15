"""Build the versioned Croissant 1.1 release from canonical RQ1 artifacts.

The release preserves pipeline stages instead of presenting incompatible counts as
one corpus:

* R1 annotation archive: the complete MiniMax annotation artifact.
* R2 cross-model consensus: the three-model intersection and majority vote.
* R2 cross-round consensus: the three-model test-retest consensus.

Usage:
    uv run python scripts/process/build_croissant_release.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.models import is_bot
from lib.paths import (
    CONSENSUS_A2A,
    CONSENSUS_ERC,
    CROSS_ROUND_A2A,
    CROSS_ROUND_ERC,
    DATA_ANNOTATED_R1_RECORDS,
    DATA_CROISSANT_V1,
    ROOT,
)


RELEASE_VERSION = "1.0.0"
RELEASE_DATE = "2026-07-15"
RELEASE_DIR = DATA_CROISSANT_V1
DATASET_URL = "https://huggingface.co/datasets/kl41r3/erc8004-vs-a2a-governance"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc/4.0/"

LEGACY_MODEL_IDS = {
    "deepseek": "deepseek-v4-flash",
    "glm": "glm-4-plus",
    "kimi": "moonshot-v1-auto",
}

COMMON_FIELDS = [
    ("record_id", pa.string(), "Stable SHA-256 identifier for this pipeline-layer annotation event."),
    ("source_record_id", pa.string(), "Stable SHA-256 identifier shared by the same public source record across layers."),
    ("source_record_key", pa.string(), "Human-readable canonical key used to generate source_record_id."),
    ("release_layer", pa.string(), "Pipeline layer represented by this row."),
    ("case", pa.string(), "Governance case recorded by the source artifact."),
    ("source", pa.string(), "Source record type."),
    ("platform", pa.string(), "Source platform."),
    ("record_type", pa.string(), "More specific record subtype when available."),
    ("erc", pa.string(), "ERC number for ERC-cluster records when available."),
    ("tier", pa.string(), "R2 ERC sampling tier when available."),
    ("native_id", pa.string(), "Native platform identifier selected for this record."),
    ("date", pa.string(), "ISO 8601 timestamp supplied by the source."),
    ("author", pa.string(), "Public author handle."),
    ("author_display", pa.string(), "Public display name when available."),
    ("title", pa.string(), "Issue, pull request, discussion, or topic title when available."),
    ("raw_text", pa.string(), "Record text used by the annotation pipeline."),
    ("own_text", pa.string(), "Quote-stripped forum text when available."),
    ("url", pa.string(), "Public source URL when available."),
    ("state", pa.string(), "Repository object state when available."),
    ("merged", pa.bool_(), "Whether the pull request was merged when available."),
    ("text_length", pa.int64(), "Length of stripped raw_text in Unicode code points."),
    ("is_known_bot", pa.bool_(), "Whether the current shared bot registry classifies the author as a bot."),
    ("meets_min_text_20", pa.bool_(), "Whether stripped raw_text contains at least 20 characters."),
    ("annotation_error", pa.string(), "Annotation error recorded by the source artifact."),
]

R1_ANNOTATION_FIELDS = [
    ("stakeholder_institution", pa.string(), "MiniMax institutional-affiliation label."),
    ("argument_type", pa.string(), "MiniMax argument-type label."),
    ("stance", pa.string(), "MiniMax stance label."),
    ("consensus_signal", pa.string(), "MiniMax decision-signal label."),
    ("key_point", pa.string(), "MiniMax short summary."),
]

CROSS_MODEL_ANNOTATION_FIELDS = [
    ("stakeholder_institution", pa.string(), "Cross-model consensus institutional-affiliation label."),
    ("argument_type", pa.string(), "Cross-model consensus argument-type label."),
    ("stance", pa.string(), "Cross-model consensus stance label."),
    ("consensus_signal", pa.string(), "Cross-model consensus decision-signal label."),
    ("stakeholder_institution_confidence", pa.float64(), "Share of model votes supporting the selected label."),
    ("argument_type_confidence", pa.float64(), "Share of model votes supporting the selected label."),
    ("stance_confidence", pa.float64(), "Share of model votes supporting the selected label."),
    ("consensus_signal_confidence", pa.float64(), "Share of model votes supporting the selected label."),
]

CROSS_ROUND_ANNOTATION_FIELDS = [
    ("argument_type", pa.string(), "Cross-round consensus argument-type label."),
    ("stance", pa.string(), "Cross-round consensus stance label."),
    ("consensus_signal", pa.string(), "Cross-round consensus decision-signal label."),
    ("overall_consensus_confidence", pa.float64(), "Mean agreement confidence across the three fields."),
]

VOTE_FIELDS = [
    ("record_id", pa.string(), "Stable identifier of the consensus annotation event."),
    ("source_record_id", pa.string(), "Stable identifier of the underlying public source record."),
    ("release_layer", pa.string(), "Consensus layer that produced the vote."),
    ("annotation_field", pa.string(), "Annotation field being voted on."),
    ("model", pa.string(), "Canonical annotator model identifier."),
    ("vote", pa.string(), "Label supplied by the model."),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def native_id(record: dict[str, Any]) -> str:
    for key in (
        "post_id",
        "comment_id",
        "_record_id",
        "discussion_number",
        "issue_number",
        "pr_number",
        "sha",
        "topic_id",
    ):
        value = record.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    text_digest = hashlib.sha256((record.get("raw_text") or "").encode("utf-8")).hexdigest()
    return f"text_sha256:{text_digest}"


def source_record_key(record: dict[str, Any]) -> str:
    case = str(record.get("_case") or "unknown")
    source = str(record.get("source") or "unknown")
    url = str(record.get("url") or record.get("pr_url") or record.get("issue_url") or "").strip()
    identity = f"url:{url}" if url else native_id(record)
    date = str(record.get("date") or "")
    return "|".join((case, source, identity, date))


def stable_source_record_id(record: dict[str, Any]) -> str:
    key = source_record_key(record)
    return "rq1_" + hashlib.sha256(key.encode("utf-8")).hexdigest()


def stable_record_id(record: dict[str, Any], release_layer: str) -> str:
    source_id = stable_source_record_id(record)
    variant = str(record.get("_record_id") or record.get("_note") or "primary")
    key = "|".join((release_layer, source_id, variant))
    return "rq1_event_" + hashlib.sha256(key.encode("utf-8")).hexdigest()


def optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def base_row(record: dict[str, Any], release_layer: str) -> dict[str, Any]:
    text = str(record.get("raw_text") or "")
    title = (
        record.get("topic_title")
        or record.get("discussion_title")
        or record.get("pr_title")
        or record.get("title")
    )
    url = record.get("url") or record.get("pr_url") or record.get("issue_url")
    return {
        "record_id": stable_record_id(record, release_layer),
        "source_record_id": stable_source_record_id(record),
        "source_record_key": source_record_key(record),
        "release_layer": release_layer,
        "case": optional_text(record.get("_case")),
        "source": optional_text(record.get("source")),
        "platform": optional_text(record.get("platform")),
        "record_type": optional_text(record.get("record_type")),
        "erc": optional_text(record.get("erc")),
        "tier": optional_text(record.get("tier")),
        "native_id": native_id(record),
        "date": optional_text(record.get("date")),
        "author": optional_text(record.get("author")),
        "author_display": optional_text(record.get("author_display")),
        "title": optional_text(title),
        "raw_text": text,
        "own_text": optional_text(record.get("own_text")),
        "url": optional_text(url),
        "state": optional_text(record.get("state")),
        "merged": record.get("merged") if isinstance(record.get("merged"), bool) else None,
        "text_length": len(text.strip()),
        "is_known_bot": is_bot(str(record.get("author") or "")),
        "meets_min_text_20": len(text.strip()) >= 20,
        "annotation_error": optional_text(record.get("annotation_error")),
    }


def build_r1_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        row = base_row(record, "r1_annotation_archive")
        annotation = record.get("annotation") or {}
        for field, _, _ in R1_ANNOTATION_FIELDS:
            row[field] = optional_text(annotation.get(field))
        rows.append(row)
    return rows


def build_cross_model_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        row = base_row(record, "r2_cross_model_consensus")
        annotation = record.get("annotation") or {}
        confidence = record.get("consensus_confidence") or {}
        for field in ("stakeholder_institution", "argument_type", "stance", "consensus_signal"):
            row[field] = optional_text(annotation.get(field))
            row[f"{field}_confidence"] = (
                float(confidence[field]) if confidence.get(field) is not None else None
            )
        rows.append(row)
    return rows


def build_cross_round_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        row = base_row(record, "r2_cross_round_consensus")
        annotation = record.get("annotation") or {}
        for field in ("argument_type", "stance", "consensus_signal"):
            row[field] = optional_text(annotation.get(field))
        confidence = record.get("consensus_confidence")
        row["overall_consensus_confidence"] = float(confidence) if confidence is not None else None
        rows.append(row)
    return rows


def build_vote_rows(records: list[dict[str, Any]], release_layer: str) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        record_id = stable_record_id(record, release_layer)
        source_id = stable_source_record_id(record)
        for annotation_field, votes in (record.get("consensus_votes") or {}).items():
            for model, vote in votes.items():
                rows.append(
                    {
                        "record_id": record_id,
                        "source_record_id": source_id,
                        "release_layer": release_layer,
                        "annotation_field": str(annotation_field),
                        "model": LEGACY_MODEL_IDS.get(str(model), str(model)),
                        "vote": optional_text(vote),
                    }
                )
    return rows


def arrow_schema(fields: list[tuple[str, pa.DataType, str]]) -> pa.Schema:
    return pa.schema([pa.field(name, dtype, metadata={b"description": description.encode("utf-8")})
                      for name, dtype, description in fields])


def write_parquet(
    path: Path,
    rows: list[dict[str, Any]],
    fields: list[tuple[str, pa.DataType, str]],
) -> None:
    schema = arrow_schema(fields)
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, path, compression="zstd", version="2.6")
    check = pq.read_table(path)
    if check.num_rows != len(rows):
        raise AssertionError(f"Parquet row count mismatch for {path}: {check.num_rows} != {len(rows)}")


def assert_unique(rows: list[dict[str, Any]], layer: str) -> None:
    ids = [row["record_id"] for row in rows]
    if len(ids) != len(set(ids)):
        duplicates = len(ids) - len(set(ids))
        raise AssertionError(f"{layer} has {duplicates} duplicate canonical record IDs")


def croissant_context() -> dict[str, Any]:
    return {
        "@language": "en",
        "@vocab": "https://schema.org/",
        "sc": "https://schema.org/",
        "cr": "http://mlcommons.org/croissant/",
        "rai": "http://mlcommons.org/croissant/RAI/",
        "dct": "http://purl.org/dc/terms/",
        "prov": "http://www.w3.org/ns/prov#",
        "citeAs": "cr:citeAs",
        "column": "cr:column",
        "conformsTo": "dct:conformsTo",
        "containedIn": "cr:containedIn",
        "data": {"@id": "cr:data", "@type": "@json"},
        "dataBiases": "cr:dataBiases",
        "dataCollection": "cr:dataCollection",
        "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
        "equivalentProperty": "cr:equivalentProperty",
        "examples": "cr:examples",
        "extract": "cr:extract",
        "field": "cr:field",
        "fileObject": "cr:fileObject",
        "fileProperty": "cr:fileProperty",
        "fileSet": "cr:fileSet",
        "format": "cr:format",
        "includes": "cr:includes",
        "isArray": "cr:isArray",
        "isLiveDataset": "cr:isLiveDataset",
        "jsonPath": "cr:jsonPath",
        "key": "cr:key",
        "md5": "cr:md5",
        "parentField": "cr:parentField",
        "path": "cr:path",
        "personalSensitiveInformation": "cr:personalSensitiveInformation",
        "recordSet": "cr:recordSet",
        "references": "cr:references",
        "regex": "cr:regex",
        "repeated": "cr:repeated",
        "replace": "cr:replace",
        "samplingRate": "cr:samplingRate",
        "separator": "cr:separator",
        "source": "cr:source",
        "subField": "cr:subField",
        "transform": "cr:transform",
    }


def croissant_type(dtype: pa.DataType) -> str:
    if pa.types.is_boolean(dtype):
        return "sc:Boolean"
    if pa.types.is_integer(dtype):
        return "sc:Integer"
    if pa.types.is_floating(dtype):
        return "sc:Float"
    return "sc:Text"


def record_set(
    record_set_id: str,
    name: str,
    description: str,
    file_id: str,
    fields: list[tuple[str, pa.DataType, str]],
    reference: tuple[str, str] | None = None,
) -> dict[str, Any]:
    output_fields = []
    for field_name, dtype, field_description in fields:
        field = {
            "@type": "cr:Field",
            "@id": f"{record_set_id}/{field_name}",
            "name": field_name,
            "description": field_description,
            "dataType": croissant_type(dtype),
            "source": {
                "fileObject": {"@id": file_id},
                "extract": {"column": field_name},
            },
        }
        if reference and field_name == reference[0]:
            field["references"] = {"field": {"@id": reference[1]}}
        output_fields.append(field)
    return {
        "@type": "cr:RecordSet",
        "@id": record_set_id,
        "name": name,
        "description": description,
        "key": ["record_id"],
        "field": output_fields,
    }


def file_object(path: Path, description: str) -> dict[str, Any]:
    return {
        "@type": "cr:FileObject",
        "@id": path.name,
        "name": path.name,
        "description": description,
        "contentUrl": path.name,
        "contentSize": f"{path.stat().st_size} B",
        "encodingFormat": "application/x-parquet",
        "sha256": file_sha256(path),
    }


def write_schema_doc(counts: dict[str, int]) -> None:
    text = f"""# Croissant Release v{RELEASE_VERSION}

This directory is the machine-readable distribution of the RQ1 dataset. It keeps each
pipeline stage as a separate record set so that archive size, model intersection size,
and paper-reported scope are not treated as interchangeable quantities.

## Record sets

1. `r1_annotations.parquet`: {counts['r1']} MiniMax annotation archive rows. This is the
   complete stored R1 artifact, not a claim that all rows entered every paper analysis.
2. `r2_cross_model_consensus.parquet`: {counts['r2_cross_model']} rows in the three-model
   cross-model intersection, with four categorical consensus fields.
3. `r2_cross_model_votes.parquet`: {counts['r2_cross_model_votes']} normalized model votes.
4. `r2_cross_round_consensus.parquet`: {counts['r2_cross_round']} rows in the current
   cross-round consensus artifacts, with three categorical fields.
5. `r2_cross_round_votes.parquet`: {counts['r2_cross_round_votes']} normalized model votes.

## R1 alignment decision

The manuscript reports a retained R1 corpus of ERC 142 and A2A 4,181 records. The stored
annotation artifact contains ERC 149 and A2A 5,272 records. Historical analysis artifacts
also show later filtered counts such as A2A 4,230. No row-level manifest preserving the
exact 142 and 4,181 selection exists in the repository. This release therefore publishes
the traceable 5,421-row annotation archive and exposes `is_known_bot`, `text_length`, and
`meets_min_text_20` instead of inventing a paper-membership flag.

## R2 alignment decision

R2 contains two methods rather than one mutable corpus. Cross-model consensus represents
independent model triangulation. Cross-round consensus represents test-retest stability and
uses a different field set and, for A2A, a later canonical input. Their counts are expected
to differ and are encoded as separate record sets.

## Stable identifiers

`source_record_id` is SHA-256 over case, source, the best available public URL or native
identifier, and source timestamp. The same source receives the same ID across R1 and R2.
`record_id` additionally includes pipeline layer and annotation variant. This preserves the
30 GitVote comments that appear twice in the R1 archive with different annotation results.

## Personal information

The data contain public author handles, display names, discussion text, and inferred or
profile-derived institutional affiliations. They should be used for research and auditing,
not for consequential decisions about individuals.
"""
    (RELEASE_DIR / "SCHEMA.md").write_text(text, encoding="utf-8")


def main() -> None:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    source_paths = [
        DATA_ANNOTATED_R1_RECORDS,
        CONSENSUS_ERC,
        CONSENSUS_A2A,
        CROSS_ROUND_ERC,
        CROSS_ROUND_A2A,
    ]
    for path in source_paths:
        if not path.exists():
            raise FileNotFoundError(path)

    r1_source = load_json(DATA_ANNOTATED_R1_RECORDS)
    cross_model_source = load_json(CONSENSUS_ERC) + load_json(CONSENSUS_A2A)
    cross_round_source = load_json(CROSS_ROUND_ERC) + load_json(CROSS_ROUND_A2A)

    r1_rows = build_r1_rows(r1_source)
    cross_model_rows = build_cross_model_rows(cross_model_source)
    cross_model_votes = build_vote_rows(cross_model_source, "r2_cross_model_consensus")
    cross_round_rows = build_cross_round_rows(cross_round_source)
    cross_round_votes = build_vote_rows(cross_round_source, "r2_cross_round_consensus")

    assert_unique(r1_rows, "R1 annotation archive")
    assert_unique(cross_model_rows, "R2 cross-model consensus")
    assert_unique(cross_round_rows, "R2 cross-round consensus")

    outputs = {
        "r1": RELEASE_DIR / "r1_annotations.parquet",
        "r2_cross_model": RELEASE_DIR / "r2_cross_model_consensus.parquet",
        "r2_cross_model_votes": RELEASE_DIR / "r2_cross_model_votes.parquet",
        "r2_cross_round": RELEASE_DIR / "r2_cross_round_consensus.parquet",
        "r2_cross_round_votes": RELEASE_DIR / "r2_cross_round_votes.parquet",
    }

    write_parquet(outputs["r1"], r1_rows, COMMON_FIELDS + R1_ANNOTATION_FIELDS)
    write_parquet(
        outputs["r2_cross_model"],
        cross_model_rows,
        COMMON_FIELDS + CROSS_MODEL_ANNOTATION_FIELDS,
    )
    write_parquet(outputs["r2_cross_model_votes"], cross_model_votes, VOTE_FIELDS)
    write_parquet(
        outputs["r2_cross_round"],
        cross_round_rows,
        COMMON_FIELDS + CROSS_ROUND_ANNOTATION_FIELDS,
    )
    write_parquet(outputs["r2_cross_round_votes"], cross_round_votes, VOTE_FIELDS)

    counts = {
        "r1": len(r1_rows),
        "r2_cross_model": len(cross_model_rows),
        "r2_cross_model_votes": len(cross_model_votes),
        "r2_cross_round": len(cross_round_rows),
        "r2_cross_round_votes": len(cross_round_votes),
    }
    write_schema_doc(counts)

    distributions = [
        file_object(outputs["r1"], "Complete R1 MiniMax annotation archive."),
        file_object(outputs["r2_cross_model"], "R2 three-model cross-model consensus records."),
        file_object(outputs["r2_cross_model_votes"], "Normalized votes underlying cross-model consensus."),
        file_object(outputs["r2_cross_round"], "R2 cross-round test-retest consensus records."),
        file_object(outputs["r2_cross_round_votes"], "Normalized votes underlying cross-round consensus."),
    ]

    metadata = {
        "@context": croissant_context(),
        "@type": "sc:Dataset",
        "@id": DATASET_URL,
        "conformsTo": "http://mlcommons.org/croissant/1.1",
        "name": "ERC-8004 vs Google A2A Governance Dataset, Croissant Release",
        "description": (
            "Versioned machine-readable release of the RQ1 governance dataset. It separates "
            "the R1 annotation archive, R2 cross-model consensus, and R2 cross-round consensus."
        ),
        "license": LICENSE_URL,
        "url": DATASET_URL,
        "creator": {"@type": "sc:Person", "name": "kl41r3", "url": "https://huggingface.co/kl41r3"},
        "datePublished": RELEASE_DATE,
        "dateModified": RELEASE_DATE,
        "version": RELEASE_VERSION,
        "sdVersion": RELEASE_VERSION,
        "citeAs": (
            "kl41r3 (2026). ERC-8004 vs Google A2A Governance Dataset, "
            "Croissant release 1.0.0."
        ),
        "keywords": [
            "technology governance",
            "DAO governance",
            "corporate governance",
            "ERC-8004",
            "Agent-to-Agent protocol",
            "LLM annotation",
        ],
        "inLanguage": "en",
        "dataCollection": (
            "Public Ethereum Magicians and GitHub governance records, followed by LLM annotation "
            "and model-consensus construction."
        ),
        "dataBiases": (
            "Public-platform traces omit private corporate coordination and may overrepresent "
            "highly active contributors. Institutional labels have lower inter-model agreement."
        ),
        "personalSensitiveInformation": (
            "Contains public handles, display names, authored text, and institutional-affiliation labels."
        ),
        "distribution": distributions,
        "recordSet": [
            record_set(
                "r1_annotations",
                "R1 annotation archive",
                "Complete stored MiniMax annotation artifact. Paper-specific membership is not inferred.",
                outputs["r1"].name,
                COMMON_FIELDS + R1_ANNOTATION_FIELDS,
            ),
            record_set(
                "r2_cross_model_consensus",
                "R2 cross-model consensus",
                "Three-model intersection and per-field majority-vote consensus.",
                outputs["r2_cross_model"].name,
                COMMON_FIELDS + CROSS_MODEL_ANNOTATION_FIELDS,
            ),
            record_set(
                "r2_cross_model_votes",
                "R2 cross-model votes",
                "Normalized model votes underlying cross-model consensus.",
                outputs["r2_cross_model_votes"].name,
                VOTE_FIELDS,
                reference=("record_id", "r2_cross_model_consensus/record_id"),
            ),
            record_set(
                "r2_cross_round_consensus",
                "R2 cross-round consensus",
                "Current test-retest cross-round consensus artifacts.",
                outputs["r2_cross_round"].name,
                COMMON_FIELDS + CROSS_ROUND_ANNOTATION_FIELDS,
            ),
            record_set(
                "r2_cross_round_votes",
                "R2 cross-round votes",
                "Normalized model votes underlying cross-round consensus.",
                outputs["r2_cross_round_votes"].name,
                VOTE_FIELDS,
                reference=("record_id", "r2_cross_round_consensus/record_id"),
            ),
        ],
    }
    metadata_path = RELEASE_DIR / "croissant.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "release_version": RELEASE_VERSION,
        "croissant_specification": "1.1",
        "release_date": RELEASE_DATE,
        "counts": counts,
        "source_artifacts": {
            str(path.relative_to(ROOT)): {
                "records": len(load_json(path)),
                "sha256": file_sha256(path),
            }
            for path in source_paths
        },
        "alignment": {
            "r1_paper_reported": {"erc": 142, "a2a": 4181, "total": 4323},
            "r1_annotation_archive": {"erc": 149, "a2a": 5272, "total": 5421},
            "r1_policy": (
                "Publish the traceable annotation archive; do not invent row-level paper membership "
                "because no exact retained-record manifest exists."
            ),
            "r2_policy": (
                "Publish cross-model and cross-round results as separate record sets because they use "
                "different intersections and annotation schemas."
            ),
        },
    }
    manifest_path = RELEASE_DIR / "release_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    checksum_targets = sorted(
        path for path in RELEASE_DIR.iterdir() if path.is_file() and path.name != "CHECKSUMS.json"
    )
    checksums = {
        path.name: {"sha256": file_sha256(path), "bytes": path.stat().st_size}
        for path in checksum_targets
    }
    (RELEASE_DIR / "CHECKSUMS.json").write_text(
        json.dumps(checksums, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Croissant release v{RELEASE_VERSION}: {RELEASE_DIR}")
    for key, value in counts.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
