"""T1 冒烟测试:覆盖首页 / dashboard / sourcebooks / 文档详情页 / timeline / 国内史料页。

**先看 conftest.py 顶部的说明** —— 当前(2026-08-02)这台机器和 CI 上都没有真实的
`data/research_index.sqlite`。2026-08-02 对抗性审查修复了 do_GET/do_POST 缺少
顶层异常兜底的问题,现在数据库缺失时路由会返回一个干净的 500 页面(不再直接
断开连接、不回传 traceback)。

所以下面 6 条路由里:
  - /sourcebooks 完全不碰数据库,任何时候都应该 200 —— 正常断言。
  - /domestic 对"表未初始化"做了 try/except、会退化成一个正常的 200 提示页
    —— 正常断言(断言的是退化页面的文案,不是真实史料内容)。
  - /、/dashboard、/timeline、文档详情页 目前必然因为数据库缺失返回 500
    —— 用 db_missing_reason 确认原因后,只断言 500 兜底页本身干净
    (不泄露 traceback),不假装验证了真实内容。
"""
from __future__ import annotations

import sqlite3

import pytest

from tests._http import fetch
from tests.conftest import DB_PATH


def _assert_clean_500(body: str | None) -> None:
    assert body is not None
    assert "Traceback" not in body
    assert "服务错误" in body or "页面渲染出错" in body


def test_home_smoke(live_server, db_missing_reason):
    status, body = fetch(live_server, "/")
    if db_missing_reason:
        assert status == 500, f"预期数据库缺失时返回 500 兜底页,实际是 {status}"
        _assert_clean_500(body)
        pytest.skip(f"数据库缺失,只验证了 500 兜底页干净,未验证首页真实内容: {db_missing_reason}")
    assert status == 200
    assert "Traceback" not in body and "Internal Server Error" not in body
    assert "民盟历史文献研究库" in body


def test_dashboard_smoke(live_server, db_missing_reason):
    status, body = fetch(live_server, "/dashboard")
    if db_missing_reason:
        assert status == 500, f"预期数据库缺失时返回 500 兜底页,实际是 {status}"
        _assert_clean_500(body)
        pytest.skip(f"数据库缺失,只验证了 500 兜底页干净,未验证 dashboard 真实内容: {db_missing_reason}")
    assert status == 200
    assert "Traceback" not in body and "Internal Server Error" not in body
    assert "研究进度仪表盘" in body


def test_sourcebooks_smoke(live_server):
    # /sourcebooks 不触碰数据库(sourcebook_paths / research_package_path 都是纯文件系统
    # 判断且做了 exists() 检查),不需要 db_missing_reason 兜底,任何环境都该 200。
    status, body = fetch(live_server, "/sourcebooks")
    assert status == 200
    assert "Traceback" not in body and "Internal Server Error" not in body
    assert "史料长编" in body


def test_doc_detail_smoke(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"数据库缺失,拿不到真实 doc_key,无法验证文档详情页: {db_missing_reason}")
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("SELECT doc_key FROM documents LIMIT 1").fetchone()
    finally:
        conn.close()
    if not row:
        pytest.skip("documents 表存在但一行数据都没有,无法取到真实 doc_key")
    doc_key = row[0]
    status, body = fetch(live_server, f"/doc/{doc_key}")
    assert status == 200
    assert "Traceback" not in body and "Internal Server Error" not in body


def test_timeline_smoke(live_server, db_missing_reason):
    status, body = fetch(live_server, "/timeline")
    if db_missing_reason:
        assert status == 500, f"预期数据库缺失时返回 500 兜底页,实际是 {status}"
        _assert_clean_500(body)
        pytest.skip(f"数据库缺失,只验证了 500 兜底页干净,未验证 timeline 真实内容: {db_missing_reason}")
    assert status == 200
    assert "Traceback" not in body and "Internal Server Error" not in body
    assert "年表" in body


def test_domestic_smoke(live_server):
    # domestic_page() 对 sqlite3.OperationalError 做了 try/except,数据库缺失时会
    # 退化成一个正常的 200 提示页,所以这条不需要 db_missing_reason 兜底。
    status, body = fetch(live_server, "/domestic")
    assert status == 200
    assert "Traceback" not in body and "Internal Server Error" not in body
    assert "国内史料" in body
