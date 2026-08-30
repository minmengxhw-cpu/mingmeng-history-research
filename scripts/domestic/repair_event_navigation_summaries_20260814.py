#!/usr/bin/env python3
"""Remove OCR/body snippets from domestic event-navigation summaries.

Older event-link batches copied page text into ``research_events.event_summary``.
That made a navigation row look like a verified event record.  This bounded
repair keeps every event row and page link, but replaces only the summary field
with a body-free navigation statement.  It never reads or writes page text and
never deletes database records.
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
DEFAULT_LINKS = ROOT / "data" / "domestic" / "citation_event_links.json"
DEFAULT_REPORT = ROOT / "work" / "domestic" / "event_navigation_summary_repair_20260814.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rationales(path: Path) -> dict[tuple[str, str, str], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[tuple[str, str, str], str] = {}
    for raw in payload.get("links", []):
        if not isinstance(raw, dict):
            continue
        key = (
            str(raw.get("event_id") or "").strip(),
            str(raw.get("doc_key") or "").strip(),
            str(raw.get("page_label") or "").strip(),
        )
        rationale = str(raw.get("rationale") or "").strip()
        if all(key) and rationale:
            result[key] = rationale
    return result


def canonical_summary(event_title: str, rationale: str | None) -> str:
    if rationale:
        return (
            "专题导航关联（仅导航层，非事实断言）："
            + rationale
            + " 页面正文不在事件摘要中；正式论证仍须回到具体页级 provenance。"
        )
    return (
        "专题导航关联（仅导航层，非事实断言）："
        + (event_title or "未命名页")
        + "。该行只提供专题与页级定位，不携带页面正文，不替代原件核验或正式引文。"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    before_sha = sha256_file(args.db)
    rationales = load_rationales(args.links)
    changed = 0
    domestic_rows = 0
    old_body_like = 0
    old_length_total = 0
    new_length_total = 0

    with sqlite3.connect(args.db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT e.id, e.scope_slug, e.event_title, e.event_summary,
                   d.doc_key, p.page_label
            FROM research_events e
            JOIN pages p ON p.id=e.page_id
            JOIN documents d ON d.id=p.document_id
            WHERE d.source_platform='domestic'
              AND e.scope_slug LIKE 'domestic-%'
            ORDER BY e.id
            """
        ).fetchall()
        domestic_rows = len(rows)
        updates: list[tuple[str, int]] = []
        for row in rows:
            key = (str(row["scope_slug"] or ""), str(row["doc_key"] or ""), str(row["page_label"] or ""))
            rationale = rationales.get(key)
            new_summary = canonical_summary(str(row["event_title"] or ""), rationale)
            old_summary = str(row["event_summary"] or "")
            old_length_total += len(old_summary)
            new_length_total += len(new_summary)
            if old_summary != new_summary:
                changed += 1
                updates.append((new_summary, int(row["id"])))
            if any(marker in old_summary for marker in ("OCR", "…", "…", " 乳 ", "报 版 ", "期一十第")):
                old_body_like += 1

        before_counts = {
            "documents": int(conn.execute("SELECT count(*) FROM documents").fetchone()[0]),
            "pages": int(conn.execute("SELECT count(*) FROM pages").fetchone()[0]),
            "page_fts": int(conn.execute("SELECT count(*) FROM page_fts").fetchone()[0]),
            "research_events": int(conn.execute("SELECT count(*) FROM research_events").fetchone()[0]),
        }
        if args.apply and not args.backup:
            raise SystemExit("--backup is required with --apply")
        if args.apply and args.backup.exists():
            raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")
        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.db, args.backup)
            if sha256_file(args.backup) != before_sha:
                raise SystemExit("backup verification failed")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.executemany("UPDATE research_events SET event_summary=? WHERE id=?", updates)
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = len(conn.execute("PRAGMA foreign_key_check").fetchall())
                pages_without_fts = int(conn.execute("SELECT count(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL").fetchone()[0])
                fts_without_pages = int(conn.execute("SELECT count(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL").fetchone()[0])
                after_counts = {
                    "documents": int(conn.execute("SELECT count(*) FROM documents").fetchone()[0]),
                    "pages": int(conn.execute("SELECT count(*) FROM pages").fetchone()[0]),
                    "page_fts": int(conn.execute("SELECT count(*) FROM page_fts").fetchone()[0]),
                    "research_events": int(conn.execute("SELECT count(*) FROM research_events").fetchone()[0]),
                }
                if integrity != "ok" or foreign_keys or pages_without_fts or fts_without_pages or after_counts != before_counts:
                    raise RuntimeError(
                        f"validation failed: integrity={integrity}; fk={foreign_keys}; "
                        f"fts_missing={pages_without_fts}; fts_extra={fts_without_pages}; "
                        f"counts={before_counts}->{after_counts}"
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    after_sha = sha256_file(args.db)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": before_sha,
        "database_sha_after": after_sha,
        "domestic_event_rows": domestic_rows,
        "rows_changed": changed,
        "old_body_like_rows": old_body_like,
        "old_summary_chars": old_length_total,
        "new_summary_chars": new_length_total,
        "rationale_links_available": len(rationales),
        "body_text_read": False,
        "page_text_modified": False,
        "event_rows_deleted": 0,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "status": "PASS",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
