#!/usr/bin/env python3
"""Close out the domestic evidence policy on the formal research index.

The migration is intentionally conservative:

* ``citation_ready`` means human-reviewed and must carry a human review note.
* Existing machine-verified pages remain searchable/readable but are demoted
  from formal citation status.
* Missing document dates are filled only from one unambiguous linked candidate
  date. No model inference or provenance-year guess is used.
* Dry-run uses a transaction rollback; apply creates and verifies a backup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_REPORT_DIR = ROOT / "work" / "closeout-20260813"
NOTE = "Closeout 20260813: formal citation requires human_verified plus human_review_note"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int | str:
    return conn.execute(sql, params).fetchone()[0]


def collect_metrics(conn: sqlite3.Connection) -> dict[str, int | str]:
    strict = """
        citation_ready = 1
        AND needs_human_review = 0
        AND review_status = 'human_verified'
        AND trim(COALESCE(human_review_note, '')) <> ''
    """
    return {
        "integrity_check": scalar(conn, "PRAGMA integrity_check"),
        "foreign_key_violations": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
        "documents": scalar(conn, "SELECT COUNT(*) FROM documents"),
        "domestic_documents": scalar(
            conn, "SELECT COUNT(*) FROM documents WHERE source_platform='domestic'"
        ),
        "pages": scalar(conn, "SELECT COUNT(*) FROM pages"),
        "domestic_pages": scalar(
            conn,
            """SELECT COUNT(*) FROM pages p JOIN documents d ON d.id=p.document_id
               WHERE d.source_platform='domestic'""",
        ),
        "page_fts": scalar(conn, "SELECT COUNT(*) FROM page_fts"),
        "pages_without_fts": scalar(
            conn,
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL",
        ),
        "fts_without_pages": scalar(
            conn,
            "SELECT COUNT(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL",
        ),
        "citation_ready_rows": scalar(
            conn, "SELECT COUNT(*) FROM page_provenance WHERE citation_ready=1"
        ),
        "strict_human_citation_rows": scalar(
            conn, f"SELECT COUNT(*) FROM page_provenance WHERE {strict}"
        ),
        "unsafe_citation_rows": scalar(
            conn,
            f"SELECT COUNT(*) FROM page_provenance WHERE citation_ready=1 AND NOT ({strict})",
        ),
        "domestic_pages_missing_provenance": scalar(
            conn,
            """SELECT COUNT(*) FROM pages p
               JOIN documents d ON d.id=p.document_id
               LEFT JOIN page_provenance pp ON pp.page_id=p.id
               WHERE d.source_platform='domestic' AND pp.page_id IS NULL""",
        ),
        "domestic_documents_missing_date": scalar(
            conn,
            """SELECT COUNT(*) FROM documents
               WHERE source_platform='domestic'
                 AND (date_guess IS NULL OR trim(date_guess)='')""",
        ),
    }


def migrate(conn: sqlite3.Connection) -> dict[str, int]:
    strict = """
        citation_ready = 1
        AND needs_human_review = 0
        AND review_status = 'human_verified'
        AND trim(COALESCE(human_review_note, '')) <> ''
    """
    change_start = conn.total_changes
    conn.execute(
        f"""
        UPDATE page_provenance
        SET citation_ready = 0,
            machine_review_note = CASE
                WHEN trim(COALESCE(machine_review_note, '')) = '' THEN ?
                WHEN instr(machine_review_note, ?) = 0 THEN machine_review_note || '; ' || ?
                ELSE machine_review_note
            END,
            updated_at = ?
        WHERE citation_ready = 1 AND NOT ({strict})
        """,
        (NOTE, NOTE, NOTE, datetime.now().isoformat(timespec="seconds")),
    )
    demoted = conn.total_changes - change_start

    # Use candidate dates only where exactly one distinct non-empty value maps
    # to the currently undated document. Ranges remain ranges; no date guessing.
    change_start = conn.total_changes
    conn.execute(
        """
        WITH candidate_dates AS (
            SELECT d.id AS document_id, MIN(trim(c.document_date)) AS document_date
            FROM documents d
            JOIN domestic_candidates c
              ON c.candidate_id = d.ingested_candidate_id
              OR c.ingested_document_id = d.id
            WHERE d.source_platform='domestic'
              AND (d.date_guess IS NULL OR trim(d.date_guess)='')
              AND c.document_date IS NOT NULL
              AND trim(c.document_date) <> ''
            GROUP BY d.id
            HAVING COUNT(DISTINCT trim(c.document_date)) = 1
        )
        UPDATE documents
        SET date_guess = (
            SELECT candidate_dates.document_date
            FROM candidate_dates
            WHERE candidate_dates.document_id = documents.id
        )
        WHERE id IN (SELECT document_id FROM candidate_dates)
        """
    )
    dated = conn.total_changes - change_start
    return {"citation_rows_demoted": demoted, "document_dates_backfilled": dated}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-sha")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")
    before_sha = sha256(db)
    if args.expected_sha and before_sha != args.expected_sha:
        raise SystemExit(f"hash mismatch: expected {args.expected_sha}, got {before_sha}")

    backup: Path | None = None
    if args.apply:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = db.with_name(f"{db.name}.pre_closeout_{stamp}.bak")
        shutil.copy2(db, backup)
        if sha256(backup) != before_sha:
            raise SystemExit("backup verification failed")

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys=ON")
    before = collect_metrics(conn)
    conn.execute("BEGIN IMMEDIATE")
    changes = migrate(conn)
    after = collect_metrics(conn)

    if after["integrity_check"] != "ok":
        conn.rollback()
        raise SystemExit(f"integrity check failed: {after['integrity_check']}")
    if after["foreign_key_violations"] != 0:
        conn.rollback()
        raise SystemExit(f"foreign key violations: {after['foreign_key_violations']}")
    if after["pages_without_fts"] or after["fts_without_pages"]:
        conn.rollback()
        raise SystemExit("FTS alignment failed")
    if after["unsafe_citation_rows"] != 0:
        conn.rollback()
        raise SystemExit("unsafe citation rows remain")

    if args.apply:
        conn.commit()
    else:
        conn.rollback()
    conn.close()

    after_sha = sha256(db)
    if not args.apply and after_sha != before_sha:
        raise SystemExit("dry-run changed the database")

    result = {
        "mode": "apply" if args.apply else "dry-run",
        "database": f"data/{db.name}",
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "backup": backup.name if backup else None,
        "before": before,
        "changes": changes,
        "after": after,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    output = args.report_dir / f"database_{result['mode']}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
