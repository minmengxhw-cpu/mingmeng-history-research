#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build locator-only evidence-card index from semantic triage rows."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/evidence_claim_cards"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.candidate_id, t.provenance_id, t.canonical_document_key,
               t.physical_page_no, t.triage_class, t.triage_status, t.priority,
               t.claim_family, t.tags_json, t.signals_json,
               e.source_title, e.period, e.candidate_text_sha256,
               e.source_ocr_md_path, e.source_ocr_md_sha256,
               l.audit_status
        FROM evidence_claim_semantic_triage t
        JOIN evidence_claim_candidates e ON e.candidate_id=t.candidate_id
        LEFT JOIN evidence_claim_locator_audit l ON l.candidate_id=t.candidate_id
        WHERE t.triage_status='MACHINE_TRIAGE_REVIEW_REQUIRED'
        ORDER BY CASE t.priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 9 END,
                 t.candidate_id
        """
    ).fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL UNIQUE,
            candidate_id TEXT NOT NULL UNIQUE,
            provenance_id TEXT NOT NULL,
            canonical_document_key TEXT,
            physical_page_no INTEGER,
            card_json TEXT NOT NULL,
            card_status TEXT NOT NULL,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cards = []
    priority_counts = Counter()
    class_counts = Counter()
    for row in rows:
        try:
            tags = json.loads(row["tags_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            tags = {}
        try:
            signals = json.loads(row["signals_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            signals = {}
        card = {
            "card_id": f"CLM-CARD-{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "provenance_id": row["provenance_id"],
            "canonical_document_key": row["canonical_document_key"],
            "physical_page_no": row["physical_page_no"],
            "source_title": row["source_title"],
            "period": row["period"],
            "candidate_text_sha256": row["candidate_text_sha256"],
            "source_ocr_md_path": row["source_ocr_md_path"],
            "source_ocr_md_sha256": row["source_ocr_md_sha256"],
            "locator_audit_status": row["audit_status"],
            "triage_class": row["triage_class"],
            "triage_status": row["triage_status"],
            "priority": row["priority"],
            "claim_family": row["claim_family"],
            "machine_tags": tags,
            "machine_signals": signals,
            "review_checklist": [
                "核对 OCR 文本与原始页图/原件，不以机器文本单独作引文",
                "确认物理页号、文献对象、来源 SHA 和 provenance 一致",
                "分别核对事件、人物、机构、地点和日期，不把词命中当作关系成立",
                "记录与其他来源的支持、冲突或未知状态",
                "完成语义核验后才可进入 citation gate 决策",
            ],
            "card_status": "MACHINE_CARD_REVIEW_REQUIRED",
            "body_excerpts_persisted": False,
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
        }
        conn.execute(
            """
            INSERT INTO evidence_claim_cards
            (card_id,candidate_id,provenance_id,canonical_document_key,physical_page_no,
             card_json,card_status,semantic_validation_done,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(card_id) DO UPDATE SET
              candidate_id=excluded.candidate_id,
              provenance_id=excluded.provenance_id,
              canonical_document_key=excluded.canonical_document_key,
              physical_page_no=excluded.physical_page_no,
              card_json=excluded.card_json,
              card_status=excluded.card_status,
              semantic_validation_done=0,
              citation_ready=0,
              human_verified=0
            """,
            (card["card_id"], card["candidate_id"], card["provenance_id"], card["canonical_document_key"],
             card["physical_page_no"], json.dumps(card, ensure_ascii=False), card["card_status"], 0, 0, 0),
        )
        cards.append(card)
        priority_counts[card["priority"] or "UNSET"] += 1
        class_counts[card["triage_class"]] += 1
    conn.commit()
    report = {
        "run_id": "evidence_claim_cards_index_20260730",
        "input_triage_rows": len(rows),
        "cards_written": len(cards),
        "priority_counts": dict(priority_counts),
        "triage_class_counts": dict(class_counts),
        "card_status": "MACHINE_CARD_REVIEW_REQUIRED",
        "body_excerpts_persisted": False,
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "CARDS.jsonl").write_text("\n".join(json.dumps(card, ensure_ascii=False) for card in cards) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 国内 evidence claim 卡片索引\n\n"
        "本目录只保存来源、页码、SHA、机器标签和复核清单，不保存正文摘录。\n\n"
        f"- 卡片数：{len(cards)}\n"
        f"- 状态：`MACHINE_CARD_REVIEW_REQUIRED`\n"
        f"- P0/P1/P2：{priority_counts.get('P0', 0)}/{priority_counts.get('P1', 0)}/{priority_counts.get('P2', 0)}\n"
        "- semantic validation：0\n- citation-ready：0\n- human-verified：0\n",
        encoding="utf-8",
    )
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
