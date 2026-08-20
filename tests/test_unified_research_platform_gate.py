"""Regression checks for the metadata-only unified platform gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import app
from scripts.domestic.validate_unified_research_platform import build_report


ROOT = Path(__file__).resolve().parents[1]


def test_unified_platform_gate_passes_without_claiming_content_closure():
    report = build_report()
    assert report["status"] == "PASS"
    assert report["research_content_status"] == "OPEN_PRIMARY_GAPS"
    assert report["body_read"] is False
    assert report["formal_db_written"] is False
    assert report["auto_delete"] is False
    assert report["failed_checks"] == []
    assert report["checks"]["candidate_alignment"]["missing_from_db"] == []
    registry = report["checks"]["source_registry_alignment"]
    assert registry["status"] == "PASS"
    assert registry["file_count"] == registry["db_count"]
    assert report["checks"]["academic_layer"]["crosswalk_topics"] == 9
    assert report["checks"]["academic_layer"]["scholarly_articles"] == 99
    assert report["checks"]["academic_layer"]["fulltext_priority_queue_records"] == 24
    assert report["checks"]["academic_layer"]["fulltext_priority_queue_classes"] == {
        "P0_STABLE_FULLTEXT": 5,
        "P1_FULLTEXT_CANDIDATE": 13,
        "P2_STABLE_CONTEXT": 1,
        "P3_CANDIDATE_CONTEXT": 5,
    }
    assert report["checks"]["retrieval_queue"]["formal_candidate_count"] == 690
    assert report["checks"]["pcc_1946_sourcebook_map"]["target_count"] == 6
    assert report["checks"]["pcc_1946_sourcebook_render_manifest"]["page_count"] == 9
    assert report["checks"]["pcc_1946_sourcebook_render_manifest"]["review_status"] == "page_identity_and_boundary_human_verified_body_ocr_pending"
    assert report["checks"]["research_packets"]["topic_count"] == 9
    assert report["checks"]["research_packets"]["research_usable_with_boundaries_count"] == 9
    assert report["checks"]["research_question_benchmark"]["path_ready_count"] == 36


def test_academic_gate_uses_tracked_snapshot_without_staging_report(tmp_path, monkeypatch):
    """清洁 checkout 缺 staging 审计报告时，门禁使用同一份元数据快照。"""
    import scripts.domestic.validate_unified_research_platform as gate

    monkeypatch.setattr(gate, "ACADEMIC_REPORT_PATH", tmp_path / "missing-report.json")
    result = gate.academic_layer_check()
    assert result["status"] == "PASS"
    assert result["source"] == "tracked_metadata_snapshot"
    assert result["records"] == 288
    assert result["academic_records"] == 155
    assert result["scholarly_articles"] == 99
    assert result["high_priority_academic_records_S_or_A"] == 120
    assert result["fulltext_priority_queue_records"] == 24


def test_external_navigation_sources_use_hashed_metadata_snapshots():
    source_map = json.loads(
        (ROOT / "data/domestic/1946_li_wen_source_map.json").read_text(encoding="utf-8")
    )
    sources = {
        str(source["source_id"]): source
        for source in source_map["sources"]
        if source.get("metadata_snapshot_file")
    }
    assert set(sources) == {
        "minmeng-yunnan-democracy-weekly-history",
        "jiuwenku-guangmingbao-1946-catalogue",
        "nlc-guangmingbao-1946-v8-li-wen",
    }
    for source in sources.values():
        snapshot = ROOT / source["metadata_snapshot_file"]
        digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        assert digest == source["metadata_snapshot_sha256"]


def test_domestic_search_shows_hit_reason_and_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        body = app.search("会刊", platform="domestic").decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "搜索：会刊" in body
    assert "国内史料" in body
    assert "命中理由" in body
    assert "/domestic/workbench" in body
    assert "/timeline?platform=domestic" in body
    assert "正式可引用" in body or "原件已锚定" in body or "证据待补" in body
    assert "正文已核验" not in body
    assert "primary_evidence_closed" not in body


def test_domestic_timeline_links_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        body = app.timeline(platform_slug="domestic").decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "国内史料 民盟材料年表" in body
    assert "/domestic/workbench" in body
    assert "/research/gaps" in body
    assert "国内年表" in body
    assert "正文已核验" not in body
    assert "primary_evidence_closed" not in body


def test_domestic_catalog_and_staging_search_jump_to_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        catalog = app.domestic_page({}).decode("utf-8")
        staging = app.domestic_staging_search_page({}).decode("utf-8")
    finally:
        app._request.public_mode = previous
    for body in (catalog, staging):
        assert "/domestic/workbench" in body
        assert "国内研究平台" in body
        assert "正文已核验" not in body
        assert "primary_evidence_closed" not in body


def test_domestic_nav_pages_jump_back_to_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        events = app.domestic_events_page({}).decode("utf-8")
        sources = app.domestic_sources_page().decode("utf-8")
        parity = app.research_parity_page().decode("utf-8")
    finally:
        app._request.public_mode = previous
    for body in (events, sources, parity):
        assert "/domestic/workbench" in body
        assert "国内研究平台" in body
        assert "正文已核验" not in body
        assert "primary_evidence_closed" not in body


def test_research_topic_page_jumps_back_to_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        body = app.research_topic_page("domestic-1949-new-pcc").decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "/domestic/workbench" in body
    assert "国内研究平台" in body
    assert "一手证据部分闭环" in body
    assert "正文已核验" not in body
    assert "primary_evidence_closed" not in body


def test_domestic_workbench_is_the_research_front_door():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        body = app.domestic_workbench_page().decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "国内民盟史研究平台" in body
    assert "导航可用" in body
    assert "一手证据部分闭环" in body
    assert "P0 仍待原件" in body
    assert "/research/gaps" in body
    assert "/search" in body
    assert "platform" in body and "domestic" in body
    assert "1941年中国民主政团同盟成立" in body
    assert "1947" in body
    assert "1949年新政协" in body
    assert "正文已核验" not in body
    assert "primary_evidence_closed" not in body


def test_1949_journal_routes_keep_page_identity_and_open_gap():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        topic = app.research_topic_page("domestic-1949-new-pcc").decode("utf-8")
        cite_ready = app.citation_page(20932).decode("utf-8")
        cite_draft = app.citation_page(20937).decode("utf-8")
        cite_blocked = app.citation_page(20938).decode("utf-8")
    finally:
        app._request.public_mode = previous

    assert "20932" in topic
    assert "会刊封面" in topic
    assert "开幕式程序" in topic
    assert "筹备会完整记录" in topic or "完整代表名册" in topic
    assert "一手证据部分闭环" in topic
    assert "正文已核验" not in topic
    assert "primary_evidence_closed" not in topic

    assert "引用摘录卡片" in cite_ready
    assert "正文/OCR未核验" in cite_ready
    assert "/domestic/workbench" in cite_ready
    assert "正文已核验" not in cite_ready
    assert "primary_evidence_closed" not in cite_ready

    assert "引用摘录卡片" in cite_draft
    assert "宣言草案" in cite_draft
    assert "正文/OCR未核验" in cite_draft
    assert "正文已核验" not in cite_draft

    assert "引用门禁未通过" in cite_blocked
    assert "review_only" in cite_blocked
    assert "正文已核验" not in cite_blocked
    assert "primary_evidence_closed" not in cite_blocked


def test_domestic_doc_reader_and_packet_link_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        with app.conn() as connection:
            row = connection.execute(
                """
                SELECT doc_key
                FROM documents
                WHERE source_platform='domestic'
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()
        assert row is not None
        reader = app.doc_page(row["doc_key"]).decode("utf-8")
        from scripts.domestic.research_packet import research_packet_page

        packet = research_packet_page("domestic-1947-illegal-dissolution").decode("utf-8")
        packets_index = app.research_packets_page().decode("utf-8")
    finally:
        app._request.public_mode = previous

    assert "/domestic/workbench" in reader
    assert "国内研究平台" in reader
    assert "正文已核验" not in reader
    assert "primary_evidence_closed" not in reader

    assert "/domestic/workbench" in packet
    assert "国内研究平台" in packet
    assert "正文未复制" in packet
    assert "一手证据仍开放" in packet or "开放目标" in packet
    assert "/research/gaps" in packet
    assert "/domestic/acquisition?event=domestic-1947-illegal-dissolution" in packet
    assert 'href="/cite/' in packet
    assert "正文已核验" not in packet
    assert "primary_evidence_closed" not in packet

    assert "/domestic/workbench" in packets_index
    assert "国内研究平台" in packets_index
    assert "正文已核验" not in packets_index
    assert "primary_evidence_closed" not in packets_index


def test_domestic_acquisition_and_review_link_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        acquisition = app.domestic_acquisition_page("domestic-1941-formation").decode("utf-8")
        review = app.domestic_review_page().decode("utf-8")
    finally:
        app._request.public_mode = previous

    assert "/domestic/workbench" in acquisition
    assert "国内研究平台" in acquisition
    assert "/research/gaps" in acquisition
    assert "专题原件目标" in acquisition
    assert "正文已核验" not in acquisition
    assert "primary_evidence_closed" not in acquisition

    assert "/domestic/workbench" in review
    assert "国内研究平台" in review
    assert "/research/gaps" in review
    assert "正文已核验" not in review
    assert "primary_evidence_closed" not in review


def test_domestic_academic_and_library_link_workbench():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        academic = app.domestic_academic_page().decode("utf-8")
        library = app.domestic_library_page({"layer": ["core"]}).decode("utf-8")
    finally:
        app._request.public_mode = previous

    assert "/domestic/workbench" in academic
    assert "国内研究平台" in academic
    assert "/research/gaps" in academic
    assert "解释层" in academic
    assert "正文已核验" not in academic
    assert "primary_evidence_closed" not in academic

    assert "/domestic/workbench" in library
    assert "国内研究平台" in library
    assert "/research/gaps" in library
    assert "正文已核验" not in library
    assert "primary_evidence_closed" not in library
