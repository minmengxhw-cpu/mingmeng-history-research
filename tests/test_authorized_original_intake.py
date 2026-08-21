"""授权原件接收器的安全边界回归测试。"""

from __future__ import annotations

from pathlib import Path

from scripts.domestic.prepare_authorized_original_intake import (
    build_manifest,
    discover_files,
    load_targets,
)


def test_empty_incoming_keeps_both_p0_targets_waiting(tmp_path: Path):
    incoming = tmp_path / "incoming"
    targets_path = Path(__file__).resolve().parents[1] / "data/domestic/authorized_original_intake_targets_20260821.json"
    targets = load_targets(targets_path)
    files = discover_files(incoming)
    manifest, errors = build_manifest(targets, files, [], incoming)

    assert errors == []
    assert len(manifest) == 2
    assert {row["status"] for row in manifest} == {"WAITING_FOR_LOCAL_ORIGINAL"}
    assert all(row["body_read"] is False for row in manifest)
    assert all(row["formal_db_written"] is False for row in manifest)
    assert all(row["citation_ready"] is False for row in manifest)


def test_file_requires_explicit_mapping_and_rights_before_staging(tmp_path: Path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "authorized-original.pdf"
    source.write_bytes(b"synthetic intake fixture; no document parser should run")
    targets_path = Path(__file__).resolve().parents[1] / "data/domestic/authorized_original_intake_targets_20260821.json"
    targets = load_targets(targets_path)
    files = discover_files(incoming)

    manifest, errors = build_manifest(targets, files, [], incoming)
    assert errors == [{"status": "UNMAPPED_LOCAL_FILE", "relative_path": "authorized-original.pdf", "sha256": files[0]["sha256"]}]
    assert manifest[0]["status"] == "WAITING_FOR_EXPLICIT_MAPPING"

    mapping = {
        "target_id": targets[0]["target_id"],
        "local_path": "authorized-original.pdf",
        "source_url_or_catalog_reference": "上档6-5-1216",
        "record_id_or_catalog_reference": "上档6-5-1216",
        "accessed_at": "2026-08-21T00:00:00+08:00",
        "save_permission": "user_authorized_local_save",
        "copy_permission": "citation_only",
        "public_display": "metadata_only",
    }
    manifest, errors = build_manifest(targets, files, [mapping], incoming)
    assert errors == []
    row = next(item for item in manifest if item["target_id"] == targets[0]["target_id"])
    assert row["status"] == "HASHED_NEEDS_PAGE_COUNT"
    assert row["sha256"] == files[0]["sha256"]
    assert row["page_citation_ready"] is False
    assert row["formal_db_written"] is False


def test_page_identity_review_is_last_intake_boundary(tmp_path: Path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "original.pdf"
    source.write_bytes(b"fixture")
    targets_path = Path(__file__).resolve().parents[1] / "data/domestic/authorized_original_intake_targets_20260821.json"
    targets = load_targets(targets_path)
    files = discover_files(incoming)
    mapping = {
        "target_id": targets[1]["target_id"],
        "local_path": "original.pdf",
        "source_url_or_catalog_reference": "http://example.invalid/detail/1947-11-06",
        "record_id_or_catalog_reference": "MM1941-TEST-1947-1106",
        "accessed_at": "2026-08-21T00:00:00+08:00",
        "save_permission": "user_authorized_local_save",
        "copy_permission": "citation_only",
        "public_display": "metadata_only",
        "pdf_pages": 2,
        "printed_page_map": "PDF 1-2 / physical 1-2 / printed page pending",
        "page_identity_reviewed": False,
    }
    manifest, errors = build_manifest(targets, files, [mapping], incoming)
    assert errors == []
    row = next(item for item in manifest if item["target_id"] == targets[1]["target_id"])
    assert row["status"] == "STAGED_NEEDS_PAGE_IDENTITY_REVIEW"
    assert row["citation_ready"] is False
    assert row["human_verified"] is False
