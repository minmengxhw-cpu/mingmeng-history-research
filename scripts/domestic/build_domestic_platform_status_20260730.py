#!/usr/bin/env python3
"""Create a machine-readable, non-mutating domestic platform status snapshot."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FORMAL_DB = ROOT / "data/research_index.sqlite"
STAGING_DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
QUEUE_REPORT = ROOT / "work/domestic/mmda_p1_intake_20260730/MMDA_1942_1943_ORIGINAL_PENDING_REPORT.json"
SUPPLEMENTAL_REPORT = ROOT / "work/domestic/phase2_inventory_20260730/supplemental_1942_1943/REPORT.json"
CORE_GAP_REPORT = ROOT / "work/domestic/phase2_inventory_20260730/core_gap_matrix_20260730/CORE_GAP_MATRIX.json"
RESEARCH_REPORT = ROOT / "work/domestic/phase2_inventory_20260730/research_1942_1943/REPORT.json"
OCR_PILOT_REPORT = ROOT / "work/domestic/academic_ocr_pilot_20260730/REPORT.json"
OCR_BATCH_REPORT = ROOT / "work/domestic/academic_ocr_batch_pilot_20260730/REPORT.json"
OCR_1943_TARGET_REPORT = ROOT / "work/domestic/academic_ocr_1943_target_20260730/REPORT.json"
FORMAL_AUDIT = ROOT / "work/domestic/FORMAL_DB_SHA_AUDIT_20260801.json"
FORMAL_REBASELINE = ROOT / "work/domestic/FORMAL_DB_REBASELINE_20260801.md"
OUT = ROOT / "work/domestic/CODEX_DOMESTIC_PLATFORM_STATUS_20260730.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def formal_status(audit: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(FORMAL_DB.read_bytes()).hexdigest() if FORMAL_DB.exists() else None
    integrity = None
    if FORMAL_DB.exists():
        with sqlite3.connect(FORMAL_DB) as conn:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    impact = audit.get("impact", {}) if isinstance(audit.get("impact"), dict) else {}
    intentional_detail = audit.get("intentional_detail", {}) if isinstance(audit.get("intentional_detail"), dict) else {}
    return {
        "path": str(FORMAL_DB),
        "sha256": digest,
        "previous_freeze_sha256": audit.get("previous_freeze_sha"),
        "integrity_check": integrity,
        "write_policy": "FROZEN",
        "rebaselined": bool(audit.get("current_sha") and audit.get("previous_freeze_sha") and digest == audit.get("current_sha")),
        "rebaseline_doc": str(FORMAL_REBASELINE.relative_to(ROOT)) if FORMAL_REBASELINE.exists() else None,
        "last_change_audit": str((ROOT / "work/domestic/FORMAL_DB_SHA_AUDIT_20260801.md").relative_to(ROOT)) if FORMAL_AUDIT.exists() else None,
        "last_change_at": audit.get("file_mtime"),
        "last_change_summary": audit.get("root_cause", {}).get("summary"),
        # This is deliberately separate from the non-mutating snapshot writer:
        # the audit proves a prior post-freeze write, while this script only reads.
        "formal_db_write_audited": bool(impact.get("formal_db_written")),
        "formal_db_written_since_previous_freeze": bool(impact.get("formal_db_written")),
        "formal_db_write_policy_violation_audited": bool(intentional_detail.get("freeze_policy_violation")),
        "citation_ready_delta_from_last_change": impact.get("citation_ready_delta"),
    }


def staging_status() -> dict[str, Any]:
    if not STAGING_DB.exists():
        return {"path": str(STAGING_DB), "exists": False}
    counts: dict[str, int] = {}
    phases: dict[str, int] = {}
    with sqlite3.connect(STAGING_DB) as conn:
        for table in ("documents", "page_assets", "ocr_versions", "domestic_research_materials", "evidence_claim_candidates"):
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            counts[table] = int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]) if exists else 0
        for phase, count in conn.execute("SELECT dominant_phase, count(*) FROM documents GROUP BY dominant_phase"):
            phases[str(phase or "unknown")] = int(count)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    return {"path": str(STAGING_DB), "exists": True, "integrity_check": integrity, "counts": counts, "phase_counts": phases}


def main() -> int:
    formal_audit = read_json(FORMAL_AUDIT)
    queue = read_json(QUEUE_REPORT)
    supplemental = read_json(SUPPLEMENTAL_REPORT)
    gap = read_json(CORE_GAP_REPORT)
    research = read_json(RESEARCH_REPORT)
    ocr_pilot = read_json(OCR_PILOT_REPORT)
    ocr_batch = read_json(OCR_BATCH_REPORT)
    ocr_1943_target = read_json(OCR_1943_TARGET_REPORT)
    payload = {
        "status": "ACTIVE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "local_quality_url": "http://127.0.0.1:8765/domestic/quality",
            "local_acquisition_url": "http://127.0.0.1:8765/domestic/acquisition",
            "domestic_search_url": "http://127.0.0.1:8765/domestic/search",
            "scope": "国内民盟史与多党合作史资料层",
        },
        "formal_db": formal_status(formal_audit),
        "staging_db": staging_status(),
        "mmda_1942_1943": {
            "pending_rows": queue.get("rows", 0),
            "phase_counts": queue.get("phase_counts", {}),
            "original_files_present": queue.get("original_files_present", 0),
            "citation_ready": queue.get("citation_ready", 0),
            "core_primary_gap_closed": supplemental.get("core_primary_gap_closed", False),
            "core_zero_phases": gap.get("zero_canonical_phases", []),
        },
        "research_context_1942_1943": {
            "rows": research.get("rows", 0),
            "layer_counts": research.get("layer_counts", {}),
            "fulltext_status_counts": research.get("fulltext_status_counts", {}),
            "content_status_counts": research.get("content_status_counts", {}),
            "local_extractable_content": research.get("local_extractable_content", 0),
            "pdf_needs_ocr": research.get("pdf_needs_ocr", 0),
            "citation_ready": research.get("citation_ready", 0),
            "human_verified": research.get("human_verified", 0),
            "rule": research.get("rule"),
            "ocr_pilot_pages": ocr_pilot.get("completed_pages", 0) + ocr_batch.get("completed_pages", 0),
            "ocr_pilot_mean_confidence": ocr_pilot.get("mean_confidence", 0),
            "ocr_batch_mean_confidences": ocr_batch.get("mean_confidences", {}),
            "ocr_batch_low_confidence_pages": sum(1 for value in ocr_batch.get("mean_confidences", {}).values() if float(value) < 0.85),
            "ocr_1943_target_staged_pages": ocr_1943_target.get("completed_pages", 0),
            "ocr_pilot_citation_ready": ocr_pilot.get("citation_ready_created", 0),
        },
        "rules": {
            "originals_before_citation": True,
            "ocr_staging_before_formal_apply": True,
            "do_not_promote_catalogue_or_approximate_ocr": True,
            # Compatibility field: this non-mutating status generator did not
            # itself write SQLite. Use formal_db.formal_db_write_audited for
            # the audited post-freeze write state.
            "formal_db_written_by_snapshot": False,
            "formal_db_write_audit": str(FORMAL_AUDIT.relative_to(ROOT)) if FORMAL_AUDIT.exists() else None,
            "formal_db_write_audit_note": "The current formal DB has an audited write since the previous freeze; this snapshot generator remains read-only.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "status": payload["status"], "queue_rows": queue.get("rows", 0), "formal_sha256": payload["formal_db"]["sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
