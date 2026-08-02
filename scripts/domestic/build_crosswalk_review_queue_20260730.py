#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rank specific primary-to-research crosswalk rows for review."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/crosswalk_review_queue"


def score(row: sqlite3.Row, terms: list[str], basis: list[str]) -> int:
    value = len(terms) * 2
    value += sum(2 for item in basis if item == "TITLE_TERM_OVERLAP")
    value += 3 if row["quality_tier"] == "S" else 2 if row["quality_tier"] == "A" else 1
    value += 5 if row["fulltext_status"] in ("FULLTEXT_PDF", "FULLTEXT_HTML_CANDIDATE") else 0
    value += 2 if row["layer"] == "SCHOLARLY_RESEARCH" else 1
    value += 2 if row["research_type"] in ("PRIMARY_SOURCE_EDITION", "SCHOLARLY_ARTICLE", "ACADEMIC_MONOGRAPH") else 0
    return value


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT x.unit_id, x.representative_candidate_id, x.material_external_id,
               x.matched_terms_json, x.match_basis_json, x.crosswalk_status,
               m.title, m.author, m.institution, m.layer, m.research_type,
               m.quality_tier, m.fulltext_status, m.source_url, m.local_path
        FROM claim_research_crosswalk x
        JOIN domestic_research_materials m ON m.external_id=x.material_external_id
        WHERE x.crosswalk_status='METADATA_CROSSWALK_REVIEW_REQUIRED'
        ORDER BY x.unit_id, x.material_external_id
        """
    ).fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS crosswalk_review_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id TEXT NOT NULL,
            representative_candidate_id TEXT NOT NULL,
            material_external_id TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            priority_band TEXT NOT NULL,
            queue_json TEXT NOT NULL,
            queue_status TEXT NOT NULL,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(unit_id,material_external_id)
        )
        """
    )
    conn.execute(
        "UPDATE crosswalk_review_queue SET queue_status='STALE_SUPERSEDED', citation_ready=0, human_verified=0 WHERE queue_status='CROSSWALK_MACHINE_PRIORITY_REVIEW'"
    )
    queue = []
    band_counts = Counter()
    fulltext_rows = 0
    for row in rows:
        try:
            terms = json.loads(row["matched_terms_json"] or "[]")
            basis = json.loads(row["match_basis_json"] or "[]")
        except (TypeError, json.JSONDecodeError):
            terms, basis = [], []
        match_score = score(row, terms, basis)
        band = "A_REVIEW_FIRST" if match_score >= 14 else "B_REVIEW_NEXT" if match_score >= 9 else "C_METADATA_LEAD"
        if row["fulltext_status"] in ("FULLTEXT_PDF", "FULLTEXT_HTML_CANDIDATE"):
            fulltext_rows += 1
        band_counts[band] += 1
        item = {
            "unit_id": row["unit_id"],
            "representative_candidate_id": row["representative_candidate_id"],
            "material_external_id": row["material_external_id"],
            "material_title": row["title"],
            "material_layer": row["layer"],
            "research_type": row["research_type"],
            "quality_tier": row["quality_tier"],
            "fulltext_status": row["fulltext_status"],
            "source_url": row["source_url"],
            "local_path": row["local_path"],
            "matched_terms": terms,
            "match_basis": basis,
            "match_score": match_score,
            "priority_band": band,
            "queue_status": "CROSSWALK_MACHINE_PRIORITY_REVIEW",
            "citation_ready": 0,
            "human_verified": 0,
            "next_action": "核对研究资料的具体正文/版本，再判断能否作为旁证；不得仅凭标题支持原始 claim",
        }
        conn.execute(
            """
            INSERT INTO crosswalk_review_queue
            (unit_id,representative_candidate_id,material_external_id,match_score,
             priority_band,queue_json,queue_status,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(unit_id,material_external_id) DO UPDATE SET
              representative_candidate_id=excluded.representative_candidate_id,
              match_score=excluded.match_score,
              priority_band=excluded.priority_band,
              queue_json=excluded.queue_json,
              queue_status=excluded.queue_status,
              citation_ready=0,
              human_verified=0
            """,
            (item["unit_id"], item["representative_candidate_id"], item["material_external_id"], match_score,
             band, json.dumps(item, ensure_ascii=False), item["queue_status"], 0, 0),
        )
        queue.append(item)
    stale_rows = conn.execute(
        "SELECT COUNT(*) FROM crosswalk_review_queue WHERE queue_status='STALE_SUPERSEDED'"
    ).fetchone()[0]
    queue.sort(key=lambda item: (-item["match_score"], item["unit_id"], item["material_external_id"]))
    conn.commit()
    report = {
        "run_id": "crosswalk_review_queue_20260730",
        "specific_crosswalk_rows": len(rows),
        "queue_rows": len(queue),
        "stale_superseded_rows": stale_rows,
        "fulltext_candidate_rows": fulltext_rows,
        "priority_band_counts": dict(band_counts),
        "top_100_fulltext_or_high_score": sum(1 for item in queue[:100] if item["fulltext_status"] in ("FULLTEXT_PDF", "FULLTEXT_HTML_CANDIDATE") or item["match_score"] >= 14),
        "citation_ready": 0,
        "human_verified": 0,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "QUEUE.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in queue) + "\n", encoding="utf-8")
    (OUT / "TOP_100.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in queue[:100]) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
