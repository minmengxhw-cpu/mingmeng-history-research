#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assess machine readability of representative P0/P1 review units.

This is not semantic validation. It records conservative signals that help
route review work: sentence punctuation, date/entity/event signals and OCR
fragmentation. No source text is copied into output artifacts.
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
OUT = ROOT / "work/domestic/staging_20260730/p0_p1_machine_assessment"

DATE_RE = re.compile(r"(?:19|20)\d{2}|民国[一二三四五六七八九十百零〇]{2,5}年|[一二三四五六七八九十百零〇]{2,5}年")
SENTENCE_RE = re.compile(r"[。！？!?；;]")
EVENT_RE = re.compile(r"成立|改组|代表大会|会议|宣言|声明|抗战|内战|政治协商|取缔|查封|被捕|遇害|解散|宪政|选举|联合政府|建国")


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def assess(text: str, tags: dict, signals: dict) -> dict:
    clean = re.sub(r"\s+", " ", text or "").strip()
    chars = len(clean)
    han = len(re.findall(r"[\u3400-\u9fff]", clean))
    sentences = len(SENTENCE_RE.findall(clean))
    dates = DATE_RE.findall(clean)
    events = EVENT_RE.findall(clean)
    replacement = clean.count("�")
    repeated_noise = len(re.findall(r"(.)\1{5,}", clean))
    corruption_ratio = (replacement + repeated_noise * 3) / max(chars, 1)
    entity_count = sum(len(tags.get(key, [])) for key in ("person", "organization", "place"))
    has_signal = bool(events or entity_count or tags.get("event"))
    risk_flags = []
    if chars < 160:
        risk_flags.append("SHORT_MACHINE_TEXT")
    if sentences == 0:
        risk_flags.append("NO_SENTENCE_PUNCTUATION")
    if not dates:
        risk_flags.append("NO_EXPLICIT_DATE_SIGNAL")
    if not has_signal:
        risk_flags.append("LOW_EVENT_ENTITY_SIGNAL")
    if corruption_ratio > 0.01:
        risk_flags.append("OCR_FRAGMENTATION_SIGNAL")
    if clean.startswith("目录") or "目錄" in clean[:120]:
        risk_flags.append("POSSIBLE_TABLE_OF_CONTENTS")
    grade = "MACHINE_REVIEW_RICH" if not risk_flags else "MACHINE_REVIEW_WITH_RISKS"
    if len(risk_flags) >= 3 or "OCR_FRAGMENTATION_SIGNAL" in risk_flags:
        grade = "MACHINE_REVIEW_WEAK"
    return {
        "text_chars": chars,
        "han_chars": han,
        "sentence_punctuation_count": sentences,
        "date_signal_count": len(dates),
        "date_signal_samples": dates[:12],
        "event_signal_count": len(events),
        "entity_signal_count": entity_count,
        "ocr_fragmentation_ratio_estimate": round(corruption_ratio, 5),
        "risk_flags": risk_flags,
        "machine_assessment": grade,
        "candidate_text_sha256_recomputed": text_sha(clean),
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT u.unit_id, u.representative_candidate_id, u.exact_duplicate_group_id,
               u.member_count, u.unit_kind, u.priority, u.triage_class,
               u.canonical_document_key, u.physical_page_no,
               e.source_title, e.period, e.candidate_text, e.candidate_text_sha256,
               t.tags_json, t.signals_json
        FROM evidence_claim_review_units u
        JOIN evidence_claim_candidates e ON e.candidate_id=u.representative_candidate_id
        JOIN evidence_claim_semantic_triage t ON t.candidate_id=u.representative_candidate_id
        WHERE u.priority IN ('P0','P1')
        ORDER BY CASE u.priority WHEN 'P0' THEN 0 ELSE 1 END, u.unit_id
        """
    ).fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_machine_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id TEXT NOT NULL UNIQUE,
            representative_candidate_id TEXT NOT NULL UNIQUE,
            priority TEXT NOT NULL,
            assessment_json TEXT NOT NULL,
            machine_assessment TEXT NOT NULL,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    results = []
    grade_counts = Counter()
    risk_counts = Counter()
    priority_counts = Counter()
    for row in rows:
        try:
            tags = json.loads(row["tags_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            tags = {}
        try:
            signals = json.loads(row["signals_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            signals = {}
        assessment = assess(row["candidate_text"] or "", tags, signals)
        item = {
            "unit_id": row["unit_id"],
            "representative_candidate_id": row["representative_candidate_id"],
            "exact_duplicate_group_id": row["exact_duplicate_group_id"],
            "member_count": row["member_count"],
            "priority": row["priority"],
            "triage_class": row["triage_class"],
            "canonical_document_key": row["canonical_document_key"],
            "physical_page_no": row["physical_page_no"],
            "source_title": row["source_title"],
            "period": row["period"],
            "assessment": assessment,
            "assessment_status": "MACHINE_ASSESSMENT_NOT_VALIDATED",
        }
        conn.execute(
            """
            INSERT INTO evidence_claim_machine_assessments
            (unit_id,representative_candidate_id,priority,assessment_json,machine_assessment,
             semantic_validation_done,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(unit_id) DO UPDATE SET
              representative_candidate_id=excluded.representative_candidate_id,
              priority=excluded.priority,
              assessment_json=excluded.assessment_json,
              machine_assessment=excluded.machine_assessment,
              semantic_validation_done=0,
              citation_ready=0,
              human_verified=0
            """,
            (item["unit_id"], item["representative_candidate_id"], item["priority"],
             json.dumps(item, ensure_ascii=False), assessment["machine_assessment"], 0, 0, 0),
        )
        results.append(item)
        grade_counts[assessment["machine_assessment"]] += 1
        priority_counts[row["priority"]] += 1
        for flag in assessment["risk_flags"]:
            risk_counts[flag] += 1
    conn.commit()
    report = {
        "run_id": "p0_p1_machine_assessment_20260730",
        "input_review_units": len(rows),
        "priority_counts": dict(priority_counts),
        "machine_assessment_counts": dict(grade_counts),
        "risk_counts": dict(risk_counts),
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "ASSESSMENTS.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
