"""Regression checks for the body-free sibling collection intake surface."""

from __future__ import annotations

import app


def test_sibling_intake_queue_is_loaded_as_metadata_only():
    payload = app._load_sibling_collection_intake_queue()
    assert payload["queue_record_count"] == 355
    assert payload["local_paths_included"] is False
    assert payload["body_read"] is False
    assert payload["formal_db_written"] is False
    assert payload["disposition_counts"]["PROMOTE_METADATA_REVIEW"] == 37
    assert payload["disposition_counts"]["PROMOTE_ACADEMIC_METADATA_REVIEW"] == 4


def test_sibling_intake_surface_does_not_render_local_paths_or_bodies():
    body = app.domestic_review_page().decode("utf-8")
    assert "Sibling 采集包元数据待准入" in body
    assert "355" in body
    assert "GDC-0050" in body
    assert "GDC-0090" in body
    assert "GDC-0100" in body
    assert "GDC-0104" in body
    assert "GDC-0154" in body
    assert "其余优先候选" in body
    assert "/Users/" not in body
    assert "local_path" not in body
