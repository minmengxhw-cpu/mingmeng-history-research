#!/usr/bin/env python3
"""Audit structural prerequisites for machine evidence candidates.

This is deliberately narrower than semantic validation: it verifies file
existence, SHA, page/document linkage, and queue/gate state. It never changes
candidate status and never creates citation-ready or human-verified records.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/MACHINE_EVIDENCE_STRUCTURE_AUDIT.jsonl"
REPORT = ROOT / "work/domestic/staging_20260730/MACHINE_EVIDENCE_STRUCTURE_AUDIT_REPORT.json"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_path(raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    candidates = conn.execute("SELECT * FROM evidence_claim_candidates ORDER BY candidate_id").fetchall()
    queue = {row["candidate_id"]: row for row in conn.execute("SELECT * FROM semantic_review_queue")}
    docs = {row["canonical_document_key"] for row in conn.execute("SELECT canonical_document_key FROM documents")}
    units = {row["ocr_provenance_id"] for row in conn.execute("SELECT ocr_provenance_id FROM evidence_units")}
    gate = {row["provenance_id"]: row for row in conn.execute("SELECT * FROM citation_gate_results")}
    provenance = {row["provenance_id"]: row for row in conn.execute("SELECT * FROM ocr_versions")}
    conn.close()

    results = []
    stage_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    for row in candidates:
        item = dict(row)
        candidate_id = item["candidate_id"]
        q = queue.get(candidate_id)
        reasons: list[str] = []
        path = resolve_path(item.get("source_ocr_md_path"))
        if not item.get("candidate_text", "").strip():
            reasons.append("EMPTY_CANDIDATE_TEXT")
        if len(item.get("candidate_text", "").strip()) < 80:
            reasons.append("SHORT_CANDIDATE_TEXT")
        if not item.get("physical_page_no") or int(item["physical_page_no"]) <= 0:
            reasons.append("MISSING_PHYSICAL_PAGE")
        if not item.get("canonical_document_key") or item["canonical_document_key"] not in docs:
            reasons.append("CANONICAL_DOCUMENT_NOT_FOUND")
        if item["provenance_id"] not in units:
            reasons.append("LOCATOR_UNIT_NOT_FOUND")
        if path is None or not path.exists():
            reasons.append("OCR_FILE_NOT_FOUND")
        else:
            actual_sha = file_sha256(path)
            if actual_sha != item.get("source_ocr_md_sha256"):
                reasons.append("OCR_FILE_SHA_MISMATCH")
        p = provenance.get(item["provenance_id"])
        if p is None:
            reasons.append("OCR_PROVENANCE_NOT_FOUND")
        elif not p["valid"]:
            reasons.append("OCR_PROVENANCE_INVALID")
        g = gate.get(item["provenance_id"])
        if g is None:
            reasons.append("CITATION_GATE_NOT_FOUND")
        elif not g["eligible"]:
            reasons.append("CITATION_GATE_HOLD")
        if q is None:
            reasons.append("SEMANTIC_QUEUE_NOT_FOUND")

        stage = "STRUCTURE_READY_SEMANTIC_REVIEW" if not reasons else "HOLD_STRUCTURE"
        for reason in reasons:
            reason_counts[reason] += 1
        stage_counts[stage] += 1
        results.append(
            {
                "candidate_id": candidate_id,
                "provenance_id": item["provenance_id"],
                "canonical_document_key": item.get("canonical_document_key"),
                "physical_page_no": item.get("physical_page_no"),
                "queue_stage": q["review_stage"] if q else None,
                "queue_priority": q["priority"] if q else None,
                "structure_stage": stage,
                "structure_reasons": reasons,
                "source_ocr_md_path": item.get("source_ocr_md_path"),
                "source_ocr_md_sha256": item.get("source_ocr_md_sha256"),
                "semantic_validation_done": False,
                "citation_ready": False,
                "human_verified": False,
            }
        )

    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in results) + "\n", encoding="utf-8")
    report = {
        "report": "DOMESTIC_MACHINE_EVIDENCE_STRUCTURE_AUDIT_20260730",
        "rows": len(results),
        "stage_counts": dict(sorted(stage_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "semantic_validation_done": 0,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_written": False,
        "staging_db_written": False,
        "rule": "structural prerequisites only; no semantic claim approval",
        "output": str(OUT),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
