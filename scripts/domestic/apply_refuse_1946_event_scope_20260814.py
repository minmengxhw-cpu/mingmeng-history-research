#!/usr/bin/env python3
"""Attach the 1946 refusal topic and conservative review scope to page 19000.

This is an additive provenance metadata migration.  It never changes page text,
OCR, source files, or citation gates.  ``--apply`` requires an exact database
SHA and a new backup path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
PAGE_ID = 19000
EXPECTED_DB_SHA = "03bb896b5e79706302e76b47075065ad3f55e7b1a6db54102773c411f6f17f75"
BATCH_ID = "refuse-1946-emergency-notice-visual-20260814"
SCOPE_TAGS = (
    "source_kind=official_compilation",
    "topic=domestic-1946-refuse-national-assembly",
    "evidence_role=official_compilation_refusal_statement",
    "review_scope=compiled_text_title_date_page_identity",
    f"review_batch={BATCH_ID}",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--expected-sha", default=EXPECTED_DB_SHA)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    before_sha = sha256(db)
    if args.expected_sha and before_sha != args.expected_sha:
        raise SystemExit(f"database SHA mismatch: expected {args.expected_sha}, got {before_sha}")

    with sqlite3.connect(db) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT page_id, citation_ready, needs_human_review, review_status, event_tags, period, year "
            "FROM page_provenance WHERE page_id=?",
            (PAGE_ID,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"page_id={PAGE_ID} provenance row missing")
        if not (
            int(row["citation_ready"] or 0) == 1
            and int(row["needs_human_review"] or 0) == 0
            and str(row["review_status"] or "") == "human_verified"
        ):
            raise SystemExit(f"page_id={PAGE_ID} is not strict after visual review")

        old_tags = str(row["event_tags"] or "")
        new_tags = old_tags
        for tag in SCOPE_TAGS:
            if tag not in new_tags.split(";"):
                new_tags = f"{new_tags};{tag}" if new_tags else tag

        if args.apply:
            if not args.backup:
                raise SystemExit("--backup is required with --apply")
            if args.backup.exists():
                raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "UPDATE page_provenance SET event_tags=?, period=?, year=?, batch_id=?, updated_at=? WHERE page_id=?",
                    (new_tags, "1946-11", 1946, BATCH_ID, datetime.now(timezone.utc).replace(microsecond=0).isoformat(), PAGE_ID),
                )
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = len(connection.execute("PRAGMA foreign_key_check").fetchall())
                if integrity != "ok" or foreign_keys:
                    raise RuntimeError(f"SQLite validation failed: {integrity}; foreign_keys={foreign_keys}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    after_sha = sha256(db)
    if not args.apply and after_sha != before_sha:
        raise SystemExit("dry-run changed the database")
    report = {
        "page_id": PAGE_ID,
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": before_sha,
        "database_sha_after": after_sha,
        "old_event_tags": old_tags,
        "new_event_tags": new_tags,
        "period": "1946-11",
        "year": 1946,
        "batch_id": BATCH_ID,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "body_text_modified": False,
        "source_files_modified": False,
        "status": "PASS",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
