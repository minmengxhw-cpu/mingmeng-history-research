"""Regression for bounded primary-source subunits in the topic page."""

import json
from pathlib import Path

import app
from scripts.domestic.research_packet import build_research_packet, research_packet_page


ROOT = Path(__file__).resolve().parents[1]


def test_primary_subtarget_support_is_metadata_only_and_scoped():
    path = ROOT / "data" / "domestic" / "primary_subtarget_support.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["body_read"] is False
    assert payload["formal_db_written"] is False
    assert payload["primary_evidence_closed"] is False
    assert set(payload["topics"]) == {
        "domestic-1941-formation",
        "domestic-1948-third-plenum-may-day",
        "domestic-1949-new-pcc",
        "domestic-1945-first-congress",
        "domestic-1946-pcc",
        "domestic-1946-refuse-national-assembly",
        "domestic-1947-illegal-dissolution",
    }
    assert all(
        row["status"] == "bounded_unit_ready"
        for rows in payload["topics"].values()
        for row in rows
    )


def test_topic_page_shows_bounded_units_without_closing_primary_gap():
    body_1941 = app.research_topic_page("domestic-1941-formation").decode("utf-8")
    assert "1941 成立宣言的1946汇编重刊页界" in body_1941
    assert "1941原刊目标仍开放" in body_1941

    body_1947 = app.research_topic_page("domestic-1947-illegal-dissolution").decode("utf-8")
    assert "1947-11-04至11-06 同期报刊对民盟解散的公开报道" in body_1947
    assert "政府公函" in body_1947

    body_1948 = app.research_topic_page("domestic-1948-third-plenum-may-day").decode("utf-8")
    assert "有边界可研究的一手子单元" in body_1948
    assert "页级门禁 #20665" in body_1948
    assert "主目标仍开放" in body_1948
    assert "research_ready" in body_1948

    body_1949 = app.research_topic_page("domestic-1949-new-pcc").decode("utf-8")
    assert "页级门禁 #20733" in body_1949
    assert "页级门禁 #20940" in body_1949


def test_research_packet_exports_bounded_units_without_body_text():
    packet = build_research_packet("domestic-1949-new-pcc")
    assert packet is not None
    units = packet["primary_subtarget_support"]
    assert len(units) == 4
    assert packet["counts"]["primary_subtarget_count"] == 4
    assert packet["counts"]["primary_subtarget_page_count"] == 27
    assert all(unit["body_text_included"] is False for unit in units)
    assert all("source_file" not in unit for unit in units)
    body = research_packet_page("domestic-1949-new-pcc").decode("utf-8")
    assert "有边界可研究的一手子单元" in body
    assert "页级门禁 #20733" in body

    expected = {
        "domestic-1945-first-congress": (3, 8),
        "domestic-1946-pcc": (3, 15),
        "domestic-1946-refuse-national-assembly": (4, 6),
    }
    for event_id, (unit_count, page_count) in expected.items():
        packet = build_research_packet(event_id)
        assert packet is not None
        assert packet["counts"]["primary_subtarget_count"] == unit_count
        assert packet["counts"]["primary_subtarget_page_count"] == page_count
