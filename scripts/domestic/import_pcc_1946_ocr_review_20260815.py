#!/usr/bin/env python3
"""Import the 1946 PCC sourcebook OCR pilot as local ``review_only`` pages.

This importer is deliberately narrower than a citation importer.  It binds
the nine visually identified pages to the exact source PDF, page images and
PaddleOCR drafts so the domestic search index can find them.  The source is an
L2 compilation/reprint, therefore every imported page remains
``citation_ready=0``, ``needs_human_review=1`` and ``review_status=review_only``.

The formal SQLite file is external research data.  ``--apply`` requires the
caller to provide its current SHA256 and an explicit backup path; no source or
derived asset is copied, moved, deleted or overwritten by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
SOURCE_REL = "data/domestic/sourcebooks/NLC416-01jh004019-12949_政協文獻_1946.pdf"
SOURCE_SHA = "4b45976ffdea727f0e26f79c4cb2688e01093d5d7901103c17d99823e7e4d50f"
SOURCE_URL = "https://upload.wikimedia.org/wikipedia/commons/e/e6/NLC416-01jh004019-12949_%E6%94%BF%E5%8D%8F%E6%96%87%E7%8D%BB_1946.pdf"
SOURCE_ID = "nlc-pcc-1946-sourcebook-target-pages-ocr"
DOC_KEY = "domestic-ocr/NLC:pcc-1946-sourcebook-target-pages-ocr"
BATCH_ID = "pcc-1946-sourcebook-page-ocr-20260815"
SOURCE_TITLE = "政协文献（1946）·旧政协民盟相关定向页 OCR 检索草稿"

PAGE_META = {
    23: {"printed_page": "16", "label": "pdf-023 / printed-016 / 张澜开会词"},
    24: {"printed_page": None, "label": "pdf-024 / adjacent-continuation"},
    52: {"printed_page": "45", "label": "pdf-052 / printed-045 / 张君劢闭会词"},
    62: {"printed_page": "55", "label": "pdf-062 / printed-055 / 罗隆基报告民主同盟意见"},
    63: {"printed_page": None, "label": "pdf-063 / adjacent-continuation"},
    101: {"printed_page": "94", "label": "pdf-101 / printed-094 / 民主同盟的提案"},
    125: {"printed_page": "116", "label": "pdf-125 / printed-116 / 章伯钧说明民主同盟的意见"},
    126: {"printed_page": None, "label": "pdf-126 / adjacent-continuation"},
    206: {"printed_page": "197", "label": "pdf-206 / printed-197 / 张澜三月二十一日谈话"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def db_sha256(path: Path) -> str:
    return sha256(path.resolve())


def resolve(value: str, root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def ocr_text_and_quality(path: Path) -> tuple[str, int, float]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    marker = "## 识别文本"
    if marker not in raw:
        raise ValueError(f"OCR marker missing: {path}")
    text = raw.split(marker, 1)[1]
    if "## 明细" in text:
        text = text.split("## 明细", 1)[0]
    text = text.strip()
    if not text or text == "未识别出文字。":
        raise ValueError(f"OCR text is empty: {path}")
    scores = [
        float(value)
        for value in re.findall(r"\|\s*\d+\s*\|.*?\|\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*\|", raw)
    ]
    if not scores:
        raise ValueError(f"OCR confidence table missing: {path}")
    return text, len(scores), sum(scores) / len(scores)


def read_manifest(root: Path, manifest_path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != 1:
        raise ValueError(f"expected one nine-page pilot record, got {len(rows)}")
    record = rows[0]
    if record.get("record_id") != "NLC-PCC-1946-TARGET-PAGES-OCR-20260815":
        raise ValueError("unexpected pilot record id")
    source = resolve(str(record.get("source_path") or ""), root)
    if not source.is_file() or sha256(source) != SOURCE_SHA:
        raise ValueError(f"source PDF SHA gate failed: {source}")
    pages = record.get("pages")
    if not isinstance(pages, list) or len(pages) != 9:
        raise ValueError("pilot manifest must contain nine pages")
    prepared: list[dict[str, Any]] = []
    seen: set[int] = set()
    for page in pages:
        label = str(page.get("page_label") or "")
        match = re.search(r"pdf-(\d{3})", label)
        if not match:
            raise ValueError(f"missing PDF page in label: {label}")
        pdf_page = int(match.group(1))
        if pdf_page in seen or pdf_page not in PAGE_META:
            raise ValueError(f"unexpected or duplicate PDF page: {pdf_page}")
        seen.add(pdf_page)
        image = resolve(str(page.get("page_image") or f"work/domestic/pcc_1946_sourcebook_render_20260814/pdf-{pdf_page:03d}-r270.png"), root)
        ocr = resolve(str(page.get("ocr_markdown") or ""), root)
        if not image.is_file() or not ocr.is_file():
            raise ValueError(f"missing image/OCR derivative for PDF page {pdf_page}")
        text, lines, confidence = ocr_text_and_quality(ocr)
        prepared.append(
            {
                "pdf_page": pdf_page,
                "printed_page": PAGE_META[pdf_page]["printed_page"],
                "label": PAGE_META[pdf_page]["label"],
                "image": image,
                "image_sha": sha256(image),
                "ocr": ocr,
                "ocr_sha": sha256(ocr),
                "text": text,
                "ocr_lines": lines,
                "ocr_confidence": confidence,
            }
        )
    prepared.sort(key=lambda row: row["pdf_page"])
    if [row["pdf_page"] for row in prepared] != sorted(PAGE_META):
        raise ValueError("pilot pages do not match the nine registered targets")
    return [{"source": source, "pages": prepared, "record": record}]


def bigramize(text: str) -> str:
    segments = re.findall(r"[\u3400-\u9fff]+|[^\u3400-\u9fff]+", text)
    out: list[str] = []
    for segment in segments:
        if re.fullmatch(r"[\u3400-\u9fff]+", segment):
            out.extend(segment[i : i + 2] for i in range(len(segment) - 1))
        else:
            out.append(segment)
    return " ".join(item for item in out if item)


def prepare(db: Path, batch: list[dict[str, Any]]) -> dict[str, Any]:
    pages = batch[0]["pages"]
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as conn:
        existing = conn.execute("SELECT id FROM documents WHERE doc_key=?", (DOC_KEY,)).fetchone()
    return {
        "formal_db": str(db.resolve()),
        "formal_db_sha256": db_sha256(db),
        "source_file": SOURCE_REL,
        "source_sha256": SOURCE_SHA,
        "source_title": SOURCE_TITLE,
        "doc_key": DOC_KEY,
        "page_count": len(pages),
        "pdf_page_numbers": [row["pdf_page"] for row in pages],
        "ocr_text_chars": sum(len(row["text"]) for row in pages),
        "ocr_min_confidence": min(row["ocr_confidence"] for row in pages),
        "ocr_max_confidence": max(row["ocr_confidence"] for row in pages),
        "existing_document_id": int(existing[0]) if existing else None,
        "citation_ready_pages": 0,
        "review_only_pages": len(pages),
        "evidence_level": "L2",
    }


def apply_import(db: Path, batch: list[dict[str, Any]], backup: Path) -> dict[str, Any]:
    actual_db = db.resolve()
    if backup.exists():
        raise FileExistsError(f"refusing to overwrite existing backup: {backup}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    before_sha = db_sha256(actual_db)
    shutil.copy2(actual_db, backup)
    if db_sha256(backup) != before_sha:
        raise RuntimeError("formal DB backup SHA mismatch")

    pages = batch[0]["pages"]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tags = ";".join(
        [
            "pcc_1946",
            "sourcebook_compilation",
            "evidence_level=L2",
            "source_kind=public_scan",
            "ocr_status=pilot",
            "ocr_page_status=needs_human_review",
            "citation_ready=false",
            "needs_human_review=true",
            "review_status=review_only",
            f"batch={BATCH_ID}",
        ]
    )
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            """INSERT INTO sources(source_type,source_id,title,origin_url,local_path)
               VALUES(?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET
                 title=excluded.title, origin_url=excluded.origin_url, local_path=excluded.local_path""",
            ("domestic_sourcebook_ocr", SOURCE_ID, SOURCE_TITLE, SOURCE_URL, SOURCE_REL),
        )
        source_db_id = conn.execute("SELECT id FROM sources WHERE source_id=?", (SOURCE_ID,)).fetchone()[0]
        document_id = conn.execute(
            """INSERT INTO documents(
                 source_id,doc_key,volume_id,volume_title,doc_id,title,date_guess,url,
                 local_txt,hit_type,matched_terms,source_platform)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                source_db_id,
                DOC_KEY,
                "DOMESTIC-PCC-1946",
                "政协文献（1946）",
                SOURCE_ID,
                SOURCE_TITLE,
                "1946",
                SOURCE_URL,
                SOURCE_REL,
                "domestic_sourcebook_ocr",
                tags,
                "domestic",
            ),
        ).lastrowid
        inserted_ids: list[int] = []
        for row in pages:
            pdf_page = row["pdf_page"]
            page_url = f"{SOURCE_URL}#page={pdf_page}"
            page_id = conn.execute(
                "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                (document_id, row["label"], page_url, row["text"]),
            ).lastrowid
            conn.execute(
                "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-PCC-1946", SOURCE_ID, SOURCE_TITLE, row["label"], tags, row["text"]),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-PCC-1946", SOURCE_ID, SOURCE_TITLE, row["label"], tags, bigramize(row["text"])),
            )
            conn.execute(
                """INSERT INTO page_provenance(
                    page_id,document_id,source_id,source_file,source_sha256,source_file_size,
                    pdf_page_no,physical_page_no,printed_page,page_image_path,page_image_sha256,
                    ocr_md_path,ocr_md_sha256,ocr_engine,ocr_model,ocr_mode,ocr_lines,
                    ocr_mean_confidence,text_chars,citation_ready,needs_human_review,review_status,
                    machine_review_note,human_review_note,period,year,event_tags,source_title,
                    batch_id,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    page_id,
                    document_id,
                    SOURCE_ID,
                    SOURCE_REL,
                    SOURCE_SHA,
                    Path(batch[0]["source"]).stat().st_size,
                    pdf_page,
                    pdf_page,
                    row["printed_page"],
                    str(row["image"].relative_to(ROOT)),
                    row["image_sha"],
                    str(row["ocr"].relative_to(ROOT)),
                    row["ocr_sha"],
                    "PaddleOCR 3.7.0",
                    "PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
                    "scan_pdf_paddleocr",
                    row["ocr_lines"],
                    row["ocr_confidence"],
                    len(row["text"]),
                    0,
                    1,
                    "review_only",
                    "L2 汇编扫描页的本地 PaddleOCR 检索草稿；已完成页图/标题定位，但尚未完成逐字人工复核，不得直接作为正式引文。",
                    None,
                    "1946",
                    1946,
                    tags,
                    SOURCE_TITLE,
                    BATCH_ID,
                    now,
                    now,
                ),
            )
            inserted_ids.append(page_id)
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        pages_without_fts = conn.execute(
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL"
        ).fetchone()[0]
        fts_without_pages = conn.execute(
            "SELECT COUNT(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL"
        ).fetchone()[0]
        page_provenance_count = conn.execute(
            "SELECT COUNT(*) FROM page_provenance WHERE document_id=?", (document_id,)
        ).fetchone()[0]
        citation_ready_count = conn.execute(
            "SELECT COUNT(*) FROM page_provenance WHERE document_id=? AND citation_ready=1", (document_id,)
        ).fetchone()[0]
        total = {
            "documents": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "pages": conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0],
            "page_fts": conn.execute("SELECT COUNT(*) FROM page_fts").fetchone()[0],
            "page_fts_bigram": conn.execute("SELECT COUNT(*) FROM page_fts_bigram").fetchone()[0],
        }
    return {
        "document_id": document_id,
        "page_ids": inserted_ids,
        "imported_pages": len(inserted_ids),
        "page_provenance": page_provenance_count,
        "citation_ready_pages": citation_ready_count,
        "integrity_check": integrity,
        "foreign_key_violations": fk,
        "pages_without_fts": pages_without_fts,
        "fts_without_pages": fts_without_pages,
        "totals": total,
        "formal_db_sha256_after": db_sha256(actual_db),
        "backup": str(backup),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal-db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "work/domestic/pcc_1946_sourcebook_ocr_20260814/PILOT_IMPORT_MANIFEST.jsonl",
    )
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    db = args.formal_db.expanduser().resolve()
    root = args.source_root.expanduser().resolve()
    manifest = args.manifest.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"formal DB not found: {db}")
    batch = read_manifest(root, manifest)
    prepared = prepare(db, batch)
    report: dict[str, Any] = {
        "batch_id": BATCH_ID,
        "mode": "apply" if args.apply else "dry_run",
        "gate": "PASS",
        "body_read": True,
        "raw_source_copied": False,
        **prepared,
    }
    if args.apply:
        if prepared["existing_document_id"] is not None:
            raise SystemExit("formal document already exists; refuse duplicate import")
        if not args.expected_db_sha or args.expected_db_sha != prepared["formal_db_sha256"]:
            raise SystemExit("--apply requires --expected-db-sha matching the current formal DB")
        if not args.backup:
            raise SystemExit("--apply requires --backup")
        result = apply_import(db, batch, args.backup.expanduser().resolve())
        report["apply_result"] = result
        report["formal_db_sha256_after"] = result["formal_db_sha256_after"]
        report["gate"] = "PASS" if (
            result["integrity_check"] == "ok"
            and result["foreign_key_violations"] == 0
            and result["pages_without_fts"] == 0
            and result["fts_without_pages"] == 0
            and result["citation_ready_pages"] == 0
        ) else "FAIL"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
