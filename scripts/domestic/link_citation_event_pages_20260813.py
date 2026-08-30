#!/usr/bin/env python3
"""Add an auditable navigation link from strict citation pages to domestic topics.

The input manifest is deliberately curated and body-free.  This migration only
reads document/page metadata and the page provenance gate.  It never promotes
or changes citation status and never copies page text into the event index.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_LINKS = ROOT / "data" / "domestic" / "citation_event_links.json"
DEFAULT_COVERAGE = ROOT / "data" / "domestic" / "event_coverage.json"


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
        raise ValueError(f"invalid citation link manifest: {path}")
    return payload


def load_coverage(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"event coverage must be a JSON list: {path}")
    result = {}
    for item in payload:
        if not isinstance(item, dict) or not item.get("event_id"):
            continue
        event_id = str(item["event_id"])
        if event_id in result:
            raise ValueError(f"duplicate event_id in coverage: {event_id}")
        result[event_id] = item
    return result


def strict_provenance(row: sqlite3.Row) -> bool:
    return (
        int(row["citation_ready"] or 0) == 1
        and int(row["needs_human_review"] or 0) == 0
        and str(row["review_status"] or "") == "human_verified"
        and bool(str(row["human_review_note"] or "").strip())
    )


def collect_links(
    conn: sqlite3.Connection,
    payload: dict[str, object],
    coverage: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    seen: set[tuple[str, str, str]] = set()
    links: list[dict[str, object]] = []
    for raw in payload["links"]:
        if not isinstance(raw, dict):
            raise ValueError("citation link must be an object")
        event_id = str(raw.get("event_id") or "").strip()
        doc_key = str(raw.get("doc_key") or "").strip()
        page_label = str(raw.get("page_label") or "").strip()
        key = (event_id, doc_key, page_label)
        if not all(key):
            raise ValueError(f"incomplete citation link: {raw}")
        if key in seen:
            raise ValueError(f"duplicate citation link: {key}")
        seen.add(key)
        if event_id not in coverage:
            raise ValueError(f"citation link references unknown event: {event_id}")

        row = conn.execute(
            """
            SELECT d.id AS document_id, d.doc_key, d.title, d.date_guess,
                   d.source_platform, p.id AS page_id, p.page_label,
                   pp.citation_ready, pp.needs_human_review,
                   pp.review_status, pp.human_review_note
            FROM documents d
            JOIN pages p ON p.document_id=d.id AND p.page_label=?
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE d.doc_key=?
            """,
            (page_label, doc_key),
        ).fetchone()
        if row is None:
            raise ValueError(f"document/page not found: {doc_key} page {page_label}")
        if row["source_platform"] != "domestic":
            raise ValueError(f"non-domestic source in citation link: {doc_key}")
        if not strict_provenance(row):
            raise ValueError(f"citation gate failed: {doc_key} page {page_label}")

        event = coverage[event_id]
        event_name = str(event.get("event_name") or event_id)
        rationale = str(raw.get("rationale") or "").strip()
        navigation_title = str(raw.get("navigation_title") or row["title"] or doc_key).strip()
        if not rationale:
            raise ValueError(f"missing rationale: {key}")
        links.append(
            {
                "scope_type": "topic",
                "scope_slug": event_id,
                "scope_name": event_name,
                "page_id": int(row["page_id"]),
                "event_date": str(raw.get("event_date") or row["date_guess"] or ""),
                "event_year": year_from(raw.get("event_date"), row["date_guess"], doc_key),
                "event_title": navigation_title,
                "event_summary": (
                    "专题导航关联（仅导航层，非事实断言）："
                    + rationale
                    + " 已满足严格页级引用门禁；页面仍须在具体研究论证中按原件页码引用。"
                ),
                "actors": "",
                "tags": "导航层;严格可引用页",
                "places": "",
                "organizations": "",
                "importance": 20,
                "doc_key": doc_key,
                "page_label": page_label,
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
            (
                row["scope_type"], row["scope_slug"], row["scope_name"], row["page_id"],
                row["event_date"], row["event_year"], row["event_title"],
                row["event_summary"], row["actors"], row["tags"], row["places"],
                row["organizations"], row["importance"],
            ),
        )
    return conn.total_changes - before


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-sha")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    links_path = args.links.expanduser().resolve()
    coverage_path = args.coverage.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")
    before_sha = sha256(db)
    if args.expected_sha and before_sha != args.expected_sha:
        raise SystemExit(f"hash mismatch: expected {args.expected_sha}, got {before_sha}")

    payload = load_payload(links_path)
    coverage = load_coverage(coverage_path)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("BEGIN IMMEDIATE")
    links = collect_links(conn, payload, coverage)
    inserted = insert_links(conn, links)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    if integrity != "ok" or foreign_keys:
        conn.rollback()
        raise SystemExit(f"validation failed: integrity={integrity}, foreign_keys={foreign_keys}")
    if args.apply:
        conn.commit()
    else:
        conn.rollback()
    conn.close()

    after_sha = sha256(db)
    if not args.apply and after_sha != before_sha:
        raise SystemExit("dry-run changed the database")
    result = {
        "report": "DOMESTIC_CITATION_EVENT_LINKS_20260813",
        "mode": "apply" if args.apply else "dry-run",
        "database": str(db),
        "links_manifest": str(links_path),
        "coverage_events": len(coverage),
        "links_validated": len(links),
        "rows_inserted": inserted,
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "integrity_check": integrity,
        "foreign_key_violations": foreign_keys,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "status": "PASS",
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
