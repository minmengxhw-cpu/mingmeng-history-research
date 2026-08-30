#!/usr/bin/env python3
"""Align the formal review state for the shared-boundary Minxian page.

Page 17295 was machine-labelled as a body page, but the bounded visual review
found an article/next-article layout boundary.  This migration changes only
the review disposition and provenance note.  It does not copy or rewrite OCR
body text, source files, page images, or event links.
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
PAGE_ID = 17295
DOC_KEY = "domestic-page/NLC404-00J001436-85450"
SOURCE_FILE = "data/domestic/press_scans/NLC404-00J001436-85450_民憲_第一卷第九期.pdf"
SOURCE_SHA256 = "b6e123c4d90e4b2b596a61e70758f3d0be22cbfbf63ee6ac7853f682de62d5df"
NEW_HUMAN_NOTE = (
    "2026-08-15原图复核：PDF第20页含文章与下一篇文章的版面交界，"
    "尚未完成栏位级切分；保留review_only，不作为《民主政治與非民主政治》的严格文章页。"
)
NEW_SCOPE_TAG = "review_scope=shared_page_boundary_pending_segmentation"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT p.id, d.doc_key, pp.source_file, pp.source_sha256,
                  pp.citation_ready, pp.needs_human_review, pp.review_status,
                  pp.human_review_note, pp.event_tags
           FROM pages p
           JOIN documents d ON d.id=p.document_id
           JOIN page_provenance pp ON pp.page_id=p.id
           WHERE p.id=?""",
        (PAGE_ID,),
    ).fetchone()


def validate(row: sqlite3.Row | None) -> list[str]:
    errors: list[str] = []
    if row is None:
        return [f"page {PAGE_ID} missing"]
    if row["doc_key"] != DOC_KEY:
        errors.append(f"unexpected doc_key={row['doc_key']}")
    if row["source_file"] != SOURCE_FILE or str(row["source_sha256"]).lower() != SOURCE_SHA256:
        errors.append("source provenance mismatch")
    if (int(row["citation_ready"] or 0), int(row["needs_human_review"] or 0), row["review_status"]) != (0, 0, "machine_verified"):
        errors.append(
            "expected current state (citation_ready=0, needs_human_review=0, review_status=machine_verified) "
            f"but got ({row['citation_ready']}, {row['needs_human_review']}, {row['review_status']})"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    before = sha256(db)
    if before != args.expected_sha.lower():
        raise SystemExit(f"database SHA mismatch: expected {args.expected_sha}, got {before}")
    source_path = db.parent.parent / SOURCE_FILE
    if not source_path.is_file() or sha256(source_path) != SOURCE_SHA256:
        raise SystemExit("source PDF is missing or has a different SHA256")

    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        row = fetch(conn)
        errors = validate(row)
        if errors:
            raise SystemExit("validation failed:\n- " + "\n- ".join(errors))
        if args.apply:
            if not args.backup:
                raise SystemExit("--backup is required with --apply")
            if args.backup.exists():
                raise SystemExit(f"refusing to overwrite existing backup: {args.backup}")
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            if sha256(args.backup) != before:
                raise SystemExit("backup SHA mismatch")
            current_tags = str(row["event_tags"] or "")
            updated_tags = current_tags if NEW_SCOPE_TAG in current_tags else f"{current_tags},{NEW_SCOPE_TAG}".strip(",")
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """UPDATE page_provenance
                       SET needs_human_review=1,
                           review_status='review_only',
                           human_review_note=?,
                           event_tags=?,
                           updated_at=?
                       WHERE page_id=?""",
                    (NEW_HUMAN_NOTE, updated_tags, now, PAGE_ID),
                )
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
                if integrity != "ok" or foreign_keys:
                    raise RuntimeError(f"SQLite validation failed: {integrity}; foreign_keys={len(foreign_keys)}")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        after_row = fetch(conn)

    after = sha256(db)
    report = {
        "schema": "domestic_minxian_v1n9_boundary_review_only.v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "page_id": PAGE_ID,
        "body_text_modified": False,
        "source_pdf_modified": False,
        "before": {
            "citation_ready": int(row["citation_ready"]),
            "needs_human_review": int(row["needs_human_review"]),
            "review_status": row["review_status"],
        },
        "after": {
            "citation_ready": int(after_row["citation_ready"]),
            "needs_human_review": int(after_row["needs_human_review"]),
            "review_status": after_row["review_status"],
        },
        "database_sha_before": before,
        "database_sha_after": after,
        "backup": str(args.backup) if args.apply and args.backup else "",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
