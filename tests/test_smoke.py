"""T1 冒烟测试:覆盖首页 / dashboard / sourcebooks / 文档详情页 / timeline / 国内史料页。

**先看 conftest.py 顶部的说明** —— 当前(2026-08-01)这台机器和 CI 上都没有真实的
`data/research_index.sqlite`,而 app.py 里绝大多数路由的首条 SQL 都没做
try/except 保护,数据库缺失时不是返回 500,而是直接把连接断开。

所以下面 6 条路由里:
  - /sourcebooks 完全不碰数据库,任何时候都应该 200 —— 正常断言。
  - /domestic 对"表未初始化"做了 try/except、会退化成一个正常的 200 提示页
    —— 正常断言(断言的是退化页面的文案,不是真实史料内容)。
  - /、/dashboard、/timeline、文档详情页 目前必然因为数据库缺失连接被断开
    —— 用 db_missing_reason 确认原因后 skip,不许伪装成"通过"。
"""
from __future__ import annotations

import sqlite3

import pytest

from tests._http import fetch
from tests.conftest import DB_PATH


def _skip_if_db_missing(db_missing_reason: str | None) -> None:
    if db_missing_reason:
        pytest.skip(f"数据库缺失,该路由无法在当前环境验证真实内容: {db_missing_reason}")


def test_home_smoke(live_server, db_missing_reason):
    status, body = fetch(live_server, "/")
    if status is None:
        _skip_if_db_missing(db_missing_reason)
        pytest.fail("首页请求连接被重置,且不是已知的数据库缺失场景,需要人工排查")
    assert status == 200
    assert "Traceback" not in body and "Internal Server Error" not in body
    assert "民盟历史文献研究库" in body


def test_dashboard_smoke(live_server, db_missing_reason):
    status, body = fetch(live_server, "/dashboard")
    if status is None:
        _skip_if_db_missing(db_missing_reason)
        pytest.fail("/dashboard 请求连接被重置,且不是已知的数据库缺失场景,需要人工排查")
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
    if status is None:
        _skip_if_db_missing(db_missing_reason)
        pytest.fail("/timeline 请求连接被重置,且不是已知的数据库缺失场景,需要人工排查")
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
