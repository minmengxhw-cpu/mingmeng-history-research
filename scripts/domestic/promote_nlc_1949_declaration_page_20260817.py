#!/usr/bin/env python3
"""Promote 1949 journal PDF page 220 to page-identity citation only.

The page title and 1949-09-30 date are visually confirmed. Body text is not
transcribed and OCR is not performed. This does not close the 1949 primary gap.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "research_index.sqlite"
SOURCE_FILE = "data/domestic/raw/public_sources/nlc_1949_first_plenary_conference_journal.pdf"
SOURCE_SHA256 = "20069c88dd8520e034f47beb614bca4c1c86ae6b8baf41aaf1988a13f95c7e4a"
PAGE_ID = 20937
PDF_PAGE = 220
LABEL = "pdf-220 / 宣言草案"
NOTE = (
    "审核者：grok-visual-audit-20260817；已查看本地PDF渲染页并核对来源SHA256、物理页220和页级provenance。"
    "可作为第一届全体会议宣言（草案）页的页级身份及1949-09-30日期线索；正文/OCR未核验，不转录正文。"
    "只确认草案题名、日期和页界，不逐字引用宣言正文，也不关闭完整会议档案缺口。"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    db = DB_PATH.resolve()
    source = ROOT / SOURCE_FILE
    if sha256(source) != SOURCE_SHA256:
        raise SystemExit("source SHA mismatch")
    before = sha256(db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """SELECT p.text, pp.source_file, pp.source_sha256, pp.pdf_page_no,
                  pp.review_status, pp.citation_ready, pp.needs_human_review, pp.ocr_mode
           FROM pages p JOIN page_provenance pp ON pp.page_id=p.id
           WHERE p.id=?""",
        (PAGE_ID,),
    ).fetchone()
    if row is None:
        raise SystemExit("page missing")
    if row["text"]:
        raise SystemExit("refusing to promote a page that already has body text")
    if row["source_file"] != SOURCE_FILE or row["source_sha256"] != SOURCE_SHA256:
        raise SystemExit("provenance source mismatch")
    if int(row["pdf_page_no"] or 0) != PDF_PAGE:
        raise SystemExit("pdf page mismatch")
    ready = {
        "page_id": PAGE_ID,
        "before_sha256": before,
        "current_status": row["review_status"],
        "citation_ready": row["citation_ready"],
    }
    if not args.apply:
        conn.close()
        print(json.dumps({"status": "READY", **ready}, ensure_ascii=False))
        return 0
    if args.backup is None:
        raise SystemExit("--backup is required with --apply")
    backup = args.backup if args.backup.is_absolute() else ROOT / args.backup
    if not backup.exists() or sha256(backup) != before:
        raise SystemExit("backup missing or hash mismatch")
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("BEGIN IMMEDIATE")
    conn.execute("UPDATE pages SET page_label=? WHERE id=?", (LABEL, PAGE_ID))
    conn.execute(
        """UPDATE page_provenance
           SET citation_ready=1, needs_human_review=0, review_status='human_verified',
               human_review_note=?, ocr_mode='not_performed', updated_at=?
           WHERE page_id=?""",
        (NOTE, now, PAGE_ID),
    )
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    if integrity != "ok" or fk:
        conn.rollback()
        raise SystemExit(f"validation failed integrity={integrity} fk={fk}")
    conn.commit()
    conn.close()
    print(json.dumps({"status": "APPLIED", "before_sha256": before, "after_sha256": sha256(db), "page_id": PAGE_ID}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
