"""Regression checks for the local metadata-only operations summary."""

from __future__ import annotations

import json

import app


def test_local_metadata_summary_keeps_only_aggregate_counts(tmp_path, monkeypatch):
    discovery = tmp_path / "discovery.json"
    queue = tmp_path / "queue.json"
    ocr = tmp_path / "ocr.json"
    dedupe = tmp_path / "dedupe.json"
    discovery.write_text(
        json.dumps({"file_count": 672, "manifest": "/Users/private/body.md"}),
        encoding="utf-8",
    )
    queue.write_text(
        json.dumps(
            {
                "review_first_count": 72,
                "p0_exact_filename_match_count": 0,
                "queue": "/Users/private/queue.jsonl",
            }
        ),
        encoding="utf-8",
    )
    ocr.write_text(
        json.dumps(
            {
                "disposition_counts": {
                    "TEXT_LAYER_CHECK_BEFORE_OCR": 92,
                    "HOLD_OCR_UNTIL_PROVENANCE_REVIEW": 580,
                }
            }
        ),
        encoding="utf-8",
    )
    dedupe.write_text(
        json.dumps(
            {
                "group_count": 82,
                "member_file_count": 164,
                "mib_recoverable_if_one_copy_retained": 57.84,
                "plan": "/Users/private/plan.jsonl",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "LOCAL_METADATA_DISCOVERY_REPORT_PATH", discovery)
    monkeypatch.setattr(app, "LOCAL_METADATA_REVIEW_QUEUE_REPORT_PATH", queue)
    monkeypatch.setattr(app, "LOCAL_OCR_DISPOSITION_REPORT_PATH", ocr)
    monkeypatch.setattr(app, "LOCAL_DEDUPE_PLAN_REPORT_PATH", dedupe)

    summary = app._load_local_metadata_operations_summary()
    body = app._local_metadata_operations_html(summary)

    assert summary["inventory_file_count"] == 672
    assert summary["review_first_count"] == 72
    assert summary["text_layer_check_count"] == 92
    assert summary["ocr_provenance_hold_count"] == 580
    assert summary["duplicate_group_count"] == 82
    assert summary["duplicate_recoverable_mib"] == 57.84
    assert "/Users/" not in body
    assert "672" in body
    assert "72" in body
    assert "正文读取、OCR、正式入库" in body


def test_local_metadata_summary_is_honest_when_reports_are_missing(tmp_path, monkeypatch):
    missing = tmp_path / "missing.json"
    for name in (
        "LOCAL_METADATA_DISCOVERY_REPORT_PATH",
        "LOCAL_METADATA_REVIEW_QUEUE_REPORT_PATH",
        "LOCAL_OCR_DISPOSITION_REPORT_PATH",
        "LOCAL_DEDUPE_PLAN_REPORT_PATH",
    ):
        monkeypatch.setattr(app, name, missing)

    summary = app._load_local_metadata_operations_summary()
    body = app._local_metadata_operations_html(summary)

    assert summary == {}
    assert "尚未挂载" in body
    assert "不会扫描、读取或上传本机文件" in body
    assert "/Users/" not in body


def test_local_metadata_summary_tolerates_malformed_numeric_fields(tmp_path, monkeypatch):
    discovery = tmp_path / "discovery.json"
    dedupe = tmp_path / "dedupe.json"
    discovery.write_text(json.dumps({"file_count": "not-a-number"}), encoding="utf-8")
    dedupe.write_text(
        json.dumps({"group_count": "bad", "mib_recoverable_if_one_copy_retained": "NaN"}),
        encoding="utf-8",
    )
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(app, "LOCAL_METADATA_DISCOVERY_REPORT_PATH", discovery)
    monkeypatch.setattr(app, "LOCAL_METADATA_REVIEW_QUEUE_REPORT_PATH", missing)
    monkeypatch.setattr(app, "LOCAL_OCR_DISPOSITION_REPORT_PATH", missing)
    monkeypatch.setattr(app, "LOCAL_DEDUPE_PLAN_REPORT_PATH", dedupe)

    summary = app._load_local_metadata_operations_summary()

    assert summary["inventory_file_count"] == 0
    assert summary["duplicate_group_count"] == 0
    assert summary["duplicate_recoverable_mib"] == 0.0
