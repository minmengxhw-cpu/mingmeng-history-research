#!/usr/bin/env python3
"""Link existing foreign source pages to legacy event-card slugs.

This is a metadata-only, navigation-only migration.  It does not search or
copy page bodies, does not change citation gates, and requires an explicit
backup plus an exact database SHA before applying.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_LINKS = ROOT / "data" / "foreign_event_aliases.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def year_from(*values: object) -> str:
    text = " ".join(str(value or "") for value in values)
    match = re.search(r"\b(19[4-5][0-9])\b", text)
    return match.group(1) if match else "未注明"


def load_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("links"), list):
        raise ValueError(f"invalid alias manifest: {path}")
    return payload


def collect_links(conn: sqlite3.Connection, payload: dict[str, object]) -> list[dict[str, object]]:
    seen: set[tuple[str, int]] = set()
    links: list[dict[str, object]] = []
    for raw in payload["links"]:
        if not isinstance(raw, dict):
            raise ValueError("alias link must be an object")
        slug = str(raw.get("scope_slug") or "").strip()
        page_id = int(raw.get("page_id") or 0)
        key = (slug, page_id)
        if not slug or not page_id:
            raise ValueError(f"incomplete alias link: {raw}")
        if key in seen:
            raise ValueError(f"duplicate alias link: {key}")
        seen.add(key)
        row = conn.execute(
            """
            SELECT d.id AS document_id, d.doc_key, d.title, d.date_guess,
                   d.url, d.source_platform, p.id AS page_id, p.page_label,
                   p.page_url
            FROM pages p JOIN documents d ON d.id=p.document_id
            WHERE p.id=?
            """,
            (page_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"page not found: {page_id}")
        if str(row["source_platform"] or "") == "domestic":
            raise ValueError(f"domestic source cannot be foreign alias: {page_id}")
        if str(raw.get("doc_key") or "") != str(row["doc_key"] or ""):
            raise ValueError(f"doc_key mismatch for page {page_id}")
        if str(raw.get("page_label") or "") != str(row["page_label"] or ""):
            raise ValueError(f"page_label mismatch for page {page_id}")
        rationale = str(raw.get("rationale") or "").strip()
        if not rationale:
            raise ValueError(f"missing rationale for {key}")
        title = str(raw.get("event_title") or row["title"] or slug).strip()
        scope_name = str(raw.get("scope_name") or slug).strip()
        links.append(
            {
                "scope_type": "topic",
                "scope_slug": slug,
                "scope_name": scope_name,
                "page_id": page_id,
                "event_date": str(row["date_guess"] or ""),
                "event_year": year_from(row["date_guess"], row["doc_key"]),
                "event_title": title,
                "event_summary": "境外专题别名导航（仅导航层，非事实断言）：" + rationale,
                "actors": "",
                "tags": "境外别名;导航层",
                "places": "",
                "organizations": "",
                "importance": 10,
            }
        )
    return links


def insert_links(conn: sqlite3.Connection, links: list[dict[str, object]]) -> int:
    before = conn.total_changes
    for row in links:
        conn.execute(
            """
            INSERT OR IGNORE INTO research_events(
                scope_type, scope_slug, scope_name, page_id, event_date, event_year,
                event_title, event_summary, actors, tags, places, organizations, importance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[key] for key in (
                "scope_type", "scope_slug", "scope_name", "page_id", "event_date",
                "event_year", "event_title", "event_summary", "actors", "tags",
                "places", "organizations", "importance",
            )),
        )
    return conn.total_changes - before


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    before_sha = sha256(db)
    if before_sha != args.expected_sha:
        raise SystemExit(f"hash mismatch: expected {args.expected_sha}, got {before_sha}")
    payload = load_payload(args.links.expanduser().resolve())
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("BEGIN IMMEDIATE")
    links = collect_links(conn, payload)
    inserted = insert_links(conn, links)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    if integrity != "ok" or foreign_keys:
        conn.rollback()
        raise SystemExit(f"validation failed: integrity={integrity}, foreign_keys={foreign_keys}")
    if args.apply:
        if not args.backup:
            conn.rollback()
            raise SystemExit("--backup is required with --apply")
        if args.backup.exists():
            conn.rollback()
            raise SystemExit(f"backup already exists: {args.backup}")
        args.backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db, args.backup)
        conn.commit()
    else:
        conn.rollback()
    conn.close()
    after_sha = sha256(db)
    if not args.apply and after_sha != before_sha:
        raise SystemExit("dry-run changed the database")
    result = {
        "report": "FOREIGN_EVENT_ALIAS_LINKS_20260813",
        "mode": "apply" if args.apply else "dry-run",
        "body_read": False,
        "links_validated": len(links),
        "rows_inserted": inserted,
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "integrity_check": integrity,
        "foreign_key_violations": foreign_keys,
        "completed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
