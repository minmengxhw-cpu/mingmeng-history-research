#!/usr/bin/env python3
"""Conservatively fill dates that are explicit in a domestic title.

The formal index contains a small number of OCR drafts whose date field was
left blank.  This script only uses an unambiguous year or year range printed
in the document title; it never infers a date from an event tag, file access
time, OCR text, or a broad historical period.  Dry-run is the default and an
apply requires an exact database SHA plus an external backup path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data/research_index.sqlite"
BATCH_ID = "domestic-explicit-date-backfill-20260813"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_title(title: str) -> str:
    return (
        title.replace("—", "-")
        .replace("–", "-")
        .replace("－", "-")
        .replace("﹣", "-")
    )


def explicit_title_date(title: str) -> tuple[str | None, str | None]:
    """Return a date only when the title contains one unambiguous date token."""

    text = normalize_title(title)
    ranges = re.findall(r"(?<!\d)((?:19|20)\d{2})\s*-\s*((?:19|20)\d{2})(?!\d)", text)
    if len(ranges) == 1:
        start, end = ranges[0]
        return f"{start}-{end}", "title_explicit_year_range"

    years_with_marker = re.findall(r"(?<!\d)((?:19|20)\d{2})年", text)
    if len(set(years_with_marker)) == 1:
        return years_with_marker[0], "title_explicit_chinese_year"
    if len(set(years_with_marker)) > 1:
        return None, None

    # This covers titles such as ``..._1946.pdf``.  It is deliberately
    # restricted to a single standalone historical year.
    standalone = re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", text)
    if len(set(standalone)) == 1:
        return standalone[0], "title_single_year_token"
    return None, None


def prepare(db_path: Path) -> dict:
    with sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, doc_key, title, date_guess
            FROM documents
            WHERE source_platform='domestic'
              AND trim(COALESCE(date_guess, ''))=''
            ORDER BY id
            """
        ).fetchall()

    candidates = []
    unresolved = []
    for row in rows:
        date_value, rule = explicit_title_date(str(row["title"] or ""))
        item = {
            "id": int(row["id"]),
            "doc_key": str(row["doc_key"]),
            "title": str(row["title"] or ""),
            "old_date_guess": row["date_guess"],
        }
        if date_value:
            item.update({"new_date_guess": date_value, "rule": rule})
            candidates.append(item)
        else:
            unresolved.append(item)

    return {
        "batch_id": BATCH_ID,
        "db_path": str(db_path),
        "formal_db_sha256": sha256_file(db_path.resolve()),
        "missing_date_rows_before": len(rows),
        "candidate_updates": candidates,
        "candidate_update_count": len(candidates),
        "unresolved_rows": unresolved,
        "unresolved_count": len(unresolved),
    }


def apply_updates(db_path: Path, candidates: list[dict], backup: Path) -> dict:
    actual_db = db_path.resolve()
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    updated = []
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN")
        for item in candidates:
            result = conn.execute(
                """
                UPDATE documents
                   SET date_guess=?
                 WHERE id=?
                   AND source_platform='domestic'
                   AND trim(COALESCE(date_guess, ''))=''
                """,
                (item["new_date_guess"], item["id"]),
            )
            if result.rowcount:
                updated.append({**item, "updated_at": now})
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        remaining = conn.execute(
            """
            SELECT count(*) FROM documents
            WHERE source_platform='domestic'
              AND trim(COALESCE(date_guess, ''))=''
            """
        ).fetchone()[0]
    return {
        "updated": updated,
        "updated_count": len(updated),
        "integrity_check": integrity,
        "foreign_key_violations": foreign_keys,
        "missing_date_rows_after": int(remaining),
        "backup": str(backup),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")
    prepared = prepare(db)
    report = {
        **prepared,
        "mode": "apply" if args.apply else "dry_run",
        "db_path": str(args.db),
        "gate": "PASS",
    }

    if args.apply:
        if not args.expected_db_sha or prepared["formal_db_sha256"] != args.expected_db_sha:
            raise SystemExit("--apply requires --expected-db-sha matching the current database")
        if not args.backup:
            raise SystemExit("--apply requires --backup outside the repository")
        result = apply_updates(db, prepared["candidate_updates"], args.backup.expanduser().resolve())
        report["apply_result"] = result
        report["formal_db_sha256_after"] = sha256_file(db)
        report["gate"] = (
            "PASS"
            if result["integrity_check"] == "ok" and result["foreign_key_violations"] == 0
            else "FAIL"
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
