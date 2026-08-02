#!/usr/bin/env python3
"""Add the domestic official/web machine-text layer to staging.

This migration is idempotent, touches only the disposable staging database,
and verifies that the formal research database remains byte-for-byte stable.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
QUEUE = ROOT / "work/domestic/grok_next_stage_20260730/05_handoff/DOMESTIC_MACHINE_TEXT_QUEUE.jsonl"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "857e2b3fc485af17c2852c39aede6a8e4129f8efe7ddecca8c16129d4312f07d"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def main() -> int:
    if not DB.exists():
        raise SystemExit(f"missing staging database: {DB}")
    if not QUEUE.exists():
        raise SystemExit(f"missing machine-text queue: {QUEUE}")
    formal_before = sha256(FORMAL_DB)
    if formal_before != EXPECTED_FORMAL_SHA:
        raise SystemExit(f"formal DB baseline changed before migration: {formal_before}")
    source_rows = load_rows(QUEUE)
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS machine_text_records (
            id INTEGER PRIMARY KEY,
            object_id TEXT NOT NULL UNIQUE,
            title TEXT,
            formation_date TEXT,
            formation_institution TEXT,
            document_type TEXT,
            source_url TEXT,
            landing_url TEXT,
            local_path TEXT,
            sha256 TEXT,
            file_magic TEXT,
            evidence_tier TEXT,
            historical_phase TEXT,
            reclass_bucket TEXT,
            access_status TEXT,
            rights_note TEXT,
            shanghai_relevant INTEGER,
            ocr_needed INTEGER,
            track TEXT,
            handoff_source TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_machine_text_phase ON machine_text_records(historical_phase);
        CREATE INDEX IF NOT EXISTS idx_machine_text_tier ON machine_text_records(evidence_tier);
        CREATE VIRTUAL TABLE IF NOT EXISTS machine_text_search USING fts5(
            object_id UNINDEXED,
            title,
            formation_institution,
            document_type,
            evidence_tier,
            historical_phase,
            content='machine_text_records',
            content_rowid='id'
        );
        """
    )
    for row in source_rows:
        c.execute(
            """INSERT INTO machine_text_records
               (object_id,title,formation_date,formation_institution,document_type,
                source_url,landing_url,local_path,sha256,file_magic,evidence_tier,
                historical_phase,reclass_bucket,access_status,rights_note,
                shanghai_relevant,ocr_needed,track,handoff_source)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(object_id) DO UPDATE SET
                 title=excluded.title, formation_date=excluded.formation_date,
                 formation_institution=excluded.formation_institution,
                 document_type=excluded.document_type, source_url=excluded.source_url,
                 landing_url=excluded.landing_url, local_path=excluded.local_path,
                 sha256=excluded.sha256, file_magic=excluded.file_magic,
                 evidence_tier=excluded.evidence_tier,
                 historical_phase=excluded.historical_phase,
                 reclass_bucket=excluded.reclass_bucket,
                 access_status=excluded.access_status, rights_note=excluded.rights_note,
                 shanghai_relevant=excluded.shanghai_relevant,
                 ocr_needed=excluded.ocr_needed, track=excluded.track,
                 handoff_source=excluded.handoff_source""",
            (
                row.get("object_id"), row.get("title"), row.get("formation_date"),
                row.get("formation_institution"), row.get("document_type"),
                row.get("source_url"), row.get("landing_url"), row.get("local_path"),
                row.get("sha256"), row.get("magic"), row.get("evidence_tier"),
                row.get("historical_phase"), row.get("reclass_bucket"),
                row.get("access_status"), row.get("rights_note"),
                int(bool(row.get("shanghai_relevant"))), int(bool(row.get("ocr_needed"))),
                row.get("track"), row.get("handoff_source"),
            ),
        )
    c.execute("INSERT INTO machine_text_search(machine_text_search) VALUES ('rebuild')")
    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(c.execute("PRAGMA foreign_key_check").fetchall())
    counts = {
        "machine_text_records": c.execute("SELECT count(*) FROM machine_text_records").fetchone()[0],
        "machine_text_search": c.execute("SELECT count(*) FROM machine_text_search").fetchone()[0],
        "official_html": c.execute("SELECT count(*) FROM machine_text_records WHERE file_magic='html'").fetchone()[0],
        "ocr_needed": c.execute("SELECT count(*) FROM machine_text_records WHERE ocr_needed=1").fetchone()[0],
    }
    c.close()
    formal_after = sha256(FORMAL_DB)
    report = {
        "migration": "STAGING_MACHINE_TEXT_20260730",
        "source_queue": str(QUEUE),
        "source_rows": len(source_rows),
        "counts": counts,
        "integrity_check": integrity,
        "foreign_key_violation_count": fk_count,
        "formal_db_sha_before": formal_before,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_before == formal_after == EXPECTED_FORMAL_SHA,
    }
    out = DB.parent / "MACHINE_TEXT_MIGRATION_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
