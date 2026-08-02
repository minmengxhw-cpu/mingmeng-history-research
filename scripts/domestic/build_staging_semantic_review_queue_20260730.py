#!/usr/bin/env python3
"""Build a conservative semantic-review queue from machine claim candidates.

This is prioritisation, not semantic approval.  It deliberately requires
signals in the OCR text itself, rather than relying only on source metadata.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "e4417bd1dfce77772832e0fcee17f5fb33bbd0fc9d1e6b2618932a64e9c8c0a5"

EVENT_TERMS = ["成立", "代表大会", "代表大會", "政治协商", "政治協商", "解散", "非法", "五一口号", "五一口號", "三中全会", "三中全會", "抗战", "抗戰", "反右", "宪政", "憲政"]
ENTITY_TERMS = ["民盟", "民主同盟", "中國民主同盟", "中国民主同盟", "国民党", "國民黨", "政协", "政協", "光明报", "光明報", "民宪", "民憲"]


def main() -> int:
    formal_before = hashlib.sha256(FORMAL_DB.read_bytes()).hexdigest()
    if formal_before != EXPECTED_FORMAL_SHA:
        raise SystemExit(f"formal DB baseline changed: {formal_before}")
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        """SELECT e.*, o.valid, o.ocr_confidence, o.binding_status,
                  g.eligible, a.claim_family
           FROM evidence_claim_candidates e
           JOIN ocr_versions o ON o.provenance_id=e.provenance_id
           JOIN citation_gate_results g ON g.provenance_id=e.provenance_id
           LEFT JOIN evidence_candidate_annotations a ON a.candidate_id=e.candidate_id
           ORDER BY e.candidate_id"""
    ).fetchall()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS semantic_review_queue (
            id INTEGER PRIMARY KEY,
            review_id TEXT NOT NULL UNIQUE,
            candidate_id TEXT NOT NULL UNIQUE,
            provenance_id TEXT NOT NULL,
            canonical_document_key TEXT,
            physical_page_no INTEGER,
            review_stage TEXT NOT NULL,
            priority TEXT NOT NULL,
            signals_json TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(candidate_id) REFERENCES evidence_claim_candidates(candidate_id),
            FOREIGN KEY(provenance_id) REFERENCES ocr_versions(provenance_id)
        );
        CREATE INDEX IF NOT EXISTS idx_semantic_review_stage ON semantic_review_queue(review_stage, priority);
        """
    )
    counts = Counter()
    for row in rows:
        text = str(row["candidate_text"] or "")
        events = sorted({term for term in EVENT_TERMS if term in text})
        entities = sorted({term for term in ENTITY_TERMS if term in text})
        signals = {
            "text_chars": len(text),
            "event_terms_in_text": events,
            "entity_terms_in_text": entities,
            "ocr_confidence": row["ocr_confidence"],
            "claim_family_from_metadata_and_text": row["claim_family"],
        }
        reasons = []
        if row["eligible"] != 1:
            reasons.append("citation_gate_not_eligible")
        if row["binding_status"] != "BOUND_CANONICAL":
            reasons.append("canonical_binding_not_confirmed")
        if not row["valid"]:
            reasons.append("ocr_provenance_invalid")
        if len(text) < 80:
            reasons.append("text_too_short")
        if not events and not entities:
            reasons.append("no_event_or_entity_signal_in_ocr_text")
        if row["ocr_confidence"] is not None and float(row["ocr_confidence"]) < 0.60:
            reasons.append("low_ocr_confidence")
        if reasons:
            stage = "HOLD_MACHINE_TRIAGE"
            priority = "P1" if "low_ocr_confidence" in reasons or "ocr_provenance_invalid" in reasons else "P2"
            action = ";".join(reasons)
        else:
            stage = "READY_SEMANTIC_REVIEW"
            priority = "P0" if events and entities else "P1"
            action = "review claim wording, locator, entity/event tags, and contradiction status"
        c.execute(
            """INSERT INTO semantic_review_queue
               (review_id,candidate_id,provenance_id,canonical_document_key,physical_page_no,
                review_stage,priority,signals_json,recommended_action,semantic_validation_done,
                citation_ready,human_verified)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(candidate_id) DO UPDATE SET
                 review_stage=excluded.review_stage, priority=excluded.priority,
                 signals_json=excluded.signals_json, recommended_action=excluded.recommended_action,
                 semantic_validation_done=excluded.semantic_validation_done,
                 citation_ready=excluded.citation_ready, human_verified=excluded.human_verified""",
            (
                f"SRQ-{row['candidate_id']}", row["candidate_id"], row["provenance_id"],
                row["canonical_document_key"], row["physical_page_no"], stage, priority,
                json.dumps(signals, ensure_ascii=False), action, 0, 0, 0,
            ),
        )
        counts["rows"] += 1
        counts[f"stage:{stage}"] += 1
        counts[f"priority:{priority}"] += 1
    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(c.execute("PRAGMA foreign_key_check").fetchall())
    counts["queue_rows"] = c.execute("SELECT count(*) FROM semantic_review_queue").fetchone()[0]
    formal_after = hashlib.sha256(FORMAL_DB.read_bytes()).hexdigest()
    report = {
        "report": "DOMESTIC_SEMANTIC_REVIEW_QUEUE_20260730",
        "counts": dict(counts),
        "integrity_check": integrity,
        "foreign_key_violation_count": fk_count,
        "formal_db_sha_before": formal_before,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_before == formal_after == EXPECTED_FORMAL_SHA,
        "semantic_validation_done": 0,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "rule": "text-signal triage only; no semantic claim approval",
    }
    out = DB.parent / "SEMANTIC_REVIEW_QUEUE_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    c.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
