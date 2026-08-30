#!/usr/bin/env python3
"""Validate the domestic academic discovery and full-text priority layers.

This is a metadata-only gate.  It reads the versioned academic index and its
priority queue, but never reads source bodies, performs OCR, writes the formal
SQLite database, or exposes local file paths.  A passing result means that the
queue is structurally safe and consistently classified; it does not make any
record citation-ready.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA = ROOT / "data" / "domestic" / "academic_layer_metadata.json"
DEFAULT_QUEUE = ROOT / "data" / "domestic" / "academic_fulltext_priority_queue.json"

ALLOWED_QUALITY_TIERS = {"S", "A", "B", "C"}
ALLOWED_QUEUE_CLASSES = {
    "P0_STABLE_FULLTEXT",
    "P1_FULLTEXT_CANDIDATE",
    "P2_STABLE_CONTEXT",
    "P3_CANDIDATE_CONTEXT",
}
ALLOWED_FULLTEXT_STATUSES = {"FULLTEXT_PDF", "FULLTEXT_HTML_CANDIDATE"}
PLACEHOLDER_INSTITUTIONS = {
    "",
    "—",
    "-",
    "待核",
    "待从全文页核验",
    "未知",
    "N/A",
    "NA",
}
PENDING_INSTITUTION_MARKERS = ("待核", "待补强", "相关", "文末署名")
LOCAL_MARKERS = (
    "/Users/",
    "/private/",
    "/tmp/",
    "file://",
    "local_path",
    "source_file",
    "page_image_path",
)


def load_json(path: Path, label: str) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{label} unreadable: {exc}"]


def records_from(payload: Any, label: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        errors.append(f"{label} must be an object")
        return []
    records = payload.get("records")
    if not isinstance(records, list):
        errors.append(f"{label}.records must be a list")
        return []
    result: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{label}.records[{index}] must be an object")
            continue
        result.append(record)
    return result


def record_id(record: dict[str, Any]) -> str:
    return str(record.get("external_id") or record.get("record_id") or "").strip()


def flag_is_true(value: Any) -> bool:
    if value is None or value is False or value == 0:
        return False
    if isinstance(value, str) and value.strip().lower() in {"", "0", "false", "no", "none", "null"}:
        return False
    return bool(value)


def institution_status(value: Any) -> str:
    text = str(value or "").strip()
    if text in PLACEHOLDER_INSTITUTIONS:
        return "placeholder"
    if any(marker in text for marker in PENDING_INSTITUTION_MARKERS):
        return "qualification_pending"
    return "present"


def validate_payload_flags(payload: Any, label: str, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        return
    for field in ("body_read", "formal_db_written", "local_paths_included"):
        if payload.get(field) is not False:
            errors.append(f"{label}.{field} must be false")


def check_no_local_markers(records: list[dict[str, Any]], label: str, errors: list[str]) -> None:
    serialized = json.dumps(records, ensure_ascii=False)
    for marker in LOCAL_MARKERS:
        if marker in serialized:
            errors.append(f"{label} contains forbidden local marker: {marker}")


def validate(
    metadata_path: Path = DEFAULT_METADATA,
    queue_path: Path = DEFAULT_QUEUE,
) -> dict[str, Any]:
    errors: list[str] = []
    metadata, metadata_errors = load_json(metadata_path, "academic metadata")
    queue, queue_errors = load_json(queue_path, "academic queue")
    errors.extend(metadata_errors)
    errors.extend(queue_errors)

    if isinstance(metadata, dict) and metadata.get("schema_version") != "domestic_academic_layer_metadata.v1":
        errors.append("unsupported academic metadata schema")
    if isinstance(queue, dict) and queue.get("schema_version") != "domestic_academic_fulltext_priority_queue.v1":
        errors.append("unsupported academic queue schema")
    validate_payload_flags(metadata, "academic metadata", errors)
    validate_payload_flags(queue, "academic queue", errors)

    metadata_records = records_from(metadata, "academic metadata", errors)
    queue_records = records_from(queue, "academic queue", errors)

    metadata_ids: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(metadata_records):
        identifier = record_id(record)
        if not identifier:
            errors.append(f"academic metadata.records[{index}] has no external_id")
        elif identifier in metadata_ids:
            errors.append(f"duplicate academic metadata id: {identifier}")
        else:
            metadata_ids[identifier] = record
        tier = str(record.get("quality_tier") or "")
        if tier not in ALLOWED_QUALITY_TIERS:
            errors.append(f"academic metadata record {identifier} has invalid quality_tier: {tier}")
        if flag_is_true(record.get("citation_ready")):
            errors.append(f"academic metadata record {identifier} is citation_ready")
        if flag_is_true(record.get("human_verified")):
            errors.append(f"academic metadata record {identifier} is human_verified")

    queue_ids: set[str] = set()
    for index, record in enumerate(queue_records):
        identifier = record_id(record)
        if not identifier:
            errors.append(f"academic queue.records[{index}] has no external_id")
        elif identifier in queue_ids:
            errors.append(f"duplicate academic queue id: {identifier}")
        queue_ids.add(identifier)
        if identifier not in metadata_ids:
            errors.append(f"academic queue id absent from metadata index: {identifier}")
        tier = str(record.get("quality_tier") or "")
        if tier not in ALLOWED_QUALITY_TIERS:
            errors.append(f"academic queue record {identifier} has invalid quality_tier: {tier}")
        fulltext_status = str(record.get("fulltext_status") or "")
        if fulltext_status not in ALLOWED_FULLTEXT_STATUSES:
            errors.append(f"academic queue record {identifier} has invalid fulltext_status: {fulltext_status}")
        queue_class = str(record.get("queue_class") or "")
        if queue_class not in ALLOWED_QUEUE_CLASSES:
            errors.append(f"academic queue record {identifier} has invalid queue_class: {queue_class}")
        if queue_class in {"P0_STABLE_FULLTEXT", "P1_FULLTEXT_CANDIDATE"} and tier not in {"S", "A"}:
            errors.append(f"preferred queue record {identifier} must be S/A: {tier}")
        url = str(record.get("source_url") or "")
        if not url.startswith(("https://", "http://")):
            errors.append(f"academic queue record {identifier} source_url must be http(s)")
        if flag_is_true(record.get("citation_ready")):
            errors.append(f"academic queue record {identifier} is citation_ready")
        if flag_is_true(record.get("human_verified")):
            errors.append(f"academic queue record {identifier} is human_verified")
        if record.get("academic_crosswalk_eligible") is False:
            errors.append(f"ineligible academic record entered queue: {identifier}")

    check_no_local_markers(queue_records, "academic queue records", errors)

    metadata_quality = Counter(str(record.get("quality_tier") or "") for record in metadata_records)
    metadata_fulltext = Counter(str(record.get("fulltext_status") or "") for record in metadata_records)
    queue_classes = Counter(str(record.get("queue_class") or "") for record in queue_records)
    queue_quality = Counter(str(record.get("quality_tier") or "") for record in queue_records)
    queue_fulltext = Counter(str(record.get("fulltext_status") or "") for record in queue_records)
    queue_institution = Counter(institution_status(record.get("institution")) for record in queue_records)
    preferred_records = [record for record in queue_records if str(record.get("quality_tier") or "") in {"S", "A"}]
    preferred_admission = Counter(
        "preferred" if institution_status(record.get("institution")) == "present" else "hold_metadata"
        for record in preferred_records
    )
    context_records = [record for record in queue_records if str(record.get("quality_tier") or "") not in {"S", "A"}]

    summary = {
        "metadata_records": len(metadata_records),
        "metadata_quality_tiers": dict(metadata_quality),
        "metadata_fulltext_statuses": dict(metadata_fulltext),
        "queue_records": len(queue_records),
        "queue_classes": dict(queue_classes),
        "queue_quality_tiers": dict(queue_quality),
        "queue_fulltext_statuses": dict(queue_fulltext),
        "queue_institution_status": dict(queue_institution),
        "preferred_queue_records": len(preferred_records),
        "preferred_queue_admission": dict(preferred_admission),
        "context_only_queue_records": len(context_records),
        "metadata_duplicate_groups": (metadata or {}).get("duplicate_group_count", 0)
        if isinstance(metadata, dict)
        else 0,
        "metadata_duplicate_records": (metadata or {}).get("duplicate_record_count", 0)
        if isinstance(metadata, dict)
        else 0,
    }
    return {
        "schema_version": "domestic_academic_layer_validation.v1",
        "metadata_path": str(metadata_path),
        "queue_path": str(queue_path),
        "body_read": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "summary": summary,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.metadata, args.queue)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
