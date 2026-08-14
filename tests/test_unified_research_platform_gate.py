"""Regression checks for the metadata-only unified platform gate."""

from __future__ import annotations

from scripts.domestic.validate_unified_research_platform import build_report


def test_unified_platform_gate_passes_without_claiming_content_closure():
    report = build_report()
    assert report["status"] == "PASS"
    assert report["research_content_status"] == "OPEN_PRIMARY_GAPS"
    assert report["body_read"] is False
    assert report["formal_db_written"] is False
    assert report["auto_delete"] is False
    assert report["failed_checks"] == []
    assert report["checks"]["candidate_alignment"]["missing_from_db"] == []
    assert report["checks"]["source_registry_alignment"]["file_count"] == 90
    assert report["checks"]["retrieval_queue"]["formal_candidate_count"] == 690
    assert report["checks"]["research_packets"]["topic_count"] == 9
    assert report["checks"]["research_question_benchmark"]["path_ready_count"] == 36
