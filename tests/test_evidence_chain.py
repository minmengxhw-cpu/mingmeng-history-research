"""Evidence-chain policy tests that do not mutate the research database."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from scripts.closeout.repair_evidence_chain_20260813 import (
    catalog_keys,
    compatible_most_precise,
    page_number,
    valid_date,
)
from scripts.closeout.verify_research_index_manifest import audit_source_files
from scripts.domestic.validate_topic_evidence_chain import (
    DEFAULT_CHAIN,
    DEFAULT_COVERAGE,
    DEFAULT_DB,
    validate,
)


def test_date_consensus_accepts_only_compatible_precision() -> None:
    assert compatible_most_precise(["1947", "1947-08", "1947-08-08"]) == "1947-08-08"
    assert compatible_most_precise(["1947-01-08", "1947-08-08"]) is None
    assert valid_date("1947-08-08") == "1947-08-08"
    assert valid_date("1947-13-08") is None


def test_catalog_and_page_locators_are_deterministic() -> None:
    assert catalog_keys("nlc404-01jh001298-72818", "irrelevant") == {
        "NLC404-01JH001298-72818"
    }
    assert page_number("scan.pdf#page=007", "", Path("scan.pdf")) == 7
    assert page_number("", "0009", Path("scan.pdf")) == 9
    assert page_number("", "0009", Path("scan.txt")) is None


def _audit_connection(source_file: str, source_sha256: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE documents (id INTEGER PRIMARY KEY, source_platform TEXT);
        CREATE TABLE page_provenance (
            document_id INTEGER,
            source_file TEXT,
            source_sha256 TEXT
        );
        INSERT INTO documents VALUES (1, 'domestic');
        """
    )
    conn.execute(
        "INSERT INTO page_provenance VALUES (1, ?, ?)",
        (source_file, source_sha256),
    )
    return conn


def test_source_audit_accepts_project_relative_matching_bytes(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    source = project_root / "data" / "source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("source bytes", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    conn = _audit_connection("data/source.txt", digest)
    try:
        result = audit_source_files(conn, project_root)
    finally:
        conn.close()
    assert result == {
        "source_files_checked": 1,
        "source_file_bytes": len(b"source bytes"),
        "source_files_missing": 0,
        "source_hash_mismatches": 0,
        "absolute_source_paths": 0,
        "source_files_outside_project": 0,
    }


def test_source_audit_blocks_relative_path_escape(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("not project evidence", encoding="utf-8")
    digest = hashlib.sha256(outside.read_bytes()).hexdigest()
    conn = _audit_connection("../outside.txt", digest)
    try:
        result = audit_source_files(conn, project_root)
    finally:
        conn.close()
    assert result["source_files_outside_project"] == 1
    assert result["source_file_bytes"] == 0


def test_1949_journal_page_identity_split_stays_on_open_primary() -> None:
    report = validate(DEFAULT_DB, DEFAULT_COVERAGE, DEFAULT_CHAIN)
    assert report["status"] == "PASS"
    assert report["layer_item_counts"]["missing_primary"] == 9
    journal = [
        row
        for row in report["page_refs"]
        if row["event_id"] == "domestic-1949-new-pcc"
        and row["doc_key"] == "domestic-nlc/NLC:1949-first-plenary-conference-journal"
    ]
    by_id = {int(row["page_id"]): row for row in journal}
    assert set(by_id) == {20932, 20933, 20934, 20935, 20936, 20937, 20938, 20939}
    for page_id in (20932, 20933, 20934, 20935, 20936, 20937):
        assert by_id[page_id]["status"] == "strict_citation"
        assert by_id[page_id]["layer"] == "cross_source"
    for page_id in (20938, 20939):
        assert by_id[page_id]["status"] == "review_only"
        assert by_id[page_id]["layer"] == "cross_source"
