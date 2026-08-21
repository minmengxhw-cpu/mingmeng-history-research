from __future__ import annotations

import json
import sqlite3

from scripts.domestic.build_content_tier_audit import build_report


def _seed_db(path):
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE sources (
                id INTEGER PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                title TEXT,
                origin_url TEXT,
                local_path TEXT
            );
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                source_id INTEGER NOT NULL REFERENCES sources(id),
                doc_key TEXT NOT NULL UNIQUE,
                title TEXT,
                source_platform TEXT
            );
            CREATE TABLE pages (
                id INTEGER PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id),
                page_label TEXT,
                page_url TEXT,
                text TEXT NOT NULL
            );
            CREATE TABLE domestic_candidates (
                id INTEGER PRIMARY KEY,
                candidate_id TEXT NOT NULL UNIQUE,
                review_status TEXT NOT NULL,
                ingested_document_id INTEGER
            );
            CREATE TABLE domestic_editorial_decisions (
                candidate_id TEXT NOT NULL,
                decision TEXT NOT NULL
            );
            CREATE TABLE domestic_sources (
                id INTEGER PRIMARY KEY,
                source_id TEXT NOT NULL,
                status TEXT NOT NULL
            );
            INSERT INTO sources VALUES
                (1, 'domestic_page_ocr', 'd1', '国内页', NULL, NULL),
                (2, 'domestic_ocr_pilot', 'd2', 'OCR试验', NULL, NULL),
                (3, 'frus_epub', 'f1', '海外', NULL, NULL);
            INSERT INTO documents VALUES
                (1, 1, 'dom-1', '国内', 'domestic'),
                (2, 2, 'dom-2', '试验', 'domestic'),
                (3, 3, 'foreign-1', '海外', 'frus');
            INSERT INTO pages VALUES
                (1, 1, '1', NULL, 'body must not affect the counts'),
                (2, 2, '1', NULL, 'staging body');
            INSERT INTO domestic_candidates VALUES
                (1, 'c1', 'accepted', 1),
                (2, 'c2', 'needs_human_review', NULL);
            INSERT INTO domestic_editorial_decisions VALUES ('c2', 'hold');
            INSERT INTO domestic_sources VALUES (1, 's1', 'verified_entry');
            """
        )


def test_content_tier_audit_is_metadata_only_and_separates_staging(tmp_path):
    db = tmp_path / "index.sqlite"
    academic = tmp_path / "academic.json"
    _seed_db(db)
    academic.write_text(
        json.dumps(
            {
                "body_read": False,
                "formal_db_written": False,
                "local_paths_included": False,
                "records": [
                    {
                        "quality_tier": "A",
                        "fulltext_status": "METADATA_ONLY",
                        "record_role": "SCHOLARLY_RESEARCH",
                        "citation_ready": 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(db, academic)

    assert report["status"] == "PASS"
    assert report["body_read"] is False
    assert report["formal_db_written"] is False
    assert report["auto_delete"] is False
    layers = {row["code"]: row for row in report["layers"]}
    assert layers["DOMESTIC_SEARCH_LAYER"]["documents"] == 1
    assert layers["DOMESTIC_OCR_STAGING"]["documents"] == 1
    assert layers["FOREIGN_RESEARCH_LAYER"]["documents"] == 1
    assert report["academic_snapshot"]["records"] == 1


def test_content_tier_audit_reports_unknown_source_roles(tmp_path):
    db = tmp_path / "index.sqlite"
    academic = tmp_path / "academic.json"
    _seed_db(db)
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO sources VALUES (4, 'new_unclassified', 'x', 'x', NULL, NULL)")
        conn.execute("INSERT INTO documents VALUES (4, 4, 'x-1', 'x', 'domestic')")
    academic.write_text(json.dumps({"records": []}), encoding="utf-8")

    report = build_report(db, academic)

    unknown = next(row for row in report["layers"] if row["code"] == "UNMAPPED_SOURCE_TYPES")
    assert unknown["source_types"] == ["new_unclassified"]
    assert "UNMAPPED_SOURCE_TYPES" in report["next_actions"][0]
