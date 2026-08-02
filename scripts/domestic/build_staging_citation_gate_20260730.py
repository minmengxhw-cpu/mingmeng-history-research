#!/usr/bin/env python3
"""Evaluate a conservative citation-candidate gate for staging OCR rows.

The gate only records eligibility.  It never sets formal citation-ready flags
and never changes the formal research database.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "4837dbd671ec8d2965b8a7cb06e37ceebd6b1ea7337f75e30fc18bf6b1adfa7a"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_file(path_value: str | None, expected: str | None) -> tuple[bool, str]:
    if not path_value:
        return False, "PATH_MISSING"
    path = ROOT / path_value
    if not path.is_file():
        return False, "FILE_MISSING"
    if not expected:
        return False, "SHA_MISSING"
    actual = sha256(path)
    return actual == expected, "SHA_MATCH" if actual == expected else "SHA_MISMATCH"


def main() -> int:
    formal_before = sha256(FORMAL_DB)
    if formal_before != EXPECTED_FORMAL_SHA:
        raise SystemExit(f"formal DB baseline changed: {formal_before}")
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    rows = c.execute("SELECT * FROM ocr_versions ORDER BY provenance_id").fetchall()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS citation_gate_results (
            id INTEGER PRIMARY KEY,
            provenance_id TEXT NOT NULL UNIQUE,
            canonical_document_key TEXT,
            gate_status TEXT NOT NULL,
            eligible INTEGER NOT NULL,
            reasons_json TEXT NOT NULL,
            source_file_check TEXT NOT NULL,
            ocr_file_check TEXT NOT NULL,
            page_image_check TEXT NOT NULL,
            evaluated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(provenance_id) REFERENCES ocr_versions(provenance_id)
        );
        CREATE INDEX IF NOT EXISTS idx_citation_gate_status ON citation_gate_results(gate_status, eligible);
        """
    )
    counts = Counter()
    for row in rows:
        reasons: list[str] = []
        source_ok, source_check = check_file(row["source_file"], row["source_sha256"])
        ocr_ok, ocr_check = check_file(row["ocr_md_path"], row["ocr_md_sha256"])
        image_ok, image_check = check_file(row["page_image_path"], row["page_image_sha256"])
        if row["binding_status"] != "BOUND_CANONICAL":
            reasons.append("CANONICAL_BINDING_NOT_CONFIRMED")
        if not row["valid"]:
            reasons.append("PROVENANCE_VALID_FALSE")
        if not source_ok:
            reasons.append(f"SOURCE_{source_check}")
        if not ocr_ok:
            reasons.append(f"OCR_{ocr_check}")
        if not image_ok:
            reasons.append(f"PAGE_IMAGE_{image_check}")
        if row["text_structure_status"] != "MACHINE_OCR_COMPLETE":
            reasons.append("TEXT_STRUCTURE_NOT_COMPLETE")
        if not row["rights_status"]:
            reasons.append("RIGHTS_STATUS_MISSING")
        eligible = not reasons
        status = "citation_candidate" if eligible else "hold_or_review"
        c.execute(
            """INSERT INTO citation_gate_results
               (provenance_id,canonical_document_key,gate_status,eligible,reasons_json,
                source_file_check,ocr_file_check,page_image_check)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(provenance_id) DO UPDATE SET
                 canonical_document_key=excluded.canonical_document_key,
                 gate_status=excluded.gate_status, eligible=excluded.eligible,
                 reasons_json=excluded.reasons_json, source_file_check=excluded.source_file_check,
                 ocr_file_check=excluded.ocr_file_check, page_image_check=excluded.page_image_check,
                 evaluated_at=datetime('now')""",
            (
                row["provenance_id"], row["canonical_document_key"], status, int(eligible),
                json.dumps(reasons, ensure_ascii=False), source_check, ocr_check, image_check,
            ),
        )
        counts["rows"] += 1
        counts[status] += 1
        counts["eligible"] += int(eligible)
        for reason in reasons:
            counts[f"reason:{reason}"] += 1
    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(c.execute("PRAGMA foreign_key_check").fetchall())
    formal_after = sha256(FORMAL_DB)
    report = {
        "report": "DOMESTIC_CITATION_GATE_20260730",
        "counts": dict(counts),
        "integrity_check": integrity,
        "foreign_key_violation_count": fk_count,
        "formal_db_sha_before": formal_before,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_before == formal_after == EXPECTED_FORMAL_SHA,
        "formal_citation_ready_written": 0,
        "human_verified_written": 0,
        "rule": "eligible is a staging citation_candidate only; formal DB remains untouched",
    }
    out = DB.parent / "CITATION_GATE_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    c.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
