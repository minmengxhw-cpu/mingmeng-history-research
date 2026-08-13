#!/usr/bin/env python3
"""Apply bounded visual reviews for two 1946 *Guangming Bao* issues.

This migration changes only page-level provenance and citation scope for three
existing pages.  It does not read or rewrite OCR, PDF bytes, page images, or
page body text.  The citation gate is intentionally limited to issue identity,
date, PDF/physical page, layout, and the visible editorial title.

Dry-run is the default.  Applying requires a new, non-overwriting backup.
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
DEFAULT_REPORT = ROOT / "work" / "domestic" / "guangmingbao_1946_issue8_11_visual_review_20260814" / "APPLY_REPORT.json"
EXPECTED_DB_SHA = "94746937a0b71be94c18af474ef285503dabe95f0cee5dd652459d5216e1ae1b"
SCOPE = "review_scope=periodical_issue_identity_editorial_title"
BATCH_ID = "guangmingbao-1946-issues8-11-visual-review-20260814"

TARGETS = [
    {
        "page_id": 16367,
        "doc_key": "domestic-page/NLC404-01J000514-10429",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-10429_光明報_1946年8期.pdf",
        "source_sha256": "a0953d77e33497a9af58d458818a2cbafae011e76ef88f0901ac4a11e4702773",
        "source_title": "《光明報》1946 年8期",
        "pdf_page_no": 1,
        "physical_page_no": 1,
        "year": 1946,
        "period": "1946-08",
        "page_url": "https://commons.wikimedia.org/wiki/File:NLC404-01J000514-10429_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B48%E6%9C%9F.pdf#page=1",
        "event_tags": "pcc_1946,topic=domestic-1946-refuse-national-assembly",
        "note": "本地原始PDF第1页视觉复核确认《光明報》新八號、民国三十五年八月及《论有条件参加国大》版面标题；仅开放刊期、日期、PDF/物理页、版面和社论题名，不把OCR正文作为逐字引文，也不把同期机关报社论当作民盟正式拒参声明。",
    },
    {
        "page_id": 16634,
        "doc_key": "domestic-page/NLC404-01J000514-23806",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
        "source_sha256": "5b95a725e79886275c6cac9046d23651ad88bbe56f0895ba89de9c73864d6d83",
        "source_title": "《光明報》1946 年11期",
        "pdf_page_no": 1,
        "physical_page_no": 1,
        "year": 1946,
        "period": "1946-09",
        "page_url": "https://commons.wikimedia.org/wiki/File:NLC404-01J000514-23806_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B411%E6%9C%9F.pdf#page=1",
        "event_tags": "pcc_1946,topic=domestic-1946-refuse-national-assembly",
        "note": "本地原始PDF第1页视觉复核确认《光明報》新十一號、民国三十五年九月十三日、目录页及《反对一党独裁宪法（社论）》目录项；仅开放刊期、日期、PDF/物理页、版面和目录题名，不把目录或OCR正文作为逐字引文，也不把同期机关报社论当作民盟正式拒参声明。",
    },
    {
        "page_id": 16636,
        "doc_key": "domestic-page/NLC404-01J000514-23806",
        "source_file": "data/domestic/press_scans/NLC404-01J000514-23806_光明報_1946年11期.pdf",
        "source_sha256": "5b95a725e79886275c6cac9046d23651ad88bbe56f0895ba89de9c73864d6d83",
        "source_title": "《光明報》1946 年11期",
        "pdf_page_no": 3,
        "physical_page_no": 3,
        "year": 1946,
        "period": "1946-09",
        "page_url": "https://commons.wikimedia.org/wiki/File:NLC404-01J000514-23806_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B411%E6%9C%9F.pdf#page=3",
        "event_tags": "pcc_1946,topic=domestic-1946-refuse-national-assembly",
        "note": "本地原始PDF第3页视觉复核确认《反对一党独裁的宪法！》正文首页标题及期号页眉；仅开放刊期、日期、PDF/物理页、版面和社论题名，不把OCR正文作为逐字引文，也不把同期机关报社论当作民盟正式拒参声明。",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute(
        """SELECT count(*) FROM page_provenance
           WHERE citation_ready=1 AND needs_human_review=0
             AND review_status='human_verified'
             AND trim(COALESCE(human_review_note,''))<>''"""
    ).fetchone()[0])


def exact_page(url: str, expected: int) -> bool:
    fragment = urlsplit(url or "").fragment
    match = re.fullmatch(r"page=0*(\d+)", fragment)
    return bool(match and int(match.group(1)) == expected)


def merged_tags(current: str, additions: str) -> str:
    values = [value.strip() for value in (current or "").split(",") if value.strip()]
    for value in additions.split(","):
        value = value.strip()
        if value and value not in values:
            values.append(value)
    if SCOPE not in values:
        values.append(SCOPE)
    return ",".join(values)


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
    rows: dict[int, sqlite3.Row] = {}
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        for item in TARGETS:
            row = conn.execute(
                """SELECT p.id, p.page_label, p.page_url, d.doc_key,
                          d.source_platform, pp.source_file, pp.source_sha256,
                          pp.source_file_size, pp.pdf_page_no, pp.physical_page_no,
                          pp.review_status, pp.citation_ready, pp.needs_human_review,
                          pp.event_tags
                   FROM pages p JOIN documents d ON d.id=p.document_id
                   JOIN page_provenance pp ON pp.page_id=p.id
                   WHERE p.id=?""",
                (item["page_id"],),
            ).fetchone()
            if row is None:
                errors.append(f"page {item['page_id']} missing")
                continue
            rows[item["page_id"]] = row
            checks = {
                "doc_key": (str(row["doc_key"] or ""), item["doc_key"]),
                "source_platform": (str(row["source_platform"] or ""), "domestic"),
                "source_file": (str(row["source_file"] or ""), item["source_file"]),
                "source_sha256": (str(row["source_sha256"] or "").lower(), item["source_sha256"]),
                "pdf_page_no": (int(row["pdf_page_no"] or 0), item["pdf_page_no"]),
                "physical_page_no": (int(row["physical_page_no"] or 0), item["physical_page_no"]),
            }
            for name, (actual, expected) in checks.items():
                if actual != expected:
                    errors.append(f"page {item['page_id']} {name}: {actual!r} != {expected!r}")
            source = db.parent.parent / item["source_file"]
            if not source.is_file():
                errors.append(f"page {item['page_id']} source missing: {source}")
            elif sha256(source) != item["source_sha256"]:
                errors.append(f"page {item['page_id']} source SHA256 mismatch")
            if not exact_page(item["page_url"], item["pdf_page_no"]):
                errors.append(f"page {item['page_id']} URL lacks exact PDF page anchor")
        before_count = strict_count(conn)

        if before_sha != EXPECTED_DB_SHA:
            errors.append(f"database SHA mismatch: expected {EXPECTED_DB_SHA}, got {before_sha}")
        if args.apply:
            if not args.backup:
                raise SystemExit("--backup is required with --apply")
            if args.backup.exists():
                raise SystemExit(f"backup already exists: {args.backup}")

        if errors:
            report = {
                "schema_version": 1,
                "mode": "apply" if args.apply else "dry_run",
                "database_sha_before": before_sha,
                "database_sha_after": before_sha,
                "page_ids": [item["page_id"] for item in TARGETS],
                "accepted_decisions": 0,
                "validation_errors": errors,
                "strict_citation_count_before": before_count,
                "strict_citation_count_after": before_count,
                "body_text_modified": False,
                "source_pdf_modified": False,
            }
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise SystemExit("validation failed: " + "; ".join(errors))

        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            if sha256(args.backup) != before_sha:
                raise SystemExit("backup verification failed")
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute("BEGIN IMMEDIATE")
            try:
                for item in TARGETS:
                    row = rows[item["page_id"]]
                    conn.execute("UPDATE pages SET page_url=? WHERE id=?", (item["page_url"], item["page_id"]))
                    conn.execute(
                        """UPDATE page_provenance
                           SET source_file=?, source_sha256=?, source_file_size=?,
                               pdf_page_no=?, physical_page_no=?, citation_ready=1,
                               needs_human_review=0, review_status='human_verified',
                               human_review_note=?, period=?, year=?, event_tags=?,
                               source_title=?, batch_id=?, updated_at=?
                           WHERE page_id=?""",
                        (
                            item["source_file"], item["source_sha256"], int(row["source_file_size"] or 0),
                            item["pdf_page_no"], item["physical_page_no"],
                            f"审核者：codex-visual-audit-20260814；{item['note']}",
                            item["period"], item["year"], merged_tags(str(row["event_tags"] or ""), item["event_tags"]),
                            item["source_title"], BATCH_ID, now, item["page_id"],
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
        after_count = strict_count(conn)

    after_sha = sha256(db)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": before_sha,
        "database_sha_after": after_sha,
        "page_ids": [item["page_id"] for item in TARGETS],
        "accepted_decisions": len(TARGETS),
        "validation_errors": [],
        "strict_citation_count_before": before_count,
        "strict_citation_count_after": after_count,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "citation_scope": "periodical_issue_identity_editorial_title",
        "body_text_modified": False,
        "source_pdf_modified": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
