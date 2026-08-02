#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a conservative semantic-triage index for structurally ready claims.

This layer groups existing machine tags and OCR signals for review routing. It
does not paraphrase or approve claim text, and it does not change any existing
claim/citation/human-verification flags.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
AUDIT_REPORT = ROOT / "work/domestic/staging_20260730/evidence_claim_locator_audit/REPORT.json"
OUT = ROOT / "work/domestic/staging_20260730/claim_semantic_triage"


def as_list(raw: object) -> list[str]:
    try:
        value = json.loads(str(raw or "[]"))
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in value] if isinstance(value, list) else []


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT e.candidate_id, e.provenance_id, e.canonical_document_key,
               e.physical_page_no, e.source_title, e.period,
               e.candidate_text_sha256, e.claim_status,
               a.claim_family, a.person_tags_json, a.organization_tags_json,
               a.event_tags_json, a.place_tags_json, a.publication_tags_json,
               a.matched_terms_json, s.review_stage, s.priority, s.signals_json,
               la.audit_status, la.audit_json
        FROM evidence_claim_candidates e
        LEFT JOIN evidence_candidate_annotations a ON a.candidate_id=e.candidate_id
        LEFT JOIN semantic_review_queue s ON s.candidate_id=e.candidate_id
        LEFT JOIN evidence_claim_locator_audit la ON la.candidate_id=e.candidate_id
        ORDER BY e.candidate_id
        """
    ).fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_semantic_triage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT NOT NULL UNIQUE,
            provenance_id TEXT NOT NULL,
            canonical_document_key TEXT,
            physical_page_no INTEGER,
            triage_class TEXT NOT NULL,
            triage_status TEXT NOT NULL,
            priority TEXT,
            claim_family TEXT,
            tags_json TEXT NOT NULL,
            signals_json TEXT NOT NULL,
            machine_notes TEXT NOT NULL,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    ready = []
    holds = []
    class_counts = Counter()
    for row in rows:
        tags = {
            "person": as_list(row["person_tags_json"]),
            "organization": as_list(row["organization_tags_json"]),
            "event": as_list(row["event_tags_json"]),
            "place": as_list(row["place_tags_json"]),
            "publication": as_list(row["publication_tags_json"]),
            "matched": as_list(row["matched_terms_json"]),
        }
        try:
            signals = json.loads(row["signals_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            signals = {}
        audit_status = row["audit_status"] or "HOLD_CLAIM_LOCATOR"
        if audit_status != "STRUCTURE_READY_CLAIM_INDEX":
            item = {
                "candidate_id": row["candidate_id"],
                "provenance_id": row["provenance_id"],
                "canonical_document_key": row["canonical_document_key"],
                "physical_page_no": row["physical_page_no"],
                "hold_status": "HOLD_CLAIM_LOCATOR",
                "locator_audit_status": audit_status,
                "next_action": "补物理页号或补充可用识别文本后重新审计",
            }
            try:
                audit = json.loads(row["audit_json"] or "{}")
                item["failed_checks"] = audit.get("failed_checks", [])
            except (TypeError, json.JSONDecodeError):
                item["failed_checks"] = []
            holds.append(item)
            continue
        if tags["event"]:
            triage_class = "EVENT_ENTITY_CANDIDATE"
        elif tags["person"] or tags["organization"] or tags["place"]:
            triage_class = "ENTITY_CONTEXT_CANDIDATE"
        else:
            triage_class = "CONTEXT_ONLY_CANDIDATE"
        class_counts[triage_class] += 1
        machine_notes = (
            f"机器标签：{', '.join(tags['matched']) or '无'}；"
            f"OCR 文本字符数：{signals.get('text_chars', 'NA')}；"
            f"OCR 置信度：{signals.get('ocr_confidence', 'NA')}；"
            "仅用于复核分流，不构成语义结论。"
        )
        item = {
            "candidate_id": row["candidate_id"],
            "provenance_id": row["provenance_id"],
            "canonical_document_key": row["canonical_document_key"],
            "physical_page_no": row["physical_page_no"],
            "source_title": row["source_title"],
            "period": row["period"],
            "candidate_text_sha256": row["candidate_text_sha256"],
            "claim_family": row["claim_family"],
            "triage_class": triage_class,
            "triage_status": "MACHINE_TRIAGE_REVIEW_REQUIRED",
            "priority": row["priority"],
            "tags": tags,
            "signals": signals,
            "machine_notes": machine_notes,
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
        }
        conn.execute(
            """
            INSERT INTO evidence_claim_semantic_triage
            (candidate_id,provenance_id,canonical_document_key,physical_page_no,
             triage_class,triage_status,priority,claim_family,tags_json,signals_json,
             machine_notes,semantic_validation_done,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(candidate_id) DO UPDATE SET
              provenance_id=excluded.provenance_id,
              canonical_document_key=excluded.canonical_document_key,
              physical_page_no=excluded.physical_page_no,
              triage_class=excluded.triage_class,
              triage_status=excluded.triage_status,
              priority=excluded.priority,
              claim_family=excluded.claim_family,
              tags_json=excluded.tags_json,
              signals_json=excluded.signals_json,
              machine_notes=excluded.machine_notes,
              semantic_validation_done=0,
              citation_ready=0,
              human_verified=0
            """,
            (item["candidate_id"], item["provenance_id"], item["canonical_document_key"], item["physical_page_no"],
             item["triage_class"], item["triage_status"], item["priority"], item["claim_family"],
             json.dumps(item["tags"], ensure_ascii=False), json.dumps(item["signals"], ensure_ascii=False),
             item["machine_notes"], 0, 0, 0),
        )
        ready.append(item)
    conn.commit()
    report = {
        "run_id": "claim_semantic_triage_index_20260730",
        "input_candidates": len(rows),
        "triage_rows_written": len(ready),
        "hold_rows": len(holds),
        "triage_class_counts": dict(class_counts),
        "hold_reason_counts": dict(Counter(reason for row in holds for reason in row.get("failed_checks", []))),
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "TRIAGE.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in ready) + "\n", encoding="utf-8")
    (OUT / "HOLD_WORKLIST.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in holds) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
