#!/usr/bin/env python3
"""Audit academic records that can reuse an existing page-level OCR document.

The audit is deliberately metadata-only.  It reads the tracked academic queue,
the body-free reuse map, and SQLite source/document/page/provenance identifiers
and aggregates; it never selects page text, performs OCR, writes SQLite, or
deletes/renames a local file.

The distinction between ``formal_academic_source_rows`` and a reuse mapping is
important: an existing ``domestic_page_ocr`` document can be reused for search
and page navigation without copying 622 pages into a second academic source.
That reuse does not make the compilation an original 1941-1949 archival object
or make every page citation-ready.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_QUEUE = ROOT / "data" / "domestic" / "academic_fulltext_priority_queue.json"
DEFAULT_MAP = ROOT / "data" / "domestic" / "academic_formal_reuse_map.json"
FORMAL_SOURCE_TYPE = "domestic_academic_fulltext"
PRINTED_PAGE_LABEL_RE = re.compile(r"^pdf-\d+\s*/\s*printed-\d+")
EXPLICIT_PAIRS = (
    (145, "115"),
    (147, "117"),
    (148, "118"),
    (149, "119"),
    (150, "120"),
    (151, "121"),
    (152, "122"),
    (153, "123"),
    (157, "127"),
    (158, "128"),
    (159, "129"),
    (160, "130"),
    (161, "131"),
    (162, "132"),
    (163, "133"),
    (164, "134"),
    (165, "135"),
)


def load_object(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{label} unreadable: {exc}"]
    if not isinstance(payload, dict):
        return {}, [f"{label} must be an object"]
    return payload, []


def record_id(record: dict[str, Any]) -> str:
    return str(record.get("external_id") or record.get("record_id") or "").strip()


def flag_is_false(payload: dict[str, Any], field: str, errors: list[str], label: str) -> None:
    if payload.get(field) is not False:
        errors.append(f"{label}.{field} must be false")


def safe_count(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def audit(
    db_path: Path = DEFAULT_DB,
    queue_path: Path = DEFAULT_QUEUE,
    map_path: Path = DEFAULT_MAP,
) -> dict[str, Any]:
    errors: list[str] = []
    queue_payload, queue_errors = load_object(queue_path, "academic queue")
    map_payload, map_errors = load_object(map_path, "academic reuse map")
    errors.extend(queue_errors)
    errors.extend(map_errors)

    for field in ("body_read", "formal_db_written", "local_paths_included", "auto_delete"):
        flag_is_false(map_payload, field, errors, "academic reuse map")
    if map_payload.get("schema_version") != "domestic_academic_source_reuse_map.v1":
        errors.append("unsupported academic reuse map schema")
    serialized_map = json.dumps(map_payload, ensure_ascii=False)
    for marker in ("/Users/", "/private/", '"local_path"', '"source_file"', '"page_image_path"'):
        if marker in serialized_map:
            errors.append(f"academic reuse map contains forbidden local marker: {marker}")

    queue_records = queue_payload.get("records") if isinstance(queue_payload, dict) else []
    map_records = map_payload.get("records") if isinstance(map_payload, dict) else []
    if not isinstance(queue_records, list):
        errors.append("academic queue records must be a list")
        queue_records = []
    if not isinstance(map_records, list):
        errors.append("academic reuse map records must be a list")
        map_records = []

    queue_by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(queue_records):
        if not isinstance(record, dict):
            errors.append(f"academic queue record {index} is not an object")
            continue
        identifier = record_id(record)
        if not identifier:
            errors.append(f"academic queue record {index} has no external_id")
        elif identifier in queue_by_id:
            errors.append(f"duplicate academic queue id: {identifier}")
        else:
            queue_by_id[identifier] = record

    seen_map_ids: set[str] = set()
    valid_map_records: list[dict[str, Any]] = []
    for index, record in enumerate(map_records):
        if not isinstance(record, dict):
            errors.append(f"academic reuse map record {index} is not an object")
            continue
        identifier = record_id(record)
        if not identifier or identifier in seen_map_ids:
            errors.append(f"duplicate or empty academic reuse id: {identifier or '<empty>'}")
            continue
        seen_map_ids.add(identifier)
        valid_map_records.append(record)
        queue_record = queue_by_id.get(identifier)
        if queue_record is None:
            errors.append(f"reuse map id absent from academic queue: {identifier}")
            continue
        for field in ("title", "quality_tier", "source_url"):
            if str(record.get(field) or "") != str(queue_record.get(field) or ""):
                errors.append(f"reuse map field drift: {identifier}.{field}")
        if record.get("reuse_status") != "REUSE_EXISTING_PAGE_OCR_NO_DUPLICATE_INGEST":
            errors.append(f"unsupported reuse status: {identifier}")
        if record.get("existing_source_type") != "domestic_page_ocr":
            errors.append(f"reuse candidate must point to domestic_page_ocr: {identifier}")
        if len(str(record.get("source_sha256") or "")) != 64:
            errors.append(f"reuse candidate has invalid SHA256: {identifier}")
        for key in ("expected_page_count", "expected_pdf_page_min", "expected_pdf_page_max"):
            try:
                if int(record.get(key)) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"reuse candidate has invalid {key}: {identifier}")
        mapping_status = record.get("printed_page_mapping_status")
        if mapping_status not in {"NOT_REGISTERED", "PARTIAL_EXPLICIT_REGISTRATION"}:
            errors.append(f"unsupported printed page mapping status: {identifier}")
        explicit = record.get("explicit_printed_page_registration")
        if mapping_status == "PARTIAL_EXPLICIT_REGISTRATION":
            if not isinstance(explicit, dict):
                errors.append(f"partial printed-page mapping needs a manifest object: {identifier}")
            else:
                if explicit.get("status") != "PARTIAL_EXPLICIT_REGISTRATION":
                    errors.append(f"partial printed-page registration status mismatch: {identifier}")
                if explicit.get("manifest") != "data/domestic/mmhist_1946_pcc_page_identity_review_20260822.json":
                    errors.append(f"partial printed-page manifest mismatch: {identifier}")
                if safe_count(explicit.get("registered_page_count")) != len(EXPLICIT_PAIRS):
                    errors.append(f"partial printed-page count mismatch: {identifier}")
                if explicit.get("registered_pdf_pages") != [pdf_page for pdf_page, _ in EXPLICIT_PAIRS]:
                    errors.append(f"partial registered PDF page list mismatch: {identifier}")
                if explicit.get("registered_printed_pages") != [printed_page for _, printed_page in EXPLICIT_PAIRS]:
                    errors.append(f"partial registered printed-page list mismatch: {identifier}")
        elif explicit is not None:
            errors.append(f"unregistered reuse candidate must not carry an explicit registration object: {identifier}")

    db_checked = False
    db_status = "NOT_AVAILABLE"
    database_records: list[dict[str, Any]] = []
    if db_path.is_file() and valid_map_records:
        db_checked = True
        db_status = "VERIFIED"
        try:
            db_uri = f"file:{db_path.resolve()}?mode=ro"
            with sqlite3.connect(db_uri, uri=True) as connection:
                for record in valid_map_records:
                    identifier = record_id(record)
                    source_id = str(record.get("existing_source_id") or "")
                    doc_key = str(record.get("existing_doc_key") or "")
                    expected_sha = str(record.get("source_sha256") or "").lower()
                    source_rows = connection.execute(
                        "SELECT id, source_type, source_id, title FROM sources WHERE source_id=?",
                        (source_id,),
                    ).fetchall()
                    if len(source_rows) != 1:
                        errors.append(f"expected one existing source row: {identifier}")
                        database_records.append({"external_id": identifier, "status": "FAIL", "source_row_count": len(source_rows)})
                        continue
                    source_row = source_rows[0]
                    if str(source_row[1] or "") != str(record.get("existing_source_type") or ""):
                        errors.append(f"existing source type mismatch: {identifier}")
                    document_rows = connection.execute(
                        "SELECT id, doc_key, title FROM documents WHERE source_id=? AND doc_key=?",
                        (source_row[0], doc_key),
                    ).fetchall()
                    if len(document_rows) != 1:
                        errors.append(f"expected one existing document row: {identifier}")
                        database_records.append({"external_id": identifier, "status": "FAIL", "document_row_count": len(document_rows)})
                        continue
                    document_id = int(document_rows[0][0])
                    page_count = safe_count(
                        connection.execute("SELECT count(*) FROM pages WHERE document_id=?", (document_id,)).fetchone()[0]
                    )
                    stats = connection.execute(
                        """SELECT count(*), count(distinct pdf_page_no), min(pdf_page_no), max(pdf_page_no),
                                  count(distinct source_sha256), min(source_sha256), max(source_sha256),
                                  sum(case when citation_ready=1 then 1 else 0 end),
                                  sum(case when needs_human_review=1 then 1 else 0 end),
                                  sum(case when human_review_note is not null and trim(human_review_note)<>'' then 1 else 0 end),
                                  sum(case when printed_page is not null and trim(printed_page)<>'' then 1 else 0 end)
                           FROM page_provenance WHERE document_id=?""",
                        (document_id,),
                    ).fetchone()
                    page_label_rows = connection.execute(
                        """SELECT p.page_label, pp.citation_ready
                           FROM pages AS p
                           JOIN page_provenance AS pp ON pp.page_id=p.id
                           WHERE p.document_id=?""",
                        (document_id,),
                    ).fetchall()
                    page_label_printed_count = sum(
                        bool(PRINTED_PAGE_LABEL_RE.search(str(row[0] or "")))
                        for row in page_label_rows
                    )
                    page_label_printed_citation_ready_count = sum(
                        bool(PRINTED_PAGE_LABEL_RE.search(str(row[0] or ""))) and bool(row[1])
                        for row in page_label_rows
                    )
                    status_counts = {
                        str(row[0] or ""): safe_count(row[1])
                        for row in connection.execute(
                            "SELECT review_status, count(*) FROM page_provenance WHERE document_id=? GROUP BY review_status",
                            (document_id,),
                        ).fetchall()
                    }
                    formal_academic_rows = safe_count(
                        connection.execute(
                            "SELECT count(*) FROM sources WHERE source_type=? AND source_id=?",
                            (FORMAL_SOURCE_TYPE, f"domestic-academic-pdf:{identifier}"),
                        ).fetchone()[0]
                    )
                    registered_pairs = tuple(
                        (int(row[0]), str(row[1]))
                        for row in connection.execute(
                            """SELECT pdf_page_no, printed_page
                               FROM page_provenance
                              WHERE document_id=? AND printed_page IS NOT NULL
                                AND trim(printed_page)<>''
                              ORDER BY pdf_page_no""",
                            (document_id,),
                        ).fetchall()
                    )
                    expected_page_count = safe_count(record.get("expected_page_count"))
                    expected_page_min = safe_count(record.get("expected_pdf_page_min"))
                    expected_page_max = safe_count(record.get("expected_pdf_page_max"))
                    actual_sha_min = str(stats[5] or "").lower()
                    actual_sha_max = str(stats[6] or "").lower()
                    if page_count != expected_page_count:
                        errors.append(f"page count mismatch: {identifier}")
                    if safe_count(stats[0]) != expected_page_count or safe_count(stats[1]) != expected_page_count:
                        errors.append(f"provenance page count mismatch: {identifier}")
                    if safe_count(stats[2]) != expected_page_min or safe_count(stats[3]) != expected_page_max:
                        errors.append(f"PDF page range mismatch: {identifier}")
                    if safe_count(stats[4]) != 1 or actual_sha_min != expected_sha or actual_sha_max != expected_sha:
                        errors.append(f"source SHA mismatch or mixed provenance: {identifier}")
                    if formal_academic_rows:
                        errors.append(f"reuse candidate has duplicate formal academic source row: {identifier}")
                    expected_status_counts = record.get("review_status_counts")
                    if isinstance(expected_status_counts, dict) and status_counts != {
                        str(key): safe_count(value) for key, value in expected_status_counts.items()
                    }:
                        errors.append(f"review status counts drift: {identifier}")
                    if safe_count(stats[7]) != safe_count(record.get("citation_ready_page_count")):
                        errors.append(f"citation-ready page count drift: {identifier}")
                    if safe_count(stats[8]) != safe_count(record.get("needs_human_review_page_count")):
                        errors.append(f"human-review page count drift: {identifier}")
                    if safe_count(stats[9]) != safe_count(record.get("human_review_note_page_count")):
                        errors.append(f"human-review note count drift: {identifier}")
                    if safe_count(stats[10]) != safe_count(record.get("printed_page_registered_count")):
                        errors.append(f"printed-page registration drift: {identifier}")
                    expected_registered_pairs = EXPLICIT_PAIRS if record.get("printed_page_mapping_status") == "PARTIAL_EXPLICIT_REGISTRATION" else ()
                    if registered_pairs != expected_registered_pairs:
                        errors.append(f"registered printed-page pairs drift: {identifier}")
                    if page_label_printed_count != safe_count(record.get("page_label_printed_count")):
                        errors.append(f"page-label printed mapping drift: {identifier}")
                    if page_label_printed_citation_ready_count != safe_count(
                        record.get("page_label_printed_citation_ready_count")
                    ):
                        errors.append(f"page-label citation mapping drift: {identifier}")
                    database_records.append(
                        {
                            "external_id": identifier,
                            "status": "PASS",
                            "source_type": str(source_row[1] or ""),
                            "existing_source_id": source_id,
                            "existing_doc_key": doc_key,
                            "page_count": page_count,
                            "provenance_page_count": safe_count(stats[0]),
                            "pdf_page_min": safe_count(stats[2]),
                            "pdf_page_max": safe_count(stats[3]),
                            "source_sha256_distinct_count": safe_count(stats[4]),
                            "citation_ready_page_count": safe_count(stats[7]),
                            "needs_human_review_page_count": safe_count(stats[8]),
                            "human_review_note_page_count": safe_count(stats[9]),
                            "printed_page_registered_count": safe_count(stats[10]),
                            "registered_pairs": [list(pair) for pair in registered_pairs],
                            "page_label_printed_count": page_label_printed_count,
                            "page_label_printed_citation_ready_count": page_label_printed_citation_ready_count,
                            "review_status_counts": dict(sorted(status_counts.items())),
                            "formal_academic_source_rows": formal_academic_rows,
                        }
                    )
        except (OSError, sqlite3.Error) as exc:
            db_status = "ERROR"
            errors.append(f"formal database unreadable: {exc}")
    elif db_path.is_file() and not valid_map_records:
        db_status = "NO_VALID_MAP_RECORDS"

    mapped_ids = sorted(seen_map_ids)
    queue_ids = set(queue_by_id)
    unmapped_queue_ids = sorted(queue_ids - set(mapped_ids))
    return {
        "schema_version": "domestic_academic_source_reuse_audit.v1",
        "scope": "source/document/page/provenance metadata and aggregate counts only",
        "body_read": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "auto_delete": False,
        "queue_record_count": len(queue_by_id),
        "reuse_map_record_count": len(valid_map_records),
        "mapped_queue_ids": mapped_ids,
        "unmapped_queue_ids": unmapped_queue_ids,
        "database_checked": db_checked,
        "database_status": db_status,
        "verified_reuse_count": sum(row.get("status") == "PASS" for row in database_records),
        "formal_academic_source_rows_for_reuse_candidates": sum(
            int(row.get("formal_academic_source_rows") or 0) for row in database_records
        ),
        "records": database_records,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--map", dest="map_path", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = audit(args.db, args.queue, args.map_path)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
