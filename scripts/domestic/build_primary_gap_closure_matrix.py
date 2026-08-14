#!/usr/bin/env python3
"""Build the machine-readable domestic primary-evidence gap matrix.

This report is deliberately metadata-only.  It joins the declared event
coverage, the primary retrieval queue, and the event source maps so that a
worker can see what remains to be acquired without mistaking navigation,
reprints, OCR drafts, or academic context for a closed primary source.

The report never reads page bodies, never downloads files, and never writes
to SQLite.  It is safe to regenerate after every staged acquisition batch.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE = ROOT / "data/domestic/event_coverage.json"
DEFAULT_QUEUE = ROOT / "data/domestic/primary_retrieval_queue.json"
DEFAULT_SOURCE_MAP_DIR = ROOT / "data/domestic"


PRIORITIES: dict[str, tuple[str, str]] = {
    "domestic-1941-formation": (
        "P0",
        "成立宣言和早期组织来源决定整个国内时间轴的起点。",
    ),
    "domestic-1947-illegal-dissolution": (
        "P0",
        "政府公函与解散公告是组织危机叙事的事件定义原件。",
    ),
    "domestic-1945-first-congress": (
        "P1",
        "大会政治报告、宣言和组织规程是组织制度史的核心底本。",
    ),
    "domestic-1946-pcc": (
        "P1",
        "正式会议记录和民盟代表发言需要与报刊、境外记录逐日对位。",
    ),
    "domestic-1946-refuse-national-assembly": (
        "P1",
        "拒参声明或函电决定政治立场能否以民盟自身文件引用。",
    ),
    "domestic-1946-li-wen": (
        "P1",
        "独立抗议、司法或行政档案可把报刊反应与事件过程分开。",
    ),
    "domestic-1944-reorganization": (
        "P2",
        "需要把改组会议、改名决定和同期刊物从后期汇编中拆出。",
    ),
    "domestic-1948-third-plenum-may-day": (
        "P2",
        "需将三中全会、五一口号和香港传播拆成独立证据单元。",
    ),
    "domestic-1949-new-pcc": (
        "P2",
        "已有公开影像入口，下一步是会议连续件、代表名册和民盟发言对位。",
    ),
}


CLOSURE_REQUIREMENTS: dict[str, list[str]] = {
    "domestic-1941-formation": [
        "original_periodical_or_archive_image",
        "catalogue_call_number_and_version_crosswalk",
        "page_level_visual_review",
    ],
    "domestic-1944-reorganization": [
        "reorganization_record_or_reliable_original",
        "contemporary_periodical_full_page",
        "reprint_to_original_version_crosswalk",
    ],
    "domestic-1945-first-congress": [
        "congress_record_or_reliable_base_text",
        "report_declaration_and_regulation_version_crosswalk",
        "page_level_missing_page_audit",
    ],
    "domestic-1946-pcc": [
        "formal_pcc_record",
        "date_axis_and_representative_identity_crosswalk",
        "page_level_speech_alignment",
    ],
    "domestic-1946-refuse-national-assembly": [
        "minmeng_statement_or_correspondence_original",
        "issuer_date_and_version_record",
        "contemporary_report_cross_check",
    ],
    "domestic-1946-li-wen": [
        "independent_statement_or_case_record",
        "contemporary_periodical_full_page",
        "event_date_and_actor_crosswalk",
    ],
    "domestic-1947-illegal-dissolution": [
        "government_letter_or_gazette_original",
        "minmeng_dissolution_notice_original",
        "date_actor_version_and_page_chain",
    ],
    "domestic-1948-third-plenum-may-day": [
        "archive_item_and_call_number",
        "three_plenary_meeting_unit",
        "may_day_release_and_propagation_crosswalk",
    ],
    "domestic-1949-new-pcc": [
        "continuous_preparatory_record",
        "complete_representative_roster_chain",
        "minmeng_speech_and_session_alignment",
    ],
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_map_for(source_map_dir: Path, event_id: str) -> tuple[Path, dict[str, Any]]:
    suffix = {
        "domestic-1941-formation": "1941_formation_source_map.json",
        "domestic-1944-reorganization": "1944_reorganization_source_map.json",
        "domestic-1945-first-congress": "1945_first_congress_source_map.json",
        "domestic-1946-pcc": "1946_old_pcc_source_map.json",
        "domestic-1946-refuse-national-assembly": "1946_refuse_national_assembly_source_map.json",
        "domestic-1946-li-wen": "1946_li_wen_source_map.json",
        "domestic-1947-illegal-dissolution": "1947_dissolution_source_map.json",
        "domestic-1948-third-plenum-may-day": "1948_third_plenum_mayday_source_map.json",
        "domestic-1949-new-pcc": "1949_new_pcc_source_map.json",
    }[event_id]
    path = source_map_dir / suffix
    return path, load(path)


def compact_route(route: dict[str, Any]) -> dict[str, Any]:
    """Keep the matrix actionable without copying large candidate records."""

    return {
        "candidate_id": route.get("candidate_id"),
        "title": route.get("title"),
        "route_status": route.get("route_status"),
        "route_label": route.get("route_label"),
        "authenticity_level": route.get("authenticity_level"),
        "evidence_type": route.get("evidence_type"),
        "access_mode": route.get("access_mode"),
        "target_match": route.get("target_match") is True,
        "route_score": route.get("route_score"),
        "formal_page_count": route.get("formal_page_count", 0),
        "body_read": route.get("body_read") is True,
    }


def build(coverage_path: Path, queue_path: Path, source_map_dir: Path) -> dict[str, Any]:
    coverage = load(coverage_path)
    queue = load(queue_path)
    if not isinstance(coverage, list) or not coverage:
        raise ValueError("event coverage must be a non-empty list")
    if not isinstance(queue, dict) or not isinstance(queue.get("topics"), list):
        raise ValueError("primary retrieval queue must contain a topics list")
    if queue.get("body_read") is not False:
        raise ValueError("queue body_read must remain false")
    if queue.get("formal_db_written") is not False:
        raise ValueError("queue formal_db_written must remain false")
    if queue.get("auto_promote_primary_closed") is not False:
        raise ValueError("queue auto_promote_primary_closed must remain false")

    coverage_by_id = {str(row["event_id"]): row for row in coverage}
    queue_by_id = {str(row["event_id"]): row for row in queue["topics"]}
    if set(coverage_by_id) != set(queue_by_id):
        raise ValueError("coverage and queue topic sets differ")

    topics: list[dict[str, Any]] = []
    route_statuses: Counter[str] = Counter()
    target_route_count = 0
    source_map_page_count = 0
    source_map_count = 0

    for event_id, coverage_row in coverage_by_id.items():
        queue_row = queue_by_id[event_id]
        map_path, source_map = source_map_for(source_map_dir, event_id)
        status = str(coverage_row.get("primary_evidence_status") or "unclassified")
        if status not in {"partial", "closed"}:
            raise ValueError(f"unsupported primary evidence status for {event_id}: {status}")
        if status == "partial" and source_map.get("primary_evidence_closed") is not False:
            raise ValueError(f"source map claims closure for open topic: {event_id}")

        routes = [row for row in queue_row.get("candidate_routes", []) if isinstance(row, dict)]
        for route in routes:
            route_statuses[str(route.get("route_status") or "UNCLASSIFIED")] += 1
        matched = [route for route in routes if route.get("target_match") is True]
        target_route_count += len(matched)
        matched.sort(key=lambda route: (int(route.get("route_score") or 0), str(route.get("candidate_id") or "")), reverse=True)

        sources = [row for row in source_map.get("sources", []) if isinstance(row, dict)]
        source_page_count = sum(len(row.get("page_records") or []) for row in sources)
        source_map_count += 1
        source_map_page_count += source_page_count
        source_levels = Counter(str(row.get("evidence_level") or "UNCLASSIFIED") for row in sources)

        open_targets = []
        for target in queue_row.get("missing_primary", []):
            if not isinstance(target, dict):
                continue
            open_targets.append({
                "target": target.get("target"),
                "why_it_matters": target.get("why_it_matters"),
                "status": target.get("status"),
                "retrieval_class": target.get("retrieval_class"),
                "next_action": target.get("next_action"),
                "candidate_route_count": target.get("candidate_route_count", len(routes)),
                "formal_page_count": target.get("formal_page_count", 0),
                "formal_strict_citation_page_count": target.get("formal_strict_citation_page_count", 0),
            })

        priority, rationale = PRIORITIES.get(event_id, ("P2", "未设置优先级，需在下一轮人工确认。"))
        topics.append({
            "event_id": event_id,
            "event_name": coverage_row.get("event_name"),
            "priority": priority,
            "priority_rationale": rationale,
            "primary_evidence_status": status,
            "primary_evidence_label": coverage_row.get("primary_evidence_label"),
            "primary_evidence_gap": coverage_row.get("primary_evidence_gap"),
            "open_target_count": len(open_targets),
            "open_targets": open_targets,
            "candidate_route_count": len(routes),
            "target_match_route_count": len(matched),
            "route_status_counts": dict(sorted(Counter(str(row.get("route_status") or "UNCLASSIFIED") for row in routes).items())),
            "priority_candidate_routes": [compact_route(row) for row in matched[:8]],
            "event_link_pages": int(queue_row.get("event_link_pages") and len(queue_row.get("event_link_pages")) or 0),
            "event_link_strict_page_count": int(queue_row.get("event_link_strict_page_count") or 0),
            "source_map": {
                "path": str(map_path.relative_to(ROOT)),
                "review_status": source_map.get("review_status"),
                "primary_evidence_closed": source_map.get("primary_evidence_closed"),
                "source_count": len(sources),
                "page_record_count": source_page_count,
                "evidence_level_counts": dict(sorted(source_levels.items())),
            },
            "minimum_closure_checks": CLOSURE_REQUIREMENTS.get(event_id, []),
            "body_read": False,
            "formal_db_written": False,
            "status": "closed" if status == "closed" else "open_primary_gap",
        })

    topics.sort(key=lambda row: (row["priority"], row["event_id"]))
    return {
        "schema": "domestic_primary_gap_closure_matrix.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "九个国内专题的主证据闭环执行矩阵",
        "body_read": False,
        "formal_db_written": False,
        "policy": "导航、汇编重刊、目录、OCR草稿和学术解释不自动关闭主证据缺口；每个升级必须保留来源、版本、页码、SHA256和复核边界。",
        "inputs": {
            "coverage": str(coverage_path.relative_to(ROOT)),
            "queue": str(queue_path.relative_to(ROOT)),
            "source_map_dir": str(source_map_dir.relative_to(ROOT)),
        },
        "summary": {
            "topic_count": len(topics),
            "open_primary_topics": sum(row["status"] == "open_primary_gap" for row in topics),
            "closed_primary_topics": sum(row["status"] == "closed" for row in topics),
            "open_target_count": sum(row["open_target_count"] for row in topics),
            "candidate_route_count": sum(row["candidate_route_count"] for row in topics),
            "target_match_route_count": target_route_count,
            "source_map_count": source_map_count,
            "source_map_page_record_count": source_map_page_count,
            "route_status_counts": dict(sorted(route_statuses.items())),
        },
        "topics": topics,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--source-map-dir", type=Path, default=DEFAULT_SOURCE_MAP_DIR)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.coverage, args.queue, args.source_map_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "status": report["status"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
