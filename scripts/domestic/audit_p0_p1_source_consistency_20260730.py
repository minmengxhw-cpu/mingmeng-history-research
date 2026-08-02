#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check P0/P1 representative candidates against their local OCR source files."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/p0_p1_source_consistency"


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def resolve(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT u.unit_id, u.representative_candidate_id, u.priority,
               e.provenance_id, e.canonical_document_key, e.physical_page_no,
               e.candidate_text, e.candidate_text_sha256, e.source_ocr_md_path,
               e.source_ocr_md_sha256, o.physical_page_no AS provenance_page,
               o.valid AS provenance_valid, d.canonical_document_key AS document_key,
               l.audit_status
        FROM evidence_claim_review_units u
        JOIN evidence_claim_candidates e ON e.candidate_id=u.representative_candidate_id
        LEFT JOIN ocr_versions o ON o.provenance_id=e.provenance_id
        LEFT JOIN documents d ON d.canonical_document_key=e.canonical_document_key
        LEFT JOIN evidence_claim_locator_audit l ON l.candidate_id=e.candidate_id
        WHERE u.priority IN ('P0','P1')
        ORDER BY CASE u.priority WHEN 'P0' THEN 0 ELSE 1 END, u.unit_id
        """
    ).fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_source_consistency (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id TEXT NOT NULL UNIQUE,
            candidate_id TEXT NOT NULL UNIQUE,
            priority TEXT NOT NULL,
            consistency_json TEXT NOT NULL,
            consistency_status TEXT NOT NULL,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    results = []
    status_counts = Counter()
    reason_counts = Counter()
    for row in rows:
        path = resolve(row["source_ocr_md_path"])
        source_text = ""
        source_exists = bool(path and path.exists())
        actual_source_sha = None
        if source_exists:
            actual_source_sha = file_sha(path)
            source_text = path.read_text(encoding="utf-8", errors="replace")
        candidate = norm(row["candidate_text"] or "")
        prefix = candidate[:80]
        checks = {
            "source_file_exists": source_exists,
            "source_sha_matches": bool(source_exists and row["source_ocr_md_sha256"] and actual_source_sha == row["source_ocr_md_sha256"]),
            "candidate_prefix_locatable": bool(prefix and prefix in norm(source_text)),
            "candidate_sha_present": bool(row["candidate_text_sha256"]),
            "canonical_document_exists": bool(row["document_key"]),
            "physical_page_matches_provenance": bool(row["physical_page_no"] and row["physical_page_no"] == row["provenance_page"]),
            "provenance_valid": bool(row["provenance_valid"]),
            "locator_audit_ready": row["audit_status"] == "STRUCTURE_READY_CLAIM_INDEX",
        }
        failed = [key for key, value in checks.items() if not value]
        status = "SOURCE_CONSISTENT_LOCATABLE" if not failed else "HOLD_SOURCE_CONSISTENCY"
        status_counts[status] += 1
        for reason in failed:
            reason_counts[reason] += 1
        item = {
            "unit_id": row["unit_id"],
            "candidate_id": row["representative_candidate_id"],
            "priority": row["priority"],
            "provenance_id": row["provenance_id"],
            "canonical_document_key": row["canonical_document_key"],
            "physical_page_no": row["physical_page_no"],
            "source_ocr_md_path": row["source_ocr_md_path"],
            "checks": checks,
            "failed_checks": failed,
            "consistency_status": status,
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
        }
        conn.execute(
            """
            INSERT INTO evidence_claim_source_consistency
            (unit_id,candidate_id,priority,consistency_json,consistency_status,
             semantic_validation_done,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(unit_id) DO UPDATE SET
              candidate_id=excluded.candidate_id,
              priority=excluded.priority,
              consistency_json=excluded.consistency_json,
              consistency_status=excluded.consistency_status,
              semantic_validation_done=0,
              citation_ready=0,
              human_verified=0
            """,
            (item["unit_id"], item["candidate_id"], item["priority"], json.dumps(item, ensure_ascii=False), status, 0, 0, 0),
        )
        results.append(item)
    conn.commit()
    report = {
        "run_id": "p0_p1_source_consistency_20260730",
        "input_review_units": len(rows),
        "status_counts": dict(status_counts),
        "reason_counts": dict(reason_counts),
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "CONSISTENCY.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
