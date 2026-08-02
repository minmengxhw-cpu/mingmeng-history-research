"""T1 真实路由冒烟测试。"""
from __future__ import annotations

import pytest

from tests._http import fetch


def _require_database(reason: str | None) -> None:
    if reason:
        pytest.skip(f"数据库依赖路由未验证：{reason}")


def _assert_page(base_url: str, path: str, marker: str) -> None:
    status, body = fetch(base_url, path)
    assert status == 200, f"{path} 返回 {status}"
    assert body is not None
    assert "Traceback" not in body
    assert "Internal Server Error" not in body
    assert marker in body


def test_home_smoke(live_server, db_missing_reason):
    _require_database(db_missing_reason)
    _assert_page(live_server, "/", "民盟历史文献研究库")


def test_dashboard_smoke(live_server, db_missing_reason):
    _require_database(db_missing_reason)
    _assert_page(live_server, "/dashboard", "研究进度仪表盘")


def test_sourcebooks_smoke(live_server):
    _assert_page(live_server, "/sourcebooks", "史料长编")


def test_doc_detail_smoke(live_server, document_key):
    _assert_page(live_server, f"/doc/{document_key}", "民盟历史文献研究库")


def test_timeline_smoke(live_server, db_missing_reason):
    _require_database(db_missing_reason)
    _assert_page(live_server, "/timeline", "年表")


def test_domestic_smoke(live_server, staging_missing_reason):
    if staging_missing_reason:
        pytest.skip(f"国内史料真实页面未验证：{staging_missing_reason}")
    _assert_page(live_server, "/domestic", "国内史料")


def test_domestic_library_smoke(live_server, db_missing_reason):
    _require_database(db_missing_reason)
    _assert_page(live_server, "/domestic/library", "已收国内资料")
