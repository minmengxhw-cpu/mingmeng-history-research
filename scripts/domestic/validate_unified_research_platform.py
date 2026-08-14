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
ADMISSION_PATH = ROOT / "work" / "domestic" / "source_admission_20260814" / "SOURCE_ADMISSION_QUEUE.json"
QUEUE_PATH = ROOT / "data" / "domestic" / "primary_retrieval_queue.json"
CARDS_PATH = ROOT / "data" / "domestic" / "topic_comparison_cards.json"
COVERAGE_PATH = ROOT / "data" / "domestic" / "event_coverage.json"


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


def build_report() -> dict[str, Any]:
    db_path = Path(app.DB_PATH).resolve()
    candidate_check = candidate_alignment_check(db_path)
    checks = {
        "manifest": manifest_check(db_path),
        "candidate_alignment": candidate_check,
        "source_admission": admission_check(),
        "retrieval_queue": retrieval_queue_check(int(candidate_check.get("db_count") or 0)),
        "missing_provenance": missing_provenance_check(db_path),
        "research_packets": packet_check(),
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
