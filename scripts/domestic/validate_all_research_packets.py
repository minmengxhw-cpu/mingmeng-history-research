#!/usr/bin/env python3
"""Batch-validate all domestic topic research packets.

This is a metadata-only acceptance report. It checks every declared domestic
topic, page-level resolution, citation gates, database SHA, and the explicit
no-body-export boundary. It never writes to SQLite or copies page text.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app  # noqa: E402
from scripts.domestic.research_packet import build_research_packet  # noqa: E402
from scripts.domestic.validate_research_packet import validate_packet  # noqa: E402


def build_report() -> dict[str, object]:
    topics = app._research_topic_rows()
    rows: list[dict[str, object]] = []
    for topic in topics:
        event_id = str(topic["item"].get("event_id") or "")
        packet = build_research_packet(event_id)
        if packet is None:
            rows.append({"event_id": event_id, "status": "FAIL", "errors": ["packet not found"]})
            continue
        result = validate_packet(packet, event_id)
        counts = packet.get("counts") or {}
        scope = packet.get("scope") or {}
        result.update(
            {
                "event_name": packet.get("event_name"),
                "primary_evidence_status": scope.get("primary_evidence_status"),
                "primary_evidence_label": scope.get("primary_evidence_label"),
                "open_primary_targets": len(packet.get("open_primary_targets") or []),
                "evidence_chain_page_items": counts.get("evidence_chain_page_items", 0),
                "evidence_chain_strict_gate_passed": counts.get("evidence_chain_strict_gate_passed", 0),
                "linked_domestic_pages": counts.get("domestic_pages", 0),
                "linked_domestic_strict_pages": counts.get("domestic_strict_pages", 0),
                "topic_event_domestic_pages": counts.get("topic_event_domestic_pages", 0),
                "topic_event_domestic_file_backed_pages": counts.get(
                    "topic_event_domestic_file_backed_pages", 0
                ),
                "topic_event_domestic_strict_pages": counts.get(
                    "topic_event_domestic_strict_pages", 0
                ),
                "academic_candidates": counts.get("academic_candidates", 0),
                "foreign_machine_pages": counts.get("foreign_machine_pages", 0),
            }
        )
        rows.append(result)
    statuses = [str(row.get("status")) for row in rows]
    return {
        "schema_version": "domestic_research_packets_batch.v1",
        "scope": "formal_domestic_database_metadata_only",
        "body_read": False,
        "report_does_not_copy_page_text": True,
        "topic_count": len(rows),
        "packet_count": sum(status == "PASS" for status in statuses),
        "failed_packet_count": sum(status != "PASS" for status in statuses),
        "primary_evidence_partial_count": sum(
            row.get("primary_evidence_status") == "partial" for row in rows
        ),
        "research_ready_count": sum(
            row.get("primary_evidence_status") == "closed" for row in rows
        ),
        "database_sha256": next(
            (str(row.get("database_sha256")) for row in rows if row.get("database_sha256")),
            "",
        ),
        "topics": rows,
        "status": "PASS" if rows and all(status == "PASS" for status in statuses) else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "work" / "domestic" / "research_packets_batch" / "REPORT.json",
    )
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "topic_count", "packet_count", "failed_packet_count", "primary_evidence_partial_count",
        "research_ready_count", "status",
    )}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
