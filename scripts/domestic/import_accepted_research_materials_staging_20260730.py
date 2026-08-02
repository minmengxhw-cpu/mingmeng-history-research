#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Import the accepted domestic research-material layer into staging only.

The source acceptance run already performed cross-layer deduplication and
file checks. This script imports its 285 metadata records into a separate
staging table, carries forward the corrected full-text status for the 77
audited records, and never writes the formal research database or copies
source bodies.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
ACCEPTED = ROOT / "work/domestic/research_layers_acceptance_20260730/UNIFIED_ACCEPTED_RECORDS.jsonl"
CORRECTIONS = ROOT / "work/domestic/research_layers_acceptance_20260730/FULLTEXT_STATUS_CORRECTIONS.jsonl"
SUMMARY = ROOT / "work/domestic/research_layers_acceptance_20260730/ACCEPTANCE_SUMMARY.json"
OUT = ROOT / "work/domestic/research_layers_acceptance_20260730/staging_import"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def status_for(record: dict, corrections: dict[str, dict]) -> str:
    correction = corrections.get(record["external_id"])
    if correction:
        return correction["corrected_fulltext_status"]
    local_path = record.get("local_path")
    if local_path and Path(local_path).is_file():
        return "LOCAL_FILE_PRESENT_METADATA_ONLY"
    return "METADATA_ONLY"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = read_jsonl(ACCEPTED)
    corrections = {row["record_id"]: row for row in read_jsonl(CORRECTIONS)}
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS domestic_research_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT NOT NULL UNIQUE,
            layer TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            institution TEXT,
            publication_date TEXT,
            research_type TEXT,
            quality_tier TEXT,
            source_url TEXT,
            local_path TEXT,
            sha256 TEXT,
            fulltext_status TEXT NOT NULL,
            review_status TEXT NOT NULL,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            metadata_json TEXT NOT NULL,
            acceptance_summary_json TEXT,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS domestic_research_materials_fts USING fts5(
            external_id UNINDEXED, title, author, institution, layer, research_type,
            fulltext_status, content='domestic_research_materials', content_rowid='id',
            tokenize='unicode61'
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS domestic_research_materials_fts_trigram USING fts5(
            external_id UNINDEXED, title, author, institution, layer, research_type,
            fulltext_status, content='domestic_research_materials', content_rowid='id',
            tokenize='trigram'
        )
        """
    )
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = []
    status_counts = Counter()
    layer_counts = Counter()
    for record in records:
        fulltext_status = status_for(record, corrections)
        status_counts[fulltext_status] += 1
        layer_counts[record["layer"]] += 1
        rows.append({**record, "fulltext_status": fulltext_status})
        conn.execute(
            """
            INSERT INTO domestic_research_materials
            (external_id,layer,title,author,institution,publication_date,research_type,
             quality_tier,source_url,local_path,sha256,fulltext_status,review_status,
             citation_ready,human_verified,metadata_json,acceptance_summary_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(external_id) DO UPDATE SET
              layer=excluded.layer, title=excluded.title, author=excluded.author,
              institution=excluded.institution, publication_date=excluded.publication_date,
              research_type=excluded.research_type, quality_tier=excluded.quality_tier,
              source_url=excluded.source_url, local_path=excluded.local_path,
              sha256=excluded.sha256, fulltext_status=excluded.fulltext_status,
              review_status=excluded.review_status, citation_ready=0,
              human_verified=0, metadata_json=excluded.metadata_json,
              acceptance_summary_json=excluded.acceptance_summary_json
            """,
            (record["external_id"], record["layer"], record["title"], record.get("author"),
             record.get("institution"), record.get("publication_date"), record.get("research_type"),
             record.get("quality_tier"), record.get("source_url"), record.get("local_path"),
             record.get("sha256"), fulltext_status, record["review_status"], 0, 0,
             json.dumps(record.get("metadata", {}), ensure_ascii=False), json.dumps(summary, ensure_ascii=False)),
        )
    conn.execute("INSERT INTO domestic_research_materials_fts(domestic_research_materials_fts) VALUES('rebuild')")
    conn.execute("INSERT INTO domestic_research_materials_fts_trigram(domestic_research_materials_fts_trigram) VALUES('rebuild')")
    conn.commit()
    report = {
        "run_id": "domestic_research_materials_staging_20260730",
        "input_records": len(records),
        "imported_records": conn.execute("SELECT count(*) FROM domestic_research_materials").fetchone()[0],
        "fts_records": conn.execute("SELECT count(*) FROM domestic_research_materials_fts").fetchone()[0],
        "fts_trigram_records": conn.execute("SELECT count(*) FROM domestic_research_materials_fts_trigram").fetchone()[0],
        "layer_counts": dict(layer_counts),
        "fulltext_status_counts": dict(status_counts),
        "citation_ready": conn.execute("SELECT count(*) FROM domestic_research_materials WHERE citation_ready=1").fetchone()[0],
        "human_verified": conn.execute("SELECT count(*) FROM domestic_research_materials WHERE human_verified=1").fetchone()[0],
        "formal_db_written": False,
        "source_bodies_copied": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
        "acceptance_state": summary.get("acceptance_state"),
    }
    (OUT / "IMPORT_RECORDS.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
