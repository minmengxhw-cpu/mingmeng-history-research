"""证据收口看板必须显示正式库分流信息。"""

from __future__ import annotations

import app


def test_research_gap_rows_surface_formal_overlay():
    rows = app._research_gap_rows()
    target = next(row for row in rows if row["event_id"] == "domestic-1947-illegal-dissolution")
    assert int(target["formal_page_count"]) > 0
    assert int(target["formal_strict_citation_page_count"]) > 0
    assert target["status"] == "open"
    locked = next(
        candidate
        for candidate in target["candidates"]
        if candidate["candidate_id"] == "domestic:DRNH:002-020400-00012-067"
    )
    assert locked["formal_ingest_status"] == "NOT_INGESTED"

    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = False
    try:
        body = app.research_gaps_page().decode("utf-8")
        assert "正式库页" in body
        assert "已有正式页·待页级复核" in body
        assert "页级导航" in body
    finally:
        app._request.public_mode = previous


def test_research_topic_source_map_exposes_public_route_without_promoting_it():
    previous = getattr(app._request, "public_mode", False)
    app._request.public_mode = True
    try:
        body = app.research_topic_page("domestic-1947-illegal-dissolution").decode("utf-8")
        assert "九三学社中央专题页转载的1947年10月27日民盟非法化报纸图像" in body
        assert "官方转载图像" in body
        assert "没有页级记录的入口不会自动进入正式引文" in body
        assert "primary_evidence_closed" not in body
        assert "/Users/" not in body and "/private/" not in body
    finally:
        app._request.public_mode = previous
