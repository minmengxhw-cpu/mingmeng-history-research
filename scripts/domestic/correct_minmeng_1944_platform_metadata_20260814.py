#!/usr/bin/env python3
"""Correct non-body metadata on the four already-reviewed 1944 pages.

The visual review established page identity and PDF anchors, not OCR accuracy.
This reversible correction only restores the OCR status tag to real_page_ocr;
it does not alter page text, provenance hashes, citation gates, or source PDFs.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "research_index.sqlite"
EXPECTED_SHA = "dd380aad474d941d51dc6b491390fa042ceb344af26643c6959d03be66a9f2c7"
PAGE_IDS = (20141, 20142, 20143, 20144)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    db = args.db.expanduser()
    before = sha256_file(db)
    if before != EXPECTED_SHA:
        raise SystemExit(f"database SHA mismatch: expected {EXPECTED_SHA}, got {before}")
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT page_id,event_tags FROM page_provenance WHERE page_id IN (20141,20142,20143,20144) ORDER BY page_id"
        ).fetchall()
        if [int(row["page_id"]) for row in rows] != list(PAGE_IDS):
            raise SystemExit("expected four 1944 provenance rows")
        changes = []
        for row in rows:
            tags = str(row["event_tags"] or "")
            if "ocr_status=human_verified" in tags:
                changes.append((int(row["page_id"]), tags.replace("ocr_status=human_verified", "ocr_status=real_page_ocr")))
            elif "ocr_status=real_page_ocr" in tags:
                changes.append((int(row["page_id"]), tags))
            else:
                raise SystemExit(f"page_id={row['page_id']} has no expected OCR status tag")
        if args.apply:
            if not args.backup:
                raise SystemExit("--backup is required with --apply")
            if args.backup.exists():
                raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute("BEGIN IMMEDIATE")
            try:
                for page_id, tags in changes:
                    conn.execute(
                        "UPDATE page_provenance SET event_tags=?, updated_at=? WHERE page_id=?",
                        (tags, now, page_id),
                    )
                if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("SQLite integrity check failed")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    after = sha256_file(db)
    print({"mode": "apply" if args.apply else "dry_run", "before": before, "after": after, "pages": list(PAGE_IDS), "changed": len(changes), "body_text_modified": False, "source_pdfs_modified": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
