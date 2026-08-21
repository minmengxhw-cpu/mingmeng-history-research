"""Clean-checkout regression for metadata-only academic fallbacks."""

from pathlib import Path

from scripts.domestic.audit_academic_source_layer_20260813 import audit
from scripts.domestic.audit_academic_topic_crosswalk_20260813 import (
    load_tracked_crosswalk,
)


ROOT = Path(__file__).resolve().parents[1]


def test_academic_source_audit_replays_tracked_snapshot_without_staging_db():
    report = audit(
        ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite",
        ROOT / "data/domestic/academic_source_policy.json",
    )
    assert report["status"] == "PASS"
    assert report["source"] == "tracked_metadata_snapshot"
    assert report["snapshot_only"] is True
    assert report["body_read"] is False
    assert report["formal_db_written"] is False
    assert report["academic_records"] == 155
    assert report["scholarly_articles"] == 99
    assert report["citation_ready"] == 0


def test_academic_crosswalk_replays_tracked_metadata_without_staging_db():
    report = load_tracked_crosswalk(
        ROOT / "data/domestic/academic_topic_crosswalk.json",
        ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite",
    )
    assert report["status"] == "PASS"
    assert report["source"] == "tracked_metadata_crosswalk"
    assert report["snapshot_only"] is True
    assert report["body_read"] is False
    assert len(report["topics"]) == 9
    assert report["total_topic_matches"] == 159
