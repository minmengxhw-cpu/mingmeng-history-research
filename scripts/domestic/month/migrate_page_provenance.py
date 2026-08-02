#!/usr/bin/env python3
"""Month long-task step 5: additive schema migration — page-level provenance table.

WHY: the existing `pages` table is (id, document_id, page_label, page_url, text).
It has no column for physical page number, printed page, page image path, page
image SHA256, OCR file path/SHA256, citation_ready or needs_human_review — those
are currently smuggled into a comma-joined `documents.matched_terms` string.
The monthly goal ("按物理页号检索、能回溯到原始 PDF/图片和页图") is not expressible
in that shape.

WHAT THIS DOES: creates ONE new table plus indexes. It does not alter, rewrite or
delete any existing table, row or column. Existing queries keep working unchanged.

Safety: backs up the DB first, runs PRAGMA integrity_check before and after, and
refuses to continue if either check fails. Dry-run by default; --apply to write.

Usage:
  python3 scripts/domestic/month/migrate_page_provenance.py --apply \
      --report work/domestic/month_20260728/MIGRATION_page_provenance.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DDL = [
    """
    CREATE TABLE IF NOT EXISTS page_provenance (
        page_id              INTEGER PRIMARY KEY,
        document_id          INTEGER NOT NULL,
        source_id            TEXT    NOT NULL,
        source_file          TEXT    NOT NULL,
        source_sha256        TEXT    NOT NULL,
        source_file_size     INTEGER,
        pdf_page_no          INTEGER,
        physical_page_no     INTEGER NOT NULL,
        printed_page         TEXT,
        page_image_path      TEXT,
        page_image_sha256    TEXT,
        ocr_md_path          TEXT,
        ocr_md_sha256        TEXT,
        ocr_engine           TEXT,
        ocr_model            TEXT,
        ocr_mode             TEXT,
        ocr_lines            INTEGER,
        ocr_mean_confidence  REAL,
        text_chars           INTEGER,
        citation_ready       INTEGER NOT NULL DEFAULT 0,
        needs_human_review   INTEGER NOT NULL DEFAULT 1,
        review_status        TEXT    NOT NULL DEFAULT 'review_only',
        machine_review_note  TEXT,
        human_review_note    TEXT,
        period               TEXT,
        year                 INTEGER,
        event_tags           TEXT,
        source_title         TEXT,
        batch_id             TEXT,
        created_at           TEXT,
        updated_at           TEXT,
        FOREIGN KEY (page_id) REFERENCES pages(id),
        FOREIGN KEY (document_id) REFERENCES documents(id),
        CHECK (citation_ready IN (0, 1)),
        CHECK (needs_human_review IN (0, 1)),
        CHECK (review_status IN ('review_only', 'machine_verified', 'needs_fix',
                                 'unreadable', 'human_verified'))
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_page_prov_page_key ON page_provenance(source_file, physical_page_no, document_id)",
    "CREATE INDEX IF NOT EXISTS idx_page_prov_source ON page_provenance(source_id, physical_page_no)",
    "CREATE INDEX IF NOT EXISTS idx_page_prov_review ON page_provenance(review_status, citation_ready)",
    "CREATE INDEX IF NOT EXISTS idx_page_prov_year ON page_provenance(year, physical_page_no)",
    "CREATE INDEX IF NOT EXISTS idx_page_prov_document ON page_provenance(document_id)",
]


def counts(conn: sqlite3.Connection) -> dict:
    out = {}
    for table in ("documents", "pages", "page_fts", "sources"):
        out[table] = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    has = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='page_provenance'"
    ).fetchone()[0]
    out["page_provenance_exists"] = bool(has)
    if has:
        out["page_provenance"] = conn.execute("SELECT count(*) FROM page_provenance").fetchone()[0]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(REPO / "data/research_index.sqlite"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    db = Path(args.db)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {"db": str(db), "run_timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
              "applied": False, "ddl": DDL}

    conn = sqlite3.connect(db)
    report["integrity_before"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
    report["counts_before"] = counts(conn)
    conn.close()
    if report["integrity_before"] != "ok":
        report["verdict"] = "ABORT_INTEGRITY_BEFORE"
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("ABORT: integrity_check failed before migration")
        return 1

    if not args.apply:
        report["verdict"] = "DRY_RUN_OK"
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("DRY RUN: would create table page_provenance + 5 indexes; no existing object touched")
        print(json.dumps(report["counts_before"], ensure_ascii=False))
        return 0

    backup = db.with_name(db.name + f".{stamp}.pre_page_provenance.bak")
    if backup.exists():
        raise SystemExit(f"backup already exists: {backup}")
    shutil.copy2(db, backup)
    report["backup"] = str(backup)
    print(f"backup -> {backup}")

    conn = sqlite3.connect(db)
    try:
        for stmt in DDL:
            conn.execute(stmt)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        conn.close()
        report["verdict"] = "FAILED"
        report["error"] = str(exc)
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"FAILED: {exc}; database untouched, restore from {backup} if needed")
        return 1

    report["integrity_after"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
    report["counts_after"] = counts(conn)
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    report["foreign_key_violations"] = len(fk)
    conn.close()

    ok = (report["integrity_after"] == "ok"
          and report["counts_after"]["documents"] == report["counts_before"]["documents"]
          and report["counts_after"]["pages"] == report["counts_before"]["pages"]
          and report["counts_after"]["page_fts"] == report["counts_before"]["page_fts"])
    report["applied"] = True
    report["verdict"] = "PASS" if ok else "CHECK_FAILED"
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{report['verdict']}: integrity_after={report['integrity_after']} "
          f"counts unchanged={ok} report -> {args.report}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
