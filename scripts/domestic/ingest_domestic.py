#!/usr/bin/env python3
"""Create/update isolated domestic research tables in the local SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS domestic_sources (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    institution TEXT NOT NULL,
    source_type TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    official_url TEXT,
    record_or_search_url TEXT,
    material_types TEXT NOT NULL,
    shanghai_relevance TEXT NOT NULL,
    access_mode TEXT NOT NULL,
    rights_status TEXT NOT NULL,
    verification_note TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS domestic_candidates (
    id INTEGER PRIMARY KEY,
    candidate_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    creator TEXT,
    document_date TEXT,
    document_type TEXT,
    repository_code TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    collection_name TEXT,
    archive_fonds TEXT,
    archive_series TEXT,
    archive_file TEXT,
    archive_item TEXT,
    catalog_reference TEXT NOT NULL,
    catalog_reference_status TEXT NOT NULL,
    source_url TEXT,
    source_url_role TEXT,
    access_mode TEXT NOT NULL,
    access_note TEXT NOT NULL,
    medium TEXT,
    online_availability TEXT,
    rights_status TEXT NOT NULL,
    reuse_rights TEXT,
    rights_basis TEXT,
    copy_allowed TEXT,
    authenticity_level_proposed TEXT NOT NULL,
    relevance_grade_proposed TEXT NOT NULL,
    event_tags TEXT NOT NULL,
    person_tags TEXT NOT NULL,
    place_tags TEXT NOT NULL,
    evidence_note TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_locator TEXT,
    uncertainty_note TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    checked_by TEXT NOT NULL,
    review_status TEXT NOT NULL,
    review_note TEXT,
    reviewed_at TEXT,
    reviewed_by TEXT,
    check_outcome TEXT,
    authenticity_level_accepted TEXT,
    relevance_grade_accepted TEXT,
    inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS domestic_editorial_decisions (
    id INTEGER PRIMARY KEY,
    candidate_id TEXT NOT NULL UNIQUE,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    next_action TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    decided_by TEXT NOT NULL
);
"""


def value(row: dict[str, object], key: str) -> object:
    return row.get(key)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/research_index.sqlite"))
    parser.add_argument("--sources", type=Path, default=Path("data/domestic/source_registry.json"))
    parser.add_argument("--candidates", type=Path, default=Path("data/domestic/candidates.jsonl"))
    args = parser.parse_args()

    sources = json.loads(args.sources.read_text(encoding="utf-8"))
    candidate_records = [
        json.loads(line)
        for line in args.candidates.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    discovery_only_ids = {
        str(candidate["candidate_id"])
        for candidate in candidate_records
        if candidate.get("formal_candidate", True) is False
    }
    candidates = [
        candidate
        for candidate in candidate_records
        if candidate.get("formal_candidate", True) is not False
    ]

    with sqlite3.connect(args.db) as conn:
        conn.executescript(SCHEMA)
        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(domestic_candidates)")}
        for column in ("authenticity_level_accepted", "relevance_grade_accepted"):
            if column not in existing_columns:
                conn.execute(f"ALTER TABLE domestic_candidates ADD COLUMN {column} TEXT")
        if discovery_only_ids:
            placeholders = ", ".join("?" for _ in discovery_only_ids)
            existing_discovery_only = {
                str(row[0])
                for row in conn.execute(
                    f"SELECT candidate_id FROM domestic_candidates WHERE candidate_id IN ({placeholders})",
                    tuple(sorted(discovery_only_ids)),
                )
            }
            if existing_discovery_only:
                raise RuntimeError(
                    "discovery-only candidates already exist in the formal database: "
                    + ", ".join(sorted(existing_discovery_only))
                )
        conn.executemany(
            """INSERT INTO domestic_sources
            (source_id, source_name, institution, source_type, authority_level,
             official_url, record_or_search_url, material_types, shanghai_relevance,
             access_mode, rights_status, verification_note, checked_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
              source_name=excluded.source_name, institution=excluded.institution,
              source_type=excluded.source_type, authority_level=excluded.authority_level,
              official_url=excluded.official_url, record_or_search_url=excluded.record_or_search_url,
              material_types=excluded.material_types, shanghai_relevance=excluded.shanghai_relevance,
              access_mode=excluded.access_mode, rights_status=excluded.rights_status,
              verification_note=excluded.verification_note, checked_at=excluded.checked_at,
              status=excluded.status""",
            [(
                s["source_id"], s["source_name"], s["institution"], s["source_type"], s["authority_level"],
                s.get("official_url"), s.get("record_or_search_url"), json.dumps(s.get("material_types", []), ensure_ascii=False),
                s["shanghai_relevance"], s["access_mode"], s["rights_status"], s["verification_note"], s["checked_at"], s["status"]
            ) for s in sources],
        )

        columns = [
            "candidate_id", "title", "creator", "document_date", "document_type", "repository_code", "repository_name",
            "collection_name", "archive_fonds", "archive_series", "archive_file", "archive_item", "catalog_reference",
            "catalog_reference_status", "source_url", "source_url_role", "access_mode", "access_note", "medium",
            "online_availability", "rights_status", "reuse_rights", "rights_basis", "copy_allowed",
            "authenticity_level_proposed", "relevance_grade_proposed", "event_tags", "person_tags", "place_tags",
            "evidence_note", "evidence_type", "evidence_locator", "uncertainty_note", "checked_at", "checked_by",
            "review_status", "review_note", "reviewed_at", "reviewed_by", "check_outcome",
            "authenticity_level_accepted", "relevance_grade_accepted"
        ]
        sql = f"INSERT INTO domestic_candidates ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) ON CONFLICT(candidate_id) DO UPDATE SET " + ", ".join(f"{col}=excluded.{col}" for col in columns[1:])
        conn.executemany(
            sql,
            [tuple(json.dumps(c.get(col, []), ensure_ascii=False) if col in {"event_tags", "person_tags", "place_tags"} else value(c, col) for col in columns) for c in candidates],
        )
        conn.executemany(
            """INSERT INTO domestic_editorial_decisions
               (candidate_id, decision, rationale, next_action, decided_at, decided_by)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(candidate_id) DO UPDATE SET
                 decision=excluded.decision, rationale=excluded.rationale,
                 next_action=excluded.next_action, decided_at=excluded.decided_at,
                 decided_by=excluded.decided_by""",
            [(
                c["candidate_id"],
                "accepted" if c.get("review_status") == "accepted" else
                "rejected" if c.get("review_status") in {"rejected", "duplicate"} else
                "hold_for_human_review",
                c.get("review_note") or c.get("uncertainty_note") or "待人工复核",
                "保留为核心证据" if c.get("review_status") == "accepted" else
                "保留线索并补齐形成者、档号/卷期、页码/影像和权利" if c.get("review_status") not in {"rejected", "duplicate"} else
                "记录排除或重复原因",
                c.get("reviewed_at") or c.get("checked_at") or "",
                c.get("reviewed_by") or c.get("checked_by") or "codex",
            ) for c in candidates],
        )
        source_count = conn.execute("SELECT count(*) FROM domestic_sources").fetchone()[0]
        candidate_count = conn.execute("SELECT count(*) FROM domestic_candidates").fetchone()[0]
        pending_count = conn.execute("SELECT count(*) FROM domestic_candidates WHERE review_status != 'accepted'").fetchone()[0]
        decision_count = conn.execute("SELECT count(*) FROM domestic_editorial_decisions").fetchone()[0]
    print(json.dumps({
        "domestic_sources": source_count,
        "domestic_candidates": candidate_count,
        "discovery_only_skipped": len(discovery_only_ids),
        "pending_review": pending_count,
        "editorial_decisions": decision_count,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
