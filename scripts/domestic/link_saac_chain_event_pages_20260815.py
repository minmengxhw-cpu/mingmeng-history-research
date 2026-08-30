#!/usr/bin/env python3
"""Add safe navigation links for the 1949 SAAC scan chain.

This is a navigation-layer migration only.  It links the eight formal
review-only pages to the curated domestic topic, but deliberately does not
copy OCR text into ``research_events.event_summary``.  The event index is not
a substitute for page-level human review or a formal citation.

Default mode is read-only.  ``--apply`` requires the exact current database
SHA and a new backup path.  The script only inserts additive rows and never
changes, moves, or deletes research files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_MANIFEST = ROOT / "data" / "domestic" / "saac_scan_manifest_1949_pcc_chain_20260815.json"
SCOPE_TYPE = "topic"
SCOPE_SLUG = "domestic-1949-new-pcc"
SCOPE_NAME = "1949年新政协筹备、民主人士北上与第一届全体会议"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "domestic_saac_scan_batch_manifest.v1":
        raise ValueError("unexpected SAAC scan manifest schema")
    if not isinstance(payload.get("items"), list) or not payload["items"]:
        raise ValueError("manifest items must be non-empty")
    return payload


def split_tags(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def collect_links(db: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    links: list[dict[str, Any]] = []
    seen_pages: set[int] = set()
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_events'"
        ).fetchone()
        if table is None:
            raise RuntimeError("research_events table is missing")
        for item in manifest["items"]:
            candidate = conn.execute(
                "SELECT candidate_id, ingested_document_id FROM domestic_candidates WHERE candidate_id=?",
                (item["candidate_id"],),
            ).fetchone()
            if candidate is None or candidate["ingested_document_id"] is None:
                raise RuntimeError(f"candidate is not linked: {item['candidate_id']}")
            document = conn.execute(
                "SELECT id, doc_key, title, date_guess, source_platform FROM documents WHERE doc_key=?",
                (item["doc_key"],),
            ).fetchone()
            if document is None:
                raise RuntimeError(f"document is missing: {item['doc_key']}")
            if int(document["id"]) != int(candidate["ingested_document_id"]):
                raise RuntimeError(f"candidate/document mismatch: {item['candidate_id']}")
            if document["source_platform"] != "domestic":
                raise RuntimeError(f"document is not domestic: {item['doc_key']}")
            pages = conn.execute(
                "SELECT id FROM pages WHERE document_id=? ORDER BY id", (document["id"],)
            ).fetchall()
            if len(pages) != len(item["pages"]):
                raise RuntimeError(
                    f"page count mismatch for {item['doc_key']}: {len(pages)} != {len(item['pages'])}"
                )
            event_tags = sorted(set(["saac_scan", "navigation_only", "review_only"] + split_tags(item.get("event_tags"))))
            actors = "; ".join(split_tags(item.get("person_tags")))
            places = "; ".join(split_tags(item.get("place_tags")))
            for page_row in pages:
                page_id = int(page_row["id"])
                if page_id in seen_pages:
                    raise RuntimeError(f"page appears more than once: {page_id}")
                seen_pages.add(page_id)
                existing = conn.execute(
                    """SELECT id FROM research_events
                       WHERE scope_type=? AND scope_slug=? AND page_id=?""",
                    (SCOPE_TYPE, SCOPE_SLUG, page_id),
                ).fetchone()
                links.append(
                    {
                        "scope_type": SCOPE_TYPE,
                        "scope_slug": SCOPE_SLUG,
                        "scope_name": SCOPE_NAME,
                        "page_id": page_id,
                        "event_date": item["date_guess"],
                        "event_year": str(item["date_guess"])[:4],
                        "event_title": item["title"],
                        "event_summary": (
                            "专题导航关联（仅导航层，非事实断言）：该页为国家档案局官方扫描图的 "
                            "OCR 检索入口，正文与人名数字仍需人工复核，不替代正式引文。"
                        ),
                        "actors": actors,
                        "tags": "; ".join(event_tags),
                        "places": places,
                        "organizations": "",
                        "importance": 10,
                        "existing_id": int(existing["id"]) if existing else None,
                    }
                )
    new_links = [row for row in links if row["existing_id"] is None]
    return {
        "manifest": str(manifest_path.resolve()),
        "batch_id": manifest["batch_id"],
        "scope_slug": SCOPE_SLUG,
        "link_count": len(links),
        "existing_count": len(links) - len(new_links),
        "new_count": len(new_links),
        "links": links,
    }


def insert_links(conn: sqlite3.Connection, links: list[dict[str, Any]]) -> int:
    before = conn.total_changes
    for row in links:
        conn.execute(
            """INSERT OR IGNORE INTO research_events(
                scope_type, scope_slug, scope_name, page_id, event_date, event_year,
                event_title, event_summary, actors, tags, places, organizations, importance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["scope_type"], row["scope_slug"], row["scope_name"], row["page_id"],
                row["event_date"], row["event_year"], row["event_title"],
                row["event_summary"], row["actors"], row["tags"], row["places"],
                row["organizations"], row["importance"],
            ),
        )
    return conn.total_changes - before


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    if args.apply == args.dry_run:
        parser.error("choose exactly one of --dry-run or --apply")
    db = args.db.expanduser().resolve()
    manifest = args.manifest.expanduser().resolve()
    before_sha = sha256(db)
    if args.apply and args.expected_db_sha and before_sha != args.expected_db_sha:
        raise SystemExit(f"database SHA mismatch: got {before_sha}, expected {args.expected_db_sha}")
    plan = collect_links(db, manifest)
    if args.dry_run:
        print(json.dumps({"status": "READY", "formal_db_sha256": before_sha, **{key: value for key, value in plan.items() if key != "links"}}, ensure_ascii=False, indent=2))
        return 0
    if not args.expected_db_sha or not args.backup:
        parser.error("--apply requires --expected-db-sha and --backup")
    backup = args.backup.expanduser().resolve()
    if backup.exists():
        raise SystemExit(f"refusing to overwrite backup: {backup}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db, backup)
    if sha256(backup) != before_sha:
        raise RuntimeError("formal DB backup SHA mismatch")
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN IMMEDIATE")
        inserted = insert_links(conn, plan["links"])
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        linked = conn.execute(
            "SELECT COUNT(*) FROM research_events WHERE scope_type=? AND scope_slug=?",
            (SCOPE_TYPE, SCOPE_SLUG),
        ).fetchone()[0]
    print(json.dumps({
        "status": "APPLIED",
        "batch_id": plan["batch_id"],
        "scope_slug": SCOPE_SLUG,
        "planned_links": plan["link_count"],
        "inserted_links": inserted,
        "scope_links_after": linked,
        "before_db_sha256": before_sha,
        "after_db_sha256": sha256(db),
        "backup": str(backup),
        "integrity_check": integrity,
        "foreign_key_violations": fk,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
