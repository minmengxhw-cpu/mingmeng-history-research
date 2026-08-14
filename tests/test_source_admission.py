"""资料准入和 OCR 分流的纯元数据回归测试。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.domestic.build_source_admission_queue import build_rows, load_policy


def test_source_admission_separates_ocr_and_page_reconciliation(tmp_path: Path):
    inventory = tmp_path / "inventory.csv"
    fields = ["source_path", "source_group", "pdf_pages", "sha256", "indexed_pages", "ocr_draft_pages", "status"]
    rows = [
        {
            "source_path": "data/domestic/sourcebooks/1945_纲领.pdf",
            "source_group": "sourcebooks",
            "pdf_pages": "10",
            "sha256": "a" * 64,
            "indexed_pages": "10",
            "ocr_draft_pages": "10",
            "status": "formal_page_complete",
        },
        {
            "source_path": "data/domestic/press_scans/1947_光明報.pdf",
            "source_group": "press_scans",
            "pdf_pages": "10",
            "sha256": "b" * 64,
            "indexed_pages": "1",
            "ocr_draft_pages": "10",
            "status": "draft_ready_formal_gap",
        },
        {
            "source_path": "data/domestic/press_scans/1941_索引.pdf",
            "source_group": "press_scans",
            "pdf_pages": "2",
            "sha256": "c" * 64,
            "indexed_pages": "0",
            "ocr_draft_pages": "2",
            "status": "formal_page_count_anomaly",
        },
    ]
    with inventory.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    policy_path = Path(__file__).resolve().parents[1] / "data/domestic/source_admission_policy.json"
    policy = load_policy(policy_path)
    result = build_rows(rows, policy)
    by_path = {row["source_path"]: row for row in result}
    assert by_path[rows[0]["source_path"]]["ocr_action"] == "NO_REPEAT_OCR_FORMAL_PAGES_EXIST"
    assert by_path[rows[1]["source_path"]]["ocr_action"] == "USE_EXISTING_OCR_TARGETED_REVIEW"
    assert by_path[rows[2]["source_path"]]["admission_class"] == "RETAIN_NAVIGATION_ONLY"
    assert all(row["body_read"] is False for row in result)
    assert all(row["auto_delete"] is False for row in result)


def test_source_admission_declared_electronic_text_skips_ocr():
    policy_path = Path(__file__).resolve().parents[1] / "data/domestic/source_admission_policy.json"
    policy = load_policy(policy_path)
    rows = [
        {
            "source_path": "data/domestic/research/1946_article.html",
            "source_group": "html",
            "pdf_pages": "0",
            "sha256": "d" * 64,
            "indexed_pages": "1",
            "ocr_draft_pages": "0",
            "status": "source_only",
            "text_mode": "electronic_text",
        }
    ]
    result = build_rows(rows, policy)
    assert result[0]["source_form"] == "ELECTRONIC_TEXT"
    assert result[0]["ocr_action"] == "SKIP_OCR_ELECTRONIC_TEXT"


def test_reconciliation_releases_complete_page_anomaly():
    policy_path = Path(__file__).resolve().parents[1] / "data/domestic/source_admission_policy.json"
    policy = load_policy(policy_path)
    rows = [
        {
            "source_path": "data/domestic/press_scans/1947_issue.pdf",
            "source_group": "press_scans",
            "pdf_pages": "16",
            "sha256": "e" * 64,
            "indexed_pages": "18",
            "ocr_draft_pages": "16",
            "status": "formal_page_count_anomaly",
        }
    ]
    reconciliation = {
        rows[0]["source_path"]: {
            "disposition": "RECONCILED_DUPLICATE_COMPLETE_LAYERS"
        }
    }
    result = build_rows(rows, policy, reconciliation)
    assert result[0]["admission_class"] == "RETAIN_FORMAL_PAGE_CHAIN"
    assert result[0]["ocr_action"] == "NO_REPEAT_OCR_FORMAL_PAGES_EXIST"
    assert "PAGE_RECONCILED_COMPLETE_CANONICAL_LAYER" in result[0]["reason_codes"]
