"""Regression checks for the private local/formal hash reconciliation summary."""

from __future__ import annotations

import json

import app


def test_hash_summary_projects_counts_without_paths(tmp_path, monkeypatch):
    report = tmp_path / "hash.json"
    report.write_text(
        json.dumps(
            {
                "inventory_file_count": 672,
                "formal_existing_file_count": 271,
                "local_hashed_file_count": 672,
                "formal_hashed_file_count": 271,
                "exact_formal_source_path_count": 0,
                "exact_formal_source_hash_local_file_count": 0,
                "unmatched_local_file_count": 672,
                "local_path": "/Users/private/source.pdf",
                "body_text": "must not render",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "LOCAL_FORMAL_HASH_RECONCILIATION_REPORT_PATH", report)

    summary = app._load_local_formal_hash_reconciliation_summary()
    body = app._local_formal_hash_reconciliation_html(summary)

    assert summary["local_hashed_file_count"] == 672
    assert summary["formal_hashed_file_count"] == 271
    assert summary["unmatched_local_file_count"] == 672
    assert "/Users/" not in body
    assert "body_text" not in body
    assert "精确匹配" in body


def test_hash_summary_is_honest_when_report_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "LOCAL_FORMAL_HASH_RECONCILIATION_REPORT_PATH", tmp_path / "missing.json")

    summary = app._load_local_formal_hash_reconciliation_summary()
    body = app._local_formal_hash_reconciliation_html(summary)

    assert summary == {}
    assert "尚未挂载" in body
    assert "不会扫描、读取或上传本机文件" in body
    assert "/Users/" not in body


def test_hash_summary_safely_defaults_malformed_counts(tmp_path, monkeypatch):
    report = tmp_path / "hash.json"
    report.write_text(
        json.dumps(
            {
                "local_hashed_file_count": "not-a-number",
                "formal_hashed_file_count": "NaN",
                "exact_formal_source_path_count": True,
                "unmatched_local_file_count": -5,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "LOCAL_FORMAL_HASH_RECONCILIATION_REPORT_PATH", report)

    summary = app._load_local_formal_hash_reconciliation_summary()

    assert summary["local_hashed_file_count"] == 0
    assert summary["formal_hashed_file_count"] == 0
    assert summary["exact_formal_source_path_count"] == 0
    assert summary["unmatched_local_file_count"] == 0
