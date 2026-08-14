"""公开模式的国内资料边界测试。

公开站点只能显示候选记录明确标记为 public 且处于 L0--L3 的文档；
正式库里有 OCR 或 page_provenance 不能单独构成公开授权。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import app


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "research_index.sqlite"


def test_public_core_sql_only_returns_explicitly_public_documents():
    sql, params = app._domestic_core_documents_sql(core_only=True, public_only=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(sql, params).fetchall()
        assert rows
        for row in rows:
            assert app._public_domestic_document_visible(connection, int(row["id"])) is True


def test_public_domestic_library_does_not_render_private_core_documents():
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        private_sql, private_params = app._domestic_core_documents_sql(core_only=True)
        private_rows = connection.execute(private_sql, private_params).fetchall()
        private_row = next(
            (
                row
                for row in private_rows
                if not app._public_domestic_document_visible(connection, int(row["id"]))
            ),
            None,
        )
        assert private_row is not None

    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        body = app.domestic_library_page({"layer": ["core"]}).decode("utf-8")
        assert "公开模式仅显示已明确标记为 public" in body
        assert str(private_row["title"] or "") not in body
    finally:
        app._request.public_mode = previous


def test_public_mode_hides_internal_domestic_workbench_routes():
    assert "/domestic/academic" in app.PUBLIC_HIDDEN_PATHS
    assert "/domestic/quality" in app.PUBLIC_HIDDEN_PATHS
    assert "/domestic/acquisition" in app.PUBLIC_HIDDEN_PATHS
    assert "/research/gaps" in app.PUBLIC_HIDDEN_PATHS


def test_public_shared_entry_points_do_not_render_private_domestic_title():
    with sqlite3.connect(DB_PATH) as connection:
        private_title = connection.execute(
            """SELECT title
               FROM domestic_candidates
               WHERE lower(COALESCE(rights_status, '')) <> 'public'
                 AND trim(COALESCE(title, '')) <> ''
               ORDER BY id
               LIMIT 1"""
        ).fetchone()[0]

    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        pages = [
            app.search("民盟", platform="domestic"),
            app.docs(platform="domestic"),
            app.source_page("domestic"),
            app.timeline(platform_slug="domestic"),
            app.event_overview(),
            app.events(topic_slug="domestic-1941-formation"),
        ]
        assert all(private_title not in page.decode("utf-8") for page in pages)
        assert all(b"Traceback" not in page for page in pages)
    finally:
        app._request.public_mode = previous
