#!/usr/bin/env python3
"""Build a conservative 40-item core evidence manifest.

This is a planning and audit artifact, not a claim that every item is
citation-ready. Existing OCR evidence units are preserved as-is. Candidate
records without local originals are represented as metadata-only leads with
an empty page list and citation_ready=false.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UNITS = ROOT / "data/domestic/evidence_units.jsonl"
DB = ROOT / "data/research_index.sqlite"
OUT = ROOT / "work/domestic/CORE_EVIDENCE_MANIFEST_20260728.jsonl"
REPORT = ROOT / "work/domestic/CORE_EVIDENCE_MANIFEST_20260728.md"


def read_units() -> list[dict]:
    return [json.loads(line) for line in UNITS.read_text(encoding="utf-8").splitlines() if line.strip()]


def pick(rows: list[dict], period: str, count: int) -> list[dict]:
    selected = [row for row in rows if row.get("period") == period]
    if len(selected) < count:
        raise SystemExit(f"not enough evidence units for {period}: {len(selected)} < {count}")
    return selected[:count]


def candidate_row(row: sqlite3.Row, ordinal: int) -> dict:
    return {
        "evidence_id": f"core-1942-43-candidate-{ordinal:02d}",
        "period": "1942-1943",
        "article_title_normalized": row["title"],
        "article_title_original": row["title"],
        "author_original": row["creator"] or "",
        "document_id": None,
        "source_id": row["candidate_id"],
        "source_kind": "catalog_metadata_only",
        "evidence_level": row["authenticity_level_accepted"] or "L3",
        "ocr_status": "not_acquired",
        "page_ids": [],
        "pdf_page": "",
        "printed_page": "",
        "date_normalized": row["document_date"] or "",
        "date_original": row["document_date"] or "",
        "article_start_marker": "",
        "article_end_marker": "",
        "uncertainties": (
            "仅有目录/题名与记录级定位；原件尚未进入本地工作区，"
            "不能作为正文引文。"
        ),
        "catalog_reference": row["catalog_reference"],
        "repository_code": row["repository_code"],
        "repository_name": row["repository_name"],
        "source_url": row["source_url"],
        "citation_ready": False,
        "core_selection_reason": "覆盖1942—1943资料断档，先保留高价值目录入口",
    }


def main() -> int:
    units = read_units()
    selected: list[dict] = []
    for period, count in (
        ("1941", 8),
        ("1944-1945", 10),
        ("1946", 5),
        ("1947", 4),
        ("1948-1949", 8),
    ):
        for row in pick(units, period, count):
            copy = dict(row)
            copy["core_selection_reason"] = f"覆盖{period}核心时段，沿用既有证据单元"
            selected.append(copy)

    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    try:
        candidates = connection.execute(
            """
            SELECT candidate_id, title, creator, document_date, repository_code,
                   repository_name, catalog_reference, source_url,
                   authenticity_level_accepted
            FROM domestic_candidates
            WHERE review_status = 'accepted'
              AND authenticity_level_accepted = 'L3'
              AND relevance_grade_accepted = 'core'
              AND (document_date LIKE '1942%' OR document_date LIKE '1943%')
            ORDER BY CASE
                       WHEN document_date = '1942' THEN 0
                       WHEN document_date = '1943' THEN 1
                       ELSE 2
                     END,
                     document_date, candidate_id
            LIMIT 5
            """
        ).fetchall()
    finally:
        connection.close()

    if len(candidates) != 5:
        raise SystemExit(f"expected 5 accepted 1942-1943 candidates, found {len(candidates)}")
    selected.extend(candidate_row(row, index) for index, row in enumerate(candidates, 1))

    if len(selected) != 40:
        raise SystemExit(f"manifest size mismatch: {len(selected)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )
    counts = Counter(row["period"] for row in selected)
    metadata_only = sum(row["source_kind"] == "catalog_metadata_only" for row in selected)
    REPORT.write_text(
        "\n".join(
            [
                "# 国内民盟史核心证据集清单（2026-07-28）",
                "",
                f"- 总数：{len(selected)}",
                f"- 目录元数据待补原件：{metadata_only}",
                "- citation_ready：全部为 false；本清单用于证据覆盖规划，不替代原件核验。",
                "",
                "## 时段覆盖",
                "",
                *[f"- {period}：{counts[period]} 条" for period in ("1941", "1942-1943", "1944-1945", "1946", "1947", "1948-1949")],
                "",
                "## 处理门槛",
                "",
                "- 1942—1943 的 5 条是已验收目录记录，不代表已取得全文。",
                "- 只有补齐原件、页码、OCR/人工复核和稳定来源定位后，才允许升级 citation_ready。",
                "- 原始 evidence_units.jsonl 未修改。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"manifest": str(OUT), "report": str(REPORT), "rows": len(selected), "periods": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
