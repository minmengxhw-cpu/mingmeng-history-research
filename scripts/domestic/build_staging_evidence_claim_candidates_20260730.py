#!/usr/bin/env python3
"""Extract conservative machine claim candidates from eligible OCR pages.

This is a text-location step only.  It preserves the OCR wording, records a
snippet hash, and leaves every row in ``machine_claim_candidate`` with review
required.  No semantic truth or citation-ready status is asserted.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "e4257587a8c32695399c3660d499504c8ccbcd7568ac9170b60553f51ddb7159"


def sha256_bytes(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def extract_text_block(markdown: str) -> str:
    match = re.search(r"^##\s*识别文本\s*$", markdown, flags=re.M)
    if not match:
        return ""
    block = markdown[match.end():]
    block = re.split(r"^##\s+", block, maxsplit=1, flags=re.M)[0]
    lines = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("<!--") or line.startswith("```"):
            continue
        if line.startswith("|") or set(line) <= {"-", "|", ":", " "}:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def main() -> int:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        """SELECT o.*, g.eligible FROM ocr_versions o
           JOIN citation_gate_results g ON g.provenance_id=o.provenance_id
           WHERE g.eligible=1 ORDER BY o.provenance_id"""
    ).fetchall()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS evidence_claim_candidates (
            id INTEGER PRIMARY KEY,
            candidate_id TEXT NOT NULL UNIQUE,
            provenance_id TEXT NOT NULL UNIQUE,
            canonical_document_key TEXT,
            physical_page_no INTEGER,
            source_title TEXT,
            period TEXT,
            candidate_text TEXT NOT NULL,
            candidate_text_sha256 TEXT NOT NULL,
            source_ocr_md_path TEXT NOT NULL,
            source_ocr_md_sha256 TEXT NOT NULL,
            extraction_method TEXT NOT NULL,
            claim_status TEXT NOT NULL,
            review_required INTEGER NOT NULL DEFAULT 1,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(provenance_id) REFERENCES ocr_versions(provenance_id)
        );
        CREATE INDEX IF NOT EXISTS idx_claim_candidates_document ON evidence_claim_candidates(canonical_document_key);
        CREATE INDEX IF NOT EXISTS idx_claim_candidates_status ON evidence_claim_candidates(claim_status);
        """
    )
    counts = Counter()
    for row in rows:
        path = ROOT / str(row["ocr_md_path"] or "")
        if not path.is_file():
            counts["missing_markdown"] += 1
            continue
        text = extract_text_block(path.read_text(encoding="utf-8", errors="replace"))
        # Bound the display/claim candidate size, while retaining a deterministic
        # prefix and its hash; the full OCR file remains the source of record.
        text = text[:4000].strip()
        if not text:
            counts["empty_text"] += 1
            continue
        candidate_id = f"CLM-{row['provenance_id']}"
        c.execute(
            """INSERT INTO evidence_claim_candidates
               (candidate_id,provenance_id,canonical_document_key,physical_page_no,
                source_title,period,candidate_text,candidate_text_sha256,
                source_ocr_md_path,source_ocr_md_sha256,extraction_method,
                claim_status,review_required,citation_ready,human_verified)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(provenance_id) DO UPDATE SET
                 canonical_document_key=excluded.canonical_document_key,
                 physical_page_no=excluded.physical_page_no, source_title=excluded.source_title,
                 period=excluded.period, candidate_text=excluded.candidate_text,
                 candidate_text_sha256=excluded.candidate_text_sha256,
                 source_ocr_md_path=excluded.source_ocr_md_path,
                 source_ocr_md_sha256=excluded.source_ocr_md_sha256,
                 extraction_method=excluded.extraction_method,
                 claim_status=excluded.claim_status, review_required=excluded.review_required,
                 citation_ready=excluded.citation_ready, human_verified=excluded.human_verified""",
            (
                candidate_id, row["provenance_id"], row["canonical_document_key"],
                row["physical_page_no"], row["source_title"], row["period"], text,
                sha256_bytes(text), row["ocr_md_path"], row["ocr_md_sha256"],
                "OCR_TEXT_BLOCK_PREFIX_4000", "machine_claim_candidate", 1, 0, 0,
            ),
        )
        counts["candidates"] += 1
    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(c.execute("PRAGMA foreign_key_check").fetchall())
    counts["table_rows"] = c.execute("SELECT count(*) FROM evidence_claim_candidates").fetchone()[0]
    formal_before = hashlib.sha256(FORMAL_DB.read_bytes()).hexdigest()
    formal_after = hashlib.sha256(FORMAL_DB.read_bytes()).hexdigest()
    report = {
        "report": "DOMESTIC_EVIDENCE_CLAIM_CANDIDATES_20260730",
        "gate_input_rows": len(rows),
        "counts": dict(counts),
        "integrity_check": integrity,
        "foreign_key_violation_count": fk_count,
        "formal_db_sha_before": formal_before,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_before == formal_after == EXPECTED_FORMAL_SHA,
        "claim_status": "machine_claim_candidate",
        "semantic_validation_done": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = DB.parent / "EVIDENCE_CLAIM_CANDIDATES_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    c.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
