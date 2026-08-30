#!/usr/bin/env python3
"""Register the verified 1943 source-edition OCR pilot in domestic staging.

This is deliberately narrow and idempotent.  It adds one source-edition
container, its source PDF plus two page assets, and two locator-only OCR
provenance rows to the disposable staging database.  It never writes the
formal research database, never marks a row citation-ready, and never changes
the raw PDF, page images, or OCR Markdown.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
FORMAL_DB = ROOT / "data/research_index.sqlite"
OUT = ROOT / "work/domestic/academic_ocr_1943_target_20260730"
PAGE_MAP = OUT / "SOURCE_PAGE_MAP.jsonl"
MANIFEST = OUT / "MANIFEST.jsonl"
SOURCE_PDF = ROOT / "data/domestic/academic_public_20260730/pdf/中国民主同盟历史文献_1941-1949_marxists.pdf"
FORMAL_SHA = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"
SOURCE_SHA = "257bb7be70abe374be9864ec451b5a4a90e2442ae8c877b15f4e6bbb8bb30be3"
CANONICAL = "source-edition:MZHTM-1941-1949"
SOURCE_TITLE = "中国民主同盟历史文献（1941—1949）公开扫描"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    if not DB.is_file():
        raise SystemExit(f"missing staging DB: {DB}")
    if not SOURCE_PDF.is_file():
        raise SystemExit(f"missing source PDF: {SOURCE_PDF}")
    if sha256(FORMAL_DB) != FORMAL_SHA:
        raise SystemExit("formal DB baseline changed before staging registration")
    if sha256(SOURCE_PDF) != SOURCE_SHA:
        raise SystemExit("source PDF SHA does not match the accepted manifest")

    page_rows = read_jsonl(PAGE_MAP)
    if len(page_rows) != 2:
        raise SystemExit(f"expected exactly 2 page-map rows, got {len(page_rows)}")
    manifest_rows = read_jsonl(MANIFEST)
    manifest_by_page = {int(row["pdf_page_no"]): row for row in manifest_rows}

    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("BEGIN")

    existing_doc = c.execute(
        "SELECT id FROM documents WHERE canonical_document_key = ?", (CANONICAL,)
    ).fetchone()
    if existing_doc:
        document_id = int(existing_doc["id"])
    else:
        document_id = int(
            c.execute(
                """INSERT INTO documents
                   (canonical_document_key,title,dominant_phase,phase_counts_json,
                    bucket_counts_json,source_row_count,page_row_count,file_row_count,
                    unique_sha256_count,unique_path_count,evidence_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    CANONICAL,
                    json.dumps([SOURCE_TITLE], ensure_ascii=False),
                    "1941-1949",
                    json.dumps({"1941-1949": 0}, ensure_ascii=False),
                    json.dumps({"domestic_formed_primary_original": 0}, ensure_ascii=False),
                    0,
                    0,
                    0,
                    0,
                    0,
                    "located_public_staging_source_edition",
                ),
            ).lastrowid
        )

    assets = [
        {
            "object_id": "ACADEMIC-PRIMARY-EDITION-MZHTM-1941-1949-PDF",
            "local_path": rel(SOURCE_PDF),
            "page_no": None,
            "sha256": SOURCE_SHA,
            "file_kind": "pdf_original_or_scan",
            "historical_phase": "1941-1949",
            "title": SOURCE_TITLE,
        }
    ]
    for row in page_rows:
        image = ROOT / row["page_image"]
        ocr = ROOT / row["ocr_md"]
        page_manifest = manifest_by_page[int(row["pdf_page_no"])]
        if not image.is_file() or not ocr.is_file():
            raise SystemExit(f"missing derived page files for PDF page {row['pdf_page_no']}")
        if sha256(image) != page_manifest["page_image_sha256"]:
            raise SystemExit(f"page image SHA mismatch for PDF page {row['pdf_page_no']}")
        assets.append(
            {
                "object_id": f"ACADEMIC-PRIMARY-EDITION-MZHTM-1943-P{int(row['pdf_page_no']):04d}",
                "local_path": row["page_image"],
                "page_no": int(row["pdf_page_no"]),
                "sha256": page_manifest["page_image_sha256"],
                "file_kind": "page_image",
                "historical_phase": "1943",
                "title": f"1943 · {row['source_title']}",
            }
        )

    for asset in assets:
        c.execute(
            """INSERT INTO page_assets
               (document_id,object_id,local_path,page_no,sha256,file_kind,
                historical_phase,reclass_bucket,title)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(document_id,local_path) DO UPDATE SET
                 object_id=excluded.object_id, page_no=excluded.page_no,
                 sha256=excluded.sha256, file_kind=excluded.file_kind,
                 historical_phase=excluded.historical_phase,
                 reclass_bucket=excluded.reclass_bucket, title=excluded.title""",
            (
                document_id,
                asset["object_id"],
                asset["local_path"],
                asset["page_no"],
                asset["sha256"],
                asset["file_kind"],
                asset["historical_phase"],
                "domestic_formed_primary_original",
                asset["title"],
            ),
        )

    page_count = c.execute(
        "SELECT count(*) FROM page_assets WHERE document_id = ? AND file_kind = 'page_image'",
        (document_id,),
    ).fetchone()[0]
    file_count = c.execute(
        "SELECT count(*) FROM page_assets WHERE document_id = ? AND file_kind != 'page_image'",
        (document_id,),
    ).fetchone()[0]
    asset_count = c.execute("SELECT count(*) FROM page_assets WHERE document_id = ?", (document_id,)).fetchone()[0]
    unique_sha = c.execute("SELECT count(DISTINCT sha256) FROM page_assets WHERE document_id = ?", (document_id,)).fetchone()[0]
    unique_path = c.execute("SELECT count(DISTINCT local_path) FROM page_assets WHERE document_id = ?", (document_id,)).fetchone()[0]
    phase_counts = {
        str(row[0] or "unknown"): int(row[1])
        for row in c.execute(
            "SELECT historical_phase,count(*) FROM page_assets WHERE document_id = ? GROUP BY historical_phase",
            (document_id,),
        )
    }
    bucket_counts = {
        str(row[0] or "unknown"): int(row[1])
        for row in c.execute(
            "SELECT reclass_bucket,count(*) FROM page_assets WHERE document_id = ? GROUP BY reclass_bucket",
            (document_id,),
        )
    }
    c.execute(
        """UPDATE documents SET title=?, dominant_phase=?, phase_counts_json=?,
           bucket_counts_json=?, source_row_count=?, page_row_count=?, file_row_count=?,
           unique_sha256_count=?, unique_path_count=?, evidence_status=?
           WHERE id=?""",
        (
            json.dumps([SOURCE_TITLE], ensure_ascii=False),
            "1941-1949",
            json.dumps(phase_counts, ensure_ascii=False),
            json.dumps(bucket_counts, ensure_ascii=False),
            asset_count,
            page_count,
            file_count,
            unique_sha,
            unique_path,
            "located_public_staging_source_edition",
            document_id,
        ),
    )

    for row in page_rows:
        pdf_page = int(row["pdf_page_no"])
        manifest = manifest_by_page[pdf_page]
        ocr_path = ROOT / row["ocr_md"]
        provenance_id = f"PROV-ACADEMIC-MZHTM-1943-P{pdf_page:04d}"
        ocr_sha = sha256(ocr_path)
        if manifest.get("ocr_md_sha256") and ocr_sha != manifest["ocr_md_sha256"]:
            raise SystemExit(f"OCR Markdown SHA mismatch for PDF page {pdf_page}")
        values = (
            provenance_id,
            CANONICAL,
            row["source_id"],
            rel(SOURCE_PDF),
            SOURCE_SHA,
            SOURCE_PDF.stat().st_size,
            row["source_title"],
            int(row["book_page_no"]),
            pdf_page,
            str(row["book_page_no"]),
            row["page_image"],
            manifest["page_image_sha256"],
            row["ocr_md"],
            ocr_sha,
            int(manifest["line_count"]),
            float(row["ocr_mean_confidence"]),
            "PaddleOCR 3.7.0",
            "PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
            "REAL_PAGE_BY_PAGE",
            "MACHINE_OCR_COMPLETE",
            "NOT_REVIEWED",
            1,
            0,
            0,
            1943,
            "1943",
            "1943",
            "中国民主同盟历史文献（1941—1949）",
            "MZHTM-1943-ZHANG-LAN-LETTER-P016-P017",
            "source_edition_staging_review_required",
            "PRIMARY_SOURCE_PAGE_REVIEW_REQUIRED",
            "BOUND_CANONICAL",
            rel(PAGE_MAP),
            page_rows.index(row) + 1,
        )
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
                 canonical_document_key=excluded.canonical_document_key, source_id=excluded.source_id,
                 source_file=excluded.source_file, source_sha256=excluded.source_sha256,
                 source_file_size=excluded.source_file_size, source_title=excluded.source_title,
                 physical_page_no=excluded.physical_page_no, pdf_page_no=excluded.pdf_page_no,
                 printed_page=excluded.printed_page, page_image_path=excluded.page_image_path,
                 page_image_sha256=excluded.page_image_sha256, ocr_md_path=excluded.ocr_md_path,
                 ocr_md_sha256=excluded.ocr_md_sha256, ocr_lines=excluded.ocr_lines,
                 ocr_confidence=excluded.ocr_confidence, ocr_engine=excluded.ocr_engine,
                 ocr_model=excluded.ocr_model, ocr_mode=excluded.ocr_mode,
                 text_structure_status=excluded.text_structure_status,
                 machine_visual_status=excluded.machine_visual_status, valid=excluded.valid,
                 citation_ready=0, human_verified=0, year=excluded.year, period=excluded.period,
                 issue_date=excluded.issue_date, edition=excluded.edition, mapping_id=excluded.mapping_id,
                 rights_status=excluded.rights_status, relation_required=excluded.relation_required,
                 binding_status=excluded.binding_status, manifest_path=excluded.manifest_path,
                 manifest_line=excluded.manifest_line""",
            values,
        )
        c.execute(
            """INSERT INTO evidence_units
               (unit_id,canonical_document_key,ocr_provenance_id,unit_type,claim_text,
                locator_json,evidence_status,uncertainty_note,citation_ready,human_verified)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(ocr_provenance_id) DO UPDATE SET
                 canonical_document_key=excluded.canonical_document_key,
                 locator_json=excluded.locator_json, evidence_status=excluded.evidence_status,
                 uncertainty_note=excluded.uncertainty_note, citation_ready=0, human_verified=0""",
            (
                f"OCRLOC-{provenance_id}",
                CANONICAL,
                provenance_id,
                "ocr_locator",
                None,
                json.dumps(
                    {
                        "physical_page_no": int(row["book_page_no"]),
                        "pdf_page_no": pdf_page,
                        "printed_page": str(row["book_page_no"]),
                        "page_image_path": row["page_image"],
                        "ocr_md_path": row["ocr_md"],
                        "ocr_md_sha256": ocr_sha,
                    },
                    ensure_ascii=False,
                ),
                "machine_locator_only",
                "OCR 页级定位，不代表语义事实主张；需复核后才可形成 citation-ready 证据",
                0,
                0,
            ),
        )

    c.execute("INSERT INTO document_search(document_search) VALUES ('rebuild')")
    c.execute("INSERT INTO page_search(page_search) VALUES ('rebuild')")
    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(c.execute("PRAGMA foreign_key_check").fetchall())
    counts = {
        "source_edition_documents": c.execute(
            "SELECT count(*) FROM documents WHERE canonical_document_key = ?", (CANONICAL,)
        ).fetchone()[0],
        "source_edition_assets": c.execute(
            "SELECT count(*) FROM page_assets WHERE document_id = ?", (document_id,)
        ).fetchone()[0],
        "source_edition_ocr": c.execute(
            "SELECT count(*) FROM ocr_versions WHERE canonical_document_key = ?", (CANONICAL,)
        ).fetchone()[0],
        "source_edition_locators": c.execute(
            "SELECT count(*) FROM evidence_units WHERE canonical_document_key = ?", (CANONICAL,)
        ).fetchone()[0],
        "citation_ready": c.execute(
            "SELECT count(*) FROM ocr_versions WHERE canonical_document_key = ? AND citation_ready=1", (CANONICAL,)
        ).fetchone()[0],
        "human_verified": c.execute(
            "SELECT count(*) FROM ocr_versions WHERE canonical_document_key = ? AND human_verified=1", (CANONICAL,)
        ).fetchone()[0],
    }
    c.close()
    formal_after = sha256(FORMAL_DB)
    report = {
        "report": "REGISTER_1943_SOURCE_EDITION_STAGING_20260730",
        "canonical_document_key": CANONICAL,
        "source_pdf": rel(SOURCE_PDF),
        "source_pdf_sha256": SOURCE_SHA,
        "counts": counts,
        "staging_integrity": integrity,
        "foreign_key_violation_count": fk_count,
        "formal_db_sha_before": FORMAL_SHA,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_after == FORMAL_SHA,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "raw_files_modified": False,
        "scope": "staging_only_idempotent_source_edition_registration",
    }
    (OUT / "STAGING_REGISTRATION_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
