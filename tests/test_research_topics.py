"""统一国内外专题入口的真实数据库冒烟测试。"""
from __future__ import annotations

import pytest

from tests._http import fetch


def test_research_topics_smoke(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证专题统计: {db_missing_reason}")
    status, body = fetch(live_server, "/research")
    assert status == 200
    assert body is not None
    assert "多源专题研究" in body
    assert "国内候选" in body
    assert "机器命中" in body
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_research_topic_detail_smoke(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,无法验证专题详情: {db_missing_reason}")
    status, body = fetch(live_server, "/research/domestic-1941-formation")
    assert status == 200
    assert body is not None
    assert "国内候选记录" in body
    assert "证据边界" in body
    assert "下一步核验" in body
    assert "Traceback" not in body and "Internal Server Error" not in body
