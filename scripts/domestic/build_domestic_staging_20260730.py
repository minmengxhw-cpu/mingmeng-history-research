#!/usr/bin/env python3
"""Build a disposable domestic staging SQLite from phase-0 manifests.

This never opens the formal research_index.sqlite for writes.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/domestic/phase0_reconciliation_20260730"
OUT_DIR = ROOT / "work/domestic/staging_20260730"
DB = OUT_DIR / "domestic_staging.sqlite"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "5d44cb3f91d1019c4320339093ce401cd840a76162845c05796ace09535c4239"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            yield json.loads(line)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        raise SystemExit(f"refusing to overwrite existing staging db: {DB}")
    documents = list(rows(RECON / "DOCUMENTS.jsonl"))
    pages = list(rows(RECON / "PAGE_ASSETS.jsonl"))
    scholarly_path = ROOT / "work/domestic/grok_next_stage_20260730/05_handoff/SCHOLARLY_FULLTEXT_QUEUE.jsonl"
    scholarly = list(rows(scholarly_path)) if scholarly_path.exists() else []
    formal_before = sha256(FORMAL_DB)

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE ingest_runs (
            run_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            source_reconciliation TEXT NOT NULL,
            formal_db_sha256 TEXT NOT NULL,
            formal_db_unchanged INTEGER NOT NULL
        );
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            canonical_document_key TEXT NOT NULL UNIQUE,
            title TEXT,
            dominant_phase TEXT,
            phase_counts_json TEXT NOT NULL,
            bucket_counts_json TEXT NOT NULL,
            source_row_count INTEGER NOT NULL,
            page_row_count INTEGER NOT NULL,
            file_row_count INTEGER NOT NULL,
            unique_sha256_count INTEGER NOT NULL,
            unique_path_count INTEGER NOT NULL,
            evidence_status TEXT NOT NULL DEFAULT 'located_public'
        );
        CREATE TABLE page_assets (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL,
            object_id TEXT,
            local_path TEXT,
            page_no INTEGER,
            sha256 TEXT,
            file_kind TEXT NOT NULL,
            historical_phase TEXT,
            reclass_bucket TEXT,
            title TEXT,
            FOREIGN KEY(document_id) REFERENCES documents(id),
            UNIQUE(document_id, local_path)
        );
        CREATE TABLE scholarly_fulltexts (
            id INTEGER PRIMARY KEY,
            object_id TEXT UNIQUE,
            title TEXT,
            author TEXT,
            institution TEXT,
            quality_tier TEXT,
            local_path TEXT,
            sha256 TEXT,
            file_magic TEXT,
            evidence_status TEXT NOT NULL DEFAULT 'machine_text_ready'
        );
        CREATE TABLE quality_flags (
            id INTEGER PRIMARY KEY,
            flag_type TEXT NOT NULL,
            object_key TEXT NOT NULL,
            detail TEXT NOT NULL,
            severity TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE document_search USING fts5(
            canonical_document_key UNINDEXED,
            title,
            dominant_phase,
            content='documents',
            content_rowid='id'
        );
        CREATE VIRTUAL TABLE page_search USING fts5(
            object_id UNINDEXED,
            local_path,
            title,
            historical_phase,
            reclass_bucket,
            content='page_assets',
            content_rowid='id'
        );
        """
    )
    conn.execute(
        "INSERT INTO ingest_runs VALUES (?, datetime('now'), ?, ?, ?)",
        (
            "STAGING_20260730_PHASE0",
            str(RECON / "REPORT.json"),
            formal_before,
            int(formal_before == EXPECTED_FORMAL_SHA),
        ),
    )
    doc_id_by_key: dict[str, int] = {}
    for doc in documents:
        cur = conn.execute(
            """INSERT INTO documents
            (canonical_document_key,title,dominant_phase,phase_counts_json,bucket_counts_json,
             source_row_count,page_row_count,file_row_count,unique_sha256_count,unique_path_count)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                doc["canonical_document_key"],
                json.dumps(doc.get("title", []), ensure_ascii=False),
                doc.get("dominant_phase"),
                json.dumps(doc.get("phase_counts", {}), ensure_ascii=False),
                json.dumps(doc.get("bucket_counts", {}), ensure_ascii=False),
                doc.get("row_count", 0),
                doc.get("page_row_count", 0),
                doc.get("file_row_count", 0),
                doc.get("unique_sha256_count", 0),
                doc.get("unique_path_count", 0),
            ),
        )
        doc_id_by_key[doc["canonical_document_key"]] = cur.lastrowid

    for page in pages:
        doc_id = doc_id_by_key[page["canonical_document_key"]]
        try:
            conn.execute(
                """INSERT INTO page_assets
                (document_id,object_id,local_path,page_no,sha256,file_kind,historical_phase,reclass_bucket,title)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    doc_id,
                    page.get("object_id"),
                    page.get("local_path"),
                    page.get("page_no"),
                    page.get("sha256"),
                    page.get("file_kind"),
                    page.get("historical_phase"),
                    page.get("reclass_bucket"),
                    page.get("title"),
                ),
            )
        except sqlite3.IntegrityError:
            conn.execute(
                "INSERT INTO quality_flags(flag_type,object_key,detail,severity) VALUES (?,?,?,?)",
                ("DUPLICATE_PAGE_PATH", str(page.get("local_path")), "same document/local path repeated", "WARN"),
            )

    for item in scholarly:
        conn.execute(
            """INSERT INTO scholarly_fulltexts
            (object_id,title,author,institution,quality_tier,local_path,sha256,file_magic)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                item.get("object_id"), item.get("title"), item.get("author"),
                item.get("institution"), item.get("quality_tier"), item.get("local_path"),
                item.get("sha256"), item.get("magic"),
            ),
        )

    conn.execute("INSERT INTO document_search(document_search) VALUES ('rebuild')")
    conn.execute("INSERT INTO page_search(page_search) VALUES ('rebuild')")
    conn.commit()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    counts = {
        "documents": conn.execute("SELECT count(*) FROM documents").fetchone()[0],
        "page_assets": conn.execute("SELECT count(*) FROM page_assets").fetchone()[0],
        "scholarly_fulltexts": conn.execute("SELECT count(*) FROM scholarly_fulltexts").fetchone()[0],
        "quality_flags": conn.execute("SELECT count(*) FROM quality_flags").fetchone()[0],
        "document_search": conn.execute("SELECT count(*) FROM document_search").fetchone()[0],
        "page_search": conn.execute("SELECT count(*) FROM page_search").fetchone()[0],
    }
    conn.close()
    formal_after = sha256(FORMAL_DB)
    report = {
        "staging_db": str(DB),
        "formal_db_sha_before": formal_before,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_before == formal_after == EXPECTED_FORMAL_SHA,
        "integrity_check": integrity,
        "foreign_key_violation_count": fk_count,
        "counts": counts,
        "source_reconciliation": str(RECON / "REPORT.json"),
    }
    (OUT_DIR / "BUILD_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
