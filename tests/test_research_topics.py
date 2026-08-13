"""统一国内外专题入口的真实数据库冒烟测试。"""
from __future__ import annotations

import json
import hashlib
import re
import sqlite3
from pathlib import Path

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
    assert "Traceback" not in body and "Internal Server Error" not in body


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
    assert "下一步核验" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_domestic_academic_layer_smoke(live_server):
    status, body = fetch(live_server, "/domestic/academic")
    assert status == 200
    assert body is not None
    assert "国内学术研究层" in body
    assert "学术研究用于解释" in body or "学术研究作为解释层" in body
    assert "citation-ready" in body
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
        assert str(source_file).lower().endswith(".pdf"), page_id
        assert re.fullmatch(r"[0-9a-f]{64}", str(source_sha256 or "").lower()), page_id
        assert re.search(r"#page=0*%d(?:$|[^0-9])" % int(pdf_page_no), str(page_url or "")), page_id
        assert "Codex" in str(note)
