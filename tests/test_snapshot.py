"""T1 六条路由的字节级 HTML 快照护栏。"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

import pytest

from tests._http import fetch

SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"
ASSET_VERSION_RE = re.compile(r"(/static/(?:style|fonts)\.css\?v=)\d+")


def _normalize(html: str, *, normalize_today: bool = False) -> str:
    normalized = ASSET_VERSION_RE.sub(r"\1NORMALIZED", html)
    if normalize_today:
        normalized = normalized.replace(datetime.date.today().isoformat(), "TODAY")
    # HTML 模板缩进可能产生行尾空格；快照只护栏结构和内容，不护栏空白实现细节。
    return "\n".join(line.rstrip() for line in normalized.splitlines()) + "\n"


def _assert_snapshot(name: str, html: str, *, normalize_today: bool = False) -> None:
    path = SNAPSHOT_DIR / f"{name}.html"
    normalized = _normalize(html, normalize_today=normalize_today)
    if not path.exists():
        path.write_text(normalized, encoding="utf-8")
        pytest.fail(f"{name} 快照基线已生成，请重新运行测试确认：{path}")
    assert normalized == path.read_text(encoding="utf-8"), (
        f"{name} 页面与已提交快照不一致；若是预期行为变化，应先更新 T1 基线。"
    )


def _fetch_snapshot(base_url: str, path: str) -> str:
    status, body = fetch(base_url, path)
    assert status == 200, f"{path} 返回 {status}"
    assert body is not None
    assert "Traceback" not in body
    assert "Internal Server Error" not in body
    return body


def test_home_snapshot(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"首页快照未生成：{db_missing_reason}")
    _assert_snapshot("home", _fetch_snapshot(live_server, "/"))


def test_dashboard_snapshot(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"dashboard 快照未生成：{db_missing_reason}")
    _assert_snapshot("dashboard", _fetch_snapshot(live_server, "/dashboard"))


def test_sourcebooks_snapshot(live_server):
    _assert_snapshot("sourcebooks", _fetch_snapshot(live_server, "/sourcebooks"))


def test_doc_snapshot(live_server, document_key):
    _assert_snapshot(
        "doc",
        _fetch_snapshot(live_server, f"/doc/{document_key}"),
        normalize_today=True,
    )


def test_timeline_snapshot(live_server, db_missing_reason):
    if db_missing_reason:
        pytest.skip(f"timeline 快照未生成：{db_missing_reason}")
    _assert_snapshot("timeline", _fetch_snapshot(live_server, "/timeline"))


def test_domestic_snapshot(live_server, staging_missing_reason):
    if staging_missing_reason:
        pytest.skip(f"国内史料快照未生成：{staging_missing_reason}")
    _assert_snapshot("domestic", _fetch_snapshot(live_server, "/domestic"))
