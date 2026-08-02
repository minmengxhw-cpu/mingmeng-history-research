#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turn high-overlap machine rows into locator-only semantic review cards."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OVERLAP = ROOT / "work/domestic/staging_20260730/fulltext_text_overlap_queue/OVERLAP_QUEUE.jsonl"
LOCATORS = ROOT / "work/domestic/staging_20260730/fulltext_locator_candidates/LOCATOR_CANDIDATES.jsonl"
MATERIALS = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/MATERIALS.jsonl"
CARDS = ROOT / "work/domestic/staging_20260730/evidence_claim_cards/CARDS.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/fulltext_semantic_review_cards"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    materials = {
        row["material_external_id"]: row
        for row in (json.loads(line) for line in MATERIALS.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    cards = {}
    for line in CARDS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            cards[row["candidate_id"]] = row
    locators = {
        (row["unit_id"], row["material_external_id"]): row.get("locators", [])
        for row in (json.loads(line) for line in LOCATORS.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    overlap_rows = [
        json.loads(line)
        for line in OVERLAP.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    overlap_rows = [row for row in overlap_rows if row["text_overlap_status"] == "STRONG_TEXT_OVERLAP_REVIEW_REQUIRED"]
    output = []
    for row in overlap_rows:
        material = materials.get(row["material_external_id"], {})
        card = cards.get(row["representative_candidate_id"], {})
        output.append({
            "review_card_id": f"FT-SEM-{row['unit_id']}-{row['material_external_id']}",
            "unit_id": row["unit_id"],
            "representative_candidate_id": row["representative_candidate_id"],
            "primary_document_key": card.get("canonical_document_key"),
            "primary_source_title": card.get("source_title"),
            "primary_physical_page_no": row.get("candidate_physical_page_no"),
            "primary_ocr_md_path": row.get("source_ocr_md_path"),
            "primary_ocr_md_sha256": card.get("source_ocr_md_sha256"),
            "primary_candidate_text_sha256": row.get("candidate_text_sha256"),
            "fulltext_material_external_id": row["material_external_id"],
            "fulltext_title": row["material_title"],
            "fulltext_local_path": material.get("local_path"),
            "fulltext_sha256": row.get("material_sha256"),
            "fulltext_source_url": material.get("source_url"),
            "fulltext_locators": locators.get((row["unit_id"], row["material_external_id"]), []),
            "overlap_token_count": row.get("overlap_token_count", 0),
            "specific_term_hit_count": row.get("specific_term_hit_count", 0),
            "exact_candidate_text_match": row.get("exact_candidate_text_match", False),
            "machine_priority": "HIGH_TEXT_OVERLAP",
            "semantic_relation": "UNVERIFIED",
            "review_questions": [
                "核对全文位置是否讨论同一事件、人物、机构或地点",
                "区分支持、冲突、独立背景和未知，不把词项重叠当作支持",
                "记录全文页码/HTML 位置与 primary 页码是否形成可解释的证据链",
                "确认研究资料的性质，不能让二手研究替代一手原件",
            ],
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
            "body_excerpt_persisted": False,
        })
    report = {
        "run_id": "fulltext_semantic_review_cards_20260730",
        "input_high_overlap_rows": len(overlap_rows),
        "review_cards": len(output),
        "semantic_relation_counts": {"UNVERIFIED": len(output)},
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
    }
    (OUT / "REVIEW_CARDS.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8"
    )
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
