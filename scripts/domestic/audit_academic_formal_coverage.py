#!/usr/bin/env python3
"""Audit formal academic-layer coverage against the tracked queue.

The audit reads only SQLite source/document/page identifiers and page counts;
it never selects page text.  A partial queue is expected while acquisition is
open, so ``status=PASS`` means the formal rows are structurally aligned and
``coverage_status`` reports whether the queue is complete.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_QUEUE = ROOT / "data" / "domestic" / "academic_fulltext_priority_queue.json"
DEFAULT_REUSE_MAP = ROOT / "data" / "domestic" / "academic_formal_reuse_map.json"
SOURCE_TYPE = "domestic_academic_fulltext"


def load_queue(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"queue unreadable: {exc}"]
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        return [], ["queue records must be a list"]
    records = [record for record in payload["records"] if isinstance(record, dict)]
    if len(records) != len(payload["records"]):
        return records, ["queue contains a non-object record"]
    return records, []


def queue_id(record: dict[str, Any]) -> str:
    return str(record.get("external_id") or record.get("record_id") or "").strip()


def formal_id(source_id: Any) -> str:
    text = str(source_id or "").strip()
    return text.rsplit(":", 1)[-1] if text else ""


def load_reuse_ids(path: Path) -> tuple[set[str], list[str]]:
    """Load only body-free, queue-compatible reuse identifiers."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return set(), [f"reuse map unreadable: {exc}"]
    if not isinstance(payload, dict):
        return set(), ["reuse map must be an object"]
    if payload.get("schema_version") != "domestic_academic_source_reuse_map.v1":
        return set(), ["unsupported reuse map schema"]
    errors = [
        f"reuse map {field} must be false"
        for field in ("body_read", "formal_db_written", "local_paths_included", "auto_delete")
        if payload.get(field) is not False
    ]
    serialized = json.dumps(payload, ensure_ascii=False)
    for marker in ("/Users/", "/private/", '"local_path"', '"source_file"', '"page_image_path"'):
        if marker in serialized:
            errors.append(f"reuse map contains forbidden local marker: {marker}")
    records = payload.get("records")
    if not isinstance(records, list):
        return set(), errors + ["reuse map records must be a list"]
    identifiers: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"reuse map record {index} is not an object")
            continue
        identifier = str(record.get("external_id") or "").strip()
        if not identifier or identifier in identifiers:
            errors.append(f"reuse map duplicate or empty id: {identifier or '<empty>'}")
            continue
        if record.get("reuse_status") != "REUSE_EXISTING_PAGE_OCR_NO_DUPLICATE_INGEST":
            errors.append(f"unsupported reuse status: {identifier}")
            continue
        identifiers.add(identifier)
    return identifiers, errors


def audit(
    db_path: Path = DEFAULT_DB,
    queue_path: Path = DEFAULT_QUEUE,
    reuse_map_path: Path = DEFAULT_REUSE_MAP,
) -> dict[str, Any]:
    errors: list[str] = []
    queue_records, queue_errors = load_queue(queue_path)
    errors.extend(queue_errors)
    queue_by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(queue_records):
        identifier = queue_id(record)
        if not identifier:
            errors.append(f"queue record {index} has no external_id")
        elif identifier in queue_by_id:
            errors.append(f"duplicate queue id: {identifier}")
        else:
            queue_by_id[identifier] = record

    source_rows: list[dict[str, Any]] = []
    try:
        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT s.source_id,
                       s.title,
                       s.origin_url,
                       COUNT(DISTINCT d.id) AS document_count,
                       COUNT(p.id) AS page_count
                FROM sources AS s
                LEFT JOIN documents AS d ON d.source_id = s.id
                LEFT JOIN pages AS p ON p.document_id = d.id
                WHERE s.source_type = ?
                GROUP BY s.id
                ORDER BY s.id
                """,
                (SOURCE_TYPE,),
            ).fetchall()
    except (OSError, sqlite3.Error) as exc:
        errors.append(f"formal database unreadable: {exc}")
        rows = []

    formal_by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        identifier = formal_id(row[0])
        if not identifier:
            errors.append(f"formal source row {index} has no source_id")
            continue
        if identifier in formal_by_id:
            errors.append(f"duplicate formal academic source id: {identifier}")
            continue
        record = {
            "external_id": identifier,
            "title": str(row[1] or ""),
            "origin_url": str(row[2] or ""),
            "document_count": int(row[3] or 0),
            "page_count": int(row[4] or 0),
        }
        formal_by_id[identifier] = record
        if not record["title"]:
            errors.append(f"formal academic source has empty title: {identifier}")
        if not record["origin_url"].startswith(("http://", "https://")):
            errors.append(f"formal academic source URL is not http(s): {identifier}")
        if record["document_count"] <= 0 or record["page_count"] <= 0:
            errors.append(f"formal academic source has no document/page rows: {identifier}")

    queue_ids = set(queue_by_id)
    formal_ids = set(formal_by_id)
    missing_formal = sorted(queue_ids - formal_ids)
    formal_not_queue = sorted(formal_ids - queue_ids)
    if formal_not_queue:
        errors.append(f"formal academic sources absent from tracked queue: {formal_not_queue}")

    class_coverage: dict[str, dict[str, int]] = {}
    for queue_class in sorted({str(record.get("queue_class") or "") for record in queue_records}):
        class_ids = {
            identifier
            for identifier, record in queue_by_id.items()
            if str(record.get("queue_class") or "") == queue_class
        }
        class_coverage[queue_class] = {
            "queue_records": len(class_ids),
            "formal_records": len(class_ids & formal_ids),
            "missing_formal": len(class_ids - formal_ids),
        }

    formal_quality = Counter(
        str(queue_by_id[identifier].get("quality_tier") or "")
        for identifier in formal_ids & queue_ids
    )
    reuse_ids, reuse_errors = load_reuse_ids(reuse_map_path)
    errors.extend(reuse_errors)
    preferred_ids = {
        identifier
        for identifier, record in queue_by_id.items()
        if str(record.get("quality_tier") or "") in {"S", "A"}
    }
    context_only_ids = queue_ids - preferred_ids
    reused_queue_ids = sorted((queue_ids - formal_ids) & reuse_ids)
    reused_preferred_queue_ids = sorted(set(reused_queue_ids) & preferred_ids)
    preferred_formal_coverage = len(formal_ids & preferred_ids)
    effective_missing = sorted(preferred_ids - formal_ids - reuse_ids)
    effective_coverage = preferred_formal_coverage + len(reused_preferred_queue_ids)
    context_formal_coverage = len(formal_ids & context_only_ids)
    return {
        "schema_version": "domestic_academic_formal_coverage_audit.v1",
        "scope": "formal academic source/document/page identifiers and counts only",
        "source_type": SOURCE_TYPE,
        "page_bodies_read": False,
        "formal_db_written": False,
        "auto_delete": False,
        "queue_records": len(queue_ids),
        "formal_source_rows": len(formal_ids),
        "formal_queue_coverage": len(formal_ids & queue_ids),
        "reuse_map_records": len(reuse_ids),
        "reused_queue_ids": reused_queue_ids,
        "preferred_queue_records": len(preferred_ids),
        "context_only_queue_records": len(context_only_ids),
        "preferred_formal_queue_coverage": preferred_formal_coverage,
        "reused_preferred_queue_ids": reused_preferred_queue_ids,
        "effective_queue_coverage": effective_coverage,
        "effective_queue_scope": "S/A preferred full-text queue; B context records remain discovery-only",
        "effective_missing_ids": effective_missing,
        "context_formal_queue_coverage": context_formal_coverage,
        "context_only_unmapped_ids": sorted(context_only_ids - formal_ids - reuse_ids),
        "coverage_status": "COMPLETE" if not missing_formal else "PARTIAL_OPEN_GAPS",
        "effective_coverage_status": "COMPLETE" if not effective_missing else "PARTIAL_OPEN_GAPS",
        "missing_formal_ids": missing_formal,
        "formal_not_in_queue_ids": formal_not_queue,
        "queue_class_coverage": class_coverage,
        "formal_quality_tiers": dict(formal_quality),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--reuse-map", type=Path, default=DEFAULT_REUSE_MAP)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = audit(args.db, args.queue, args.reuse_map)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
