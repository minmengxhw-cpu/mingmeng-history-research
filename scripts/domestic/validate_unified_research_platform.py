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
ACADEMIC_CROSSWALK_PATH = ROOT / "data" / "domestic" / "academic_topic_crosswalk.json"
ADMISSION_PATH = ROOT / "work" / "domestic" / "source_admission_20260814" / "SOURCE_ADMISSION_QUEUE.json"
QUEUE_PATH = ROOT / "data" / "domestic" / "primary_retrieval_queue.json"
CARDS_PATH = ROOT / "data" / "domestic" / "topic_comparison_cards.json"
COVERAGE_PATH = ROOT / "data" / "domestic" / "event_coverage.json"
PCC_1946_SOURCEBOOK_MAP_PATH = ROOT / "data" / "domestic" / "pcc_1946_sourcebook_targets.json"
PCC_1946_RENDER_MANIFEST_PATH = ROOT / "data" / "domestic" / "pcc_1946_sourcebook_render_manifest.json"


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
    report = json.loads(ACADEMIC_REPORT_PATH.read_text(encoding="utf-8"))
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
    return {
        "status": "PASS" if not errors else "FAIL",
        "records": report.get("records"),
        "academic_records": report.get("academic_records"),
        "scholarly_articles": report.get("scholarly_articles"),
        "high_priority_academic_records_S_or_A": report.get("high_priority_academic_records_S_or_A"),
        "quality_tiers": report.get("quality_tiers", {}),
        "crosswalk_topics": len(actual_topics),
        "total_topic_matches": crosswalk.get("total_topic_matches"),
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
        "pcc_1946_sourcebook_map": pcc_1946_sourcebook_map_check(),
        "pcc_1946_sourcebook_render_manifest": pcc_1946_render_manifest_check(),
        "missing_provenance": missing_provenance_check(db_path),
        "research_packets": packet_check(),
        "event_source_map_coverage": event_source_map_coverage_check(),
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
