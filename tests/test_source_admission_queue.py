"""Metadata-only regression tests for domestic source admission.

These tests intentionally use synthetic inventory rows.  They verify routing
and safety invariants without opening source bodies or touching the formal DB.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.domestic.build_source_admission_queue import build_rows, load_policy


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "data/domestic/source_admission_policy.json"
if not POLICY_PATH.exists():
    pytest.skip("外部研究 corpus 未挂载：缺少 source_admission_policy.json", allow_module_level=True)
POLICY = load_policy(POLICY_PATH)


def row(**overrides: str) -> dict[str, str]:
    base = {
        "source_path": "data/domestic/press_scans/民盟_1947_原件.pdf",
        "sha256": "a" * 64,
        "status": "source_only",
        "pdf_pages": "2",
        "indexed_pages": "0",
        "ocr_draft_pages": "0",
        "source_group": "press_scans",
        "text_mode": "",
        "source_form": "",
        "text_layer_status": "",
        "content_mode": "",
    }
    base.update(overrides)
    return base


def test_formal_page_chain_never_repeats_ocr_or_promotes_evidence():
    rows = build_rows(
        [row(status="formal_page_complete")],
        POLICY,
        {
            row()["source_path"]: {
                "source_path": row()["source_path"],
                "disposition": "RECONCILED_CANONICAL_PAGE_CHAIN",
            }
        },
    )

    item = rows[0]
    assert item["admission_class"] == "RETAIN_FORMAL_PAGE_CHAIN"
    assert item["ocr_action"] == "NO_REPEAT_OCR_FORMAL_PAGES_EXIST"
    assert item["body_read"] is False
    assert item["citation_ready_changed"] is False
    assert item["auto_delete"] is False


def test_electronic_text_skips_ocr_even_when_source_status_is_candidate():
    item = build_rows(
        [row(status="source_only", text_mode="electronic_text")],
        POLICY,
    )[0]

    assert item["source_form"] == "ELECTRONIC_TEXT"
    assert item["ocr_action"] == "SKIP_OCR_ELECTRONIC_TEXT"
    assert item["body_read"] is False
    assert item["auto_delete"] is False


def test_index_source_stays_navigation_only_and_is_not_full_ocr_target():
    item = build_rows(
        [row(source_path="data/domestic/catalogue/1947_民盟目录_index.pdf")],
        POLICY,
    )[0]

    assert item["admission_class"] == "RETAIN_NAVIGATION_ONLY"
    assert item["ocr_action"] == "NO_FULL_OCR_INDEX_ONLY"
    assert item["body_read"] is False
    assert item["citation_ready_changed"] is False
    assert item["auto_delete"] is False


def test_existing_ocr_is_targeted_review_not_full_reocr():
    item = build_rows(
        [row(status="draft_ready_formal_gap")],
        POLICY,
        {
            row()["source_path"]: {
                "source_path": row()["source_path"],
                "disposition": "RECONCILED_COMPLETE_OCR_LAYER",
            }
        },
    )[0]

    assert item["admission_class"] == "RETAIN_TARGETED_REVIEW"
    assert item["ocr_action"] == "USE_EXISTING_OCR_TARGETED_REVIEW"
    assert item["body_read"] is False
    assert item["auto_delete"] is False


def test_same_sha_is_a_review_group_not_an_auto_delete_instruction():
    first = row(source_path="data/domestic/press_scans/a_1947.pdf")
    second = row(source_path="data/domestic/press_scans/b_1947.pdf")
    items = build_rows([first, second], POLICY)

    assert {item["duplicate_status"] for item in items} == {"SAME_SHA_REVIEW_GROUP"}
    assert all(item["duplicate_group"].startswith("sha256:") for item in items)
    assert all(item["auto_delete"] is False for item in items)
