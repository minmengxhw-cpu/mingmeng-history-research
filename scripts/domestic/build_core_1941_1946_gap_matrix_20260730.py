#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a machine-readable 1941-1946 source-family and gap matrix."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "work/domestic/phase2_inventory_20260730/CORE_DOCUMENT_INVENTORY.jsonl"
MMDA = ROOT / "work/domestic/MMDA_1942_1943_PRIORITY_QUEUE_20260728.jsonl"
OUT = ROOT / "work/domestic/phase2_inventory_20260730/core_gap_matrix_20260730"

PHASES = ("1941", "1942", "1943", "1944-1945", "1946")
FAMILIES = (
    "CONTEMPORARY_PRESS",
    "ORGANIZATIONAL_PRIMARY",
    "MEETING_SPEECH_DECLARATION",
    "OFFICIAL_RETROSPECTIVE",
    "SCHOLARLY_RESEARCH",
    "PERSON_PLACE_VISUAL",
    "UNCLASSIFIED_MACHINE",
)


def infer_family(row: dict) -> str:
    title = row.get("title_display") or row.get("title") or ""
    key = row.get("canonical_document_key") or ""
    if "Wikimedia" in key or "肖像" in title or "照片" in title or "题字" in title:
        return "PERSON_PLACE_VISUAL"
    if any(term in title for term in ("新华日报", "报刊", "报纸", "日报", "大公报", "光明报")):
        return "CONTEMPORARY_PRESS"
    if any(term in title for term in ("政治报告", "宣言", "政纲", "决议", "名单", "筹备", "会议", "支部", "总支部", "文件")):
        if any(term in title for term in ("会议", "报告", "宣言", "决议")):
            return "MEETING_SPEECH_DECLARATION"
        return "ORGANIZATIONAL_PRIMARY"
    if any(term in title for term in ("历史", "简史", "贡献", "回忆", "研究", "论文")):
        return "OFFICIAL_RETROSPECTIVE"
    return "UNCLASSIFIED_MACHINE"


def phase_rows(rows: list[dict], phase: str) -> list[dict]:
    if phase == "1942":
        return [row for row in rows if row.get("dominant_phase") == "1942"]
    if phase == "1943":
        return [row for row in rows if row.get("dominant_phase") == "1943"]
    return [row for row in rows if row.get("dominant_phase") == phase]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = [json.loads(line) for line in INVENTORY.read_text(encoding="utf-8").splitlines() if line.strip()]
    mmda_rows = [json.loads(line) for line in MMDA.read_text(encoding="utf-8").splitlines() if line.strip()]
    matrix = []
    worklist = []
    for phase in PHASES:
        rows = phase_rows(inventory, phase)
        family_counts = Counter(infer_family(row) for row in rows)
        evidence_counts = Counter(row.get("evidence_status") or "UNKNOWN" for row in rows)
        matrix.append({
            "phase": phase,
            "canonical_document_count": len(rows),
            "page_asset_count": sum(int(row.get("page_asset_count_live") or 0) for row in rows),
            "family_counts": {family: family_counts.get(family, 0) for family in FAMILIES},
            "evidence_status_counts": dict(evidence_counts),
            "selection_status_counts": dict(Counter(row.get("selection_status") or "UNKNOWN" for row in rows)),
            "machine_only": True,
        })
        if not rows:
            for mmda in mmda_rows:
                date = str(mmda.get("document_date") or "")
                if phase in date:
                    worklist.append({
                        "phase": phase,
                        "candidate_id": mmda.get("candidate_id"),
                        "title": mmda.get("title"),
                        "document_date": date,
                        "repository_code": mmda.get("repository_code"),
                        "catalog_reference": mmda.get("catalog_reference"),
                        "queue_rank": mmda.get("queue_rank"),
                        "relevance_grade": mmda.get("relevance_grade_accepted"),
                        "evidence_type": mmda.get("evidence_type"),
                        "online_availability": mmda.get("online_availability"),
                        "ingest_gate": mmda.get("ingest_gate"),
                        "next_action": mmda.get("next_action"),
                        "gap_basis": "staging_core_inventory_has_zero_canonical_documents_for_phase",
                        "machine_only": True,
                        "citation_ready": False,
                    })
    report = {
        "run_id": "core_gap_matrix_20260730",
        "scope": "1941-1946 core source-family matrix",
        "inventory_rows": len(inventory),
        "mmda_catalog_rows": len(mmda_rows),
        "phase_matrix": matrix,
        "zero_canonical_phases": [row["phase"] for row in matrix if row["canonical_document_count"] == 0],
        "gap_worklist_rows": len(worklist),
        "machine_only": True,
        "formal_db_written": False,
    }
    (OUT / "CORE_GAP_MATRIX.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "CORE_GAP_WORKLIST.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in worklist) + ("\n" if worklist else ""),
        encoding="utf-8",
    )
    (OUT / "README.md").write_text(
        "# 1941—1946 核心来源家族与缺口矩阵\n\n"
        "本目录只用于补证排序。`CORE_GAP_MATRIX.json` 按时期和来源家族统计 staging 候选；"
        "`CORE_GAP_WORKLIST.jsonl` 只登记 1942/1943 零 canonical 覆盖时期的 MMDA 目录候选。"
        "目录项必须取得原件 PDF/影像并完成 SHA、页级 provenance、OCR 与语义闸门后才能进入正式引用层。\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
