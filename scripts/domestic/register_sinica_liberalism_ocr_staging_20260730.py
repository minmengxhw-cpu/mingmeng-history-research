#!/usr/bin/env python3
"""Register the bounded Sinica academic OCR batch in domestic staging.

The source PDF and derived page/OCR files remain unchanged.  This script only
adds an idempotent scholarly-fulltext object, page assets, OCR provenance and
locator units to the disposable domestic staging database.  It never writes
the formal database and never promotes OCR to citation-ready.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
FORMAL_DB = ROOT / "data/research_index.sqlite"
SOURCE_PDF = ROOT / "data/domestic/academic_public_20260730/pdf/bulk2_59a819121b70.pdf"
OCR_DIR = ROOT / "work/domestic/academic_ocr_sinica_batch_20260730"
MANIFEST = OCR_DIR / "MANIFEST.jsonl"
OUT = ROOT / "work/domestic/academic_ocr_sinica_batch_20260730"

FORMAL_SHA = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"
SOURCE_SHA = "a97bdf981bbbfac4504a69ecf1ad879cdbb4c9698805d02261f573f0f57ffcf0"
CANONICAL = "scholarly:sinica:chen-yishen-liberalism-1941-1949"
SOURCE_ID = "GAR-9EAACC89D5"
TITLE = "《国共斗争下的自由主义（1941—1949）》"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def printed_page(ocr_path: Path) -> tuple[str | None, str]:
    text = ocr_path.read_text(encoding="utf-8")
    match = re.search(r"(?:^|\n)\s*[-—]\s*(\d{1,4})\s*[-—]\s*$", text, re.MULTILINE)
    if match:
        return match.group(1), "OCR_FOOTER_PATTERN"
    return None, "UNKNOWN_PRINTED_PAGE"


def main() -> int:
    if sha256(FORMAL_DB) != FORMAL_SHA:
        raise SystemExit("formal DB baseline changed before Sinica staging registration")
    if sha256(SOURCE_PDF) != SOURCE_SHA:
        raise SystemExit("Sinica source PDF SHA mismatch")
    rows = read_jsonl(MANIFEST)
    if len(rows) != 29:
        raise SystemExit(f"expected 29 OCR manifest rows, got {len(rows)}")

    prepared = []
    for line_no, row in enumerate(rows, start=1):
        pdf_page = int(row["pdf_page_no"])
        image = ROOT / row["page_image"]
        ocr = ROOT / row["ocr_md"]
        if not image.is_file() or not ocr.is_file():
            raise SystemExit(f"missing OCR derivative for PDF page {pdf_page}")
        image_sha = sha256(image)
        ocr_sha = sha256(ocr)
        if image_sha != row["page_image_sha256"]:
            raise SystemExit(f"page image SHA mismatch for PDF page {pdf_page}")
        printed, printed_status = printed_page(ocr)
        prepared.append({
            "line_no": line_no,
            "pdf_page": pdf_page,
            "image": image,
            "ocr": ocr,
            "image_sha": image_sha,
            "ocr_sha": ocr_sha,
            "printed_page": printed,
            "printed_page_status": printed_status,
            "line_count": int(row["line_count"]),
            "confidence": float(row["mean_confidence"]),
        })

    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("BEGIN")
    existing = c.execute("SELECT id FROM documents WHERE canonical_document_key=?", (CANONICAL,)).fetchone()
    if existing:
        document_id = int(existing["id"])
    else:
        document_id = int(c.execute(
            """INSERT INTO documents
               (canonical_document_key,title,dominant_phase,phase_counts_json,bucket_counts_json,
                source_row_count,page_row_count,file_row_count,unique_sha256_count,unique_path_count,evidence_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (CANONICAL, json.dumps([TITLE], ensure_ascii=False), "1941-1949",
             json.dumps({"1941-1949": 0}, ensure_ascii=False),
             json.dumps({"scholarly_secondary_fulltext": 0}, ensure_ascii=False),
             0, 0, 0, 0, 0, "scholarly_fulltext_staging"),
        ).lastrowid)

    assets = [{
        "object_id": f"SCHOLARLY-FULLTEXT-{SOURCE_ID}-PDF",
        "path": rel(SOURCE_PDF),
        "page_no": None,
        "sha": SOURCE_SHA,
        "kind": "pdf_research_fulltext",
        "title": TITLE,
    }]
    for item in prepared:
        assets.append({
            "object_id": f"SCHOLARLY-FULLTEXT-{SOURCE_ID}-P{item['pdf_page']:04d}",
            "path": rel(item["image"]),
            "page_no": item["pdf_page"],
            "sha": item["image_sha"],
            "kind": "page_image",
            "title": f"{TITLE} · PDF 页 {item['pdf_page']:04d}",
        })

    for asset in assets:
        c.execute(
            """INSERT INTO page_assets
               (document_id,object_id,local_path,page_no,sha256,file_kind,historical_phase,reclass_bucket,title)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(document_id,local_path) DO UPDATE SET
                 object_id=excluded.object_id,page_no=excluded.page_no,sha256=excluded.sha256,
                 file_kind=excluded.file_kind,historical_phase=excluded.historical_phase,
                 reclass_bucket=excluded.reclass_bucket,title=excluded.title""",
            (document_id, asset["object_id"], asset["path"], asset["page_no"], asset["sha"],
             asset["kind"], "1941-1949", "scholarly_secondary_fulltext", asset["title"]),
        )

    page_count = c.execute("SELECT count(*) FROM page_assets WHERE document_id=? AND file_kind='page_image'", (document_id,)).fetchone()[0]
    file_count = c.execute("SELECT count(*) FROM page_assets WHERE document_id=? AND file_kind!='page_image'", (document_id,)).fetchone()[0]
    asset_count = c.execute("SELECT count(*) FROM page_assets WHERE document_id=?", (document_id,)).fetchone()[0]
    unique_sha = c.execute("SELECT count(DISTINCT sha256) FROM page_assets WHERE document_id=?", (document_id,)).fetchone()[0]
    unique_path = c.execute("SELECT count(DISTINCT local_path) FROM page_assets WHERE document_id=?", (document_id,)).fetchone()[0]
    phase_counts = {str(row[0] or "unknown"): int(row[1]) for row in c.execute(
        "SELECT historical_phase,count(*) FROM page_assets WHERE document_id=? GROUP BY historical_phase", (document_id,)
    )}
    bucket_counts = {str(row[0] or "unknown"): int(row[1]) for row in c.execute(
        "SELECT reclass_bucket,count(*) FROM page_assets WHERE document_id=? GROUP BY reclass_bucket", (document_id,)
    )}
    c.execute(
        """UPDATE documents SET title=?,dominant_phase=?,phase_counts_json=?,bucket_counts_json=?,
           source_row_count=?,page_row_count=?,file_row_count=?,unique_sha256_count=?,unique_path_count=?,evidence_status=?
           WHERE id=?""",
        (json.dumps([TITLE], ensure_ascii=False), "1941-1949", json.dumps(phase_counts, ensure_ascii=False),
         json.dumps(bucket_counts, ensure_ascii=False), asset_count, page_count, file_count, unique_sha, unique_path,
         "scholarly_fulltext_staging", document_id),
    )

    for item in prepared:
        pdf_page = item["pdf_page"]
        provenance_id = f"PROV-SINICA-LIBERALISM-1941-1949-P{pdf_page:04d}"
        c.execute(
            """INSERT INTO ocr_versions
               (provenance_id,canonical_document_key,source_id,source_file,source_sha256,source_file_size,source_title,
                physical_page_no,pdf_page_no,printed_page,page_image_path,page_image_sha256,ocr_md_path,ocr_md_sha256,
                ocr_lines,ocr_confidence,ocr_engine,ocr_model,ocr_mode,text_structure_status,machine_visual_status,
                valid,citation_ready,human_verified,year,period,issue_date,edition,mapping_id,rights_status,relation_required,
                binding_status,manifest_path,manifest_line)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(provenance_id) DO UPDATE SET
                 canonical_document_key=excluded.canonical_document_key,source_id=excluded.source_id,
                 source_file=excluded.source_file,source_sha256=excluded.source_sha256,source_file_size=excluded.source_file_size,
                 source_title=excluded.source_title,physical_page_no=excluded.physical_page_no,pdf_page_no=excluded.pdf_page_no,
                 printed_page=excluded.printed_page,page_image_path=excluded.page_image_path,page_image_sha256=excluded.page_image_sha256,
                 ocr_md_path=excluded.ocr_md_path,ocr_md_sha256=excluded.ocr_md_sha256,ocr_lines=excluded.ocr_lines,
                 ocr_confidence=excluded.ocr_confidence,ocr_engine=excluded.ocr_engine,ocr_model=excluded.ocr_model,
                 ocr_mode=excluded.ocr_mode,text_structure_status=excluded.text_structure_status,
                 machine_visual_status=excluded.machine_visual_status,valid=excluded.valid,citation_ready=0,human_verified=0,
                 year=excluded.year,period=excluded.period,issue_date=excluded.issue_date,edition=excluded.edition,
                 mapping_id=excluded.mapping_id,rights_status=excluded.rights_status,relation_required=excluded.relation_required,
                 binding_status=excluded.binding_status,manifest_path=excluded.manifest_path,manifest_line=excluded.manifest_line""",
            (provenance_id, CANONICAL, SOURCE_ID, rel(SOURCE_PDF), SOURCE_SHA, SOURCE_PDF.stat().st_size, TITLE,
             pdf_page, pdf_page, item["printed_page"], rel(item["image"]), item["image_sha"], rel(item["ocr"]), item["ocr_sha"],
             item["line_count"], item["confidence"], "PaddleOCR 3.7.0", "PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
             "REAL_PAGE_BY_PAGE", "MACHINE_OCR_COMPLETE", "NOT_REVIEWED", 1, 0, 0, None, "1941-1949", None,
             "Sinica academic fulltext OCR", "SINICA-LIBERALISM-P001-P029", "PUBLIC_SOURCE_REVIEW_REQUIRED",
             "SCHOLARLY_RESEARCH_NOT_PRIMARY", "BOUND_CANONICAL", rel(MANIFEST), item["line_no"]),
        )
        c.execute(
            """INSERT INTO evidence_units
               (unit_id,canonical_document_key,ocr_provenance_id,unit_type,claim_text,locator_json,evidence_status,
                uncertainty_note,citation_ready,human_verified)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(ocr_provenance_id) DO UPDATE SET
                 canonical_document_key=excluded.canonical_document_key,locator_json=excluded.locator_json,
                 evidence_status=excluded.evidence_status,uncertainty_note=excluded.uncertainty_note,
                 citation_ready=0,human_verified=0""",
            (f"OCRLOC-{provenance_id}", CANONICAL, provenance_id, "ocr_locator", None,
             json.dumps({"pdf_page_no": pdf_page, "printed_page": item["printed_page"],
                         "printed_page_status": item["printed_page_status"], "page_image_path": rel(item["image"]),
                         "ocr_md_path": rel(item["ocr"]), "ocr_md_sha256": item["ocr_sha"]}, ensure_ascii=False),
             "scholarly_fulltext_machine_locator", "学术研究正文 OCR 定位；不构成同期一手事实主张，需复核后才可引用", 0, 0),
        )

    c.execute("INSERT INTO document_search(document_search) VALUES ('rebuild')")
    c.execute("INSERT INTO page_search(page_search) VALUES ('rebuild')")
    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = len(c.execute("PRAGMA foreign_key_check").fetchall())
    counts = {
        "documents": c.execute("SELECT count(*) FROM documents WHERE canonical_document_key=?", (CANONICAL,)).fetchone()[0],
        "assets": c.execute("SELECT count(*) FROM page_assets WHERE document_id=?", (document_id,)).fetchone()[0],
        "ocr_versions": c.execute("SELECT count(*) FROM ocr_versions WHERE canonical_document_key=?", (CANONICAL,)).fetchone()[0],
        "locator_units": c.execute("SELECT count(*) FROM evidence_units WHERE canonical_document_key=?", (CANONICAL,)).fetchone()[0],
        "citation_ready": c.execute("SELECT count(*) FROM ocr_versions WHERE canonical_document_key=? AND citation_ready=1", (CANONICAL,)).fetchone()[0],
        "human_verified": c.execute("SELECT count(*) FROM ocr_versions WHERE canonical_document_key=? AND human_verified=1", (CANONICAL,)).fetchone()[0],
    }
    c.close()
    report = {
        "report": "REGISTER_SINICA_LIBERALISM_OCR_STAGING_20260730",
        "canonical_document_key": CANONICAL,
        "source_id": SOURCE_ID,
        "source_pdf": rel(SOURCE_PDF),
        "source_pdf_sha256": SOURCE_SHA,
        "registered_pages": len(prepared),
        "printed_page_status_counts": {
            status: sum(item["printed_page_status"] == status for item in prepared)
            for status in sorted({item["printed_page_status"] for item in prepared})
        },
        "mean_confidence": round(sum(item["confidence"] for item in prepared) / len(prepared), 6),
        "min_confidence": min(item["confidence"] for item in prepared),
        "counts": counts,
        "staging_integrity": integrity,
        "foreign_key_violation_count": foreign_keys,
        "formal_db_sha_before": FORMAL_SHA,
        "formal_db_sha_after": sha256(FORMAL_DB),
        "formal_db_unchanged": sha256(FORMAL_DB) == FORMAL_SHA,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "raw_files_modified": False,
        "scope": "staging_only_scholarly_fulltext_ocr_registration",
    }
    (OUT / "STAGING_REGISTRATION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
