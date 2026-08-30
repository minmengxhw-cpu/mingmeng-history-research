#!/usr/bin/env python3
"""Apply the bounded metadata review for *Guangming Bao* issue 7.

This migration upgrades one existing page, not a new document.  It binds the
page to the public PDF URL and opens only the metadata-level citation scope
(issue/date/page/title).  OCR remains a locator and is not exposed as a
verbatim quotation.  Dry-run is the default; apply requires a new backup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import re

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_BATCH = ROOT / "work" / "domestic" / "guangmingbao_1946_issue7_visual_review_20260814" / "BATCH.json"
DEFAULT_DECISIONS = ROOT / "work" / "domestic" / "guangmingbao_1946_issue7_visual_review_20260814" / "REVIEW_DECISIONS.json"
DEFAULT_REPORT = ROOT / "work" / "domestic" / "guangmingbao_1946_issue7_visual_review_20260814" / "APPLY_REPORT.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute(
        """SELECT count(*) FROM page_provenance
           WHERE citation_ready=1 AND needs_human_review=0
             AND review_status='human_verified'
             AND trim(COALESCE(human_review_note,''))<>''"""
    ).fetchone()[0])


def exact_page(url: str, expected: int) -> bool:
    match = re.fullmatch(r"page=0*(\d+)", urlsplit(url or "").fragment)
    return bool(match and int(match.group(1)) == expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    batch = json.loads(args.batch.expanduser().read_text(encoding="utf-8"))
    decisions = json.loads(args.decisions.expanduser().read_text(encoding="utf-8"))
    pages = batch.get("pages") or []
    decision_rows = decisions.get("pages") or []
    if len(pages) != 1 or len(decision_rows) != 1:
        raise SystemExit("this bounded migration expects exactly one page and one decision")
    item = pages[0]
    decision = decision_rows[0]
    expected_db_sha = str(batch.get("database", {}).get("sha256") or "").lower()
    actual_db_sha = sha256(db)
    if expected_db_sha != actual_db_sha:
        raise SystemExit(f"database SHA mismatch: expected {expected_db_sha}, got {actual_db_sha}")
    if batch.get("body_text_included") is not False or decisions.get("body_text_included") is not False:
        raise SystemExit("body_text_included must be false")
    if decision.get("decision") != "human_verified" or len(str(decision.get("note") or "").strip()) < 20:
        raise SystemExit("decision must be human_verified with a 20+ character note")
    page_id = int(item["page_id"])
    source_file = str(item["source_file"])
    source = db.parent.parent / source_file
    errors: list[str] = []
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT p.id,p.page_label,p.page_url,d.doc_key,d.source_platform,
                      pp.source_file,pp.source_sha256,pp.source_file_size,
                      pp.pdf_page_no,pp.physical_page_no,pp.review_status,
                      pp.citation_ready,pp.needs_human_review
               FROM pages p JOIN documents d ON d.id=p.document_id
               JOIN page_provenance pp ON pp.page_id=p.id WHERE p.id=?""",
            (page_id,),
        ).fetchone()
        if row is None:
            errors.append(f"page {page_id} missing")
        else:
            checks = {
                "doc_key": (str(row["doc_key"] or ""), str(item["doc_key"])),
                "page_label": (str(row["page_label"] or ""), str(item["page_label"])),
                "source_platform": (str(row["source_platform"] or ""), "domestic"),
                "source_file": (str(row["source_file"] or ""), source_file),
                "source_sha256": (str(row["source_sha256"] or "").lower(), str(item["source_sha256"]).lower()),
                "source_file_size": (int(row["source_file_size"] or 0), int(item["source_file_size"])),
                "pdf_page_no": (int(row["pdf_page_no"] or 0), int(item["pdf_page_no"])),
                "physical_page_no": (int(row["physical_page_no"] or 0), int(item["physical_page_no"])),
            }
            for name, (actual, expected) in checks.items():
                if actual != expected:
                    errors.append(f"{name}: {actual!r} != {expected!r}")
            if not source.is_file() or sha256(source) != str(item["source_sha256"]).lower():
                errors.append("source PDF missing or SHA256 mismatch")
            if not exact_page(str(item["new_page_url"]), int(item["pdf_page_no"])):
                errors.append("new page URL lacks exact PDF page anchor")
        before = strict_count(conn)
        if errors:
            report = {
                "mode": "apply" if args.apply else "dry_run",
                "database_sha_before": actual_db_sha,
                "database_sha_after": actual_db_sha,
                "page_id": page_id,
                "accepted_decisions": 0,
                "validation_errors": errors,
                "strict_citation_count_before": before,
                "strict_citation_count_after": before,
                "body_text_included": False,
                "source_pdfs_modified": False,
            }
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise SystemExit("validation failed: " + "; ".join(errors))
        if args.apply and not args.backup:
            raise SystemExit("--backup is required with --apply")
        if args.apply and args.backup.exists():
            raise SystemExit(f"backup already exists: {args.backup}")
        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            if sha256(args.backup) != actual_db_sha:
                raise SystemExit("backup verification failed")
            note = f"审核者：{decision['reviewer']}；{decision['note']}"
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("UPDATE pages SET page_url=? WHERE id=?", (item["new_page_url"], page_id))
                conn.execute(
                    """UPDATE page_provenance
                       SET source_file=?, source_sha256=?, source_file_size=?,
                           pdf_page_no=?, physical_page_no=?, citation_ready=1,
                           needs_human_review=0, review_status='human_verified',
                           human_review_note=?, period=?, year=?, event_tags=?,
                           source_title=?, batch_id=?, updated_at=?
                       WHERE page_id=?""",
                    (
                        source_file, item["source_sha256"], int(item["source_file_size"]),
                        int(item["pdf_page_no"]), int(item["physical_page_no"]), note,
                        item["period"], int(item["year"]), item["event_tags"],
                        item["source_title"], batch.get("batch_id", ""), now, page_id,
                    ),
                )
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
                if integrity != "ok" or foreign_keys:
                    raise RuntimeError(f"SQLite validation failed: {integrity}; foreign_keys={len(foreign_keys)}")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        after = strict_count(conn)
    final_sha = sha256(db)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": actual_db_sha,
        "database_sha_after": final_sha,
        "batch_sha": expected_db_sha,
        "page_id": page_id,
        "decisions": 1,
        "accepted_decisions": 1,
        "validation_errors": [],
        "strict_citation_count_before": before,
        "strict_citation_count_after": after,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "body_text_included": False,
        "source_pdfs_modified": False,
        "citation_scope": "periodical_issue_identity_editorial_title",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
