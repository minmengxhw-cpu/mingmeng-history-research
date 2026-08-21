"""Regression checks for the metadata-only unified platform gate."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
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
    public_surface = report["checks"]["public_surface"]
    assert public_surface["status"] == "PASS"
    assert public_surface["route_count"] == 22
    assert public_surface["errors"] == []
    source_map_consistency = report["checks"]["source_map_status_consistency"]
    assert source_map_consistency["status"] == "PASS"
    assert source_map_consistency["checked_page_count"] > 0
    assert source_map_consistency["strict_claim_count"] > 0
    assert source_map_consistency["citation_claim_count"] > 0
    subtargets = report["checks"]["primary_subtarget_support"]
    assert subtargets["status"] == "PASS"
    assert subtargets["topic_count"] == 9
    assert subtargets["unit_count"] == 22
    assert subtargets["page_count"] == 85
    assert subtargets["unique_page_count"] == 85
    previews = report["checks"]["drnh_preview_event_map"]
    assert previews["status"] == "PASS"
    assert previews["event_count"] == 4
    assert previews["document_count"] == 11
    assert previews["preview_page_count"] == 21
    assert report["checks"]["research_question_benchmark"]["path_ready_count"] == 36
    fragments = report["checks"]["citation_fragment_ledger"]
    assert fragments["status"] == "PASS"
    assert fragments["fragment_count"] == 14
    assert fragments["fragment_citation_ready_count"] == 14
    assert fragments["page_citation_ready_count"] == 0
    assert fragments["formal_db_written_count"] == 0


def test_question_first_research_entry_covers_all_declared_questions():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        body = app.research_questions_page().decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "研究问题入口" in body
    assert "<b>36</b> 个问题" in body
    assert body.count("evidence-matrix-item") == 36
    assert "1941年前后是否已经形成可识别的组织与成立表达" in body
    assert "/research/domestic-1941-formation/packet" in body


def test_domestic_fragment_ledger_and_page_panel_keep_page_gate_separate():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        ledger = app.domestic_fragment_ledger_page({}).decode("utf-8")
        citation = app.citation_page(20911).decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "国内片段证据台账" in ledger
    assert "片段级可引用" in ledger
    assert "page_citation_ready=false" in ledger
    assert "政治協商會議會期中就政府改組問題爭執最久" in ledger
    assert "片段级证据（非整页引用）" in citation
    assert "政治協商會議會期中就政府改組問題爭執最久" in citation
    assert "整页正文仍未逐字校读" in citation


def test_verified_domestic_page_image_is_hash_bound_and_private():
    matched = app.domestic_page_image_file(1473)
    assert matched is not None
    image_path, content_type = matched
    assert image_path.is_file()
    assert content_type == "image/png"
    source = app.domestic_source_file(1473)
    assert source is not None
    source_path, source_type = source
    assert source_path.is_file()
    assert source_type == "application/pdf"
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        private_body = app.citation_page(1473).decode("utf-8")
        assert "/domestic/page-image/1473" in private_body
        assert "打开本机页图" in private_body
        assert "/domestic/source-file/1473" in private_body
        assert "打开本机原文件" in private_body
        app._request.public_mode = True
        public_body = app.citation_page(1473).decode("utf-8")
        assert "/domestic/page-image/1473" not in public_body
        assert "/domestic/source-file/1473" not in public_body
        assert "公开模式不可用" in public_body
    finally:
        app._request.public_mode = previous


def test_domestic_source_file_route_streams_private_and_blocks_public():
    class FakeRequest:
        def __init__(self, path):
            self.path = path
            self.headers = {}
            self.wfile = BytesIO()
            self.events = []

        def send_response(self, value):
            self.events.append(("status", value))

        def send_header(self, key, value):
            self.events.append((key, value))

        def end_headers(self):
            self.events.append(("end", None))

    previous = getattr(app._request, "public_mode", False)
    try:
        private = FakeRequest("/domestic/source-file/1473")
        app.Handler._do_GET_inner(private)
        assert ("status", 200) in private.events
        assert ("Content-Type", "application/pdf") in private.events
        assert private.wfile.getvalue()[:5] == b"%PDF-"

        public = FakeRequest("/domestic/source-file/1473?public=1")
        app.Handler._do_GET_inner(public)
        assert ("status", 302) in public.events
        assert ("Location", "/public") in public.events
    finally:
        app._request.public_mode = previous


def test_fragments_are_discoverable_from_unified_search_and_domestic_timeline():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        search = app.search("政府改组", platform="domestic").decode("utf-8")
        timeline = app.timeline(platform_slug="domestic").decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "国内片段级证据命中" in search
    assert "政治協商會議會期中就政府改組問題爭執最久" in search
    assert "片段级证据时间锚点" in timeline
    assert "1946（出版年锚点）" in timeline
    search_1949 = app.search("共同纲领", platform="domestic", year="1949").decode("utf-8")
    assert "共同纲领第一条开头" in search_1949
    assert "国家档案局官方影像第2图（印刷页54）" in search_1949
    search_1945 = app.search("大会宣言", platform="domestic", year="1945").decode("utf-8")
    assert "1945临时全国代表大会宣言题名身份" in search_1945
    assert "PDF 第 73 页（印刷页 65）" in search_1945
    search_1946 = app.search("李聞慘案前後", platform="domestic", year="1946").decode("utf-8")
    assert "1946年《光明報》李闻惨案前后的昆明题名身份" in search_1946
    assert "PDF 第 14 页（印刷页未登记）" in search_1946
    refuse_1946 = app.search("反對參加國大", platform="domestic", year="1946").decode("utf-8")
    assert "1946年《光明報》拒参国大社论题名身份" in refuse_1946
    assert "PDF 第 2 页（印刷页 2）" in refuse_1946
    search_1947_shanghai = app.search("民盟今日解散", platform="domestic", year="1947").decode("utf-8")
    assert "1947年《大公報》上海版民盟今日解散题名身份" in search_1947_shanghai
    assert "上海版试用数据库单页副本（PDF第1页；印刷版次未登记）" in search_1947_shanghai
    search_1947_tianjin = app.search("民盟宣布解散", platform="domestic", year="1947").decode("utf-8")
    assert "1947年《大公報》天津版民盟宣布解散题名身份" in search_1947_tianjin
    assert "天津版试用数据库单页副本（PDF第1页；印刷版次未登记）" in search_1947_tianjin
    assert "1945（文件日期锚点；1946汇编）" in timeline


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


def test_1941_catalogue_routes_do_not_claim_original_source_closure():
    source_map = json.loads(
        (ROOT / "data/domestic/1941_formation_source_map.json").read_text(encoding="utf-8")
    )
    sources = {str(source["source_id"]): source for source in source_map["sources"]}
    hku = sources["hku-guangmingbao-1941-microfilm"]
    lnu = sources["lnu-guangmingbao-1941-index"]
    assert hku["source_role"] == "university_catalogue_access_route"
    assert "1941-09-18至1941-12-12" in hku["access_note"]
    assert "With Gaps=Nil" in hku["access_note"]
    assert hku["page_records"][0]["citation_ready"] is False
    assert "目录确认馆藏范围" in hku["page_records"][0]["caveat"]
    assert lnu["page_records"][0]["status"] == "navigation_only"
    assert lnu["page_records"][0]["citation_ready"] is False


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


def test_public_domestic_intake_hides_local_paths_and_internal_field_names():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        body = app.domestic_authorized_intake_page().decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "公开模式隐藏本地路径" in body
    assert "/Users/" not in body
    assert "/private/" not in body
    assert "local_path" not in body
    assert "授权原件文件" in body


def test_public_domestic_views_hide_relative_artifact_paths():
    pages = {
        "domestic": lambda: app.domestic_page({}),
        "acquisition": lambda: app.domestic_acquisition_page(
            "domestic-1947-illegal-dissolution"
        ),
        "events": lambda: app.domestic_events_page(
            {"event": ["domestic-1947-illegal-dissolution"]}
        ),
        "sources": app.domestic_sources_page,
        "research": app.research_topics_page,
        "topic": lambda: app.research_topic_page(
            "domestic-1947-illegal-dissolution"
        ),
    }
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        for name, page in pages.items():
            body = page().decode("utf-8")
            assert "/Users/" not in body, name
            assert "/private/" not in body, name
            assert "data/domestic/" not in body, name
            assert "work/domestic/" not in body, name
            assert "source_file" not in body, name
            assert "local_path" not in body, name
    finally:
        app._request.public_mode = previous


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
    assert "可研究（带边界）" in body
    assert "尚未 research_ready" in body
    assert "严格页" in body
    assert "学术匹配" in body
    academic = app.domestic_academic_page().decode("utf-8")
    assert "高价值全文清单" in academic
    assert "中国民主同盟历史文献（1941—1949）" in academic
    assert "P0 稳定全文" in academic
    assert "正文未读取" in academic
    assert "专题回接" in academic
    assert "/research/domestic-1941-formation" in academic
    assert "一手证据部分闭环" in body
    assert "P0 仍待原件" in body
    assert "授权原件接收状态" in body
    assert "incoming 文件 0" in body
    assert "/domestic/intake" in body
    assert "/research/gaps" in body
    assert "/domestic/academic" in body
    assert "/domestic/search?scope=research" in body
    assert "学术资料层" in body
    assert "稳定全文" in body
    assert "/search" in body
    assert "platform" in body and "domestic" in body
    assert "1941年中国民主政团同盟成立" in body
    assert "1947" in body
    assert "1949年新政协" in body
    assert "正文已核验" not in body
    assert "primary_evidence_closed" not in body


def test_authorized_original_intake_page_is_honest_before_download(tmp_path, monkeypatch):
    previous = getattr(app._request, "public_mode", False)
    monkeypatch.setattr(
        app,
        "AUTHORIZED_ORIGINAL_INTAKE_REPORT_PATH",
        tmp_path / "missing" / "REPORT.json",
    )
    monkeypatch.setattr(
        app,
        "AUTHORIZED_ORIGINAL_INTAKE_MANIFEST_PATH",
        tmp_path / "missing" / "INTAKE_MANIFEST.jsonl",
    )
    app._request.public_mode = False
    try:
        body = app.domestic_authorized_intake_page().decode("utf-8")
    finally:
        app._request.public_mode = previous
    assert "授权原件接收前置门禁" in body
    assert "1947-10-27" in body
    assert "1947-11-06" in body
    assert "尚未运行接收检查" in body
    assert "不 OCR" in body
    assert "正式引用" in body
    assert "data/domestic/raw/authorized_originals/incoming" in body


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
