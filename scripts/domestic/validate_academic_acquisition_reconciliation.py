#!/usr/bin/env python3
"""Validate body-free conclusions from academic source-identity reconciliation.

The reconciliation file may record that a source body was sampled during an
acquisition audit, but it must not contain the body, a local path, or a formal
database write.  This validator reads the conclusion and the tracked academic
metadata only; it never opens a source file and never changes the database.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECONCILIATION = ROOT / "data" / "domestic" / "academic_acquisition_reconciliation.json"
DEFAULT_METADATA = ROOT / "data" / "domestic" / "academic_layer_metadata.json"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
LOCAL_MARKERS = (
    "/Users/",
    "/private/",
    "/tmp/",
    "file://",
    '"local_path"',
    '"source_file"',
    '"page_image_path"',
    '"derived_text_path"',
)


def load_json(path: Path, label: str) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{label} unreadable: {exc}"]


def validate(
    reconciliation_path: Path = DEFAULT_RECONCILIATION,
    metadata_path: Path = DEFAULT_METADATA,
) -> dict[str, Any]:
    payload, errors = load_json(reconciliation_path, "academic reconciliation")
    metadata, metadata_errors = load_json(metadata_path, "academic metadata")
    errors.extend(metadata_errors)
    if not isinstance(payload, dict):
        errors.append("academic reconciliation must be an object")
        payload = {}
    if payload.get("schema_version") != "domestic_academic_acquisition_reconciliation.v1":
        errors.append("unsupported academic reconciliation schema")
    for field in ("body_text_included", "formal_db_written", "local_paths_included", "auto_delete"):
        if payload.get(field) is not False:
            errors.append(f"academic reconciliation {field} must be false")
    serialized = json.dumps(payload, ensure_ascii=False)
    if any(marker in serialized for marker in LOCAL_MARKERS):
        errors.append("academic reconciliation contains a local/body path marker")

    metadata_records = metadata.get("records") if isinstance(metadata, dict) else []
    metadata_by_id = {
        str(record.get("external_id") or ""): record
        for record in metadata_records
        if isinstance(record, dict) and str(record.get("external_id") or "")
    }
    records = payload.get("records") if isinstance(payload, dict) else []
    if not isinstance(records, list) or not records:
        errors.append("academic reconciliation records must be a non-empty list")
        records = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"academic reconciliation record {index} is not an object")
            continue
        identifier = str(record.get("external_id") or "").strip()
        if not identifier or identifier in seen:
            errors.append(f"academic reconciliation duplicate or empty id: {identifier or '<empty>'}")
            continue
        seen.add(identifier)
        target = metadata_by_id.get(identifier)
        matched_id = str(record.get("matched_record_id") or "").strip()
        matched = metadata_by_id.get(matched_id)
        if target is None:
            errors.append(f"reconciliation target absent from metadata: {identifier}")
        if matched is None:
            errors.append(f"reconciliation matched record absent from metadata: {matched_id or '<empty>'}")
        if record.get("status") != "WRONG_PAGE_ALIAS_HOLD":
            errors.append(f"unsupported reconciliation status: {identifier}")
        if not str(record.get("source_url") or "").startswith(("http://", "https://")):
            errors.append(f"reconciliation source_url must be http(s): {identifier}")
        if not SHA256_RE.fullmatch(str(record.get("observed_source_sha256") or "")):
            errors.append(f"reconciliation SHA256 is invalid: {identifier}")
        if record.get("target_fulltext_present") is not False:
            errors.append(f"reconciliation target_fulltext_present must be false: {identifier}")
        if record.get("formal_import_allowed") is not False:
            errors.append(f"reconciliation formal_import_allowed must be false: {identifier}")
        if target is not None:
            if target.get("fulltext_status") != "METADATA_OR_WRONG_PAGE":
                errors.append(f"metadata status not downgraded to wrong-page hold: {identifier}")
            if target.get("review_status") != "wrong_page_alias_hold":
                errors.append(f"metadata review status not aligned: {identifier}")
            if target.get("matched_record_id") != matched_id:
                errors.append(f"metadata matched_record_id drift: {identifier}")
            if target.get("source_quality_audit") != "WRONG_PAGE_ALIAS_HOLD":
                errors.append(f"metadata source_quality_audit drift: {identifier}")
            if target.get("academic_crosswalk_eligible") is not False:
                errors.append(f"wrong-page target must be excluded from academic crosswalk: {identifier}")
        if matched is not None and str(record.get("observed_page_title") or "") != str(matched.get("title") or ""):
            errors.append(f"observed title does not match matched record: {identifier}")

    return {
        "schema_version": "domestic_academic_acquisition_reconciliation_validation.v1",
        "reconciliation_path": str(reconciliation_path),
        "metadata_path": str(metadata_path),
        "records": len(records),
        "source_body_sampled": bool(payload.get("source_body_sampled")),
        "body_text_included": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "auto_delete": False,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconciliation", type=Path, default=DEFAULT_RECONCILIATION)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.reconciliation, args.metadata)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
