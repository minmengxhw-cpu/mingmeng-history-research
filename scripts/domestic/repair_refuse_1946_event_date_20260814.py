#!/usr/bin/env python3
"""Correct the navigation-only event date for the 1946 refusal page.

The source document is a 1941--1949 compilation, but page 19000 identifies a
specific 1946-11-14 notice.  This migration changes only the existing
research_events date fields for that one page/topic link; it does not touch
page text, document metadata, provenance, citation gates, or source files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    before_sha = sha256(db)
    if before_sha != args.expected_sha:
        raise SystemExit(f"hash mismatch: expected {args.expected_sha}, got {before_sha}")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("BEGIN IMMEDIATE")
    rows = conn.execute(
        """
        SELECT re.id, re.event_date, re.event_year, re.page_id,
               re.scope_slug, d.doc_key, p.page_label,
               pp.citation_ready, pp.needs_human_review,
               pp.review_status, pp.human_review_note
        FROM research_events re
        JOIN pages p ON p.id=re.page_id
        JOIN documents d ON d.id=p.document_id
        LEFT JOIN page_provenance pp ON pp.page_id=p.id
        WHERE re.scope_slug=? AND re.page_id=? AND d.doc_key=? AND p.page_label=?
        """,
        (
            "domestic-1946-refuse-national-assembly",
            19000,
            "domestic-page/SRC-257bb7be70",
            "276",
        ),
    ).fetchall()
    if len(rows) != 1:
        conn.rollback()
        raise SystemExit(f"expected one target event row, got {len(rows)}")
    row = rows[0]
    if not (
        int(row["citation_ready"] or 0) == 1
        and int(row["needs_human_review"] or 0) == 0
        and str(row["review_status"] or "") == "human_verified"
        and str(row["human_review_note"] or "").strip()
    ):
        conn.rollback()
        raise SystemExit("target page no longer satisfies strict citation gate")

    conn.execute(
        """
        UPDATE research_events
        SET event_date=?, event_year=?
        WHERE id=?
        """,
        ("1946-11-14", "1946", int(row["id"])),
    )
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    if integrity != "ok" or foreign_keys:
        conn.rollback()
        raise SystemExit(f"validation failed: integrity={integrity}, foreign_keys={foreign_keys}")
    if args.apply:
        conn.commit()
    else:
        conn.rollback()
    conn.close()

    after_sha = sha256(db)
    if not args.apply and after_sha != before_sha:
        raise SystemExit("dry-run changed the database")
    result = {
        "report": "DOMESTIC_REFUSE_1946_EVENT_DATE_REPAIR_20260814",
        "mode": "apply" if args.apply else "dry-run",
        "page_id": 19000,
        "scope_slug": "domestic-1946-refuse-national-assembly",
        "old_event_date": str(row["event_date"] or ""),
        "old_event_year": str(row["event_year"] or ""),
        "new_event_date": "1946-11-14",
        "new_event_year": "1946",
        "body_text_changed": False,
        "source_metadata_changed": False,
        "provenance_changed": False,
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "integrity_check": integrity,
        "foreign_key_violations": foreign_keys,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "status": "PASS",
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
