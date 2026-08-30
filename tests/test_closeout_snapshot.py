from __future__ import annotations

import json

from scripts.closeout.build_closeout_snapshot import load_p0_target_statuses, p0_status


def test_p0_status_prefers_explicit_status_and_preserves_waiting_fallback():
    assert p0_status({"status": "PARTIAL", "status_counts": {"WAITING_FOR_LOCAL_ORIGINAL": 2}}, 2) == "PARTIAL"
    assert p0_status({"status_counts": {"WAITING_FOR_LOCAL_ORIGINAL": 2}}, 2) == "WAITING_FOR_LOCAL_ORIGINAL"
    assert p0_status({"status_counts": {"WAITING_FOR_LOCAL_ORIGINAL": 1}}, 2) == "NOT_RUN"


def test_p0_target_statuses_expose_metadata_without_path_field_names(tmp_path):
    manifest = tmp_path / "INTAKE_MANIFEST.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "target_id": "P0-TEST",
                "status": "WAITING_FOR_LOCAL_ORIGINAL",
                "missing_fields": ["local_path", "source_file", "target_id"],
                "local_path": "/private/should-not-be-emitted.pdf",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    rows = load_p0_target_statuses(manifest)

    assert rows == [
        {
            "target_id": "P0-TEST",
            "status": "WAITING_FOR_LOCAL_ORIGINAL",
            "missing_fields": ["file_mapping", "target_id"],
        }
    ]
    assert "local_path" not in json.dumps(rows, ensure_ascii=False)
    assert "/private/" not in json.dumps(rows, ensure_ascii=False)
