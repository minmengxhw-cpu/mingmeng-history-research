"""统一国内外专题入口的真实数据库冒烟测试。"""
from __future__ import annotations

import json
import hashlib
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest
import requests

from tests._http import fetch
from tests.conftest import DB_PATH


def test_research_topics_smoke(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证专题统计: {db_missing_reason}")
    status, body = fetch(live_server, "/research")
    assert status == 200
    assert body is not None
    assert "多源专题研究" in body
    assert "国内候选" in body
    assert "国内已入库文档" in body
    assert "机器命中" in body
    assert "证据链" in body
    assert "页级" in body
    assert "待补原件" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_research_gap_dashboard_smoke(live_server, db_missing_reason):
    """开放主证据目标必须能从专题索引进入执行看板。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内证据缺口看板: {db_missing_reason}")
    status, body = fetch(live_server, "/research/gaps")
    assert status == 200
    assert body is not None
    assert "国内一手证据收口看板" in body
    assert "9" in body
    assert "开放目标" in body
    assert "为什么重要" in body
    assert "下一步" in body
    assert "1941年中国民主政团同盟成立" in body
    assert "1949年新政协筹备" in body
    assert "专题详情" in body
    assert "官方数字影像可达，访客锁定" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_primary_evidence_access_audit_is_non_promoting():
    """Locked official viewers must remain weaker than local page provenance."""
    root = Path(__file__).resolve().parents[1]
    from scripts.domestic.validate_primary_evidence_access_audit import validate

    report = validate(
        root / "data/domestic/primary_evidence_access_audit.json",
        DB_PATH,
        root / "data/domestic/event_coverage.json",
    )
    assert report["status"] == "PASS"
    assert report["body_read"] is False
    assert report["records"] >= 1


def test_research_topic_detail_smoke(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证专题详情: {db_missing_reason}")
    status, body = fetch(live_server, "/research/domestic-1941-formation")
    assert status == 200
    assert body is not None
    assert "国内候选记录" in body
    assert "国内已入库证据样本" in body
    assert "引用门禁" in body
    assert "证据边界" in body
    assert "国内—境外对读卡" in body
    assert "学术解释层" in body
    assert "学术研究资料（解释层）" in body
    assert "一手对照" in body
    assert "一手证据部分闭环" in body
    assert "一手闭环缺口" in body
    assert "四层证据链" in body
    assert "研究问题—证据矩阵" in body
    assert "formation-organization-date" in body
    assert "/cite/1473" in body
    assert "国内—境外子问题对读" in body
    assert "暂无同命题境外专题" in body
    assert "打开研究包" in body
    assert "主证据（页级）" in body
    assert "同期交叉" in body
    assert "负向核查" in body
    assert "仍待补原件" in body
    assert "下一步核验" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_research_packet_is_metadata_only_and_page_traceable():
    """专题研究包必须可回链到页级证据，且不得复制正文。"""
    import app

    app._request.public_mode = False
    from scripts.domestic.research_packet import build_research_packet, packet_json_bytes, research_packet_page

    packet = build_research_packet("domestic-1945-first-congress")
    assert packet is not None
    assert packet["counts"]["evidence_chain_page_items"] == 40
    assert packet["counts"]["evidence_chain_resolved_page_items"] == 40
    assert packet["counts"]["evidence_chain_strict_gate_passed"] == 40
    assert packet["counts"]["topic_event_domestic_pages"] == 188
    assert packet["counts"]["topic_event_domestic_strict_pages"] == 40
    assert packet["counts"]["topic_event_sample_rows"] == 24
    assert all(row["body_text_included"] is False for row in packet["topic_event_pages"])
    assert packet["audit"]["body_text_included"] is False
    assert packet["audit"]["ocr_text_included"] is False
    assert packet["audit"]["verbatim_quote_included"] is False
    assert packet["audit"]["page_rows_all_resolved"] is True
    assert packet["audit"]["research_matrix_body_text_included"] is False
    assert packet["audit"]["research_matrix_questions"] == 4
    assert packet["audit"]["foreign_crosswalk_body_text_included"] is False
    assert packet["audit"]["foreign_crosswalk_questions"] == 4
    assert set(packet["foreign_crosswalk"]["questions"]) == {
        item["id"] for item in packet["research_matrix"]["questions"]
    }
    assert all(
        item["body_text_included"] is False
        for item in packet["foreign_crosswalk"]["questions"].values()
    )
    assert len(packet["research_matrix"]["questions"]) == 4
    assert all(item["body_text_included"] is False for item in packet["research_matrix"]["questions"])
    raw = packet_json_bytes("domestic-1945-first-congress").decode("utf-8")
    assert '"text"' not in raw
    assert "原文摘录：" not in raw
    assert "/cite/20149" in raw
    body = research_packet_page("domestic-1945-first-congress").decode("utf-8")
    assert "专题研究包" in body
    assert "正文未复制" in body
    assert "仍待补原件" in body
    assert "数据库 SHA256" in body
    assert "专题回接严格页" in body
    assert "专题事件索引页" in body
    assert "研究问题—证据矩阵" in body
    assert "国内—境外子问题对读" in body
    assert "专题回接" in body
    assert "原文摘录：" not in body
    assert "中文译文（" not in body


def test_topic_research_matrix_is_complete_and_page_traceable():
    """九个专题的研究矩阵必须覆盖四个子问题且只引用已有链条页号。"""
    root = Path(__file__).resolve().parents[1]
    matrix = json.loads((root / "data/domestic/topic_research_matrix.json").read_text(encoding="utf-8"))
    chains = json.loads((root / "data/domestic/topic_evidence_chain.json").read_text(encoding="utf-8"))
    chain_by_id = {item["event_id"]: item for item in chains}
    assert matrix["status"] == "metadata_only"
    assert matrix["body_read_by_builder"] is False
    assert len(matrix["topics"]) == 9
    assert all(len(item["questions"]) == 4 for item in matrix["topics"])
    for topic in matrix["topics"]:
        chain_pages = {
            int(item["page_id"])
            for values in chain_by_id[topic["event_id"]]["layers"].values()
            if isinstance(values, list)
            for item in values
            if isinstance(item, dict) and item.get("page_id") is not None
        }
        for question in topic["questions"]:
            assert question["id"]
            assert question["question"]
            assert question["evidence_scope"]
            assert question["caveat"]
            assert question["next_action"]
            assert set(question["evidence_page_ids"]) | set(question["negative_page_ids"]) <= chain_pages
            assert question.get("body_text_included") is not True


def test_topic_foreign_crosswalk_is_complete_and_explicit():
    """每个国内子问题必须显式声明境外关系，缺少对应项也要写明。"""
    root = Path(__file__).resolve().parents[1]
    matrix = json.loads((root / "data/domestic/topic_research_matrix.json").read_text(encoding="utf-8"))
    crosswalk = json.loads((root / "data/domestic/topic_foreign_crosswalk.json").read_text(encoding="utf-8"))
    question_ids = {q["id"] for topic in matrix["topics"] for q in topic["questions"]}
    assert crosswalk["status"] == "metadata_only"
    assert crosswalk["body_read_by_builder"] is False
    assert set(crosswalk["questions"]) == question_ids
    allowed = set(crosswalk["relationship_labels"])
    for item in crosswalk["questions"].values():
        assert item["relationship"] in allowed
        assert item["scope"]
        assert item["caveat"]
        assert all(isinstance(slug, str) and slug for slug in item["foreign_routes"])

    import app

    for slug in {
        slug
        for item in crosswalk["questions"].values()
        for slug in item["foreign_routes"]
    }:
        assert app._research_foreign_definition(slug) is not None, slug


def test_li_wen_packet_exposes_official_compilation_entries_without_promoting_them():
    """李闻专题应能回链官方汇编声明页，但不能把 machine_verified 当成严格引用。"""
    import app

    app._request.public_mode = False
    from scripts.domestic.research_packet import build_research_packet, packet_json_bytes

    packet = build_research_packet("domestic-1946-li-wen")
    assert packet is not None
    assert packet["counts"]["evidence_chain_page_items"] == 5
    assert packet["counts"]["evidence_chain_resolved_page_items"] == 5
    assert packet["counts"]["evidence_chain_strict_gate_passed"] == 1
    assert [row["page_id"] for row in packet["evidence_chain"]["primary"]] == [18936, 18945, 18948]
    assert all(row["status"] == "review_only" for row in packet["evidence_chain"]["primary"])
    assert packet["audit"]["body_text_included"] is False
    assert packet["audit"]["ocr_text_included"] is False
    raw = packet_json_bytes("domestic-1946-li-wen").decode("utf-8")
    assert '"text"' not in raw
    assert "/Users/" not in raw


def test_formation_packet_exposes_continuous_verified_pages():
    """1941成立专题应同时展示成立宣言连续页和早期政治主张页。"""
    import app

    app._request.public_mode = False
    from scripts.domestic.research_packet import build_research_packet, packet_json_bytes

    packet = build_research_packet("domestic-1941-formation")
    assert packet is not None
    assert packet["counts"]["evidence_chain_page_items"] == 6
    assert packet["counts"]["evidence_chain_resolved_page_items"] == 6
    assert packet["counts"]["evidence_chain_strict_gate_passed"] == 5
    assert [row["page_id"] for row in packet["evidence_chain"]["primary"]] == [1473, 1474, 1475]
    assert [row["page_id"] for row in packet["evidence_chain"]["cross_source"][:2]] == [1476, 1477]
    raw = packet_json_bytes("domestic-1941-formation").decode("utf-8")
    assert '"text"' not in raw
    assert "/Users/" not in raw


def test_research_packet_route_and_json(live_server, db_missing_reason):
    """研究包页面和 JSON 下载路由必须从真实 HTTP 入口可用。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证专题研究包路由: {db_missing_reason}")
    status, body = fetch(live_server, "/research/domestic-1945-first-congress/packet")
    assert status == 200
    assert body is not None
    assert "专题研究包" in body
    assert "正文未复制" in body
    assert "下载 JSON" in body
    assert "Traceback" not in body and "Internal Server Error" not in body
    status, body = fetch(live_server, "/research/domestic-1945-first-congress/packet.json")
    assert status == 200
    assert body is not None
    packet = json.loads(body)
    assert packet["event_id"] == "domestic-1945-first-congress"
    assert packet["audit"]["body_text_included"] is False
    assert '"text"' not in body


def test_all_research_packets_index(live_server, db_missing_reason):
    """九个专题必须有统一的研究包索引入口。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证全部专题研究包: {db_missing_reason}")
    status, body = fetch(live_server, "/research/packets")
    assert status == 200
    assert body is not None
    assert "全部专题研究包" in body
    assert body.count("研究包可生成") == 9
    assert "正文不复制" in body
    assert "专题回接" in body
    assert "1945年民盟第一次全国代表大会" in body
    assert "1946年李公朴、闻一多遇害及各方反应" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_all_research_packets_batch_validator(tmp_path):
    """批量研究包验收必须覆盖九个专题且不复制正文。"""
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "research-packets.json"
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/domestic/validate_all_research_packets.py"),
            "--output",
            str(output),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["topic_count"] == 9
    assert report["packet_count"] == 9
    assert report["failed_packet_count"] == 0
    assert report["research_ready_count"] == 0
    assert report["body_read"] is False
    assert report["report_does_not_copy_page_text"] is True
    assert all(
        "topic_event_domestic_strict_pages" in topic
        for topic in report["topics"]
    )


def test_domestic_academic_layer_smoke(live_server):
    status, body = fetch(live_server, "/domestic/academic")
    assert status == 200
    assert body is not None
    assert "国内学术研究层" in body
    assert "学术研究用于解释" in body or "学术研究作为解释层" in body
    assert "citation-ready" in body
    assert "学术—专题交叉索引" in body
    assert "1941年中国民主政团同盟成立" in body
    assert "正文读取：false" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_domestic_platform_and_timeline_smoke(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内平台年表: {db_missing_reason}")
    status, body = fetch(live_server, "/sources/domestic")
    assert status == 200
    assert body is not None
    assert "国内研究平台" in body
    assert "国内史料层" in body

    status, body = fetch(live_server, "/timeline?platform=domestic")
    assert status == 200
    assert body is not None
    assert "国内史料" in body
    assert "国内" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_unified_search_labels_domestic_evidence(live_server, db_missing_reason):
    """统一搜索中的国内命中必须显示来源层和页级证据状态。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证统一国内搜索: {db_missing_reason}")
    status, body = fetch(live_server, "/search?q=%E6%B0%91%E7%9B%9F&platform=domestic")
    assert status == 200
    assert body is not None
    assert "搜索：民盟" in body
    assert "国内史料" in body
    assert any(
        label in body
        for label in ("正式可引用", "机器可阅", "原件已锚定 · 待复核", "证据待补")
    )
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_domestic_strict_citation_uses_domestic_provenance_format(live_server, db_missing_reason):
    """国内正式页必须导出国内来源链，而不是套用 FRUS 书目模板。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内正式引用卡: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT pp.page_id
            FROM page_provenance pp
            JOIN pages p ON p.id=pp.page_id
            JOIN documents d ON d.id=p.document_id
            WHERE d.source_platform='domestic'
              AND pp.citation_ready=1
              AND pp.needs_human_review=0
              AND pp.review_status='human_verified'
              AND trim(COALESCE(pp.human_review_note,''))<>''
            ORDER BY pp.page_id
            LIMIT 1
            """
        ).fetchone()
    assert row is not None
    status, body = fetch(live_server, f"/cite/{row[0]}")
    assert status == 200
    assert body is not None
    assert "国内页级 provenance" in body
    assert "来源文件 SHA256" in body
    assert "PDF 第" in body
    assert "human_verified" in body
    assert "Foreign Relations of the United States" not in body
    assert "引用摘录卡片" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_domestic_document_entry_uses_domestic_citation_boundary(live_server, db_missing_reason):
    """国内文档总页不能把文献级入口误写成 FRUS 引用。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内文档入口: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """SELECT d.doc_key
               FROM documents d
               JOIN pages p ON p.document_id=d.id
               JOIN page_provenance pp ON pp.page_id=p.id
               WHERE d.source_platform='domestic'
                 AND pp.citation_ready=1
                 AND pp.review_status='human_verified'
               ORDER BY p.id
               LIMIT 1"""
        ).fetchone()
    assert row is not None
    status, body = fetch(live_server, f"/doc/{quote(row[0], safe='')}")
    assert status == 200
    assert body is not None
    assert "国内史料入口（页级引用）" in body
    assert "文献级来源入口" in body
    assert "正式可引用" in body
    assert "Foreign Relations of the United States" not in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_minxian_contents_citation_is_scope_limited(live_server, db_missing_reason):
    """目录页只开放刊期/日期/页码身份，不把未校勘 OCR 导出成逐字引文。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证《民憲》目录页引用范围: {db_missing_reason}")
    status, body = fetch(live_server, "/cite/20290")
    assert status == 200
    assert body is not None
    assert "机器识别内容（仅供定位，不作逐字引文）" in body
    assert "证据范围：本页人工复核仅覆盖刊名、卷期、出版日、目录页身份及页码锚点。" in body
    assert "原文摘录：" not in body
    assert "来源文件 SHA256" in body
    assert "PDF 第 2 页" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_guangmingbao_issue_identity_citation_is_scope_limited(live_server, db_missing_reason):
    """同期报刊页只开放刊期、日期、页码、版面和题名身份，不导出未校勘正文。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证《光明報》1946年新七號引用范围: {db_missing_reason}")
    status, body = fetch(live_server, "/cite/16351")
    assert status == 200
    assert body is not None
    assert "机器识别内容（仅供定位，不作逐字引文）" in body
    assert "证据范围：本页人工复核仅覆盖刊名、期号、出版日、PDF 页码、版面及社论题名。" in body
    assert "目录页身份及页码锚点" not in body
    assert "原文摘录：" not in body
    assert "来源文件 SHA256" in body
    assert "PDF 第 1 页" in body
    assert "Traceback" not in body


def test_minmeng_compiled_1944_text_citation_is_scope_limited(live_server, db_missing_reason):
    """官方汇编中的1944文本只开放题名、日期和页码身份，不输出未校勘正文。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证1944汇编页引用范围: {db_missing_reason}")
    status, body = fetch(live_server, "/cite/20141")
    assert status == 200
    assert body is not None
    assert "机器识别内容（仅供定位，不作逐字引文）" in body
    assert "官方汇编中的 1944 文本" in body
    assert "原文摘录：" not in body
    assert "中文译文 ·" not in body
    assert "来源文件 SHA256" in body
    assert "PDF 第 22 页" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_minmeng_compiled_1945_text_citation_is_scope_limited(live_server, db_missing_reason):
    """官方汇编中的1945文本只开放题名、日期和页码身份，不输出未校勘正文。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证1945汇编页引用范围: {db_missing_reason}")
    status, body = fetch(live_server, "/cite/20149")
    assert status == 200
    assert body is not None
    assert "机器识别内容（仅供定位，不作逐字引文）" in body
    assert "官方汇编中的 1945 文本" in body
    assert "官方汇编中的 1944 文本" not in body
    assert "原文摘录：" not in body
    assert "中文译文 ·" not in body
    assert "来源文件 SHA256" in body
    assert "PDF 第 48 页" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_domestic_non_strict_citation_stays_blocked(live_server, db_missing_reason):
    """国内未通过人工门禁的页仍只能阅读，不能生成引用卡。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内引用门禁: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT p.id
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE d.source_platform='domestic'
              AND COALESCE(pp.citation_ready,0)=0
            ORDER BY p.id
            LIMIT 1
            """
        ).fetchone()
    assert row is not None
    status, body = fetch(live_server, f"/cite/{row[0]}")
    assert status == 200
    assert body is not None
    assert "引用门禁未通过" in body
    assert "不生成正式引文" in body
    assert "国内页级 provenance" not in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_drnh_preview_is_not_presented_as_citable_original(live_server, db_missing_reason):
    """DRNH 水印/锁定图必须在阅读页也保持预览与正文的证据边界。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证 DRNH 预览边界: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT d.doc_key
            FROM documents d
            JOIN drnh_images i ON i.document_id=d.id
            WHERE d.source_platform='drnh'
            ORDER BY d.id
            LIMIT 1
            """
        ).fetchone()
    assert row is not None
    status, body = fetch(live_server, f"/doc/{quote(row[0], safe='')}")
    assert status == 200
    assert body is not None
    assert "国史馆官方访客预览" in body
    assert "目录卡片（非正文）" in body
    assert "不可直接引用" in body
    assert "点击查看无水印原图" not in body
    assert "台北档案史料原档释读" not in body
    assert "Traceback" not in body


def test_drnh_preview_image_uses_database_sibling_asset_root(live_server, db_missing_reason):
    """外置正式库旁的数据盘影像也必须能被安全地预览。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证 DRNH 影像资产路径: {db_missing_reason}")
    import app

    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT d.doc_key, i.file_path
            FROM documents d
            JOIN drnh_images i ON i.document_id=d.id
            WHERE d.source_platform='drnh'
            ORDER BY d.id, i.page_num
            LIMIT 1
            """
        ).fetchone()
    assert row is not None
    doc_key, file_path = row
    image_name = Path(file_path).name
    safe_doc_key = str(doc_key).replace(":", "__").replace("/", "_")
    alternate_name = safe_doc_key.removeprefix("drnh__")
    image_exists = any(
        (root / name / image_name).is_file()
        for root in app.drnh_image_roots()
        for name in {safe_doc_key, alternate_name}
    )
    if not image_exists:
        pytest.skip("当前机器只有 DRNH 数据库索引，没有对应本地访客影像文件")

    response = requests.get(
        f"{live_server}/drnh-img/{quote(str(doc_key), safe='')}/{quote(image_name, safe='')}",
        timeout=10,
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("image/jpeg")
    assert response.content[:2] == b"\xff\xd8"


def test_drnh_catalogue_card_citation_is_blocked(live_server, db_missing_reason):
    """DRNH 目录卡不能绕过页级人工复核门禁生成正式引文。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证 DRNH 引用门禁: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT p.id
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            WHERE d.source_platform='drnh' AND p.page_label='catalogue-card'
            ORDER BY p.id
            LIMIT 1
            """
        ).fetchone()
    assert row is not None
    status, body = fetch(live_server, f"/cite/{row[0]}")
    assert status == 200
    assert body is not None
    assert "DRNH 引用门禁未通过" in body
    assert "目录卡片/访客预览（不可直接引用）" in body
    assert "引用摘录卡片" not in body
    assert "Traceback" not in body


def test_domestic_event_index_smoke(live_server, db_missing_reason):
    """国内专题可以进入与境外专题相同的事件线索页。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内事件索引: {db_missing_reason}")
    status, body = fetch(live_server, "/events?topic=domestic-1941-formation")
    assert status == 200
    assert body is not None
    assert "1941年中国民主政团同盟成立事件线索" in body
    assert "国内关联来自声明式覆盖表" in body
    assert "国内原始入口" in body
    assert "证据复核" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_domestic_event_index_links_only_domestic_pages(db_missing_reason):
    """共享事件表的国内专题行必须只指向国内正式页，且覆盖九个专题。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法核对国内事件索引: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        scopes, rows, pages, bad = connection.execute(
            """
            SELECT
                COUNT(DISTINCT e.scope_slug),
                COUNT(*),
                COUNT(DISTINCT e.page_id),
                SUM(CASE WHEN d.source_platform <> 'domestic' THEN 1 ELSE 0 END)
            FROM research_events e
            JOIN pages p ON p.id=e.page_id
            JOIN documents d ON d.id=p.document_id
            WHERE e.scope_slug LIKE 'domestic-%'
            """
        ).fetchone()
    assert scopes == 9
    assert rows >= 400
    assert pages >= 400
    assert bad == 0


def test_domestic_candidate_detail_is_traceable(live_server, db_missing_reason):
    """候选目录必须能进入集中展示来源链、权利和复核状态的详情页。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内候选详情: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        candidate_id = connection.execute(
            "SELECT candidate_id FROM domestic_candidates ORDER BY id LIMIT 1"
        ).fetchone()[0]
    status, body = fetch(live_server, f"/domestic/candidate/{quote(candidate_id, safe='')}")
    assert status == 200
    assert body is not None
    assert "形成与目录" in body
    assert "获取与权利" in body
    assert "证据边界" in body
    assert candidate_id in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_public_mode_hides_internal_candidate_detail(live_server, db_missing_reason):
    """公开模式不能通过直接猜 URL 读取 L4/LX 内部线索详情。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证公开模式: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT candidate_id FROM domestic_candidates WHERE authenticity_level_proposed IN ('L4', 'LX') ORDER BY id LIMIT 1"
        ).fetchone()
    if row is None:
        pytest.skip("没有 L4/LX 候选可用于公开模式边界测试")
    candidate_id = row[0]
    status, body = fetch(live_server, f"/domestic/candidate/{quote(candidate_id, safe='')}?public=1")
    assert status == 200
    assert body is not None
    assert "国内候选未找到" in body
    assert candidate_id not in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_public_mode_blocks_unlinked_domestic_document_and_citation(live_server, db_missing_reason):
    """公开模式不能绕过候选门禁直达未授权的国内正文或摘录页。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证国内正文公开门禁: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """SELECT d.doc_key, p.id
               FROM documents d JOIN pages p ON p.document_id=d.id
               LEFT JOIN domestic_candidates c ON c.ingested_document_id=d.id
               WHERE d.source_platform='domestic' AND c.id IS NULL
               ORDER BY d.id, p.id LIMIT 1"""
        ).fetchone()
    if row is None:
        pytest.skip("没有未关联候选的国内文档可用于公开门禁测试")
    doc_key, page_id = row
    status, body = fetch(live_server, f"/doc/{quote(doc_key, safe='')}?public=1")
    assert status == 200
    assert body is not None
    assert "公开模式不可用" in body
    status, body = fetch(live_server, f"/cite/{page_id}?public=1")
    assert status == 200
    assert body is not None
    assert "公开模式不可用" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_event_coverage_has_no_dangling_links(db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法核对专题覆盖: {db_missing_reason}")
    coverage_path = Path(__file__).resolve().parents[1] / "data" / "domestic" / "event_coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    assert len(coverage) == 9
    assert len({item["event_id"] for item in coverage}) == len(coverage)
    with sqlite3.connect(DB_PATH) as connection:
        candidate_ids = {
            row[0] for row in connection.execute("SELECT candidate_id FROM domestic_candidates")
        }
    dangling_candidates = sorted(
        candidate_id
        for item in coverage
        for candidate_id in item.get("domestic_candidate_ids", [])
        if candidate_id not in candidate_ids
    )
    assert not dangling_candidates
    from app import event_by_slug, topic_by_slug

    dangling_foreign = sorted(
        slug
        for item in coverage
        for slug in item.get("foreign_event_slugs", [])
        if not (event_by_slug(slug) or topic_by_slug(slug))
    )
    assert not dangling_foreign


def test_topic_evidence_chain_is_page_traceable(db_missing_reason):
    """四层证据链的页级条目必须回到正式库同一文档和严格门禁。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法核对专题证据链: {db_missing_reason}")
    chain_path = Path(__file__).resolve().parents[1] / "data" / "domestic" / "topic_evidence_chain.json"
    chains = json.loads(chain_path.read_text(encoding="utf-8"))
    assert len(chains) == 9
    assert len({item["event_id"] for item in chains}) == 9
    expected_layers = {"primary", "cross_source", "negative_checks", "missing_primary"}
    with sqlite3.connect(DB_PATH) as connection:
        for chain in chains:
            assert set(chain["layers"]) == expected_layers
            assert chain["layers"]["missing_primary"]
            for layer, items in chain["layers"].items():
                for item in items:
                    if "page_id" not in item:
                        continue
                    row = connection.execute(
                        """SELECT d.doc_key, pp.review_status, pp.citation_ready,
                                  pp.needs_human_review
                           FROM pages p JOIN documents d ON d.id=p.document_id
                           LEFT JOIN page_provenance pp ON pp.page_id=p.id
                           WHERE p.id=?""",
                        (item["page_id"],),
                    ).fetchone()
                    assert row is not None, (chain["event_id"], layer, item["page_id"])
                    assert row[0] == item["doc_key"]
                    if item["status"] == "strict_citation":
                        assert row[1:] == ("human_verified", 1, 0)

    dissolution = next(item for item in chains if item["event_id"] == "domestic-1947-illegal-dissolution")
    assert len(dissolution["layers"]["primary"]) >= 3
    assert len(dissolution["layers"]["negative_checks"]) >= 2
    assert any("1947-10-27政府公函" in item["target"] for item in dissolution["layers"]["missing_primary"])


def test_topic_comparison_cards_complete():
    root = Path(__file__).resolve().parents[1]
    coverage = json.loads((root / "data/domestic/event_coverage.json").read_text(encoding="utf-8"))
    cards = json.loads((root / "data/domestic/topic_comparison_cards.json").read_text(encoding="utf-8"))
    coverage_ids = {item["event_id"] for item in coverage}
    card_ids = {item["event_id"] for item in cards}
    required = {"research_question", "academic_terms", "domestic_anchor", "foreign_anchor", "difference", "boundary", "next_action", "academic_use"}
    assert coverage_ids == card_ids
    assert len(cards) == 9
    for card in cards:
        assert required <= set(card)
        assert isinstance(card["academic_terms"], list) and card["academic_terms"]
        assert all(str(card[field]).strip() for field in required)
        assert "不能" in card["boundary"] or "不得" in card["boundary"]


def test_primary_evidence_status_is_explicit():
    """专题导航不能把页级入口自动升级成一手原件闭环。"""
    root = Path(__file__).resolve().parents[1]
    coverage = json.loads((root / "data/domestic/event_coverage.json").read_text(encoding="utf-8"))
    assert len(coverage) == 9
    assert all(item.get("primary_evidence_status") in {"partial", "closed"} for item in coverage)
    assert all(str(item.get("primary_evidence_label")).strip() for item in coverage)
    assert all(str(item.get("primary_evidence_gap")).strip() for item in coverage)
    assert sum(item["primary_evidence_status"] == "partial" for item in coverage) == 9


def test_parity_matrix_separates_navigation_from_primary_closure(tmp_path):
    """可导航专题与已完成一手闭环专题必须是两个独立统计。"""
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "parity.json"
    command = [
        sys.executable,
        str(root / "scripts/domestic/build_domestic_parity_matrix_20260813.py"),
        "--output",
        str(output),
    ]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    summary = report["summary"]
    assert summary["navigation_ready"] == 9
    assert summary["research_ready"] == 0
    assert summary["primary_evidence_partial"] == 9
    assert summary["evidence_chain_ready"] == 9
    assert summary["evidence_chain_page_items"] == 93
    assert summary["evidence_chain_strict_items"] == 82
    assert summary["evidence_chain_open_targets"] == 9
    assert all(row["navigation_ready"] for row in report["topics"])
    assert all(row["evidence_chain_ready"] for row in report["topics"])
    assert all(not row["research_ready"] for row in report["topics"])


def test_evidence_chain_validator_is_reproducible(tmp_path):
    """独立证据链校验器必须能从当前正式库重算 PASS。"""
    root = Path(__file__).resolve().parents[1]
    report_path = tmp_path / "evidence-chain.json"
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/domestic/validate_topic_evidence_chain.py"),
            "--report",
            str(report_path),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["topics"] == report["chains"] == 9
    assert report["page_items"] == 93
    assert report["strict_citation_items"] == 82


def test_high_value_reviewed_pages_are_reconnected_without_primary_upgrade():
    """本轮精选页必须可回链，但不能把汇编/报刊页升级成事件定义原件。"""
    root = Path(__file__).resolve().parents[1]
    chains = json.loads((root / "data/domestic/topic_evidence_chain.json").read_text(encoding="utf-8"))
    expected = {
        "domestic-1945-first-congress": {1501, 1502, 1503, 1504},
        "domestic-1946-pcc": {1512, 1513, 1514, 1515, 1516},
        "domestic-1947-illegal-dissolution": {1583, 1584},
    }
    for event_id, page_ids in expected.items():
        chain = next(item for item in chains if item["event_id"] == event_id)
        cross = {item["page_id"]: item for item in chain["layers"]["cross_source"]}
        assert page_ids <= set(cross)
        assert all(cross[page_id]["status"] == "strict_citation" for page_id in page_ids)
        assert all(
            any(term in cross[page_id]["caveat"] for term in ("不替代", "不是", "不等同", "不得据此"))
            for page_id in page_ids
        )
    coverage = json.loads((root / "data/domestic/event_coverage.json").read_text(encoding="utf-8"))
    assert all(item["primary_evidence_status"] == "partial" for item in coverage)


def test_1949_new_pcc_chain_contains_verified_saac_image_pages():
    """首批 1949 影像页必须在专题链中可追溯，且仍保留完整档案缺口。"""
    root = Path(__file__).resolve().parents[1]
    chains = json.loads((root / "data/domestic/topic_evidence_chain.json").read_text(encoding="utf-8"))
    chain = next(item for item in chains if item["event_id"] == "domestic-1949-new-pcc")
    primary = chain["layers"]["primary"]
    assert {item["page_id"] for item in primary} >= {1670, 1671, 1673, 20733, 20738, 20757, 20767, 20768}
    assert all(item["status"] == "strict_citation" for item in primary)
    assert any("完整代表名册" in item["target"] for item in chain["layers"]["missing_primary"])


def test_monitor_json_parser_accepts_pretty_json():
    """完成监控不能把多行 JSON 校验器误读成最后一行。"""
    from scripts.domestic.monitor_completion import run_py

    result = run_py("validate_topic_evidence_chain.py")
    assert result["_returncode"] == 0
    assert result["status"] == "PASS"
    assert result["topics"] == 9


def test_completion_monitor_formal_check_is_read_only():
    """完成监控读取正式库时不得把候选 JSONL 回写进 SQLite。"""
    import scripts.domestic.monitor_completion as monitor

    before = hashlib.sha256(DB_PATH.resolve().read_bytes()).hexdigest()
    report = monitor.read_formal_index(monitor.load_candidates())
    after = hashlib.sha256(DB_PATH.resolve().read_bytes()).hexdigest()
    assert before == after
    assert report["readonly"] is True
    assert report["domestic_candidates"] == 689
    assert report["pending_review"] == 1
    assert report["integrity_check"] == "ok"
    assert report["foreign_key_violations"] == 0


def test_academic_topic_match_uses_metadata_only(tmp_path, monkeypatch):
    """专题学术候选匹配只读结构化 metadata，不依赖正文。"""
    import app

    staging = tmp_path / "staging.sqlite"
    with sqlite3.connect(staging) as connection:
        connection.execute(
            """CREATE TABLE domestic_research_materials (
                external_id TEXT, title TEXT, author TEXT, institution TEXT,
                publication_date TEXT, research_type TEXT, quality_tier TEXT,
                source_url TEXT, fulltext_status TEXT, review_status TEXT,
                citation_ready INTEGER, human_verified INTEGER,
                metadata_json TEXT, layer TEXT
            )"""
        )
        connection.execute(
            """INSERT INTO domestic_research_materials VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ACAD-TEST-001",
                "闻一多与1946年昆明民主运动",
                "测试作者",
                "测试研究机构",
                "2001",
                "SCHOLARLY_ARTICLE",
                "A",
                "https://example.test/article",
                "METADATA_ONLY",
                "machine_accepted",
                0,
                0,
                json.dumps({"events": ["闻一多"], "historical_periods": ["1946"]}, ensure_ascii=False),
                "SCHOLARLY_RESEARCH",
            ),
        )
    monkeypatch.setattr(app, "DOMESTIC_STAGING_DB_PATH", staging)
    result = app._research_academic_matches(
        {"event_tags": ["1946李闻血案"]},
        {"academic_terms": ["闻一多", "1946"]},
    )
    assert result["total"] == 1
    assert result["rows"][0]["external_id"] == "ACAD-TEST-001"
    assert "闻一多" in result["rows"][0]["matched_terms"]


def test_academic_formal_search_link_and_citation_label(tmp_path, monkeypatch):
    """学术 staging 结果必须能回到正式全文页，引用模板不得伪装成 FRUS。"""
    import app

    staging = tmp_path / "staging.sqlite"
    with sqlite3.connect(staging) as connection:
        connection.execute(
            """CREATE TABLE domestic_research_materials (
                external_id TEXT, title TEXT, author TEXT, institution TEXT,
                publication_date TEXT, research_type TEXT, quality_tier TEXT,
                source_url TEXT, local_path TEXT, fulltext_status TEXT,
                review_status TEXT, citation_ready INTEGER, human_verified INTEGER,
                metadata_json TEXT, layer TEXT
            )"""
        )
        connection.execute(
            """INSERT INTO domestic_research_materials VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ACAD-FORMAL-001",
                "测试学术全文",
                "测试作者",
                "测试机构",
                "2019",
                "SCHOLARLY_ARTICLE",
                "A",
                "https://example.test/formal",
                "data/domestic/test.html",
                "FULLTEXT_HTML_CANDIDATE",
                "review_only",
                0,
                0,
                "{}",
                "SCHOLARLY_RESEARCH",
            ),
        )
    formal = tmp_path / "formal.sqlite"
    with sqlite3.connect(formal) as connection:
        connection.execute(
            """CREATE TABLE documents (
                id INTEGER PRIMARY KEY, doc_key TEXT, doc_id TEXT, title TEXT,
                source_platform TEXT, hit_type TEXT
            )"""
        )
        connection.execute(
            """CREATE TABLE pages (
                id INTEGER PRIMARY KEY, document_id INTEGER, text TEXT
            )"""
        )
        connection.execute(
            "INSERT INTO documents VALUES (1, ?, ?, ?, 'domestic', 'domestic_academic_fulltext')",
            ("domestic-academic/ACAD-FORMAL-001", "ACAD-FORMAL-001", "测试学术全文"),
        )
        connection.execute("INSERT INTO pages VALUES (1, 1, '测试正文')")
    monkeypatch.setattr(app, "DOMESTIC_STAGING_DB_PATH", staging)
    monkeypatch.setattr(app, "DB_PATH", formal)

    body = app.domestic_staging_search_page({"scope": ["research"], "q": ["ACAD-FORMAL-001"]}).decode("utf-8")
    assert "/doc/domestic-academic%2FACAD-FORMAL-001" in body
    assert "正式全文页" in body

    citation = app._build_citations(
        {
            "title": "测试学术全文",
            "volume_id": "DOMESTIC-ACADEMIC",
            "doc_id": "ACAD-FORMAL-001",
            "date_guess": "2019",
            "url": "https://example.test/formal",
            "source_platform": "domestic",
            "hit_type": "domestic_academic_fulltext",
        }
    )
    assert "美国国务院" not in citation["gb"]
    assert "citation_ready=0" in citation["gb"]


def test_academic_formal_index_fallback_without_staging(tmp_path, monkeypatch, db_missing_reason):
    """清洁 checkout 缺 staging 时，正式学术层仍可检索和回接专题。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证 formal academic fallback: {db_missing_reason}")
    import app

    monkeypatch.setattr(app, "DOMESTIC_STAGING_DB_PATH", tmp_path / "staging-does-not-exist.sqlite")
    snapshot = app._academic_layer_snapshot()
    assert snapshot["fallback"] == "formal_index"
    assert snapshot["academic_records"] >= 15
    result = app._research_academic_matches(
        {"event_tags": ["1948"]},
        {"academic_terms": ["五一口号", "1948"]},
    )
    assert result["total"] >= 1
    body = app.domestic_formal_academic_search_page("五一", "").decode("utf-8")
    assert "正式全文页" in body
    assert "citation_ready=0" in body


def test_domestic_evidence_review_smoke(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证页级证据复核: {db_missing_reason}")
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT p.id
            FROM pages p JOIN documents d ON d.id=p.document_id
            WHERE d.source_platform='domestic'
            ORDER BY p.id LIMIT 1
            """
        ).fetchone()
    assert row
    status, body = fetch(live_server, f"/domestic/evidence-review/{row[0]}")
    assert status == 200
    assert body is not None
    assert "页级证据复核" in body
    assert "SHA256" in body
    assert "人工核验可引用" in body

    with sqlite3.connect(DB_PATH) as connection:
        before = connection.execute(
            "SELECT citation_ready, needs_human_review, review_status, human_review_note FROM page_provenance WHERE page_id=?",
            (row[0],),
        ).fetchone()
    response = requests.post(
        f"{live_server}/domestic/evidence-review/{row[0]}",
        data={
            "review_status": "human_verified",
            "reviewer": "test-only",
            "human_review_note": "test validation must not auto-upgrade",
        },
        timeout=10,
    )
    assert response.status_code == 400
    assert "必须确认" in response.text
    with sqlite3.connect(DB_PATH) as connection:
        after = connection.execute(
            "SELECT citation_ready, needs_human_review, review_status, human_review_note FROM page_provenance WHERE page_id=?",
            (row[0],),
        ).fetchone()
    assert after == before


def test_domestic_manifest_and_strict_citation_gate(db_missing_reason):
    """Manifest and formal citation count must describe the same live DB."""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法核对国内 manifest: {db_missing_reason}")
    manifest_path = Path(__file__).resolve().parents[1] / "data" / "research_index.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_sha = hashlib.sha256(DB_PATH.read_bytes()).hexdigest()
    assert manifest["sha256"] == actual_sha
    with sqlite3.connect(DB_PATH) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        strict_rows = connection.execute(
            """
            SELECT pp.page_id, pp.source_file, pp.source_sha256, pp.pdf_page_no,
                   p.page_url, pp.human_review_note
            FROM page_provenance pp JOIN pages p ON p.id=pp.page_id
            WHERE pp.citation_ready=1 AND pp.needs_human_review=0
              AND pp.review_status='human_verified'
              AND trim(COALESCE(pp.human_review_note,''))<>''
            ORDER BY pp.page_id
            """
        ).fetchall()
    assert integrity == "ok"
    assert 100 <= len(strict_rows) <= 200
    assert manifest["counts"]["strict_human_citation_pages"] == len(strict_rows)
    for page_id, source_file, source_sha256, pdf_page_no, page_url, note in strict_rows:
        assert Path(str(source_file)).suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}, page_id
        assert re.fullmatch(r"[0-9a-f]{64}", str(source_sha256 or "").lower()), page_id
        if pdf_page_no:
            assert re.search(r"#page=0*%d(?:$|[^0-9])" % int(pdf_page_no), str(page_url or "")), page_id
        else:
            assert Path(str(source_file)).suffix.lower() in {".jpg", ".jpeg", ".png"}, page_id
        assert "codex" in str(note).lower()


def test_research_question_benchmark_covers_all_domestic_topics(tmp_path, db_missing_reason):
    """真实研究问题必须能进入专题链，但不得被误报为一手闭环。"""
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法运行研究问题基准: {db_missing_reason}")
    script = Path(__file__).resolve().parents[1] / "scripts" / "domestic" / "build_research_question_benchmark_20260814.py"
    output = tmp_path / "research-question-benchmark.json"
    result = subprocess.run(
        [sys.executable, str(script), "--output", str(output)],
        cwd=str(script.parents[2]),
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip()
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["question_count"] == 36
    assert report["path_ready_count"] == 36
    assert report["strict_support_count"] == 36
    assert report["topic_strict_route_count"] == 36
    assert report["failed_path_count"] == 0
    assert report["topic_count"] == 9
    assert report["body_read"] is False
    assert report["report_does_not_copy_page_text"] is True
    assert all(item["questions"] == 4 for item in report["topics"].values())
    assert all(item["path_ready"] == 4 for item in report["topics"].values())
    assert all(item["topic_strict_routes"] == 4 for item in report["topics"].values())
    assert all(
        check["primary_evidence_status"] == "partial"
        for check in report["checks"]
    )
