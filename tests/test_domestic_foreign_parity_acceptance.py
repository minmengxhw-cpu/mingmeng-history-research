from __future__ import annotations

from scripts.domestic.build_domestic_foreign_parity_acceptance import build_report


def test_domestic_foreign_parity_acceptance_separates_path_from_primary_closure():
    report = build_report()
    assert report["status"] == "PASS"
    assert report["research_content_status"] == "OPEN_PRIMARY_GAPS"
    assert report["body_read"] is False
    assert report["page_bodies_read"] is False
    assert report["formal_db_written"] is False
    assert report["summary"]["topics"] == 9
    assert report["summary"]["domestic_questions"] == 36
    assert report["summary"]["domestic_question_paths_ready"] == 36
    assert report["summary"]["topics_with_parity_path"] == 9
    assert report["summary"]["research_ready"] == 0
    assert report["summary"]["open_primary_targets"] > 0
