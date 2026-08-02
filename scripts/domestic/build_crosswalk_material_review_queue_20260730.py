#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collapse crosswalk rows to distinct research-material review objects."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue"


def rank(band: str | None) -> int:
    return {"A_REVIEW_FIRST": 0, "B_REVIEW_NEXT": 1, "C_METADATA_LEAD": 2}.get(band or "", 9)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT q.unit_id,q.representative_candidate_id,q.material_external_id,
               q.match_score,q.priority_band,q.queue_status,q.queue_json,
               m.title,m.author,m.institution,m.layer,m.research_type,
               m.quality_tier,m.fulltext_status,m.source_url,m.local_path,m.sha256
        FROM crosswalk_review_queue q
        JOIN domestic_research_materials m ON m.external_id=q.material_external_id
        WHERE q.queue_status='CROSSWALK_MACHINE_PRIORITY_REVIEW'
        ORDER BY q.material_external_id,q.match_score DESC,q.unit_id
        """
    ).fetchall()
    groups = defaultdict(list)
    for row in rows:
        groups[row["material_external_id"]].append(row)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS crosswalk_material_review_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_external_id TEXT NOT NULL UNIQUE,
            material_title TEXT NOT NULL,
            material_layer TEXT,
            research_type TEXT,
            quality_tier TEXT,
            fulltext_status TEXT,
            source_url TEXT,
            local_path TEXT,
            sha256 TEXT,
            matched_unit_count INTEGER NOT NULL,
            max_match_score INTEGER NOT NULL,
            best_priority_band TEXT NOT NULL,
            matched_units_json TEXT NOT NULL,
            queue_json TEXT NOT NULL,
            queue_status TEXT NOT NULL,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "UPDATE crosswalk_material_review_queue SET queue_status='STALE_SUPERSEDED', citation_ready=0, human_verified=0 WHERE queue_status='MATERIAL_CROSSWALK_REVIEW_REQUIRED'"
    )
    output = []
    band_counts = Counter()
    fulltext_counts = Counter()
    for external_id, members in sorted(groups.items()):
        members = sorted(members, key=lambda r: (-r["match_score"], rank(r["priority_band"]), r["unit_id"]))
        first = members[0]
        best_band = min((r["priority_band"] for r in members), key=rank)
        try:
            queue_payload = json.loads(first["queue_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            queue_payload = {}
        item = {
            "material_external_id": external_id,
            "material_title": first["title"],
            "material_layer": first["layer"],
            "research_type": first["research_type"],
            "quality_tier": first["quality_tier"],
            "fulltext_status": first["fulltext_status"],
            "source_url": first["source_url"],
            "local_path": first["local_path"],
            "sha256": first["sha256"],
            "matched_unit_count": len(members),
            "max_match_score": first["match_score"],
            "best_priority_band": best_band,
            "matched_units": [r["unit_id"] for r in members],
            "queue_status": "MATERIAL_CROSSWALK_REVIEW_REQUIRED",
            "next_action": "核对该研究资料一次，再将核对结果回链到全部命中的 primary 单元；不把标题匹配当作支持",
        }
        conn.execute(
            """
            INSERT INTO crosswalk_material_review_queue
            (material_external_id,material_title,material_layer,research_type,quality_tier,
             fulltext_status,source_url,local_path,sha256,matched_unit_count,max_match_score,
             best_priority_band,matched_units_json,queue_json,queue_status,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(material_external_id) DO UPDATE SET
              material_title=excluded.material_title,
              material_layer=excluded.material_layer,
              research_type=excluded.research_type,
              quality_tier=excluded.quality_tier,
              fulltext_status=excluded.fulltext_status,
              source_url=excluded.source_url,
              local_path=excluded.local_path,
              sha256=excluded.sha256,
              matched_unit_count=excluded.matched_unit_count,
              max_match_score=excluded.max_match_score,
              best_priority_band=excluded.best_priority_band,
              matched_units_json=excluded.matched_units_json,
              queue_json=excluded.queue_json,
              queue_status=excluded.queue_status,
              citation_ready=0,
              human_verified=0
            """,
            (item["material_external_id"],item["material_title"],item["material_layer"],item["research_type"],
             item["quality_tier"],item["fulltext_status"],item["source_url"],item["local_path"],item["sha256"],
             item["matched_unit_count"],item["max_match_score"],item["best_priority_band"],
             json.dumps(item["matched_units"], ensure_ascii=False),json.dumps(queue_payload, ensure_ascii=False),
             item["queue_status"],0,0),
        )
        output.append(item)
        band_counts[best_band] += 1
        fulltext_counts[item["fulltext_status"]] += 1
    conn.commit()
    report = {
        "run_id": "crosswalk_material_review_queue_20260730",
        "specific_crosswalk_rows": len(rows),
        "distinct_material_objects": len(output),
        "stale_superseded_material_objects": conn.execute("SELECT COUNT(*) FROM crosswalk_material_review_queue WHERE queue_status='STALE_SUPERSEDED'").fetchone()[0],
        "priority_band_counts": dict(band_counts),
        "fulltext_status_counts": dict(fulltext_counts),
        "fulltext_material_objects": sum(count for status, count in fulltext_counts.items() if status in ("FULLTEXT_PDF", "FULLTEXT_HTML_CANDIDATE")),
        "citation_ready": 0,
        "human_verified": 0,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    output.sort(key=lambda item: (rank(item["best_priority_band"]), -item["max_match_score"], item["material_external_id"]))
    (OUT / "MATERIALS.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in output) + "\n", encoding="utf-8")
    (OUT / "FULLTEXT_FIRST.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in output if item["fulltext_status"] in ("FULLTEXT_PDF", "FULLTEXT_HTML_CANDIDATE")) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
