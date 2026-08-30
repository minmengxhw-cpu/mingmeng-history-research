#!/usr/bin/env python3
"""Link explicitly curated domestic candidates to the shared event index.

This is a navigation-layer migration, not a fact or citation migration.

Only candidate IDs already listed in ``data/domestic/event_coverage.json`` are
considered.  A candidate must already point at a formal ``documents`` row and
that document must be on the ``domestic`` platform.  The script inserts one
shared event-index row per linked physical page, but never changes page text,
provenance, review status, or citation gates.

The default mode is a transaction dry-run.  ``--apply`` commits additive
``INSERT OR IGNORE`` rows and requires ``--expected-sha`` when supplied.  It
does not copy, move, or delete any local research file.
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
DEFAULT_COVERAGE = ROOT / "data" / "domestic" / "event_coverage.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact(text: object, limit: int = 260) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def as_tags(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raw = str(value or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        parsed = None
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in re.split(r"[;,；、]", raw) if item.strip()]


def year_from(*values: object) -> str:
    text = " ".join(str(value or "") for value in values)
    match = re.search(r"\b(19[4-5][0-9])\b", text)
    return match.group(1) if match else "未注明"


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the shared table only when a minimal formal DB lacks it."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS research_events (
            id INTEGER PRIMARY KEY,
            scope_type TEXT NOT NULL,
            scope_slug TEXT NOT NULL,
            scope_name TEXT NOT NULL,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            event_date TEXT,
            event_year TEXT,
            event_title TEXT NOT NULL,
            event_summary TEXT NOT NULL,
            actors TEXT,
            tags TEXT,
            places TEXT,
            organizations TEXT,
            importance INTEGER NOT NULL DEFAULT 0,
            UNIQUE(scope_type, scope_slug, page_id)
        );
        CREATE INDEX IF NOT EXISTS idx_research_events_scope ON research_events(scope_type, scope_slug);
        CREATE INDEX IF NOT EXISTS idx_research_events_page ON research_events(page_id);
        CREATE INDEX IF NOT EXISTS idx_research_events_year ON research_events(event_year);
        """
    )


def load_coverage(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("event coverage must be a JSON list")
    rows = [item for item in payload if isinstance(item, dict) and item.get("event_id")]
    if len({str(item["event_id"]) for item in rows}) != len(rows):
        raise ValueError("event coverage contains duplicate event_id")
    return rows


def collect_links(
    conn: sqlite3.Connection, coverage: list[dict[str, object]]
) -> list[dict[str, object]]:
    candidates = {
        str(row["candidate_id"]): row
        for row in conn.execute("SELECT * FROM domestic_candidates")
    }
    documents = {
        int(row["id"]): row
        for row in conn.execute(
            "SELECT id, doc_key, title, date_guess, source_platform FROM documents"
        )
    }
    pages_by_document: dict[int, list[sqlite3.Row]] = {}
    for row in conn.execute(
        "SELECT id, document_id, page_label, text FROM pages ORDER BY id"
    ):
        pages_by_document.setdefault(int(row["document_id"]), []).append(row)

    links: list[dict[str, object]] = []
    for event in coverage:
        event_id = str(event["event_id"])
        event_name = str(event.get("event_name") or event_id)
        event_tags = as_tags(event.get("event_tags"))
        grouped: dict[int, list[sqlite3.Row]] = {}
        for candidate_id in event.get("domestic_candidate_ids", []):
            candidate = candidates.get(str(candidate_id))
            if not candidate or candidate["ingested_document_id"] is None:
                continue
            try:
                document_id = int(candidate["ingested_document_id"])
            except (TypeError, ValueError):
                continue
            document = documents.get(document_id)
            # The coverage file can intentionally point at a foreign-side
            # comparison record.  The shared domestic event layer must not
            # relabel those pages as domestic.
            if not document or document["source_platform"] != "domestic":
                continue
            grouped.setdefault(document_id, []).append(candidate)

        for document_id, linked_candidates in grouped.items():
            document = documents[document_id]
            candidate_titles = sorted(
                {
                    str(row["title"] or "").strip()
                    for row in linked_candidates
                    if str(row["title"] or "").strip()
                }
            )
            candidate_ids = sorted({str(row["candidate_id"]) for row in linked_candidates})
            actors = sorted(
                {
                    tag
                    for row in linked_candidates
                    for tag in as_tags(row["person_tags"])
                }
            )
            places = sorted(
                {
                    tag
                    for row in linked_candidates
                    for tag in as_tags(row["place_tags"])
                }
            )
            tags = sorted(
                set(event_tags)
                | {
                    tag
                    for row in linked_candidates
                    for tag in as_tags(row["event_tags"])
                }
            )
            date_guess = str(document["date_guess"] or "").strip()
            if not date_guess:
                candidate_dates = sorted(
                    {
                        str(row["document_date"] or "").strip()
                        for row in linked_candidates
                        if str(row["document_date"] or "").strip()
                    }
                )
                date_guess = candidate_dates[0] if len(candidate_dates) == 1 else ""
            title_suffix = candidate_titles[0] if candidate_titles else str(document["title"] or "")
            summary_prefix = (
                f"国内专题导航关联：{title_suffix}。"
                "此关联来自已登记候选，不构成事实确认或正式引文。"
            )
            for page in pages_by_document.get(document_id, []):
                page_id = int(page["id"])
                links.append(
                    {
                        "scope_type": "topic",
                        "scope_slug": event_id,
                        "scope_name": event_name,
                        "page_id": page_id,
                        "event_date": date_guess,
                        "event_year": year_from(date_guess, document["doc_key"]),
                        "event_title": title_suffix or str(document["doc_key"]),
                        "event_summary": compact(
                            summary_prefix + (" " + str(page["text"] or "") if page["text"] else "")
                        ),
                        "actors": "; ".join(actors),
                        "tags": "; ".join(tags),
                        "places": "; ".join(places),
                        "organizations": "",
                        "importance": 10,
                        "candidate_ids": candidate_ids,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-sha")
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    coverage_path = args.coverage.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")
    if not coverage_path.is_file():
        raise SystemExit(f"coverage not found: {coverage_path}")
    before_sha = sha256(db)
    if args.expected_sha and before_sha != args.expected_sha:
        raise SystemExit(f"hash mismatch: expected {args.expected_sha}, got {before_sha}")

    coverage = load_coverage(coverage_path)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("BEGIN IMMEDIATE")
    ensure_schema(conn)
    links = collect_links(conn, coverage)
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
        "mode": "apply" if args.apply else "dry-run",
        "database": str(db),
        "coverage": str(coverage_path),
        "coverage_events": len(coverage),
        "candidate_page_links_considered": len(links),
        "rows_inserted": inserted,
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
