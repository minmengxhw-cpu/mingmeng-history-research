#!/usr/bin/env python3
"""Validate the body-free sibling collection admission queue.

The queue is an intake ledger, not a formal source index.  This validator
checks its schema, safe flags, stable URLs, hashes, unique IDs, and absence of
local filesystem/body fields.  It never opens a source file and never writes
SQLite.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUEUE = ROOT / "data" / "domestic" / "sibling_collection_intake_queue.json"
ALLOWED_DISPOSITIONS = {
    "CONTEXT_ONLY",
    "KNOWN_ROUTE_NOT_CANDIDATE",
    "LEAD_ONLY_SURROGATE_REVIEW",
    "PROMOTE_ACADEMIC_METADATA_REVIEW",
    "PROMOTE_METADATA_REVIEW",
    "UNCLASSIFIED_HOLD",
}
LOCAL_MARKERS = (
    "/Users/",
    "/private/",
    "/tmp/",
    '"local_path"',
    '"source_file"',
    '"page_image_path"',
)


def validate(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "domestic_sibling_collection_intake_validation.v1",
            "queue_path": str(path),
            "status": "FAIL",
            "errors": [f"queue unreadable: {exc}"],
        }

    if not isinstance(payload, dict):
        errors.append("queue must be an object")
        records: list[dict[str, Any]] = []
    else:
        if payload.get("schema_version") != "domestic_sibling_collection_intake_queue.v1":
            errors.append("unsupported queue schema")
        for field in (
            "body_read",
            "ocr_performed",
            "formal_db_written",
            "local_paths_included",
            "files_copied",
            "files_deleted_or_moved",
        ):
            if payload.get(field) is not False:
                errors.append(f"{field} must be false")
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            errors.append("records must be a list")
            records = []
        else:
            records = [record for record in raw_records if isinstance(record, dict)]
            if len(records) != len(raw_records):
                errors.append("records contains a non-object item")

    serialized = json.dumps(payload, ensure_ascii=False)
    for marker in LOCAL_MARKERS:
        if marker in serialized:
            errors.append(f"forbidden local marker: {marker}")

    identifiers: set[str] = set()
    dispositions: Counter[str] = Counter()
    valid_hashes = 0
    for index, record in enumerate(records):
        identifier = str(record.get("external_id") or "").strip()
        if not identifier:
            errors.append(f"record {index} has no external_id")
        elif identifier in identifiers:
            errors.append(f"duplicate external_id: {identifier}")
        else:
            identifiers.add(identifier)
        source_url = str(record.get("source_url") or "").strip()
        if not source_url.startswith(("http://", "https://")):
            errors.append(f"record {identifier or index} source_url is not http(s)")
        disposition = str(record.get("disposition") or "")
        if disposition not in ALLOWED_DISPOSITIONS:
            errors.append(f"record {identifier or index} has invalid disposition: {disposition}")
        dispositions[disposition] += 1
        if record.get("metadata_only") is not True:
            errors.append(f"record {identifier or index} metadata_only must be true")
        if record.get("body_read") is not False or record.get("ocr_performed") is not False:
            errors.append(f"record {identifier or index} body/OCR flags are unsafe")
        digest = str(record.get("file_sha256") or "").strip()
        if digest and re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            valid_hashes += 1
        elif digest:
            errors.append(f"record {identifier or index} has invalid SHA256")

    if isinstance(payload, dict):
        expected_count = payload.get("queue_record_count")
        if expected_count != len(records):
            errors.append(f"queue_record_count mismatch: {expected_count} != {len(records)}")
        expected_dispositions = payload.get("disposition_counts")
        if expected_dispositions != dict(dispositions.most_common()):
            errors.append("disposition_counts mismatch")
        sidecar_count = payload.get("sidecar_record_count")
        excluded = payload.get("excluded_exact_candidate_url_count")
        if isinstance(sidecar_count, int) and isinstance(excluded, int):
            if sidecar_count != excluded + len(records):
                errors.append("sidecar count does not equal excluded plus queue records")

    return {
        "schema_version": "domestic_sibling_collection_intake_validation.v1",
        "queue_path": str(path),
        "body_read": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "queue_records": len(records),
        "unique_external_ids": len(identifiers),
        "valid_sha256_count": valid_hashes,
        "disposition_counts": dict(dispositions.most_common()),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    args = parser.parse_args()
    report = validate(args.queue.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
