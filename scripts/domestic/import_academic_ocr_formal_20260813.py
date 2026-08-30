#!/usr/bin/env python3
"""Import one verified scanned scholarly PDF into the formal search index.

This is the OCR counterpart to ``import_academic_pdf_formal_20260813.py``.
It is intentionally narrow: one S/A staging record, one exact local PDF,
and one complete page-level PaddleOCR manifest.  The imported pages remain
``review_only`` with ``citation_ready=0``; OCR never becomes a formal citation
without a later human page review.  The PDF and its derived assets are never
copied, moved, deleted, or overwritten.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from import_academic_pdf_formal_20260813 import (
    bigramize,
    formal_sha,
    parse_metadata,
    resolve_source,
    sha256_file,
    stable_source_path,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FORMAL_DB = ROOT / "data/research_index.sqlite"
DEFAULT_EXTERNAL_ID = "GAR-9EAACC89D5"
DEFAULT_OCR_DIR = ROOT / "work/domestic/academic_ocr_sinica_batch_20260813"
BATCH_ID = "academic-ocr-formal-20260813"
TIERS = {"S", "A"}


def artifact_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def ocr_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    marker = "## 识别文本"
    if marker not in raw:
        raise ValueError(f"OCR marker missing: {path}")
    text = raw.split(marker, 1)[1]
    text = re.sub(r"\n?-{3,}\s*$", "", text, flags=re.MULTILINE).strip()
    if not text or text == "未识别出文字。":
        raise ValueError(f"OCR text is empty: {path}")
    return text


def read_staging_record(staging_db: Path, source_root: Path, external_id: str) -> dict[str, Any]:
    if not staging_db.is_file():
        raise ValueError(f"staging database missing: {staging_db}")
    with sqlite3.connect(f"file:{staging_db}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT external_id,title,author,institution,publication_date,
                   research_type,quality_tier,source_url,local_path,sha256,
                   fulltext_status,review_status,metadata_json
            FROM domestic_research_materials
            WHERE external_id=?
            """,
            (external_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"staging record not found: {external_id}")
    record = dict(row)
    if record.get("quality_tier") not in TIERS:
        raise ValueError(f"record is not S/A quality: {external_id}")
    if record.get("fulltext_status") != "FULLTEXT_PDF":
        raise ValueError(f"record is not a FULLTEXT_PDF candidate: {external_id}")
    source = resolve_source(str(record.get("local_path") or ""), source_root)
    if not source.is_file():
        raise ValueError(f"source PDF missing: {source}")
    actual_sha = sha256_file(source)
    expected_sha = str(record.get("sha256") or "").lower()
    if len(expected_sha) != 64 or actual_sha != expected_sha:
        raise ValueError(f"source PDF SHA mismatch: expected={expected_sha} actual={actual_sha}")
    record["resolved_source"] = str(source)
    record["stable_source"] = stable_source_path(source, source_root)
    record["sha256_actual"] = actual_sha
    record["metadata"] = parse_metadata(str(record.get("metadata_json") or "{}"))
    return record


def read_ocr_manifest(ocr_dir: Path, source_sha: str, expected_pages: int = 29) -> list[dict[str, Any]]:
    manifest_path = ocr_dir / "MANIFEST.jsonl"
    report_path = ocr_dir / "REPORT.json"
    if not manifest_path.is_file() or not report_path.is_file():
        raise ValueError(f"OCR manifest/report missing under {ocr_dir}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("source_pdf_sha256") != source_sha:
        raise ValueError("OCR report source PDF SHA does not match staging record")
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    page_numbers = [int(row["pdf_page_no"]) for row in rows]
    if len(rows) != expected_pages or page_numbers != list(range(1, expected_pages + 1)):
        raise ValueError(f"OCR manifest must contain ordered pages 1..{expected_pages}, got {page_numbers}")

    prepared = []
    for line_no, row in enumerate(rows, start=1):
        image = artifact_path(str(row["page_image"]))
        ocr = artifact_path(str(row["ocr_md"]))
        if not image.is_file() or not ocr.is_file():
            raise ValueError(f"missing OCR derivative for page {row['pdf_page_no']}")
        image_sha = sha256_file(image)
        if image_sha != row.get("page_image_sha256"):
            raise ValueError(f"page image SHA mismatch for page {row['pdf_page_no']}")
        text = ocr_text(ocr)
        line_count = int(row.get("line_count") or 0)
        confidence = float(row.get("mean_confidence") or 0.0)
        if line_count <= 0 or confidence <= 0:
            raise ValueError(f"invalid OCR quality fields for page {row['pdf_page_no']}")
        prepared.append(
            {
                "line_no": line_no,
                "pdf_page_no": int(row["pdf_page_no"]),
                "image": image,
                "ocr": ocr,
                "image_sha": image_sha,
                "ocr_sha": sha256_file(ocr),
                "text": text,
                "line_count": line_count,
                "confidence": confidence,
            }
        )
    return prepared


def tags_for(record: dict[str, Any]) -> str:
    metadata = record["metadata"]
    events = metadata.get("events") if isinstance(metadata.get("events"), list) else []
    periods = metadata.get("historical_periods") if isinstance(metadata.get("historical_periods"), list) else []
    tags = [
        "academic_layer=scholarly_research",
        "evidence_role=secondary_interpretation",
        "source_kind=local_verified_scanned_pdf",
        "citation_ready=false",
        "needs_human_review=true",
        f"quality_tier={record.get('quality_tier') or 'unset'}",
        f"research_type={record.get('research_type') or 'unset'}",
        f"batch={BATCH_ID}",
    ]
    tags.extend(f"event={value}" for value in events[:8])
    tags.extend(f"period={value}" for value in periods[:8])
    return ",".join(tags)


def prepare(db_path: Path, record: dict[str, Any], pages: list[dict[str, Any]]) -> dict[str, Any]:
    doc_key = f"domestic-academic/{record['external_id']}"
    with sqlite3.connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id, count_pages FROM (SELECT d.id, count(p.id) AS count_pages FROM documents d LEFT JOIN pages p ON p.document_id=d.id WHERE d.doc_key=? GROUP BY d.id)",
            (doc_key,),
        ).fetchone()
    return {
        "db_path": str(db_path),
        "formal_db_sha256": formal_sha(db_path),
        "external_id": record["external_id"],
        "title": record["title"],
        "quality_tier": record["quality_tier"],
        "research_type": record["research_type"],
        "source_file": record["stable_source"],
        "source_sha256": record["sha256_actual"],
        "doc_key": doc_key,
        "ocr_page_count": len(pages),
        "ocr_text_chars": sum(len(row["text"]) for row in pages),
        "ocr_min_confidence": min(row["confidence"] for row in pages),
        "ocr_max_confidence": max(row["confidence"] for row in pages),
        "existing_document_id": int(existing[0]) if existing else None,
        "existing_page_count": int(existing[1]) if existing else 0,
        "citation_ready": False,
        "review_status": "review_only",
    }


def apply_import(db_path: Path, record: dict[str, Any], pages: list[dict[str, Any]], backup: Path) -> dict[str, Any]:
    actual_db = db_path.resolve()
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc_key = f"domestic-academic/{record['external_id']}"
    source_key = f"domestic-academic-pdf:{record['external_id']}"
    tags = tags_for(record)
    metadata = record["metadata"]
    periods = metadata.get("historical_periods") if isinstance(metadata.get("historical_periods"), list) else []
    publication = str(record.get("publication_date") or "")
    year_match = re.search(r"(?:19|20)\d{2}", publication)
    date_guess = publication if year_match else ""
    imported_pages = []

    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        if conn.execute("SELECT 1 FROM documents WHERE doc_key=?", (doc_key,)).fetchone():
            return {
                "imported_records": 0,
                "imported_pages": 0,
                "already_present": True,
                "integrity_check": conn.execute("PRAGMA integrity_check").fetchone()[0],
                "foreign_key_violations": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
                "backup": str(backup),
            }
        conn.execute(
            """
            INSERT INTO sources(source_type,source_id,title,origin_url,local_path)
            VALUES(?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
              title=excluded.title, origin_url=excluded.origin_url, local_path=excluded.local_path
            """,
            ("domestic_academic_fulltext", source_key, record["title"], record.get("source_url"), record["stable_source"]),
        )
        source_id = conn.execute("SELECT id FROM sources WHERE source_id=?", (source_key,)).fetchone()[0]
        document_id = conn.execute(
            """
            INSERT INTO documents(source_id,doc_key,volume_id,volume_title,doc_id,title,date_guess,url,local_txt,hit_type,matched_terms,source_platform)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                source_id,
                doc_key,
                "DOMESTIC-ACADEMIC",
                "国内学术研究资料",
                record["external_id"],
                record["title"],
                date_guess,
                record.get("source_url"),
                record["stable_source"],
                "domestic_academic_fulltext",
                tags,
                "domestic",
            ),
        ).lastrowid

        for item in pages:
            page_no = item["pdf_page_no"]
            page_url = (record.get("source_url") or f"file://{record['stable_source']}") + f"#page={page_no}"
            page_id = conn.execute(
                "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                (document_id, str(page_no), page_url, item["text"]),
            ).lastrowid
            conn.execute(
                "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-ACADEMIC", record["external_id"], record["title"], str(page_no), tags, item["text"]),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-ACADEMIC", record["external_id"], record["title"], str(page_no), tags, bigramize(item["text"])),
            )
            conn.execute(
                """
                INSERT INTO page_provenance(
                    page_id,document_id,source_id,source_file,source_sha256,source_file_size,
                    pdf_page_no,physical_page_no,page_image_path,page_image_sha256,ocr_md_path,ocr_md_sha256,
                    ocr_engine,ocr_model,ocr_mode,ocr_lines,ocr_mean_confidence,text_chars,
                    citation_ready,needs_human_review,review_status,machine_review_note,
                    period,year,event_tags,source_title,batch_id,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    page_id,
                    document_id,
                    source_key,
                    record["stable_source"],
                    record["sha256_actual"],
                    Path(record["resolved_source"]).stat().st_size,
                    page_no,
                    page_no,
                    str(item["image"].relative_to(ROOT)),
                    item["image_sha"],
                    str(item["ocr"].relative_to(ROOT)),
                    item["ocr_sha"],
                    "PaddleOCR 3.7.0",
                    "PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
                    "scan_pdf_paddleocr",
                    item["line_count"],
                    item["confidence"],
                    len(item["text"]),
                    0,
                    1,
                    "review_only",
                    "学术扫描 PDF 已按物理页由本地 PaddleOCR 导入检索库；这是解释层机器识别草稿，未完成视觉/文字人工复核，不可直接作为正式引文。",
                    "；".join(str(value) for value in periods[:8]),
                    int(year_match.group(0)) if year_match else None,
                    tags,
                    record["title"],
                    BATCH_ID,
                    now,
                    now,
                ),
            )
            imported_pages.append({"page_id": page_id, "pdf_page_no": page_no, "text_chars": len(item["text"])})
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        counts = {
            "pages": conn.execute("SELECT count(*) FROM pages WHERE document_id=?", (document_id,)).fetchone()[0],
            "provenance": conn.execute("SELECT count(*) FROM page_provenance WHERE document_id=?", (document_id,)).fetchone()[0],
            "citation_ready": conn.execute("SELECT count(*) FROM page_provenance WHERE document_id=? AND citation_ready=1", (document_id,)).fetchone()[0],
            "human_verified": conn.execute("SELECT count(*) FROM page_provenance WHERE document_id=? AND review_status='human_verified'", (document_id,)).fetchone()[0],
        }
        total_pages = conn.execute("SELECT count(*) FROM pages").fetchone()[0]
        total_fts = conn.execute("SELECT count(*) FROM page_fts").fetchone()[0]
        total_bigram = conn.execute("SELECT count(*) FROM page_fts_bigram").fetchone()[0]
    return {
        "imported_records": 1,
        "imported_pages": len(imported_pages),
        "document_id": document_id,
        "pages": counts["pages"],
        "provenance": counts["provenance"],
        "citation_ready": counts["citation_ready"],
        "human_verified": counts["human_verified"],
        "integrity_check": integrity,
        "foreign_key_violations": foreign_keys,
        "total_pages": total_pages,
        "total_page_fts": total_fts,
        "total_page_fts_bigram": total_bigram,
        "backup": str(backup),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-db", type=Path, default=DEFAULT_FORMAL_DB)
    parser.add_argument("--staging-db", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--ocr-dir", type=Path, default=DEFAULT_OCR_DIR)
    parser.add_argument("--external-id", default=DEFAULT_EXTERNAL_ID)
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    db = args.formal_db.expanduser().resolve()
    staging = args.staging_db.expanduser().resolve()
    source_root = args.source_root.expanduser().resolve()
    ocr_dir = args.ocr_dir.expanduser().resolve()
    record = read_staging_record(staging, source_root, args.external_id)
    pages = read_ocr_manifest(ocr_dir, record["sha256_actual"])
    prepared = prepare(db, record, pages)
    report = {
        "batch_id": BATCH_ID,
        "mode": "apply" if args.apply else "dry_run",
        "staging_db": str(staging),
        "source_root": str(source_root),
        "ocr_dir": str(ocr_dir),
        "body_read": True,
        "source_files_copied": False,
        "gate": "PASS",
        **prepared,
    }
    if args.apply:
        if prepared["existing_document_id"] is not None:
            raise SystemExit("formal document already exists; refuse to duplicate or overwrite it")
        if not args.expected_db_sha or prepared["formal_db_sha256"] != args.expected_db_sha:
            raise SystemExit("--apply requires --expected-db-sha matching the current formal DB")
        if not args.backup:
            raise SystemExit("--apply requires --backup outside the repository")
        result = apply_import(db, record, pages, args.backup.expanduser().resolve())
        report["apply_result"] = result
        report["formal_db_sha256_after"] = formal_sha(db)
        report["gate"] = "PASS" if result["integrity_check"] == "ok" and result["foreign_key_violations"] == 0 else "FAIL"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
