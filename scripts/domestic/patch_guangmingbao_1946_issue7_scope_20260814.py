#!/usr/bin/env python3
"""Correct the citation-scope label for the reviewed *Guangming Bao* page.

The prior bounded migration used the generic issue-identity token.  This
follow-up changes only the provenance event tag for page 16351 so the UI can
state the narrower, accurate scope: issue/date/PDF page/layout/editorial
title.  It never reads or rewrites page body text or the source PDF.
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
DEFAULT_REPORT = ROOT / "work" / "domestic" / "guangmingbao_1946_issue7_visual_review_20260814" / "SCOPE_PATCH_REPORT.json"
PAGE_ID = 16351
EXPECTED_DB_SHA = "70d35fcf77bd53c177dd8c35c4bd9b9aebb549f31952a4e27875885ea74b464b"
OLD_SCOPE = "review_scope=issue_identity_contents_only"
NEW_SCOPE = "review_scope=periodical_issue_identity_editorial_title"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    before_sha = sha256(db)
    errors: list[str] = []
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT p.id, d.doc_key, pp.event_tags, pp.citation_ready,
                      pp.needs_human_review, pp.review_status
               FROM pages p JOIN documents d ON d.id=p.document_id
               JOIN page_provenance pp ON pp.page_id=p.id
               WHERE p.id=?""",
            (PAGE_ID,),
        ).fetchone()
        if before_sha != EXPECTED_DB_SHA:
            errors.append(f"database SHA mismatch: expected {EXPECTED_DB_SHA}, got {before_sha}")
        if row is None:
            errors.append(f"page {PAGE_ID} missing")
        else:
            if str(row["doc_key"] or "") != "domestic-page/NLC404-01J000514-10428":
                errors.append("unexpected document for target page")
            tags = str(row["event_tags"] or "")
            if OLD_SCOPE not in tags:
                errors.append("old scope tag not present")
            if NEW_SCOPE in tags:
                errors.append("new scope tag already present")
            if (int(row["citation_ready"] or 0), int(row["needs_human_review"] or 0), row["review_status"]) != (1, 0, "human_verified"):
                errors.append("target page is not in the expected verified citation state")
        if errors:
            report = {
                "mode": "apply" if args.apply else "dry_run",
                "database_sha_before": before_sha,
                "database_sha_after": before_sha,
                "page_id": PAGE_ID,
                "validation_errors": errors,
                "body_text_modified": False,
                "source_pdf_modified": False,
            }
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise SystemExit("validation failed: " + "; ".join(errors))
        if args.apply:
            if not args.backup:
                raise SystemExit("--backup is required with --apply")
            if args.backup.exists():
                raise SystemExit(f"backup already exists: {args.backup}")
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            if sha256(args.backup) != before_sha:
                raise SystemExit("backup verification failed")
            tags = str(row["event_tags"])
            updated_tags = tags.replace(OLD_SCOPE, NEW_SCOPE, 1)
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    "UPDATE page_provenance SET event_tags=?, updated_at=? WHERE page_id=?",
                    (updated_tags, now, PAGE_ID),
                )
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
                if integrity != "ok" or foreign_keys:
                    raise RuntimeError(f"SQLite validation failed: {integrity}; foreign_keys={len(foreign_keys)}")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    after_sha = sha256(db)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": before_sha,
        "database_sha_after": after_sha,
        "page_id": PAGE_ID,
        "old_scope": OLD_SCOPE,
        "new_scope": NEW_SCOPE,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "body_text_modified": False,
        "source_pdf_modified": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
