#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write conservative, non-citation adjudication labels for relation signals."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIGNALS = ROOT / "work/domestic/staging_20260730/structured_relation_signals/SIGNALS.jsonl"
MATERIALS = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/MATERIALS.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/conservative_relation_adjudication"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    materials = {
        row["material_external_id"]: row
        for row in (json.loads(line) for line in MATERIALS.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    output = []
    counts = Counter()
    for row in (json.loads(line) for line in SIGNALS.read_text(encoding="utf-8").splitlines() if line.strip()):
        signal = row["relation_signal"]
        if signal == "POTENTIAL_SAME_CONTEXT_REVIEW_REQUIRED":
            relation = "CONTEXTUAL_CORROBORATION_CANDIDATE"
            reason_codes = ["EVENT_ENTITY_OVERLAP", "LOCATOR_PRESENT", "POSTERIOR_SOURCE_REVIEW_REQUIRED"]
            next_action = "核对一手页图与全文具体段落，确认是否同一事件；不得直接升级 citation-ready"
        elif signal == "POTENTIAL_CONTEXT_ONLY_REVIEW_REQUIRED":
            relation = "BACKGROUND_ASSOCIATION_CANDIDATE"
            reason_codes = ["LIMITED_ENTITY_OR_PLACE_OVERLAP", "NOT_DIRECT_SUPPORT"]
            next_action = "仅作为背景线索，除非取得明确事件/人物/机构关系，不进入支持结论"
        else:
            relation = "UNKNOWN"
            reason_codes = ["NO_SUBJECT_HIT"]
            next_action = "保持未知，不补写语义关系"
        counts[relation] += 1
        material = materials.get(row["fulltext_material_external_id"], {})
        output.append({
            "review_card_id": row["review_card_id"],
            "unit_id": row["unit_id"],
            "representative_candidate_id": row["representative_candidate_id"],
            "primary_physical_page_no": row["primary_physical_page_no"],
            "fulltext_material_external_id": row["fulltext_material_external_id"],
            "fulltext_title": material.get("material_title") or material.get("title"),
            "fulltext_source_url": material.get("source_url"),
            "fulltext_locators": row.get("fulltext_locators", []),
            "adjudicated_relation_candidate": relation,
            "reason_codes": reason_codes,
            "verification_status": "NOT_PROVEN",
            "support_status": "NOT_ESTABLISHED",
            "conflict_status": "NOT_ASSESSED",
            "next_action": next_action,
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
            "body_excerpt_persisted": False,
        })
    report = {
        "run_id": "conservative_relation_adjudication_20260730",
        "input_rows": len(output),
        "relation_candidate_counts": dict(counts),
        "verification_status": "NOT_PROVEN_ALL",
        "support_status": "NOT_ESTABLISHED_ALL",
        "conflict_status": "NOT_ASSESSED_ALL",
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
    }
    (OUT / "ADJUDICATION_QUEUE.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
