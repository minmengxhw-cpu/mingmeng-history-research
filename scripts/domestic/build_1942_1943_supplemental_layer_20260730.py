#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventory non-canonical 1942-1943 supplements without promoting them.

This separates research metadata and public HTML snapshots from the missing
contemporary originals, so the platform can expose useful leads without
claiming that the core primary gap is closed.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/phase2_inventory_20260730/supplemental_1942_1943"


def classify(title: str, *, kind: str, research_type: str = "") -> str:
    text = f"{title} {research_type}"
    if kind == "machine_snapshot" and any(term in title for term in ("美国", "驻华", "领事", "Ambassador", "Department of State")):
        return "FOREIGN_COMPARATIVE_SNAPSHOT"
    if any(term in text for term in ("小册子", "宣言", "报告", "讲话", "文告", "声明")):
        return "PRIMARY_SOURCE_CANDIDATE_UNVERIFIED"
    if any(term in text for term in ("传略", "人物", "传记", "生平", "资料汇编", "BIOGRAPHICAL")):
        return "BIOGRAPHICAL_OR_LOCAL_HISTORY"
    if any(term in text for term in ("历史", "简史", "贡献", "研究", "ARCHIVAL_GUIDE", "OFFICIAL")):
        return "OFFICIAL_RETROSPECTIVE_OR_GUIDE"
    return "UNCLASSIFIED_SUPPLEMENT"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    snapshots = con.execute(
        "SELECT object_id,title,historical_phase,source_url,local_path,sha256,evidence_tier,access_status "
        "FROM machine_text_records WHERE historical_phase LIKE '%1942%' OR historical_phase LIKE '%1943%'"
    ).fetchall()
    materials = con.execute(
        "SELECT external_id,title,layer,research_type,quality_tier,source_url,local_path,fulltext_status," 
        "publication_date,review_status,citation_ready,human_verified "
        "FROM domestic_research_materials WHERE title LIKE '%1942%' OR title LIKE '%1943%' "
        "OR publication_date LIKE '%1942%' OR publication_date LIKE '%1943%'"
    ).fetchall()
    con.close()
    rows = []
    for row in snapshots:
        item = dict(row)
        item.update({
            "record_id": row["object_id"],
            "record_kind": "machine_snapshot",
            "candidate_class": classify(row["title"] or "", kind="machine_snapshot"),
            "source_layer": "PUBLIC_HTML_SNAPSHOT",
            "evidence_status": "SNAPSHOT_NOT_ORIGINAL",
            "citation_ready": 0,
            "human_verified": 0,
        })
        rows.append(item)
    for row in materials:
        item = dict(row)
        item.update({
            "record_id": row["external_id"],
            "record_kind": "research_material_metadata",
            "candidate_class": classify(row["title"] or "", kind="research_material_metadata", research_type=row["research_type"] or ""),
            "source_layer": row["layer"] or "DOMESTIC_RESEARCH",
            "evidence_status": "METADATA_OR_EXISTING_FULLTEXT_POINTER",
        })
        rows.append(item)
    counts = Counter(row["candidate_class"] for row in rows)
    report = {
        "run_id": "supplemental_1942_1943_20260730",
        "records": len(rows),
        "machine_snapshot_records": len(snapshots),
        "research_metadata_records": len(materials),
        "candidate_class_counts": dict(counts),
        "core_primary_gap_closed": False,
        "citation_ready": 0,
        "human_verified": 0,
        "formal_db_written": False,
        "rule": "supplemental leads are separate from 1942-1943 core originals; no filename/title promotion",
    }
    (OUT / "SUPPLEMENTAL_1942_1943.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8"
    )
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 1942—1943 补充资料层\n\n"
        "本层收录 staging 中已有的研究元数据和公开 HTML 快照，用于补证线索和检索入口。"
        "它不关闭 1942/1943 核心一手原件缺口，不把网页快照、回顾研究或目录记录升级为同期原件。\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
