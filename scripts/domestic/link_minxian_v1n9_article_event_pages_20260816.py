#!/usr/bin/env python3
"""Link the reviewed Minxian article pages to the 1944 domestic topic.

This additive migration writes navigation rows only.  It never copies page
text, changes source provenance, promotes evidence, or closes the 1944
reorganization primary gap.  Dry-run is the default; apply requires an exact
database SHA and a new backup path.
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
DEFAULT_DB = ROOT / "data/research_index.sqlite"
SOURCE_FILE = "data/domestic/press_scans/NLC404-00J001436-85450_民憲_第一卷第九期.pdf"
SOURCE_SHA256 = "b6e123c4d90e4b2b596a61e70758f3d0be22cbfbf63ee6ac7853f682de62d5df"
PAGE_IDS = (17291, 17292, 17293, 17294)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_count(conn: sqlite3.Connection) -> int:
    return int(
        conn.execute(
            """SELECT count(*) FROM page_provenance
               WHERE citation_ready=1 AND needs_human_review=0
                 AND review_status='human_verified'"""
        ).fetchone()[0]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--expected-sha")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser()
    actual_sha = sha256_file(db)
    if args.expected_sha and actual_sha != args.expected_sha.lower():
        raise SystemExit(f"database SHA mismatch: expected {args.expected_sha}, got {actual_sha}")
    source_path = db.resolve().parent.parent / SOURCE_FILE
    if not source_path.is_file() or sha256_file(source_path) != SOURCE_SHA256:
        raise SystemExit("source PDF is missing or has a different SHA256")

    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        rows = []
        errors: list[str] = []
        for page_id in PAGE_IDS:
            row = conn.execute(
                """SELECT p.id,p.page_label,d.doc_key,d.source_platform,
                          pp.source_file,pp.source_sha256,pp.pdf_page_no,
                          pp.physical_page_no,pp.citation_ready,pp.needs_human_review,
                          pp.review_status
                   FROM pages p JOIN documents d ON d.id=p.document_id
                   JOIN page_provenance pp ON pp.page_id=p.id
                   WHERE p.id=?""",
                (page_id,),
            ).fetchone()
            if row is None:
                errors.append(f"missing page_id={page_id}")
                continue
            if row["source_platform"] != "domestic":
                errors.append(f"page_id={page_id} is not domestic")
            if row["doc_key"] != "domestic-page/NLC404-00J001436-85450":
                errors.append(f"page_id={page_id} is not the canonical issue page chain")
            if row["source_file"] != SOURCE_FILE or str(row["source_sha256"]).lower() != SOURCE_SHA256:
                errors.append(f"page_id={page_id} source provenance mismatch")
            if int(row["pdf_page_no"] or 0) != int(row["physical_page_no"] or 0):
                errors.append(f"page_id={page_id} PDF/physical page mismatch")
            if not (row["citation_ready"] and not row["needs_human_review"] and row["review_status"] == "human_verified"):
                errors.append(f"page_id={page_id} is not strict human citation ready")
            rows.append(row)

        before_links = int(
            conn.execute(
                """SELECT count(*) FROM research_events
                   WHERE scope_type='topic' AND scope_slug='domestic-1944-reorganization'
                     AND page_id IN (17291,17292,17293,17294)"""
            ).fetchone()[0]
        )
        before_strict = strict_count(conn)
        if errors:
            raise SystemExit("validation failed:\n- " + "\n- ".join(errors))
        if args.apply and not args.backup:
            raise SystemExit("--backup is required with --apply")
        if args.apply and args.backup.exists():
            raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")

        inserted = 0
        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            conn.execute("BEGIN IMMEDIATE")
        try:
            for row in rows:
                cursor = conn.execute(
                    """INSERT OR IGNORE INTO research_events(
                           scope_type,scope_slug,scope_name,page_id,event_date,event_year,
                           event_title,event_summary,actors,tags,places,organizations,importance
                       ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "topic",
                        "domestic-1944-reorganization",
                        "1944年民盟改组前后",
                        int(row["id"]),
                        "1944-11-20",
                        "1944",
                        "民主政治與非民主政治",
                        "国内专题页级关联：1944年《民憲》同期政论文章原刊页。该关联只提供来源定位，不构成改组会议、改名决定或其他事实确认。",
                        "",
                        "1944改组更名;1944民主宪政论述",
                        "",
                        "",
                        10,
                    ),
                )
                inserted += int(cursor.rowcount > 0)
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
            if integrity != "ok" or foreign_keys:
                raise RuntimeError(f"SQLite validation failed: integrity={integrity}; foreign_keys={len(foreign_keys)}")
            if args.apply:
                conn.commit()
            else:
                conn.rollback()
        except Exception:
            if args.apply:
                conn.rollback()
            raise

        after_links = int(
            conn.execute(
                """SELECT count(*) FROM research_events
                   WHERE scope_type='topic' AND scope_slug='domestic-1944-reorganization'
                     AND page_id IN (17291,17292,17293,17294)"""
            ).fetchone()[0]
        )
        after_strict = strict_count(conn)

    final_sha = sha256_file(db)
    report = {
        "schema": "domestic_minxian_v1n9_event_link.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "body_text_included": False,
        "scope": "domestic-1944-reorganization",
        "page_ids": list(PAGE_IDS),
        "links_before": before_links,
        "links_after": after_links,
        "rows_inserted": inserted,
        "strict_citation_before": before_strict,
        "strict_citation_after": after_strict,
        "database_sha_before": actual_sha,
        "database_sha_after": final_sha,
        "backup": str(args.backup) if args.apply and args.backup else "",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
