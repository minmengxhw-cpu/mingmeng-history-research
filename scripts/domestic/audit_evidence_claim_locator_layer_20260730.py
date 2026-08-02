#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit structural locators for the 465-machine-candidate evidence layer.

This is an acceptance/audit pass only. It verifies hashes, file paths,
canonical/page/provenance bindings, and the presence of machine annotations.
It does not rewrite claim text or promote any row to a historical assertion,
citation-ready, or human-verified.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/evidence_claim_locator_audit"


def sha256_bytes(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    canonical_keys = {row[0] for row in conn.execute("SELECT canonical_document_key FROM documents")}
    locator_units = {row[0] for row in conn.execute("SELECT ocr_provenance_id FROM evidence_units")}
    gate_rows = {row[0]: row[1] for row in conn.execute("SELECT provenance_id, eligible FROM citation_gate_results")}
    provenance_rows = {row[0]: row[1] for row in conn.execute("SELECT provenance_id, valid FROM ocr_versions")}
    rows = conn.execute(
        """
        SELECT e.candidate_id, e.provenance_id, e.canonical_document_key,
               e.physical_page_no, e.source_title, e.period, e.candidate_text,
               e.candidate_text_sha256, e.source_ocr_md_path, e.source_ocr_md_sha256,
               e.claim_status, e.citation_ready, e.human_verified,
               o.source_id AS ocr_source_id, o.physical_page_no AS ocr_physical_page_no,
               o.ocr_md_path, o.ocr_md_sha256, o.binding_status, o.valid,
               a.candidate_id AS annotation_candidate_id,
               s.review_stage, s.priority, s.semantic_validation_done
        FROM evidence_claim_candidates e
        LEFT JOIN ocr_versions o ON o.provenance_id=e.provenance_id
        LEFT JOIN evidence_candidate_annotations a ON a.candidate_id=e.candidate_id
        LEFT JOIN semantic_review_queue s ON s.candidate_id=e.candidate_id
        ORDER BY e.candidate_id
        """
    ).fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_locator_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT NOT NULL UNIQUE,
            provenance_id TEXT NOT NULL,
            canonical_document_key TEXT,
            physical_page_no INTEGER,
            source_ocr_md_path TEXT,
            source_ocr_md_sha256 TEXT,
            audit_json TEXT NOT NULL,
            audit_status TEXT NOT NULL,
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
        checks = {
            "canonical_bound": bool(row["canonical_document_key"]),
            "canonical_document_exists": row["canonical_document_key"] in canonical_keys,
            "physical_page_present": isinstance(row["physical_page_no"], int) and row["physical_page_no"] > 0,
            "provenance_present": bool(row["provenance_id"] and row["ocr_source_id"]),
            "provenance_valid": bool(provenance_rows.get(row["provenance_id"])),
            "ocr_page_matches": row["physical_page_no"] == row["ocr_physical_page_no"],
            "locator_unit_present": row["provenance_id"] in locator_units,
            "citation_gate_eligible": bool(gate_rows.get(row["provenance_id"])),
            "candidate_text_present": bool((row["candidate_text"] or "").strip()),
            "candidate_length_sufficient": len((row["candidate_text"] or "").strip()) >= 80,
            "candidate_sha_present": bool(row["candidate_text_sha256"]),
            "candidate_sha_matches": bool(row["candidate_text_sha256"] and row["candidate_text_sha256"] == sha256_bytes(row["candidate_text"] or "")),
            "source_path_present": bool(path and path.exists()),
            "source_sha_present": bool(row["source_ocr_md_sha256"]),
            "source_sha_matches": False,
            "annotation_present": bool(row["annotation_candidate_id"]),
            "semantic_queue_present": bool(row["review_stage"]),
        }
        if checks["source_path_present"] and checks["source_sha_present"]:
            checks["source_sha_matches"] = sha256_file(path) == row["source_ocr_md_sha256"]
        reasons = [name for name, passed in checks.items() if not passed]
        status = "STRUCTURE_READY_CLAIM_INDEX" if not reasons else "HOLD_CLAIM_LOCATOR"
        status_counts[status] += 1
        for reason in reasons:
            reason_counts[reason] += 1
        audit = {
            "candidate_id": row["candidate_id"],
            "provenance_id": row["provenance_id"],
            "canonical_document_key": row["canonical_document_key"],
            "physical_page_no": row["physical_page_no"],
            "source_title": row["source_title"],
            "period": row["period"],
            "source_ocr_md_path": row["source_ocr_md_path"],
            "checks": checks,
            "failed_checks": reasons,
            "audit_status": status,
            "claim_status": row["claim_status"],
            "review_stage": row["review_stage"],
            "priority": row["priority"],
            "semantic_validation_done": int(row["semantic_validation_done"] or 0),
            "citation_ready": int(row["citation_ready"] or 0),
            "human_verified": int(row["human_verified"] or 0),
        }
        conn.execute(
            """
            INSERT INTO evidence_claim_locator_audit
            (candidate_id,provenance_id,canonical_document_key,physical_page_no,
             source_ocr_md_path,source_ocr_md_sha256,audit_json,audit_status,
             semantic_validation_done,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(candidate_id) DO UPDATE SET
              provenance_id=excluded.provenance_id,
              canonical_document_key=excluded.canonical_document_key,
              physical_page_no=excluded.physical_page_no,
              source_ocr_md_path=excluded.source_ocr_md_path,
              source_ocr_md_sha256=excluded.source_ocr_md_sha256,
              audit_json=excluded.audit_json,
              audit_status=excluded.audit_status,
              semantic_validation_done=excluded.semantic_validation_done,
              citation_ready=0,
              human_verified=0
            """,
            (row["candidate_id"], row["provenance_id"], row["canonical_document_key"], row["physical_page_no"],
             row["source_ocr_md_path"], row["source_ocr_md_sha256"], json.dumps(audit, ensure_ascii=False),
             status, int(row["semantic_validation_done"] or 0), 0, 0),
        )
        results.append(audit)
    conn.commit()
    report = {
        "run_id": "evidence_claim_locator_audit_20260730",
        "input_candidates": len(rows),
        "status_counts": dict(status_counts),
        "reason_counts": dict(reason_counts),
        "semantic_validation_done": sum(x["semantic_validation_done"] for x in results),
        "citation_ready": sum(x["citation_ready"] for x in results),
        "human_verified": sum(x["human_verified"] for x in results),
        "body_excerpts_persisted": False,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "AUDIT.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in results) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
