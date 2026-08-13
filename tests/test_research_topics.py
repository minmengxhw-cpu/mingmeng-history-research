"""统一国内外专题入口的真实数据库冒烟测试。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

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
    assert "下一步核验" in body
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
