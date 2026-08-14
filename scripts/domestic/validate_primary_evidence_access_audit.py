#!/usr/bin/env python3
"""Validate non-promoting official-source access audit metadata.

The audit describes whether an official catalogue/viewer is reachable.  It is
deliberately weaker than page provenance: a locked viewer or a catalogue card
must never become a local original, a citation-ready page, or a closed primary
evidence target merely because a URL exists.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = ROOT / "data/domestic/primary_evidence_access_audit.json"
DEFAULT_DB = ROOT / "data/research_index.sqlite"
DEFAULT_COVERAGE = ROOT / "data/domestic/event_coverage.json"


REQUIRED_FIELDS = {
    "candidate_id",
    "event_id",
    "catalog_reference",
    "catalog_url",
    "access_status",
    "official_viewer_verified",
    "viewer_page_count",
    "session_mode",
    "download_available",
    "local_original_present",
    "citation_ready",
    "next_action",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(audit_path: Path, db_path: Path, coverage_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = _load_json(audit_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"audit_read_error: {exc}"]}

    if not isinstance(payload, dict):
        return {"status": "FAIL", "errors": ["audit_root_must_be_object"]}
    if payload.get("schema_version") != "primary_evidence_access_audit.v1":
        errors.append("schema_version_mismatch")
    if payload.get("body_read_by_auditor") is not False:
        errors.append("body_read_by_auditor_must_be_false")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append("records_must_be_nonempty_list")
        records = []

    try:
        coverage = _load_json(coverage_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": errors + [f"coverage_read_error: {exc}"]}
    coverage_by_event = {
        str(item.get("event_id")): item
        for item in coverage
        if isinstance(item, dict) and item.get("event_id")
    }

    candidate_ids: set[str] = set()
    if db_path.is_file():
        with sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True) as conn:
            candidate_ids = {
                str(row[0])
                for row in conn.execute("SELECT candidate_id FROM domestic_candidates")
            }
    else:
        errors.append("database_missing")

    seen: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix}_must_be_object")
            continue
        missing = sorted(REQUIRED_FIELDS - set(record))
        if missing:
            errors.append(f"{prefix}_missing_fields:{','.join(missing)}")
        candidate_id = str(record.get("candidate_id") or "")
        event_id = str(record.get("event_id") or "")
        if not candidate_id or candidate_id in seen:
            errors.append(f"{prefix}_duplicate_or_empty_candidate_id")
        seen.add(candidate_id)
        if candidate_id and candidate_ids and candidate_id not in candidate_ids:
            errors.append(f"{prefix}_candidate_not_in_database:{candidate_id}")
        if event_id not in coverage_by_event:
            errors.append(f"{prefix}_event_not_in_coverage:{event_id}")
        else:
            declared_ids = {
                str(value)
                for value in coverage_by_event[event_id].get("domestic_candidate_ids", [])
            }
            if candidate_id not in declared_ids:
                errors.append(f"{prefix}_candidate_not_declared_for_event:{candidate_id}")
        parsed = urlparse(str(record.get("catalog_url") or ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{prefix}_catalog_url_must_be_absolute_http_url")
        if not isinstance(record.get("official_viewer_verified"), bool):
            errors.append(f"{prefix}_official_viewer_verified_must_be_bool")
        if not isinstance(record.get("viewer_page_count"), int) or record.get("viewer_page_count", 0) < 0:
            errors.append(f"{prefix}_viewer_page_count_must_be_nonnegative_int")
        for field in ("download_available", "local_original_present", "citation_ready"):
            if not isinstance(record.get(field), bool):
                errors.append(f"{prefix}_{field}_must_be_bool")
        if record.get("access_status") == "official_viewer_locked":
            for field in ("download_available", "local_original_present", "citation_ready"):
                if record.get(field) is not False:
                    errors.append(f"{prefix}_locked_viewer_cannot_promote:{field}")

    return {
        "report": "PRIMARY_EVIDENCE_ACCESS_AUDIT",
        "audit_path": str(audit_path),
        "database_path": str(db_path),
        "coverage_path": str(coverage_path),
        "records": len(records),
        "body_read": bool(payload.get("body_read_by_auditor")),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.audit, args.db, args.coverage)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
