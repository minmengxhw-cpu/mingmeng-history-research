#!/usr/bin/env python3
"""Build a metadata-only domestic/foreign research-path acceptance report.

This is the operational counterpart to the parity matrix. It exercises the
production domestic search path for declared research questions and checks
that every topic has a shared foreign event route, an academic crosswalk, a
four-layer evidence chain, and an explicit primary-source state.

Infrastructure parity is intentionally separate from historical source
closure: ``status=PASS`` means the shared paths are usable, while
``research_content_status=OPEN_PRIMARY_GAPS`` means an event-defining original
source is still missing for one or more topics.

The benchmark queries the existing search index but never copies page bodies,
changes SQLite, promotes citation states, or downloads external material.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app  # noqa: E402
from scripts.domestic.build_research_question_benchmark_20260814 import (  # noqa: E402
    build_report as build_question_report,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _foreign_page_count(topic: dict[str, object]) -> int:
    return sum(
        int((entry.get("stats") or {}).get("pages") or 0)
        for entry in topic.get("foreign_stats") or []
        if isinstance(entry, dict)
    )


def _foreign_route_count(topic: dict[str, object]) -> int:
    return sum(
        1
        for entry in topic.get("foreign_stats") or []
        if isinstance(entry, dict)
        and int((entry.get("stats") or {}).get("documents") or 0) > 0
    )


def build_report() -> dict[str, object]:
    question_report = build_question_report()
    checks_by_topic: dict[str, list[dict[str, object]]] = {}
    for check in question_report.get("checks") or []:
        if isinstance(check, dict):
            checks_by_topic.setdefault(str(check.get("event_id") or ""), []).append(check)

    topics = app._research_topic_rows()
    topic_rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    for topic in topics:
        item = topic.get("item") or {}
        event_id = str(item.get("event_id") or "")
        question_rows = checks_by_topic.get(event_id, [])
        question_path_ready = bool(question_rows) and all(
            row.get("path_status") == "research_path_ready" for row in question_rows
        )
        foreign_routes = _foreign_route_count(topic)
        foreign_pages = _foreign_page_count(topic)
        foreign_route_ready = foreign_routes > 0 and foreign_pages > 0
        crosswalk = topic.get("foreign_crosswalk") or {}
        crosswalk_ready = bool(crosswalk)
        chain = topic.get("evidence_chain_summary") or {}
        layer_count = int(chain.get("layer_count") or 0)
        topic_strict_pages = int(topic.get("topic_event_domestic_strict_pages") or 0)
        source_map = topic.get("event_source_map") or {}
        source_map_ready = bool(source_map.get("available")) and int(
            source_map.get("page_record_count") or 0
        ) > 0
        primary_status = str(item.get("primary_evidence_status") or "unclassified")

        parity_path_ready = all(
            (
                question_path_ready,
                foreign_route_ready,
                crosswalk_ready,
                layer_count == 4,
                topic_strict_pages > 0,
                source_map_ready,
            )
        )
        research_ready = parity_path_ready and primary_status == "closed"

        row = {
            "event_id": event_id,
            "event_name": item.get("event_name"),
            "question_count": len(question_rows),
            "question_path_ready": question_path_ready,
            "question_strict_query_count": sum(
                1 for check in question_rows if int(check.get("strict_citation_hits") or 0) > 0
            ),
            "domestic_pages": int(topic.get("topic_event_domestic_pages") or 0),
            "domestic_strict_pages": topic_strict_pages,
            "foreign_route_count": foreign_routes,
            "foreign_pages": foreign_pages,
            "academic_matches": int(topic.get("academic_total") or 0),
            "academic_crosswalk_ready": crosswalk_ready,
            "evidence_chain_layers": layer_count,
            "evidence_chain_page_items": int(chain.get("page_items") or 0),
            "open_primary_targets": int(chain.get("open_targets") or 0),
            "source_map_ready": source_map_ready,
            "primary_evidence_status": primary_status,
            "parity_path_ready": parity_path_ready,
            "research_ready": research_ready,
        }
        topic_rows.append(row)

        missing = [
            label
            for label, value in (
                ("domestic_question_path", question_path_ready),
                ("foreign_event_route", foreign_route_ready),
                ("academic_crosswalk", crosswalk_ready),
                ("four_layer_evidence_chain", layer_count == 4),
                ("domestic_strict_page", topic_strict_pages > 0),
                ("source_map", source_map_ready),
            )
            if not value
        ]
        if missing:
            failures.append({"event_id": event_id, "missing": missing})

    summary = {
        "topics": len(topic_rows),
        "domestic_questions": int(question_report.get("question_count") or 0),
        "domestic_question_paths_ready": int(question_report.get("path_ready_count") or 0),
        "topics_with_parity_path": sum(int(row["parity_path_ready"]) for row in topic_rows),
        "topics_with_foreign_route": sum(
            int(row["foreign_route_count"] > 0 and row["foreign_pages"] > 0)
            for row in topic_rows
        ),
        "topics_with_academic_crosswalk": sum(
            int(row["academic_crosswalk_ready"]) for row in topic_rows
        ),
        "topics_with_strict_domestic_support": sum(
            int(row["domestic_strict_pages"] > 0) for row in topic_rows
        ),
        "research_ready": sum(int(row["research_ready"]) for row in topic_rows),
        "open_primary_targets": sum(int(row["open_primary_targets"]) for row in topic_rows),
    }
    content_status = (
        "CLOSED"
        if summary["topics"] and summary["research_ready"] == summary["topics"]
        else "OPEN_PRIMARY_GAPS"
    )
    return {
        "schema_version": "domestic_foreign_parity_acceptance.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "formal_domestic_search_index_and_shared_foreign_event_metadata",
        "body_read": False,
        "page_bodies_read": False,
        "search_index_queried": True,
        "formal_db_written": False,
        "database": {"path": str(app.DB_PATH), "sha256": _sha256(app.DB_PATH)},
        "status": "PASS" if not failures else "FAIL",
        "research_content_status": content_status,
        "summary": summary,
        "topics": topic_rows,
        "failures": failures,
        "question_benchmark": {
            "question_count": question_report.get("question_count"),
            "path_ready_count": question_report.get("path_ready_count"),
            "strict_page_query_count": question_report.get("strict_page_query_count"),
            "strict_support_count": question_report.get("strict_support_count"),
            "failed_path_count": question_report.get("failed_path_count"),
        },
        "interpretation": {
            "PASS": "国内问题路径、海外对位入口、学术交叉、证据链和页级支持均具备结构化入口。",
            "OPEN_PRIMARY_GAPS": "结构可用不等于事件定义原件闭环；仍需按开放目标取得、核验和接入原件。",
            "research_ready": "只有 parity 路径完整且 primary_evidence_status=closed 才可成立。",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "research_content_status": report["research_content_status"],
                **report["summary"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
