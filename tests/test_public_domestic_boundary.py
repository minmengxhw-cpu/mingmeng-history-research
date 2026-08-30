"""公开模式的国内资料边界测试。

公开站点只能显示候选记录明确标记为 public 且处于 L0--L3 的文档；
正式库里有 OCR 或 page_provenance 不能单独构成公开授权。
"""
from __future__ import annotations

import json
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
    assert "/domestic/intake" in app.PUBLIC_HIDDEN_PATHS
    assert "/domestic/workbench" in app.PUBLIC_HIDDEN_PATHS
    assert "/research/gaps" in app.PUBLIC_HIDDEN_PATHS


def test_public_research_question_pages_do_not_expose_private_page_links():
    matrices = app._load_topic_research_matrix()
    page_ids = set()
    for matrix in matrices.values():
        for question in matrix.get("questions", []):
            for key in ("evidence_page_ids", "negative_page_ids"):
                page_ids.update(int(value) for value in question.get(key, []) if str(value).isdigit())

    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        hidden_ids = page_ids - app._public_visible_topic_page_ids(page_ids)
        assert hidden_ids
        topic_body = app.research_topic_page("domestic-1941-formation").decode("utf-8")
        questions_body = app.research_questions_page().decode("utf-8")
        for page_id in hidden_ids:
            assert f"/cite/{page_id}" not in topic_body
            assert f"/cite/{page_id}" not in questions_body
    finally:
        app._request.public_mode = previous


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


def test_public_research_topics_filter_shared_event_and_evidence_page_links():
    """专题页不能绕过候选授权，重新暴露内部证据链页。"""
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        topics = app._research_topic_rows()
        assert len(topics) == 9
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            for topic in topics:
                for row in topic["topic_event_rows"]:
                    page = connection.execute(
                        """SELECT d.id, d.source_platform
                           FROM pages p JOIN documents d ON d.id=p.document_id
                           WHERE p.id=?""",
                        (int(row["page_id"]),),
                    ).fetchone()
                    assert page is not None
                    if page["source_platform"] == "domestic":
                        assert app._public_domestic_document_visible(
                            connection, int(page["id"])
                        ) is True
                chain = topic["evidence_chain"]
                for values in (chain.get("layers") or {}).values():
                    for item in values if isinstance(values, list) else []:
                        if isinstance(item, dict) and item.get("page_id") is not None:
                            page = connection.execute(
                                """SELECT d.id, d.source_platform
                                   FROM pages p JOIN documents d ON d.id=p.document_id
                                   WHERE p.id=?""",
                                (int(item["page_id"]),),
                            ).fetchone()
                            assert page is not None
                            if page["source_platform"] == "domestic":
                                assert app._public_domestic_document_visible(
                                    connection, int(page["id"])
                                ) is True
    finally:
        app._request.public_mode = previous


def test_public_research_packet_contains_no_private_domestic_page_ids():
    from scripts.domestic.research_packet import build_research_packet

    raw_chain = json.loads(Path(app.TOPIC_EVIDENCE_CHAIN_PATH).read_text(encoding="utf-8"))
    private_page_ids: set[int] = set()
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        for topic in raw_chain:
            for values in (topic.get("layers") or {}).values():
                for item in values if isinstance(values, list) else []:
                    if not isinstance(item, dict) or item.get("page_id") is None:
                        continue
                    page = connection.execute(
                        """SELECT d.id, d.source_platform
                           FROM pages p JOIN documents d ON d.id=p.document_id
                           WHERE p.id=?""",
                        (int(item["page_id"]),),
                    ).fetchone()
                    if (
                        page is not None
                        and page["source_platform"] == "domestic"
                        and not app._public_domestic_document_visible(
                            connection, int(page["id"])
                        )
                    ):
                        private_page_ids.add(int(item["page_id"]))

    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        for event_id in (
            "domestic-1941-formation",
            "domestic-1945-first-congress",
            "domestic-1949-new-pcc",
        ):
            packet = build_research_packet(event_id)
            assert packet is not None
            exported_ids = {
                int(item["page_id"])
                for values in packet["evidence_chain"].values()
                for item in values
                if item.get("page_id") is not None
            }
            assert exported_ids.isdisjoint(private_page_ids)
            assert all(
                item.get("body_text_included") is False
                for values in packet["evidence_chain"].values()
                for item in values
            )
    finally:
        app._request.public_mode = previous
