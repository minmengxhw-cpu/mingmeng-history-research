#!/usr/bin/env python3
"""Migrate local OCR provenance v2 into the disposable domestic staging DB.

The migration creates page-level OCR versions and locator-only evidence units.
An evidence locator is not a semantic claim and is never citation-ready.  OCR
rows whose source file cannot be bound to a canonical staging document remain
explicitly held instead of being guessed into a document.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OCR_ROOT = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "857e2b3fc485af17c2852c39aede6a8e4129f8efe7ddecca8c16129d4312f07d"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_ocr_rows() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(OCR_ROOT.glob("*PROVENANCE.v2.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict):
                value["provenance_manifest"] = str(path)
                value["provenance_manifest_line"] = line_no
                rows.append(value)
    return rows


def main() -> int:
    if not DB.exists():
        raise SystemExit(f"missing staging database: {DB}")
    formal_before = sha256(FORMAL_DB)
    if formal_before != EXPECTED_FORMAL_SHA:
        raise SystemExit(f"formal DB baseline changed before migration: {formal_before}")
    source_rows = load_ocr_rows()
    if not source_rows:
        raise SystemExit("no OCR provenance v2 rows found")

    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=ON")
    c.row_factory = sqlite3.Row
    path_to_document = {
        row["local_path"]: row["canonical_document_key"]
        for row in c.execute(
            """SELECT p.local_path, d.canonical_document_key
               FROM page_assets p JOIN documents d ON d.id=p.document_id
               WHERE p.local_path IS NOT NULL"""
        )
    }
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS ocr_versions (
            id INTEGER PRIMARY KEY,
            provenance_id TEXT NOT NULL UNIQUE,
            canonical_document_key TEXT,
            source_id TEXT,
            source_file TEXT,
            source_sha256 TEXT,
            source_file_size INTEGER,
            source_title TEXT,
            physical_page_no INTEGER,
            pdf_page_no INTEGER,
            printed_page TEXT,
            page_image_path TEXT,
            page_image_sha256 TEXT,
            ocr_md_path TEXT,
            ocr_md_sha256 TEXT,
            ocr_lines INTEGER,
            ocr_confidence REAL,
            ocr_engine TEXT,
            ocr_model TEXT,
            ocr_mode TEXT,
            text_structure_status TEXT,
            machine_visual_status TEXT,
            valid INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            year INTEGER,
            period TEXT,
            issue_date TEXT,
            edition TEXT,
            mapping_id TEXT,
            rights_status TEXT,
            relation_required TEXT,
            binding_status TEXT NOT NULL,
            manifest_path TEXT,
            manifest_line INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_ocr_versions_document ON ocr_versions(canonical_document_key);
        CREATE INDEX IF NOT EXISTS idx_ocr_versions_status ON ocr_versions(binding_status, valid);
        CREATE TABLE IF NOT EXISTS evidence_units (
            id INTEGER PRIMARY KEY,
            unit_id TEXT NOT NULL UNIQUE,
            canonical_document_key TEXT,
            ocr_provenance_id TEXT NOT NULL UNIQUE,
            unit_type TEXT NOT NULL,
            claim_text TEXT,
            locator_json TEXT NOT NULL,
            evidence_status TEXT NOT NULL,
            uncertainty_note TEXT,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(ocr_provenance_id) REFERENCES ocr_versions(provenance_id)
        );
        CREATE INDEX IF NOT EXISTS idx_evidence_units_document ON evidence_units(canonical_document_key);
        CREATE INDEX IF NOT EXISTS idx_evidence_units_status ON evidence_units(evidence_status);
        CREATE TABLE IF NOT EXISTS ocr_provenance_flags (
            id INTEGER PRIMARY KEY,
            provenance_id TEXT NOT NULL,
            flag_type TEXT NOT NULL,
            detail TEXT NOT NULL,
            severity TEXT NOT NULL,
            UNIQUE(provenance_id, flag_type)
        );
        """
    )

    counters = Counter()
    for row in source_rows:
        provenance_id = str(row.get("provenance_id") or "").strip()
        if not provenance_id:
            counters["missing_provenance_id"] += 1
            continue
        source_file = str(row.get("source_file") or "")
        canonical = path_to_document.get(source_file)
        binding_status = "BOUND_CANONICAL" if canonical else "HOLD_UNBOUND_SOURCE_FILE"
        valid = int(bool(row.get("valid")))
        citation_ready = int(bool(row.get("citation_ready")))
        human_verified = int(bool(row.get("human_verified")))
        c.execute(
            """INSERT INTO ocr_versions
               (provenance_id,canonical_document_key,source_id,source_file,source_sha256,
                source_file_size,source_title,physical_page_no,pdf_page_no,printed_page,
                page_image_path,page_image_sha256,ocr_md_path,ocr_md_sha256,ocr_lines,
                ocr_confidence,ocr_engine,ocr_model,ocr_mode,text_structure_status,
                machine_visual_status,valid,citation_ready,human_verified,year,period,
                issue_date,edition,mapping_id,rights_status,relation_required,binding_status,
                manifest_path,manifest_line)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(provenance_id) DO UPDATE SET
                 canonical_document_key=excluded.canonical_document_key,
                 source_id=excluded.source_id, source_file=excluded.source_file,
                 source_sha256=excluded.source_sha256, source_file_size=excluded.source_file_size,
                 source_title=excluded.source_title, physical_page_no=excluded.physical_page_no,
                 pdf_page_no=excluded.pdf_page_no, printed_page=excluded.printed_page,
                 page_image_path=excluded.page_image_path, page_image_sha256=excluded.page_image_sha256,
                 ocr_md_path=excluded.ocr_md_path, ocr_md_sha256=excluded.ocr_md_sha256,
                 ocr_lines=excluded.ocr_lines, ocr_confidence=excluded.ocr_confidence,
                 ocr_engine=excluded.ocr_engine, ocr_model=excluded.ocr_model,
                 ocr_mode=excluded.ocr_mode, text_structure_status=excluded.text_structure_status,
                 machine_visual_status=excluded.machine_visual_status, valid=excluded.valid,
                 citation_ready=excluded.citation_ready, human_verified=excluded.human_verified,
                 year=excluded.year, period=excluded.period, issue_date=excluded.issue_date,
                 edition=excluded.edition, mapping_id=excluded.mapping_id,
                 rights_status=excluded.rights_status, relation_required=excluded.relation_required,
                 binding_status=excluded.binding_status, manifest_path=excluded.manifest_path,
                 manifest_line=excluded.manifest_line""",
            (
                provenance_id, canonical, row.get("source_id"), source_file,
                row.get("source_sha256"), row.get("source_file_size"), row.get("source_title"),
                row.get("physical_page_no"), row.get("pdf_page_no"), row.get("printed_page"),
                row.get("page_image_path"), row.get("page_image_sha256"), row.get("ocr_md_path"),
                row.get("ocr_md_sha256"), row.get("ocr_lines"), row.get("ocr_confidence"),
                row.get("ocr_engine"), row.get("ocr_model"), row.get("ocr_mode"),
                row.get("text_structure_status"), row.get("machine_visual_status"), valid,
                citation_ready, human_verified, row.get("year"), row.get("period"),
                row.get("issue_date"), row.get("edition"), row.get("mapping_id"),
                row.get("rights_status"), row.get("relation_required"), binding_status,
                row.get("provenance_manifest"), row.get("provenance_manifest_line"),
            ),
        )
        unit_id = f"OCRLOC-{provenance_id}"
        locator = {
            "physical_page_no": row.get("physical_page_no"),
            "pdf_page_no": row.get("pdf_page_no"),
            "printed_page": row.get("printed_page"),
            "page_image_path": row.get("page_image_path"),
            "ocr_md_path": row.get("ocr_md_path"),
            "ocr_md_sha256": row.get("ocr_md_sha256"),
        }
        evidence_status = "machine_locator_only" if canonical else "hold_unbound_ocr_locator"
        c.execute(
            """INSERT INTO evidence_units
               (unit_id,canonical_document_key,ocr_provenance_id,unit_type,claim_text,
                locator_json,evidence_status,uncertainty_note,citation_ready,human_verified)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(ocr_provenance_id) DO UPDATE SET
                 canonical_document_key=excluded.canonical_document_key,
                 locator_json=excluded.locator_json, evidence_status=excluded.evidence_status,
                 uncertainty_note=excluded.uncertainty_note,
                 citation_ready=excluded.citation_ready, human_verified=excluded.human_verified""",
            (
                unit_id, canonical, provenance_id, "ocr_locator", None,
                json.dumps(locator, ensure_ascii=False), evidence_status,
                "OCR 页级定位，不代表语义事实主张；需人工/规则抽取后才可形成 evidence claim",
                0, 0,
            ),
        )
        if not canonical:
            c.execute(
                """INSERT INTO ocr_provenance_flags(provenance_id,flag_type,detail,severity)
                   VALUES (?,?,?,?) ON CONFLICT(provenance_id,flag_type) DO UPDATE SET detail=excluded.detail""",
                (provenance_id, "UNBOUND_CANONICAL_DOCUMENT", source_file, "HOLD"),
            )
        counters["rows"] += 1
        counters["bound"] += int(bool(canonical))
        counters["unbound"] += int(not canonical)
        counters["valid"] += valid
        counters["invalid"] += int(not valid)
        counters["citation_ready"] += citation_ready
        counters["human_verified"] += human_verified

    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(c.execute("PRAGMA foreign_key_check").fetchall())
    counters["ocr_versions"] = c.execute("SELECT count(*) FROM ocr_versions").fetchone()[0]
    counters["evidence_units"] = c.execute("SELECT count(*) FROM evidence_units").fetchone()[0]
    counters["flags"] = c.execute("SELECT count(*) FROM ocr_provenance_flags").fetchone()[0]
    c.close()
    formal_after = sha256(FORMAL_DB)
    report = {
        "migration": "STAGING_OCR_PROVENANCE_20260730",
        "ocr_root": str(OCR_ROOT),
        "counts": dict(counters),
        "integrity_check": integrity,
        "foreign_key_violation_count": fk_count,
        "formal_db_sha_before": formal_before,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_before == formal_after == EXPECTED_FORMAL_SHA,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "evidence_unit_semantics": "locator_only_not_claim",
    }
    out = DB.parent / "OCR_PROVENANCE_MIGRATION_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
