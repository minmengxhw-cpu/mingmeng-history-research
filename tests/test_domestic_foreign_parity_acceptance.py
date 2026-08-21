from __future__ import annotations

import json

import app
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


def test_parity_dashboard_renders_last_acceptance_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "REPORT.json"
    path.write_text(
        json.dumps(
            {
                "status": "PASS",
                "research_content_status": "OPEN_PRIMARY_GAPS",
                "summary": {
                    "domestic_question_paths_ready": 36,
                    "domestic_questions": 36,
                    "topics_with_parity_path": 9,
                    "research_ready": 0,
                    "topics": 9,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "DOMESTIC_FOREIGN_PARITY_ACCEPTANCE_REPORT_PATH", path)
    body = app.research_parity_page().decode("utf-8")
    assert "最近一次双侧研究路径回归" in body
    assert "国内问题路径 36/36" in body
    assert "内容状态 <code>OPEN_PRIMARY_GAPS</code>" in body
