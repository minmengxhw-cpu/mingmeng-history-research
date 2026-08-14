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
