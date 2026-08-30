#!/usr/bin/env python3
"""Register one locally held related primary source in the staging DB.

The source is explicitly kept separate from J067-001-001-105/108. This is an
idempotent metadata/text-derived registration and never writes the formal DB.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
SOURCE = Path("/Users/cheer/Documents/民盟/knowledge_base/data/staging/extracted/raw_inbox_研究室文件_2017年工作U盘_一届三中_给凯地__c0726897bf85/1、目录/2、中国民主同盟一届三中全会政治报告.doc")
DERIVED = ROOT / "work/domestic/local_private_ocr_metadata_20260730/historical_primary_audit/related_text/2、中国民主同盟一届三中全会政治报告.txt"
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730/historical_primary_audit"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if not SOURCE.exists() or not DERIVED.exists():
        raise SystemExit("source or derived text is missing")
    source_sha = sha256_file(SOURCE)
    derived_sha = sha256_file(DERIVED)
    conn = sqlite3.connect(DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS local_source_objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            document_date TEXT,
            source_path TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            source_bytes INTEGER NOT NULL,
            derived_text_path TEXT NOT NULL,
            derived_text_sha256 TEXT NOT NULL,
            source_layer TEXT NOT NULL,
            document_class TEXT NOT NULL,
            relation_status TEXT NOT NULL,
            evidence_status TEXT NOT NULL,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO local_source_objects
        (object_id,title,document_date,source_path,source_sha256,source_bytes,
         derived_text_path,derived_text_sha256,source_layer,document_class,
         relation_status,evidence_status,citation_ready,human_verified,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(object_id) DO UPDATE SET
          title=excluded.title,
          document_date=excluded.document_date,
          source_path=excluded.source_path,
          source_sha256=excluded.source_sha256,
          source_bytes=excluded.source_bytes,
          derived_text_path=excluded.derived_text_path,
          derived_text_sha256=excluded.derived_text_sha256,
          source_layer=excluded.source_layer,
          document_class=excluded.document_class,
          relation_status=excluded.relation_status,
          evidence_status=excluded.evidence_status,
          notes=excluded.notes
        """,
        (
            "LOCAL-PRIMARY-1948-01-19-THREE-CENTRAL-REPORT",
            "中国民主同盟一届三中全会政治报告",
            "1948-01-19",
            str(SOURCE),
            source_sha,
            SOURCE.stat().st_size,
            str(DERIVED),
            derived_sha,
            "local_private_knowledge_base",
            "historical_primary_related_source",
            "RELATED_NOT_AUTO_BOUND_TO_J067_105_OR_108",
            "original_local_doc_plus_derived_text",
            0,
            0,
            "关联一届三中全会政治报告；需独立来源/版本核对，不替代 J067-001-001-105/108 原件。",
        ),
    )
    conn.commit()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    row = conn.execute("SELECT * FROM local_source_objects WHERE object_id=?", ("LOCAL-PRIMARY-1948-01-19-THREE-CENTRAL-REPORT",)).fetchone()
    conn.close()
    report = {
        "report": "LOCAL_RELATED_PRIMARY_STAGING_20260730",
        "object_id": row[1],
        "title": row[2],
        "document_date": row[3],
        "source_sha256": source_sha,
        "derived_text_sha256": derived_sha,
        "relation_status": row[11],
        "citation_ready": False,
        "human_verified": False,
        "formal_db_written": False,
        "staging_db_written": True,
        "staging_integrity": integrity,
        "rule": "separate related primary source; no J067 auto-binding",
    }
    (OUT / "RELATED_PRIMARY_STAGING_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
