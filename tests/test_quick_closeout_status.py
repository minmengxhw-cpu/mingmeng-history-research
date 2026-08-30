from __future__ import annotations

import datetime as dt
import json

from scripts.closeout.read_closeout_status import build_status, load_json


def test_quick_status_is_metadata_only_and_redacts_path_markers():
    snapshot = {
        "schema_version": "domestic_platform_closeout_snapshot.v1",
        "generated_at": "2026-08-30T00:00:00+00:00",
        "platform": {"status": "PASS", "research_content_status": "OPEN_PRIMARY_GAPS", "failed_checks": []},
        "p0_intake": {
            "status": "WAITING_FOR_LOCAL_ORIGINAL",
            "target_count": 2,
            "incoming_file_count": 0,
            "mapping_count": 0,
            "target_statuses": [
                {
                    "target_id": "P0-TEST",
                    "status": "WAITING_FOR_LOCAL_ORIGINAL",
                    "missing_fields": ["local_path", "source_file"],
                    "local_path": "/private/secret.pdf",
                }
            ],
        },
        "safety": {
            "body_read": False,
            "formal_db_written": False,
            "sources_downloaded": False,
            "files_deleted_or_moved": False,
            "auto_delete": False,
        },
    }

    status = build_status(
        snapshot,
        now=dt.datetime(2026, 8, 30, 0, 5, tzinfo=dt.timezone.utc),
    )
    serialized = json.dumps(status, ensure_ascii=False)

    assert status["status"] == "OK"
    assert status["platform"]["research_content_status"] == "OPEN_PRIMARY_GAPS"
    assert status["p0_intake"]["target_statuses"] == [
        {
            "target_id": "P0-TEST",
            "status": "WAITING_FOR_LOCAL_ORIGINAL",
            "missing_fields": ["file_mapping"],
        }
    ]
    for marker in ("/Users/", "/private/", "/tmp/", "local_path", "source_file", "page_image_path"):
        assert marker not in serialized


def test_quick_status_marks_an_old_snapshot_stale():
    snapshot = {
        "schema_version": "domestic_platform_closeout_snapshot.v1",
        "generated_at": "2026-08-30T00:00:00+00:00",
        "platform": {"status": "PASS", "research_content_status": "OPEN_PRIMARY_GAPS", "failed_checks": []},
        "p0_intake": {"status": "WAITING_FOR_LOCAL_ORIGINAL", "target_count": 2},
        "safety": {},
    }

    status = build_status(
        snapshot,
        now=dt.datetime(2026, 8, 30, 2, 0, tzinfo=dt.timezone.utc),
        max_age_seconds=3600,
    )

    assert status["status"] == "STALE_SNAPSHOT"
    assert status["snapshot_age_seconds"] == 7200
    assert status["snapshot_freshness"] == "STALE"


def test_load_json_rejects_non_object(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(["not-a-snapshot"]), encoding="utf-8")
    assert load_json(path) is None
