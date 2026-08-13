#!/usr/bin/env python3
"""Build a metadata-only domestic/foreign/academic parity acceptance matrix.

The matrix is a gap detector, not a claim generator. It measures navigation
readiness, strict page availability, metadata-matched academic explanation,
shared foreign event indexing, and the separately declared primary-evidence
closure status. It never reads page bodies and never changes a database.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data/research_index.sqlite"
DEFAULT_COVERAGE = ROOT / "data/domestic/event_coverage.json"
DEFAULT_CARDS = ROOT / "data/domestic/topic_comparison_cards.json"
DEFAULT_CROSSWALK = ROOT / "work/domestic/academic_source_audit_20260813/TOPIC_CROSSWALK_CURRENT.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def crosswalk_by_topic(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    report = load_json(path)
    return {str(row["event_id"]): row for row in report.get("topics", []) if row.get("event_id")}


def event_metrics(conn: sqlite3.Connection, event_id: str) -> dict[str, int]:
    row = conn.execute(
        """
        SELECT count(*) AS rows,
               count(DISTINCT e.page_id) AS pages,
               count(DISTINCT p.document_id) AS documents,
               count(DISTINCT CASE WHEN pp.citation_ready=1
                                      AND pp.needs_human_review=0
                                      AND pp.review_status='human_verified'
                                   THEN p.id END) AS citation_pages,
               count(DISTINCT CASE WHEN pp.citation_ready=1
                                      AND pp.needs_human_review=0
                                      AND pp.review_status='human_verified'
                                   THEN p.document_id END) AS citation_documents
        FROM research_events e
        JOIN pages p ON p.id=e.page_id
        LEFT JOIN page_provenance pp ON pp.page_id=p.id
        WHERE e.scope_type='topic' AND e.scope_slug=?
        """,
        (event_id,),
    ).fetchone()
    return {key: int(row[key] or 0) for key in row.keys()}


def foreign_metrics(conn: sqlite3.Connection, slug: str) -> dict[str, int]:
    row = conn.execute(
        """
        SELECT count(*) AS rows, count(DISTINCT page_id) AS pages
        FROM research_events
        WHERE scope_slug=?
        """,
        (slug,),
    ).fetchone()
    return {key: int(row[key] or 0) for key in row.keys()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--academic-crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    coverage = load_json(args.coverage)
    cards = {str(row["event_id"]): row for row in load_json(args.cards)}
    crosswalk = crosswalk_by_topic(args.academic_crosswalk)
    with sqlite3.connect(f"file:{args.db.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        topics = []
        for item in coverage:
            event_id = str(item["event_id"])
            domestic = event_metrics(conn, event_id)
            academic = crosswalk.get(event_id, {})
            foreign = {}
            for slug in item.get("foreign_event_slugs", []):
                metrics = foreign_metrics(conn, str(slug))
                foreign[str(slug)] = metrics
            academic_total = int(academic.get("matched_records") or 0)
            academic_sa = sum(int((academic.get("quality_tiers") or {}).get(tier) or 0) for tier in ("S", "A"))
            gaps = []
            if domestic["pages"] == 0:
                gaps.append("no_domestic_navigation_pages")
            if domestic["citation_pages"] == 0:
                gaps.append("no_strict_human_citation_page")
            if academic_total == 0:
                gaps.append("no_metadata_matched_academic_record")
            if not any(value["rows"] for value in foreign.values()):
                gaps.append("foreign_slug_not_in_shared_event_index")
            navigation_status = "navigation_ready" if not gaps else ("citation_gap" if domestic["pages"] and domestic["citation_pages"] == 0 else "navigation_gap")
            primary_status = str(item.get("primary_evidence_status") or "unclassified")
            topics.append(
                {
                    "event_id": event_id,
                    "event_name": item.get("event_name"),
                    "research_question": cards.get(event_id, {}).get("research_question"),
                    "domestic": domestic,
                    "academic": {
                        "metadata_matches": academic_total,
                        "S_A_matches": academic_sa,
                        "shown_record_ids": academic.get("shown_record_ids", []),
                    },
                    "foreign": foreign,
                    # Keep navigation and primary-source closure separate. A
                    # topic can be usable for discovery while still lacking
                    # the event-defining original document.
                    "status": navigation_status,
                    "navigation_ready": navigation_status == "navigation_ready",
                    "primary_evidence_status": primary_status,
                    "primary_evidence_label": item.get("primary_evidence_label", "一手证据状态未标注"),
                    "primary_evidence_gap": item.get("primary_evidence_gap", "覆盖表未提供一手证据闭环说明。"),
                    "research_ready": navigation_status == "navigation_ready" and primary_status == "closed",
                    "gaps": gaps,
                    "next_action": cards.get(event_id, {}).get("next_action", "")
                }
            )

        summary = {
            "topics": len(topics),
            # `research_ready` is intentionally strict: it no longer means
            # merely that a topic has navigation, academic metadata and one
            # strict page. The former broad count is exposed as
            # `navigation_ready` instead.
            "research_ready": sum(row["research_ready"] for row in topics),
            "navigation_ready": sum(row["navigation_ready"] for row in topics),
            "primary_evidence_partial": sum(row["primary_evidence_status"] == "partial" for row in topics),
            "primary_evidence_closed": sum(row["primary_evidence_status"] == "closed" for row in topics),
            "primary_evidence_unclassified": sum(row["primary_evidence_status"] == "unclassified" for row in topics),
            "citation_gap": sum(row["status"] == "citation_gap" for row in topics),
            "navigation_gap": sum(row["status"] == "navigation_gap" for row in topics),
            "topics_with_strict_citation": sum(row["domestic"]["citation_pages"] > 0 for row in topics),
            "topics_with_academic_match": sum(row["academic"]["metadata_matches"] > 0 for row in topics),
            "total_domestic_navigation_pages": sum(row["domestic"]["pages"] for row in topics),
            "total_strict_citation_pages": sum(row["domestic"]["citation_pages"] for row in topics),
            "total_academic_metadata_matches": sum(row["academic"]["metadata_matches"] for row in topics),
        }
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]

    report = {
        "report": "DOMESTIC_PARITY_MATRIX_20260813",
        "db_path": str(args.db),
        "body_read": False,
        "matching_basis": "research_events plus strict page_provenance gates plus metadata-only academic crosswalk",
        "integrity_check": integrity,
        "summary": summary,
        "topics": topics,
        "status": "PASS" if integrity == "ok" else "FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
