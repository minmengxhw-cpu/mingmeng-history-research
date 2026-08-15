"""Regression checks for the metadata-only unified platform gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.domestic.validate_unified_research_platform import build_report


ROOT = Path(__file__).resolve().parents[1]


def test_unified_platform_gate_passes_without_claiming_content_closure():
    report = build_report()
    assert report["status"] == "PASS"
    assert report["research_content_status"] == "OPEN_PRIMARY_GAPS"
    assert report["body_read"] is False
    assert report["formal_db_written"] is False
    assert report["auto_delete"] is False
    assert report["failed_checks"] == []
    assert report["checks"]["candidate_alignment"]["missing_from_db"] == []
    assert report["checks"]["source_registry_alignment"]["file_count"] == 90
    assert report["checks"]["academic_layer"]["crosswalk_topics"] == 9
    assert report["checks"]["academic_layer"]["scholarly_articles"] == 99
    assert report["checks"]["retrieval_queue"]["formal_candidate_count"] == 690
    assert report["checks"]["pcc_1946_sourcebook_map"]["target_count"] == 6
    assert report["checks"]["pcc_1946_sourcebook_render_manifest"]["page_count"] == 9
    assert report["checks"]["pcc_1946_sourcebook_render_manifest"]["review_status"] == "page_identity_and_boundary_human_verified_body_ocr_pending"
    assert report["checks"]["research_packets"]["topic_count"] == 9
    assert report["checks"]["research_question_benchmark"]["path_ready_count"] == 36


def test_external_navigation_sources_use_hashed_metadata_snapshots():
    source_map = json.loads(
        (ROOT / "data/domestic/1946_li_wen_source_map.json").read_text(encoding="utf-8")
    )
    sources = {
        str(source["source_id"]): source
        for source in source_map["sources"]
        if source.get("metadata_snapshot_file")
    }
    assert set(sources) == {
        "minmeng-yunnan-democracy-weekly-history",
        "jiuwenku-guangmingbao-1946-catalogue",
        "nlc-guangmingbao-1946-v8-li-wen",
    }
    for source in sources.values():
        snapshot = ROOT / source["metadata_snapshot_file"]
        digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        assert digest == source["metadata_snapshot_sha256"]
