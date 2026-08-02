#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create de-duplicated review units while preserving every provenance row."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/claim_review_units"


def rank(priority: str | None) -> int:
    return {"P0": 0, "P1": 1, "P2": 2}.get(priority or "", 9)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT e.candidate_id, e.provenance_id, e.canonical_document_key,
               e.physical_page_no, e.candidate_text_sha256, e.source_title,
               e.period, t.priority, t.triage_class, t.triage_status,
               c.card_id, d.group_id AS exact_duplicate_group_id
        FROM evidence_claim_candidates e
        JOIN evidence_claim_semantic_triage t ON t.candidate_id=e.candidate_id
        LEFT JOIN evidence_claim_cards c ON c.candidate_id=e.candidate_id
        LEFT JOIN evidence_claim_duplicate_groups d
          ON d.candidate_id=e.candidate_id
         AND d.duplicate_type='EXACT_CANDIDATE_TEXT_SHA'
        WHERE t.triage_status='MACHINE_TRIAGE_REVIEW_REQUIRED'
        ORDER BY e.candidate_id
        """
    ).fetchall()
    groups = defaultdict(list)
    for row in rows:
        groups[row["candidate_text_sha256"] or row["candidate_id"]].append(row)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_review_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id TEXT NOT NULL UNIQUE,
            representative_candidate_id TEXT NOT NULL UNIQUE,
            exact_duplicate_group_id TEXT,
            member_count INTEGER NOT NULL,
            unit_kind TEXT NOT NULL,
            priority TEXT,
            triage_class TEXT,
            canonical_document_key TEXT,
            physical_page_no INTEGER,
            member_candidate_ids_json TEXT NOT NULL,
            review_status TEXT NOT NULL,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    units = []
    priority_counts = Counter()
    kind_counts = Counter()
    for index, members in enumerate(sorted(groups.values(), key=lambda m: min(x["candidate_id"] for x in m)), start=1):
        members = sorted(members, key=lambda r: (rank(r["priority"]), r["candidate_id"]))
        representative = members[0]
        unit_id = f"REVIEW-UNIT-{index:04d}"
        unit_kind = "EXACT_TEXT_REPRESENTATIVE" if len(members) > 1 else "SINGLE_CANDIDATE"
        item = {
            "unit_id": unit_id,
            "representative_candidate_id": representative["candidate_id"],
            "exact_duplicate_group_id": representative["exact_duplicate_group_id"],
            "member_count": len(members),
            "unit_kind": unit_kind,
            "priority": representative["priority"],
            "triage_class": representative["triage_class"],
            "canonical_document_key": representative["canonical_document_key"],
            "physical_page_no": representative["physical_page_no"],
            "member_candidate_ids": [row["candidate_id"] for row in members],
            "review_status": "REVIEW_UNIT_MACHINE_ONLY",
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
            "next_action": "先核对代表候选原件/页图，再回看同组成员是否同一 OCR 版本或不同文本",
        }
        conn.execute(
            """
            INSERT INTO evidence_claim_review_units
            (unit_id,representative_candidate_id,exact_duplicate_group_id,member_count,
             unit_kind,priority,triage_class,canonical_document_key,physical_page_no,
             member_candidate_ids_json,review_status,semantic_validation_done,
             citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(unit_id) DO UPDATE SET
              representative_candidate_id=excluded.representative_candidate_id,
              exact_duplicate_group_id=excluded.exact_duplicate_group_id,
              member_count=excluded.member_count,
              unit_kind=excluded.unit_kind,
              priority=excluded.priority,
              triage_class=excluded.triage_class,
              canonical_document_key=excluded.canonical_document_key,
              physical_page_no=excluded.physical_page_no,
              member_candidate_ids_json=excluded.member_candidate_ids_json,
              review_status=excluded.review_status,
              semantic_validation_done=0,
              citation_ready=0,
              human_verified=0
            """,
            (item["unit_id"], item["representative_candidate_id"], item["exact_duplicate_group_id"], item["member_count"],
             item["unit_kind"], item["priority"], item["triage_class"], item["canonical_document_key"], item["physical_page_no"],
             json.dumps(item["member_candidate_ids"], ensure_ascii=False), item["review_status"], 0, 0, 0),
        )
        units.append(item)
        priority_counts[item["priority"] or "UNSET"] += 1
        kind_counts[unit_kind] += 1
    conn.commit()
    report = {
        "run_id": "claim_review_units_20260730",
        "input_ready_candidates": len(rows),
        "review_units": len(units),
        "candidate_members_preserved": sum(item["member_count"] for item in units),
        "priority_counts": dict(priority_counts),
        "unit_kind_counts": dict(kind_counts),
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "rows_deleted": 0,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "REVIEW_UNITS.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in units) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
