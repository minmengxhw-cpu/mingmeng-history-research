#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit duplicate machine claim candidates without deleting any rows."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/claim_duplicate_audit"


def group_rows(rows, key_fn):
    groups = defaultdict(list)
    for row in rows:
        key = key_fn(row)
        if key is not None:
            groups[key].append(row)
    return {key: members for key, members in groups.items() if len(members) > 1}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT e.candidate_id, e.provenance_id, e.canonical_document_key,
               e.physical_page_no, e.candidate_text_sha256, e.source_title,
               t.priority, t.triage_class
        FROM evidence_claim_candidates e
        JOIN evidence_claim_semantic_triage t ON t.candidate_id=e.candidate_id
        WHERE t.triage_status='MACHINE_TRIAGE_REVIEW_REQUIRED'
        ORDER BY e.candidate_id
        """
    ).fetchall()
    exact = group_rows(rows, lambda r: r["candidate_text_sha256"] or None)
    page = group_rows(rows, lambda r: (r["canonical_document_key"], r["physical_page_no"]) if r["canonical_document_key"] and r["physical_page_no"] else None)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_duplicate_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            duplicate_type TEXT NOT NULL,
            group_key TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            member_count INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id,candidate_id)
        )
        """
    )
    output = []
    for duplicate_type, groups in (("EXACT_CANDIDATE_TEXT_SHA", exact), ("SAME_CANONICAL_PAGE", page)):
        for index, (key, members) in enumerate(sorted(groups.items(), key=lambda item: str(item[0])), start=1):
            group_id = f"DUP-{duplicate_type}-{index:04d}"
            group_key = json.dumps(key, ensure_ascii=False) if isinstance(key, tuple) else str(key)
            member_ids = [row["candidate_id"] for row in members]
            item = {
                "group_id": group_id,
                "duplicate_type": duplicate_type,
                "group_key": group_key,
                "member_count": len(member_ids),
                "candidate_ids": member_ids,
                "provenance_ids": [row["provenance_id"] for row in members],
                "canonical_document_keys": sorted({row["canonical_document_key"] for row in members}),
                "physical_pages": sorted({row["physical_page_no"] for row in members}),
                "action": "保留全部 provenance；复核时以原件/页图确认是否同一论点或不同 OCR 版本",
            }
            for candidate_id in member_ids:
                conn.execute(
                    "INSERT OR REPLACE INTO evidence_claim_duplicate_groups (group_id,duplicate_type,group_key,candidate_id,member_count) VALUES (?,?,?,?,?)",
                    (group_id, duplicate_type, group_key, candidate_id, len(member_ids)),
                )
            output.append(item)
    conn.commit()
    exact_members = sum(item["member_count"] for item in output if item["duplicate_type"] == "EXACT_CANDIDATE_TEXT_SHA")
    page_members = sum(item["member_count"] for item in output if item["duplicate_type"] == "SAME_CANONICAL_PAGE")
    report = {
        "run_id": "claim_duplicate_audit_20260730",
        "ready_candidate_rows": len(rows),
        "exact_text_duplicate_groups": len(exact),
        "exact_text_duplicate_members": exact_members,
        "exact_text_unique_units_estimate": len(rows) - exact_members + len(exact),
        "same_canonical_page_groups": len(page),
        "same_canonical_page_members": page_members,
        "rows_deleted": 0,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "GROUPS.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
