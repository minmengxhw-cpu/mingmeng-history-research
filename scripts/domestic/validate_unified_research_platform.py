#!/usr/bin/env python3
"""Run the metadata-only acceptance gate for the unified research platform.

This command joins the existing database, source-admission, topic-packet,
comparison-card, and research-question checks into one reproducible report.
It never reads page bodies into the report, never writes the formal SQLite
database, never downloads a source, and never deletes or renames a local file.

``status=PASS`` means the platform mechanics are coherent.  The separate
``research_content_status`` deliberately remains ``OPEN`` while topics still
have unresolved primary-source targets; this prevents a green infrastructure
check from being mistaken for historical-source closure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app  # noqa: E402
from scripts.closeout.verify_research_index_manifest import audit_source_files  # noqa: E402
from scripts.domestic.build_research_question_benchmark_20260814 import (  # noqa: E402
    build_report as build_benchmark_report,
)
from scripts.domestic.research_packet import build_research_packet  # noqa: E402
from scripts.domestic.validate_research_packet import validate_packet  # noqa: E402
from scripts.domestic.validate_topic_comparison_cards import validate as validate_cards  # noqa: E402


MANIFEST_PATH = ROOT / "data" / "research_index.manifest.json"
CANDIDATES_PATH = ROOT / "data" / "domestic" / "candidates.jsonl"
SOURCE_REGISTRY_PATH = ROOT / "data" / "domestic" / "source_registry.json"
ACADEMIC_REPORT_PATH = ROOT / "work" / "domestic" / "academic_source_audit_20260813" / "REPORT.json"
ACADEMIC_SNAPSHOT_PATH = ROOT / "data" / "domestic" / "academic_layer_snapshot.json"
ACADEMIC_METADATA_INDEX_PATH = ROOT / "data" / "domestic" / "academic_layer_metadata.json"
ACADEMIC_FULLTEXT_QUEUE_PATH = ROOT / "data" / "domestic" / "academic_fulltext_priority_queue.json"
ACADEMIC_CROSSWALK_PATH = ROOT / "data" / "domestic" / "academic_topic_crosswalk.json"
ADMISSION_PATH = ROOT / "work" / "domestic" / "source_admission_20260814" / "SOURCE_ADMISSION_QUEUE.json"
QUEUE_PATH = ROOT / "data" / "domestic" / "primary_retrieval_queue.json"
PRIMARY_GAP_MATRIX_PATH = ROOT / "data" / "domestic" / "primary_gap_closure_matrix.json"
SOURCE_MAP_DIR = ROOT / "data" / "domestic"
CARDS_PATH = ROOT / "data" / "domestic" / "topic_comparison_cards.json"
COVERAGE_PATH = ROOT / "data" / "domestic" / "event_coverage.json"
PCC_1946_SOURCEBOOK_MAP_PATH = ROOT / "data" / "domestic" / "pcc_1946_sourcebook_targets.json"
PCC_1946_RENDER_MANIFEST_PATH = ROOT / "data" / "domestic" / "pcc_1946_sourcebook_render_manifest.json"
CITATION_FRAGMENT_LEDGER_PATH = ROOT / "data" / "domestic" / "citation_fragments.jsonl"
CITATION_FRAGMENT_MANIFEST_PATH = ROOT / "data" / "domestic" / "citation_fragments_manifest.json"
PRIMARY_SUBTARGET_SUPPORT_PATH = ROOT / "data" / "domestic" / "primary_subtarget_support.json"
DRNH_PREVIEW_EVENT_MAP_PATH = ROOT / "data" / "domestic" / "drnh_preview_event_map.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar(connection: sqlite3.Connection, sql: str) -> int | str:
    return connection.execute(sql).fetchone()[0]


def read_jsonl_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            ids.add(str(item["candidate_id"]))
    return ids


def collect_database_metrics(db_path: Path) -> dict[str, Any]:
    strict = """
        citation_ready = 1
        AND needs_human_review = 0
        AND review_status = 'human_verified'
        AND trim(COALESCE(human_review_note, '')) <> ''
    """
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    actual: dict[str, Any] = {
        "database_size_bytes": db_path.stat().st_size,
        "sha256": sha256(db_path),
        "documents": scalar(connection, "SELECT COUNT(*) FROM documents"),
        "domestic_documents": scalar(
            connection, "SELECT COUNT(*) FROM documents WHERE source_platform='domestic'"
        ),
        "pages": scalar(connection, "SELECT COUNT(*) FROM pages"),
        "page_fts": scalar(connection, "SELECT COUNT(*) FROM page_fts"),
        "research_events": scalar(connection, "SELECT COUNT(*) FROM research_events"),
        "domestic_research_event_rows": scalar(
            connection, "SELECT COUNT(*) FROM research_events WHERE scope_slug LIKE 'domestic-%'"
        ),
        "domestic_research_event_pages": scalar(
            connection,
            """SELECT COUNT(DISTINCT e.page_id)
               FROM research_events e
               JOIN pages p ON p.id=e.page_id
               JOIN documents d ON d.id=p.document_id
               WHERE e.scope_slug LIKE 'domestic-%'
                 AND d.source_platform='domestic'""",
        ),
        "domestic_research_event_scopes": scalar(
            connection,
            "SELECT COUNT(DISTINCT scope_slug) FROM research_events WHERE scope_slug LIKE 'domestic-%'",
        ),
        "domestic_candidates": scalar(connection, "SELECT COUNT(*) FROM domestic_candidates"),
        "domestic_file_backed_provenance": scalar(
            connection,
            """SELECT COUNT(*) FROM page_provenance pp
               JOIN documents d ON d.id=pp.document_id
               WHERE d.source_platform='domestic'
                 AND trim(COALESCE(pp.source_file,''))<>''
                 AND length(trim(COALESCE(pp.source_sha256,'')))=64""",
        ),
        "strict_human_citation_pages": scalar(
            connection, f"SELECT COUNT(*) FROM page_provenance WHERE {strict}"
        ),
        "domestic_pages_missing_provenance": scalar(
            connection,
            """SELECT COUNT(*) FROM pages p
               JOIN documents d ON d.id=p.document_id
               LEFT JOIN page_provenance pp ON pp.page_id=p.id
               WHERE d.source_platform='domestic' AND pp.page_id IS NULL""",
        ),
        "domestic_documents_missing_date": scalar(
            connection,
            """SELECT COUNT(*) FROM documents
               WHERE source_platform='domestic'
                 AND (date_guess IS NULL OR trim(date_guess)='')""",
        ),
        "integrity_check": scalar(connection, "PRAGMA integrity_check"),
        "foreign_key_violations": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        "pages_without_fts": scalar(
            connection,
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL",
        ),
        "fts_without_pages": scalar(
            connection,
            "SELECT COUNT(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL",
        ),
    }
    actual.update(audit_source_files(connection, db_path.parent.parent))
    connection.close()
    return actual


def manifest_check(db_path: Path) -> dict[str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    actual = collect_database_metrics(db_path)
    expected = {
        "database_size_bytes": manifest["database_size_bytes"],
        "sha256": manifest["sha256"],
        **manifest["counts"],
        **manifest["checks"],
    }
    mismatches = {
        key: {"expected": expected[key], "actual": actual.get(key)}
        for key in expected
        if actual.get(key) != expected[key]
    }
    return {"status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches, "actual": actual}


def candidate_alignment_check(db_path: Path) -> dict[str, Any]:
    file_ids = read_jsonl_ids(CANDIDATES_PATH)
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    db_ids = {str(row[0]) for row in connection.execute("SELECT candidate_id FROM domestic_candidates")}
    connection.close()
    missing = sorted(file_ids - db_ids)
    extra = sorted(db_ids - file_ids)
    return {
        "status": "PASS" if not missing and not extra else "FAIL",
        "file_count": len(file_ids),
        "db_count": len(db_ids),
        "missing_from_db": missing,
        "extra_in_db": extra,
    }


def source_registry_alignment_check(db_path: Path) -> dict[str, Any]:
    file_ids = {
        str(row["source_id"])
        for row in json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    }
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    db_ids = {str(row[0]) for row in connection.execute("SELECT source_id FROM domestic_sources")}
    connection.close()
    missing = sorted(file_ids - db_ids)
    extra = sorted(db_ids - file_ids)
    return {
        "status": "PASS" if not missing and not extra else "FAIL",
        "file_count": len(file_ids),
        "db_count": len(db_ids),
        "missing_from_db": missing,
        "extra_in_db": extra,
    }


def academic_layer_check() -> dict[str, Any]:
    report_source = "staging_audit_report"
    if ACADEMIC_REPORT_PATH.is_file():
        report = json.loads(ACADEMIC_REPORT_PATH.read_text(encoding="utf-8"))
    elif ACADEMIC_SNAPSHOT_PATH.is_file():
        snapshot = json.loads(ACADEMIC_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        report_source = "tracked_metadata_snapshot"
        report = {
            "status": snapshot.get("status"),
            "body_read": snapshot.get("body_read"),
            "records": snapshot.get("records"),
            "academic_records": snapshot.get("academic_records"),
            "scholarly_articles": snapshot.get("articles"),
            "high_priority_academic_records_S_or_A": snapshot.get("high_priority"),
            "quality_tiers": snapshot.get("quality_tiers", {}),
        }
    else:
        report_source = "missing"
        report = {}
    crosswalk = json.loads(ACADEMIC_CROSSWALK_PATH.read_text(encoding="utf-8"))
    expected_topics = {
        str(topic["item"].get("event_id")) for topic in app._research_topic_rows()
    }
    actual_topics = {
        str(row.get("event_id")) for row in crosswalk.get("topics", []) if isinstance(row, dict)
    }
    errors: list[str] = []
    if report.get("status") != "PASS":
        errors.append("academic source audit is not PASS")
    if report.get("body_read") is not False or crosswalk.get("body_read") is not False:
        errors.append("academic layer must declare body_read=false")
    if expected_topics != actual_topics:
        errors.append("academic crosswalk does not cover exactly the nine research topics")
    if int(report.get("records") or 0) <= 0 or int(report.get("scholarly_articles") or 0) <= 0:
        errors.append("academic layer has no research records or scholarly articles")
    if int(crosswalk.get("total_topic_matches") or 0) <= 0:
        errors.append("academic crosswalk has no topic matches")
    metadata_index_records = 0
    metadata_index_source = "missing"
    metadata_records: list[dict[str, Any]] = []
    if ACADEMIC_METADATA_INDEX_PATH.is_file():
        try:
            metadata_index = json.loads(ACADEMIC_METADATA_INDEX_PATH.read_text(encoding="utf-8"))
            metadata_index_source = "tracked_metadata_index"
            records = metadata_index.get("records") if isinstance(metadata_index, dict) else None
            metadata_index_records = len(records) if isinstance(records, list) else 0
            metadata_records = [record for record in records if isinstance(record, dict)] if isinstance(records, list) else []
            if not isinstance(metadata_index, dict) or metadata_index.get("body_read") is not False:
                errors.append("academic metadata index must declare body_read=false")
            if not isinstance(metadata_index, dict) or metadata_index.get("local_paths_included") is not False:
                errors.append("academic metadata index must exclude local paths")
            if metadata_index_records != int(report.get("records") or 0):
                errors.append("academic metadata index record count does not match audit")
            serialized = json.dumps(metadata_index, ensure_ascii=False)
            if any(marker in serialized for marker in ("/Users/", "/private/", '"local_path"', '"derived_text_path"')):
                errors.append("academic metadata index contains a local path marker")
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            errors.append("academic metadata index is unreadable")
    else:
        errors.append("academic metadata index is missing")
    fulltext_priority_queue_records = 0
    fulltext_priority_queue_source = "missing"
    fulltext_priority_queue_classes: dict[str, int] = {}
    if ACADEMIC_FULLTEXT_QUEUE_PATH.is_file():
        try:
            priority_queue = json.loads(ACADEMIC_FULLTEXT_QUEUE_PATH.read_text(encoding="utf-8"))
            fulltext_priority_queue_source = "tracked_queue"
            queue_records = priority_queue.get("records") if isinstance(priority_queue, dict) else None
            summary = priority_queue.get("summary") if isinstance(priority_queue, dict) else None
            fulltext_priority_queue_records = len(queue_records) if isinstance(queue_records, list) else 0
            fulltext_priority_queue_classes = (
                dict(summary.get("queue_classes") or {})
                if isinstance(summary, dict) else {}
            )
            if not isinstance(priority_queue, dict):
                errors.append("academic fulltext priority queue is unreadable")
            for key in ("body_read", "formal_db_written", "local_paths_included"):
                if not isinstance(priority_queue, dict) or priority_queue.get(key) is not False:
                    errors.append(f"academic fulltext priority queue {key} must be false")
            expected_statuses = {
                "FULLTEXT_PDF", "FULLTEXT_HTML",
                "FULLTEXT_PDF_CANDIDATE", "FULLTEXT_HTML_CANDIDATE",
            }
            expected_queue_ids = {
                str(record.get("external_id"))
                for record in metadata_records
                if str(record.get("fulltext_status") or "") in expected_statuses
            }
            actual_queue_ids = {
                str(record.get("external_id"))
                for record in (queue_records or [])
                if isinstance(record, dict)
            }
            if fulltext_priority_queue_records != len(expected_queue_ids):
                errors.append("academic fulltext priority queue count does not match metadata selection")
            if actual_queue_ids != expected_queue_ids:
                errors.append("academic fulltext priority queue ids do not match metadata selection")
            if not isinstance(queue_records, list) or not all(isinstance(record, dict) for record in queue_records):
                errors.append("academic fulltext priority queue records are unreadable")
            for record in queue_records or []:
                if str(record.get("fulltext_status") or "") not in expected_statuses:
                    errors.append("academic fulltext priority queue contains an unsupported status")
                    break
            serialized = json.dumps(priority_queue, ensure_ascii=False)
            if any(marker in serialized for marker in ("/Users/", "/private/", '"local_path"', '"derived_text_path"')):
                errors.append("academic fulltext priority queue contains a local path marker")
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            errors.append("academic fulltext priority queue is unreadable")
    else:
        errors.append("academic fulltext priority queue is missing")
    return {
        "status": "PASS" if not errors else "FAIL",
        "records": report.get("records"),
        "academic_records": report.get("academic_records"),
        "scholarly_articles": report.get("scholarly_articles"),
        "high_priority_academic_records_S_or_A": report.get("high_priority_academic_records_S_or_A"),
        "quality_tiers": report.get("quality_tiers", {}),
        "crosswalk_topics": len(actual_topics),
        "total_topic_matches": crosswalk.get("total_topic_matches"),
        "source": report_source,
        "metadata_index_source": metadata_index_source,
        "metadata_index_records": metadata_index_records,
        "fulltext_priority_queue_source": fulltext_priority_queue_source,
        "fulltext_priority_queue_records": fulltext_priority_queue_records,
        "fulltext_priority_queue_classes": fulltext_priority_queue_classes,
        "errors": errors,
    }


def admission_check() -> dict[str, Any]:
    payload = json.loads(ADMISSION_PATH.read_text(encoding="utf-8"))
    rows = payload.get("rows") or []
    errors: list[str] = []
    for key in ("body_read", "formal_db_written", "auto_delete", "auto_promote_citation_ready"):
        if payload.get(key) is not False:
            errors.append(f"{key} must be false")
    if len(rows) != int(payload.get("source_rows") or -1):
        errors.append("source_rows does not match rows length")
    for index, row in enumerate(rows):
        for key in ("body_read", "citation_ready_changed", "auto_delete"):
            if row.get(key) is not False:
                errors.append(f"row[{index}].{key} must be false")
    return {
        "status": "PASS" if not errors else "FAIL",
        "source_rows": len(rows),
        "admission_counts": payload.get("admission_counts", {}),
        "ocr_action_counts": payload.get("ocr_action_counts", {}),
        "errors": errors,
    }


def retrieval_queue_check(candidate_count: int) -> dict[str, Any]:
    payload = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("schema") != "domestic_primary_retrieval_queue.v3":
        errors.append("unexpected retrieval queue schema")
    if int(payload.get("topic_count") or 0) != 9:
        errors.append("retrieval queue must cover nine topics")
    formal_index = payload.get("formal_index") or {}
    if int(formal_index.get("candidate_count") or -1) != candidate_count:
        errors.append("retrieval queue formal candidate count is stale")
    for key in ("body_read", "formal_db_written", "auto_download", "auto_promote_primary_closed"):
        if payload.get(key) is not False:
            errors.append(f"{key} must be false")
    if payload.get("missing_candidate_ids"):
        errors.append("retrieval queue contains missing candidate ids")
    return {
        "status": "PASS" if not errors else "FAIL",
        "topic_count": payload.get("topic_count"),
        "open_target_count": payload.get("open_target_count"),
        "formal_candidate_count": formal_index.get("candidate_count"),
        "event_link_page_count": (payload.get("event_link_index") or {}).get("page_count"),
        "errors": errors,
    }


def primary_gap_matrix_check() -> dict[str, Any]:
    """Ensure the committed P0 matrix is fresh against current source maps.

    The matrix is a metadata-only execution view.  It must not silently lag
    behind a newly added source-map route, otherwise researchers and local
    agents receive an obsolete queue while the platform gate remains green.
    """
    errors: list[str] = []
    try:
        matrix = json.loads(PRIMARY_GAP_MATRIX_PATH.read_text(encoding="utf-8"))
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"matrix_or_queue_unreadable: {exc}"]}
    if matrix.get("schema") != "domestic_primary_gap_closure_matrix.v1":
        errors.append("unexpected primary gap matrix schema")
    for key in ("body_read", "formal_db_written"):
        if matrix.get(key) is not False:
            errors.append(f"matrix {key} must be false")
    topics = matrix.get("topics") if isinstance(matrix.get("topics"), list) else []
    matrix_by_event = {
        str(row.get("event_id")): row
        for row in topics
        if isinstance(row, dict) and row.get("event_id")
    }
    expected_event_ids = {
        str(topic["item"].get("event_id") or "")
        for topic in app._research_topic_rows()
        if isinstance(topic, dict) and isinstance(topic.get("item"), dict)
    }
    if set(matrix_by_event) != expected_event_ids:
        errors.append("primary gap matrix topics do not match research topics")
    source_maps = sorted(SOURCE_MAP_DIR.glob("*_source_map.json"))
    actual_page_count = 0
    actual_map_ids: set[str] = set()
    for path in source_maps:
        try:
            source_map = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"source map unreadable {path.name}: {exc}")
            continue
        event_id = str(source_map.get("event_id") or "")
        actual_map_ids.add(event_id)
        pages = [
            page
            for source in source_map.get("sources", [])
            if isinstance(source, dict)
            for page in source.get("page_records", [])
            if isinstance(page, dict)
        ]
        actual_page_count += len(pages)
        matrix_topic = matrix_by_event.get(event_id)
        if matrix_topic is None:
            errors.append(f"source map missing from matrix: {event_id}")
            continue
        matrix_map = matrix_topic.get("source_map") if isinstance(matrix_topic.get("source_map"), dict) else {}
        if int(matrix_map.get("page_record_count") or 0) != len(pages):
            errors.append(f"stale source-map page count: {event_id}")
        if matrix_map.get("primary_evidence_closed") is not (source_map.get("primary_evidence_closed") is True):
            errors.append(f"source-map closure mismatch: {event_id}")
    if actual_map_ids != expected_event_ids:
        errors.append("source-map event ids do not match research topics")
    summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
    if int(summary.get("source_map_count") or 0) != len(source_maps):
        errors.append("matrix source_map_count is stale")
    if int(summary.get("source_map_page_record_count") or 0) != actual_page_count:
        errors.append("matrix source_map_page_record_count is stale")
    queue_topics = queue.get("topics") if isinstance(queue.get("topics"), list) else []
    queue_route_count = sum(
        int(target.get("candidate_route_count") or 0)
        for topic in queue_topics
        if isinstance(topic, dict)
        for target in (topic.get("missing_primary") or [])
        if isinstance(target, dict)
    )
    matrix_route_count = sum(
        int(topic.get("candidate_route_count") or 0)
        for topic in topics
        if isinstance(topic, dict)
    )
    if matrix_route_count != queue_route_count:
        errors.append("matrix candidate route count does not match retrieval queue")
    return {
        "status": "PASS" if not errors else "FAIL",
        "topic_count": len(topics),
        "source_map_count": len(source_maps),
        "source_map_page_record_count": actual_page_count,
        "candidate_route_count": matrix_route_count,
        "errors": errors,
    }


def pcc_1946_sourcebook_map_check() -> dict[str, Any]:
    """Validate the local sourcebook target map without reading its body.

    The raw PDF is intentionally ignored by Git and may be absent on another
    checkout.  The gate therefore checks only the committed provenance
    metadata, target coordinates, and aggregate non-promoting invariants. A
    target may now be page-identity/boundary verified while the sourcebook as
    a whole remains an L2 compilation and its OCR body remains unpromoted.
    """
    errors: list[str] = []
    try:
        payload = json.loads(PCC_1946_SOURCEBOOK_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "target_count": 0, "errors": [f"map unreadable: {exc}"]}
    if payload.get("schema") != "domestic_sourcebook_target_map.v1":
        errors.append("unexpected sourcebook map schema")
    if payload.get("source_role") != "sourcebook_scan" or payload.get("evidence_level") != "L2":
        errors.append("sourcebook must remain an L2 sourcebook scan")
    if payload.get("render_manifest") != "data/domestic/pcc_1946_sourcebook_render_manifest.json":
        errors.append("sourcebook render manifest path is missing or unexpected")
    for key in ("body_read", "formal_db_written", "citation_ready", "auto_promote_primary_closed"):
        if payload.get(key) is not False:
            errors.append(f"{key} must be false")
    targets = payload.get("targets") if isinstance(payload.get("targets"), list) else []
    seen: set[str] = set()
    for target in targets:
        if not isinstance(target, dict):
            errors.append("target row is not an object")
            continue
        target_id = str(target.get("id") or "")
        if not target_id or target_id in seen:
            errors.append(f"duplicate or empty target id: {target_id or '<empty>'}")
        seen.add(target_id)
        try:
            pdf_page = int(target.get("pdf_page_start"))
            printed_page = int(target.get("printed_page_start"))
        except (TypeError, ValueError):
            errors.append(f"target {target_id or '<empty>'} has invalid page coordinates")
            continue
        if not (1 <= pdf_page <= int(payload.get("page_count") or 0)):
            errors.append(f"target {target_id} PDF page is outside sourcebook")
        if printed_page < 1:
            errors.append(f"target {target_id} printed page must be positive")
        if target.get("status") not in {"title_confirmed_boundary_pending", "page_identity_boundary_verified"}:
            errors.append(f"target {target_id} has an unsupported review status")
    if len(targets) != 6:
        errors.append("expected six visually confirmed title anchors")
    return {
        "status": "PASS" if not errors else "FAIL",
        "source_id": payload.get("source_id"),
        "target_count": len(targets),
        "source_sha256": payload.get("source_sha256"),
        "errors": errors,
    }


def pcc_1946_render_manifest_check() -> dict[str, Any]:
    """Validate committed page-image hashes without requiring local images.

    The raw scan and derived PNGs remain local-only.  Git carries only the
    source identity, coordinates, image hashes, and review boundary so a
    later local rerender can prove whether the visual evidence changed.
    """
    errors: list[str] = []
    try:
        source_map = json.loads(PCC_1946_SOURCEBOOK_MAP_PATH.read_text(encoding="utf-8"))
        manifest = json.loads(PCC_1946_RENDER_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "page_count": 0, "errors": [f"render manifest unreadable: {exc}"]}
    if manifest.get("schema") != "domestic_sourcebook_render_manifest.v1":
        errors.append("unexpected sourcebook render manifest schema")
    for key in ("body_read", "formal_db_written", "citation_ready"):
        if manifest.get(key) is not False:
            errors.append(f"render manifest {key} must be false")
    if manifest.get("visual_review_status") not in {
        "title_visual_confirmed_boundary_pending",
        "page_identity_and_boundary_human_verified_body_ocr_pending",
    }:
        errors.append("render manifest has an unsupported visual review status")
    for key in ("source_id", "source_file", "source_sha256", "page_count"):
        if manifest.get(key) != source_map.get(key):
            errors.append(f"render manifest {key} does not match sourcebook map")
    if manifest.get("render_dpi") != 300:
        errors.append("render manifest DPI must be 300")
    if manifest.get("rotation") != "270deg":
        errors.append("render manifest rotation must be 270deg")
    pages = manifest.get("pages") if isinstance(manifest.get("pages"), list) else []
    if len(pages) != 9:
        errors.append("render manifest must contain nine reviewed pages")
    page_numbers: set[int] = set()
    target_ids = {str(row.get("id")) for row in source_map.get("targets", []) if isinstance(row, dict)}
    target_pairs: set[tuple[str, str, int]] = set()
    for page in pages:
        if not isinstance(page, dict):
            errors.append("render manifest page row is not an object")
            continue
        try:
            pdf_page = int(page.get("pdf_page"))
        except (TypeError, ValueError):
            errors.append("render manifest page has invalid PDF page")
            continue
        if pdf_page in page_numbers:
            errors.append(f"duplicate rendered PDF page: {pdf_page}")
        page_numbers.add(pdf_page)
        if not (1 <= pdf_page <= int(source_map.get("page_count") or 0)):
            errors.append(f"rendered PDF page outside sourcebook: {pdf_page}")
        image_sha = str(page.get("rotated_image_sha256") or "")
        if len(image_sha) != 64 or any(char not in "0123456789abcdef" for char in image_sha):
            errors.append(f"rendered PDF page {pdf_page} has invalid image SHA256")
        if int(page.get("rotated_image_bytes") or 0) <= 0:
            errors.append(f"rendered PDF page {pdf_page} has invalid image size")
        if page.get("visual_review_status") != "visually_inspected":
            errors.append(f"rendered PDF page {pdf_page} is not visually inspected")
        targets = page.get("targets") if isinstance(page.get("targets"), list) else []
        for target in targets:
            if not isinstance(target, dict):
                errors.append(f"rendered PDF page {pdf_page} target row is not an object")
                continue
            target_id = str(target.get("target_id") or "")
            role = str(target.get("role") or "")
            if target_id not in target_ids:
                errors.append(f"rendered PDF page {pdf_page} references unknown target {target_id}")
            if role not in {"title_start", "adjacent_boundary"}:
                errors.append(f"rendered PDF page {pdf_page} has invalid role {role}")
            target_pairs.add((target_id, role, pdf_page))
    expected_pairs: set[tuple[str, str, int]] = set()
    for target in source_map.get("targets", []):
        if not isinstance(target, dict):
            continue
        target_id = str(target.get("id") or "")
        expected_pairs.add((target_id, "title_start", int(target.get("pdf_page_start"))))
        for adjacent in target.get("adjacent_pdf_pages", []):
            expected_pairs.add((target_id, "adjacent_boundary", int(adjacent)))
    if target_pairs != expected_pairs:
        errors.append("render manifest target/page mapping does not match sourcebook target map")
    return {
        "status": "PASS" if not errors else "FAIL",
        "source_id": manifest.get("source_id"),
        "page_count": len(pages),
        "review_status": manifest.get("visual_review_status"),
        "errors": errors,
    }


def citation_fragment_ledger_check() -> dict[str, Any]:
    """Validate the additive fragment ledger without promoting page bodies."""
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    manifest: dict[str, Any] = {}
    if not CITATION_FRAGMENT_LEDGER_PATH.is_file():
        errors.append("citation fragment ledger is missing")
    if not CITATION_FRAGMENT_MANIFEST_PATH.is_file():
        errors.append("citation fragment manifest is missing")
    if not errors:
        try:
            manifest_payload = json.loads(CITATION_FRAGMENT_MANIFEST_PATH.read_text(encoding="utf-8"))
            if isinstance(manifest_payload, dict):
                manifest = manifest_payload
            else:
                errors.append("citation fragment manifest is not an object")
            for line in CITATION_FRAGMENT_LEDGER_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line)
                    if isinstance(item, dict):
                        rows.append(item)
                    else:
                        errors.append("citation fragment ledger contains a non-object row")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"citation fragment ledger parse failed: {exc}")
    if rows:
        if int(manifest.get("fragment_count") or -1) != len(rows):
            errors.append("manifest fragment_count does not match ledger")
        if str(manifest.get("ledger_sha256") or "") != sha256(CITATION_FRAGMENT_LEDGER_PATH):
            errors.append("manifest ledger_sha256 does not match ledger")
        if len({str(row.get("fragment_id") or "") for row in rows}) != len(rows):
            errors.append("fragment_id values are not unique")
        for row in rows:
            if row.get("fragment_citation_ready") is not True:
                errors.append(f"fragment is not citation-ready: {row.get('fragment_id')}")
            for key in ("page_citation_ready", "body_read", "formal_db_written"):
                if row.get(key) is not False:
                    errors.append(f"fragment boundary {key} is not false: {row.get('fragment_id')}")
            if len(str(row.get("source_sha256") or "")) != 64:
                errors.append(f"source SHA256 missing: {row.get('fragment_id')}")
            for key in ("fragment_review_ref", "page_review_ref", "source_file"):
                value = str(row.get(key) or "")
                if value.startswith(("/", "file://")):
                    errors.append(f"absolute path in fragment ledger: {key}")
            review_ref = str(row.get("fragment_review_ref") or "")
            if not review_ref or not (ROOT / review_ref).is_file():
                errors.append(f"fragment review artifact missing: {review_ref}")
    return {
        "status": "PASS" if rows and not errors else "FAIL",
        "fragment_count": len(rows),
        "fragment_citation_ready_count": sum(bool(row.get("fragment_citation_ready")) for row in rows),
        "page_citation_ready_count": sum(bool(row.get("page_citation_ready")) for row in rows),
        "formal_db_written_count": sum(bool(row.get("formal_db_written")) for row in rows),
        "body_read_count": sum(bool(row.get("body_read")) for row in rows),
        "errors": errors,
    }


def missing_provenance_check(db_path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """SELECT p.id AS page_id, d.doc_key, p.page_label, p.page_url
           FROM pages p JOIN documents d ON d.id=p.document_id
           LEFT JOIN page_provenance pp ON pp.page_id=p.id
           WHERE d.source_platform='domestic' AND pp.page_id IS NULL"""
    ).fetchall()
    connection.close()
    allowed = [
        row
        for row in rows
        if row["doc_key"] == "domestic-web/SAAC-ALBUM"
        and row["page_label"] == "album-index"
        and str(row["page_url"] or "").strip()
    ]
    unexpected = [dict(row) for row in rows if row not in allowed]
    return {
        "status": "PASS" if not unexpected else "FAIL",
        "missing_count": len(rows),
        "allowed_navigation_index_count": len(allowed),
        "unexpected_missing": unexpected,
    }


def packet_check() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for topic in app._research_topic_rows():
        event_id = str(topic["item"].get("event_id") or "")
        packet = build_research_packet(event_id)
        result = {"event_id": event_id, "status": "FAIL", "errors": ["packet not found"]}
        if packet is not None:
            result = validate_packet(packet, event_id)
            counts = packet.get("counts") or {}
            result["research_usable_with_boundaries"] = bool(
                result.get("status") == "PASS"
                and int(counts.get("evidence_chain_page_items") or 0) > 0
                and int(counts.get("topic_event_domestic_strict_pages") or 0) > 0
            )
        rows.append(result)
    statuses = [row.get("status") for row in rows]
    partial = sum(
        str((topic["item"] or {}).get("primary_evidence_status") or "") == "partial"
        for topic in app._research_topic_rows()
    )
    return {
        "status": "PASS" if rows and all(status == "PASS" for status in statuses) else "FAIL",
        "topic_count": len(rows),
        "packet_count": sum(status == "PASS" for status in statuses),
        "failed_packet_count": sum(status != "PASS" for status in statuses),
        "primary_evidence_partial_count": partial,
        "research_ready_count": sum(
            str((topic["item"] or {}).get("primary_evidence_status") or "") == "closed"
            for topic in app._research_topic_rows()
        ),
        "research_usable_with_boundaries_count": sum(
            bool(row.get("research_usable_with_boundaries")) for row in rows
        ),
        "errors": [row for row in rows if row.get("status") != "PASS"],
    }


def event_source_map_coverage_check() -> dict[str, Any]:
    """Require every declared research topic to expose a non-empty map.

    This is a structural/UI invariant only.  It does not promote a map to
    primary-source closure and does not inspect page bodies.
    """
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for topic in app._research_topic_rows():
        event_id = str(topic["item"].get("event_id") or "")
        summary = topic.get("event_source_map") or {}
        page_count = int(summary.get("page_record_count") or 0)
        row = {
            "event_id": event_id,
            "available": bool(summary.get("available")),
            "page_record_count": page_count,
            "strict_page_count": int(summary.get("strict_page_count") or 0),
            "review_only_page_count": int(summary.get("review_only_page_count") or 0),
            "navigation_page_count": int(summary.get("navigation_page_count") or 0),
            "access_route_count": int(summary.get("access_route_count") or 0),
        }
        rows.append(row)
        if not row["available"] or page_count <= 0:
            errors.append(row)
    return {
        "status": "PASS" if rows and not errors else "FAIL",
        "topic_count": len(rows),
        "mapped_topic_count": sum(row["available"] and row["page_record_count"] > 0 for row in rows),
        "page_record_count": sum(row["page_record_count"] for row in rows),
        "strict_page_count": sum(row["strict_page_count"] for row in rows),
        "review_only_page_count": sum(row["review_only_page_count"] for row in rows),
        "navigation_page_count": sum(row["navigation_page_count"] for row in rows),
        "access_route_count": sum(row["access_route_count"] for row in rows),
        "errors": errors,
    }


def primary_subtarget_support_check(db_path: Path) -> dict[str, Any]:
    """Validate bounded primary subunits without reading or promoting bodies.

    The support file is intentionally a partial view: it may cover only some
    of the nine topics, and a passing result never changes a topic's primary
    evidence status.  This gate checks that every declared page and source
    remains anchored to the formal database/source map while keeping the
    artifact metadata-only.
    """
    errors: list[str] = []
    payload: dict[str, Any] = {}
    if not PRIMARY_SUBTARGET_SUPPORT_PATH.is_file():
        return {
            "status": "FAIL",
            "topic_count": 0,
            "unit_count": 0,
            "page_count": 0,
            "unique_page_count": 0,
            "errors": ["primary subtarget support file is missing"],
        }
    try:
        loaded = json.loads(PRIMARY_SUBTARGET_SUPPORT_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            payload = loaded
        else:
            errors.append("primary subtarget support is not an object")
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "FAIL",
            "topic_count": 0,
            "unit_count": 0,
            "page_count": 0,
            "unique_page_count": 0,
            "errors": [f"primary subtarget support is unreadable: {exc}"],
        }

    if payload.get("schema_version") != "domestic_primary_subtarget_support.v1":
        errors.append("unexpected primary subtarget support schema")
    for key in ("body_read", "formal_db_written", "primary_evidence_closed"):
        if payload.get(key) is not False:
            errors.append(f"primary subtarget support {key} must be false")

    topics = payload.get("topics")
    if not isinstance(topics, dict):
        topics = {}
        errors.append("primary subtarget support topics must be an object")
    expected_event_ids = {
        str(topic["item"].get("event_id") or "")
        for topic in app._research_topic_rows()
        if isinstance(topic, dict) and isinstance(topic.get("item"), dict)
    }
    unknown_events = sorted(set(map(str, topics)) - expected_event_ids)
    if unknown_events:
        errors.append(f"primary subtarget support has unknown event ids: {unknown_events}")

    source_map_by_event: dict[str, dict[str, set[int]]] = {}
    for source_map_path in sorted(SOURCE_MAP_DIR.glob("*_source_map.json")):
        try:
            source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"source map unreadable {source_map_path.name}: {exc}")
            continue
        event_id = str(source_map.get("event_id") or "")
        source_map_by_event.setdefault(event_id, {})
        for source in source_map.get("sources") or []:
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("source_id") or "")
            page_ids: set[int] = set()
            for page in source.get("page_records") or []:
                if not isinstance(page, dict):
                    continue
                value = page.get("page_id")
                if isinstance(value, int) and not isinstance(value, bool):
                    page_ids.add(value)
                elif isinstance(value, str) and value.isdigit():
                    page_ids.add(int(value))
            if source_id:
                source_map_by_event[event_id][source_id] = page_ids

    unit_ids: set[str] = set()
    page_ids: list[int] = []
    for event_id, rows in topics.items():
        event_id = str(event_id)
        if not isinstance(rows, list):
            errors.append(f"primary subtarget rows are not a list: {event_id}")
            continue
        event_sources = source_map_by_event.get(event_id, {})
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"primary subtarget row is not an object: {event_id}[{index}]")
                continue
            unit_id = str(row.get("unit_id") or "")
            if not unit_id or unit_id in unit_ids:
                errors.append(f"primary subtarget unit_id is missing or duplicated: {event_id}[{index}]")
            unit_ids.add(unit_id)
            for key in ("label", "scope", "caveat"):
                if not str(row.get(key) or "").strip():
                    errors.append(f"primary subtarget {key} is missing: {unit_id or event_id}")
            if row.get("status") != "bounded_unit_ready":
                errors.append(f"primary subtarget status is not bounded_unit_ready: {unit_id or event_id}")
            declared_sources = row.get("source_ids")
            declared_pages = row.get("page_ids")
            if not isinstance(declared_sources, list) or not declared_sources:
                errors.append(f"primary subtarget source_ids are missing: {unit_id or event_id}")
                declared_sources = []
            if not isinstance(declared_pages, list) or not declared_pages:
                errors.append(f"primary subtarget page_ids are missing: {unit_id or event_id}")
                declared_pages = []
            normalized_pages: list[int] = []
            for value in declared_pages:
                if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                    normalized_pages.append(value)
                else:
                    errors.append(f"primary subtarget page_id is not a positive integer: {unit_id or event_id}")
            page_ids.extend(normalized_pages)
            normalized_sources = [str(value) for value in declared_sources if str(value).strip()]
            for source_id in normalized_sources:
                source_pages = event_sources.get(source_id)
                if source_pages is None:
                    errors.append(f"primary subtarget source is absent from event source map: {source_id}")
                elif not set(normalized_pages) & source_pages:
                    errors.append(f"primary subtarget source has no declared page overlap: {source_id}")

    if page_ids:
        placeholders = ",".join("?" for _ in sorted(set(page_ids)))
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        found_page_ids = {
            int(row[0])
            for row in connection.execute(
                f"SELECT id FROM pages WHERE id IN ({placeholders})", sorted(set(page_ids))
            )
        }
        connection.close()
        missing_page_ids = sorted(set(page_ids) - found_page_ids)
        if missing_page_ids:
            errors.append(f"primary subtarget page ids are absent from formal database: {missing_page_ids}")

    serialized = json.dumps(payload, ensure_ascii=False)
    for marker in ("/Users/", "/private/", '"body_text"', '"ocr_text"', '"source_file"'):
        if marker in serialized:
            errors.append(f"primary subtarget support contains forbidden marker: {marker}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "topic_count": len(topics),
        "unit_count": len(unit_ids),
        "page_count": len(page_ids),
        "unique_page_count": len(set(page_ids)),
        "errors": errors,
    }


def drnh_preview_event_map_check(db_path: Path) -> dict[str, Any]:
    """Validate DRNH visitor-preview routing as a non-promoting metadata layer."""
    errors: list[str] = []
    try:
        payload = json.loads(DRNH_PREVIEW_EVENT_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "event_count": 0, "document_count": 0, "preview_page_count": 0, "errors": [f"drnh preview map unreadable: {exc}"]}
    if not isinstance(payload, dict):
        return {"status": "FAIL", "event_count": 0, "document_count": 0, "preview_page_count": 0, "errors": ["drnh preview map is not an object"]}
    if payload.get("schema_version") != "domestic_drnh_visitor_preview_event_map.v1":
        errors.append("unexpected drnh preview map schema")
    for key in ("body_read", "formal_db_written", "local_paths_included", "citation_ready_written"):
        if payload.get(key) is not False:
            errors.append(f"drnh preview map {key} must be false")
    events = payload.get("events")
    if not isinstance(events, dict):
        events = {}
        errors.append("drnh preview map events must be an object")
    expected_events = {
        str(topic["item"].get("event_id") or "")
        for topic in app._research_topic_rows()
        if isinstance(topic, dict) and isinstance(topic.get("item"), dict)
    }
    unknown_events = sorted(set(map(str, events)) - expected_events)
    if unknown_events:
        errors.append(f"drnh preview map has unknown event ids: {unknown_events}")
    doc_keys: list[str] = []
    for event_id, event in events.items():
        if not isinstance(event, dict):
            errors.append(f"drnh preview event is not an object: {event_id}")
            continue
        for key in ("scope", "caveat"):
            if not str(event.get(key) or "").strip():
                errors.append(f"drnh preview event {key} is missing: {event_id}")
        keys = event.get("doc_keys")
        if not isinstance(keys, list) or not keys:
            errors.append(f"drnh preview event doc_keys are missing: {event_id}")
            continue
        doc_keys.extend(str(value) for value in keys if str(value).strip())
    if len(doc_keys) != len(set(doc_keys)):
        errors.append("drnh preview doc_keys are duplicated")
    document_count = 0
    preview_page_count = 0
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    has_images = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='drnh_images'"
    ).fetchone() is not None
    for doc_key in doc_keys:
        row = connection.execute(
            "SELECT id FROM documents WHERE doc_key=? AND source_platform='drnh'",
            (doc_key,),
        ).fetchone()
        if row is None:
            errors.append(f"drnh preview document is absent from formal database: {doc_key}")
            continue
        document_count += 1
        if has_images:
            preview_page_count += int(
                connection.execute(
                    "SELECT count(*) FROM drnh_images WHERE document_id=?", (int(row[0]),)
                ).fetchone()[0]
            )
    connection.close()
    serialized = json.dumps(payload, ensure_ascii=False)
    for marker in ("/Users/", "/private/", '"local_path"', '"file_path"'):
        if marker in serialized:
            errors.append(f"drnh preview map contains forbidden marker: {marker}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "event_count": len(events),
        "document_count": document_count,
        "preview_page_count": preview_page_count,
        "drnh_images_table_available": has_images,
        "errors": errors,
    }


def build_report() -> dict[str, Any]:
    db_path = Path(app.DB_PATH).resolve()
    candidate_check = candidate_alignment_check(db_path)
    checks = {
        "manifest": manifest_check(db_path),
        "candidate_alignment": candidate_check,
        "source_registry_alignment": source_registry_alignment_check(db_path),
        "academic_layer": academic_layer_check(),
        "source_admission": admission_check(),
        "retrieval_queue": retrieval_queue_check(int(candidate_check.get("db_count") or 0)),
        "primary_gap_matrix": primary_gap_matrix_check(),
        "pcc_1946_sourcebook_map": pcc_1946_sourcebook_map_check(),
        "pcc_1946_sourcebook_render_manifest": pcc_1946_render_manifest_check(),
        "citation_fragment_ledger": citation_fragment_ledger_check(),
        "missing_provenance": missing_provenance_check(db_path),
        "research_packets": packet_check(),
        "event_source_map_coverage": event_source_map_coverage_check(),
        "primary_subtarget_support": primary_subtarget_support_check(db_path),
        "drnh_preview_event_map": drnh_preview_event_map_check(db_path),
        "comparison_cards": validate_cards(COVERAGE_PATH, CARDS_PATH),
    }
    benchmark = build_benchmark_report()
    checks["research_question_benchmark"] = {
        "status": "PASS" if not benchmark["failures"] else "FAIL",
        "question_count": benchmark["question_count"],
        "path_ready_count": benchmark["path_ready_count"],
        "strict_page_query_count": benchmark["strict_page_query_count"],
        "failed_path_count": benchmark["failed_path_count"],
        "topic_count": benchmark["topic_count"],
    }
    failures = [name for name, result in checks.items() if result.get("status") != "PASS"]
    packet_result = checks["research_packets"]
    research_ready = int(packet_result.get("research_ready_count") or 0)
    return {
        "schema_version": "domestic_unified_research_platform_gate.v1",
        "scope": "formal_domestic_database_metadata_only",
        "body_read": False,
        "formal_db_written": False,
        "auto_delete": False,
        "status": "PASS" if not failures else "FAIL",
        "research_content_status": "CLOSED" if research_ready else "OPEN_PRIMARY_GAPS",
        "checks": checks,
        "failed_checks": failures,
        "interpretation": {
            "status": "Platform mechanics are coherent only; this is not a claim that all historical primary-source gaps are closed.",
            "research_content_status": "At least one topic still has unresolved primary-source targets." if not research_ready else "All declared topics passed the primary-evidence closure gate.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "work" / "domestic" / "unified_platform_gate_20260814" / "REPORT.json",
    )
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "research_content_status": report["research_content_status"],
                "failed_checks": report["failed_checks"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
