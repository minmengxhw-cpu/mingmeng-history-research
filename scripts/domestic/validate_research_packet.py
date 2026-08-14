#!/usr/bin/env python3
"""Validate one metadata-only domestic research packet.

The validator rebuilds the packet from the formal database and checks its
evidence boundaries.  It does not write to SQLite and does not export page
body text.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.domestic.research_packet import build_research_packet  # noqa: E402


def validate_packet(packet: dict[str, object], event_id: str) -> dict[str, object]:
    errors: list[str] = []
    audit = packet.get("audit") or {}
    if audit.get("body_text_included") is not False:
        errors.append("body_text_included must be false")
    if audit.get("ocr_text_included") is not False:
        errors.append("ocr_text_included must be false")
    if audit.get("translation_text_included") is not False:
        errors.append("translation_text_included must be false")
    if audit.get("verbatim_quote_included") is not False:
        errors.append("verbatim_quote_included must be false")
    if audit.get("research_matrix_body_text_included") is not False:
        errors.append("research_matrix_body_text_included must be false")
    matrix = packet.get("research_matrix") or {}
    matrix_questions = matrix.get("questions") if isinstance(matrix, dict) else []
    if not isinstance(matrix_questions, list):
        errors.append("research_matrix.questions must be a list")
        matrix_questions = []
    if len(matrix_questions) != audit.get("research_matrix_questions"):
        errors.append("research matrix question count mismatch")
    for question in matrix_questions:
        if question.get("body_text_included") is not False:
            errors.append(f"matrix question {question.get('id')} exports body text")
        if not question.get("id") or not question.get("question"):
            errors.append("matrix question missing id or question")
    chain = packet.get("evidence_chain") or {}
    rows = [row for values in chain.values() for row in values]
    counts = packet.get("counts") or {}
    if len(rows) != counts.get("evidence_chain_page_items"):
        errors.append("page item count mismatch")
    if sum(bool(row.get("resolved")) for row in rows) != counts.get("evidence_chain_resolved_page_items"):
        errors.append("resolved page count mismatch")
    if not audit.get("page_rows_all_resolved"):
        errors.append("not all evidence page rows resolved")
    topic_rows = packet.get("topic_event_pages") or []
    counts = packet.get("counts") or {}
    if len(topic_rows) != counts.get("topic_event_sample_rows"):
        errors.append("topic event sample count mismatch")
    for row in topic_rows:
        if row.get("body_text_included") is not False:
            errors.append(f"topic event page {row.get('page_id')} exports body text")
        if not row.get("page_id") or not row.get("reader_url"):
            errors.append("topic event row missing page link")
    for row in rows:
        if not row.get("page_id"):
            errors.append("evidence row missing page_id")
        if row.get("resolved") and not row.get("source_sha256"):
            errors.append(f"page {row.get('page_id')} missing source SHA256")
        if row.get("status") == "strict_citation" and not row.get("citation_gate_passed"):
            errors.append(f"page {row.get('page_id')} strict row failed citation gate")
        if row.get("body_text_included") is not False:
            errors.append(f"page {row.get('page_id')} exports body text")
    return {
        "event_id": event_id,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "counts": counts,
        "database_sha256": (packet.get("database") or {}).get("sha256", ""),
    }


def validate(event_id: str) -> dict[str, object]:
    packet = build_research_packet(event_id)
    if packet is None:
        return {"event_id": event_id, "status": "FAIL", "errors": ["packet not found"]}
    return validate_packet(packet, event_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_id")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.event_id)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
