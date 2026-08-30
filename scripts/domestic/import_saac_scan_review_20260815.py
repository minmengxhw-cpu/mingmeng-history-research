#!/usr/bin/env python3
"""Import one exact SAAC scan candidate as review-only OCR pages.

The 1949-09-21 first-day PCC meeting record is published by the National
Archives Administration as three handwritten scan images.  This importer
keeps the image SHA, OCR-draft SHA, page coordinates, and candidate/document
link together.  It never promotes OCR to a formal citation.

Default mode is read-only.  ``--apply`` requires the current database SHA and
a new backup path.  It refuses to overwrite an existing document or relink a
candidate to a different document.
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
CANDIDATE_ID = "domestic:SAAC:1949-09-21-06"
DOC_KEY = "domestic-ocr/SAAC:domestic:SAAC:1949-09-21-06"
SOURCE_ID = "saac-51koukou"
SOURCE_TITLE = "中央档案馆：从「五一口号」到开国大典档案文献专辑"
ITEM_URL = "https://www.saac.gov.cn/daj/gqzt/content/05/05_18.html"
BATCH_ID = "saac-scan-review-20260815"

PAGES = [
    {
        "index": 1,
        "image": "data/domestic/raw/saac_scans/sec05_05-18/01.jpg",
        "image_sha256": "92f14de5ce331845dc9d136312792b422d703af6357e21caa4e5def34d75b00c",
        "ocr": "work/domestic/saac_1949_pcc_day1_ocr_20260815/01.ocr.md",
        "ocr_sha256": "2c0cc365d997ecd4a21aab1107ff4a9d5fe72ce5a51e1cb17ba85a3319cadd17",
        "label": "image-01 / 官方扫描图 01",
    },
    {
        "index": 2,
        "image": "data/domestic/raw/saac_scans/sec05_05-18/02.jpg",
        "image_sha256": "dfdfc1a71f6f5dc26a2af57941b0eb96249cc1c56cd21eb96cad1fd94f6d1da7",
        "ocr": "work/domestic/saac_1949_pcc_day1_ocr_20260815/02.ocr.md",
        "ocr_sha256": "29307caf1eb0d7c647d37602028ee34af6cb4fbc13e5eab1ff9f0018045a3408",
        "label": "image-02 / 官方扫描图 02",
    },
    {
        "index": 3,
        "image": "data/domestic/raw/saac_scans/sec05_05-18/03.jpg",
        "image_sha256": "11ac6e9dab23cd83244f41400147df169652b01d176ae3c31774d88aa6264596",
        "ocr": "work/domestic/saac_1949_pcc_day1_ocr_20260815/03.ocr.md",
        "ocr_sha256": "ee2d5ee7c02d4a94982fd8bebe53c7bcc095fe6db819c3ebfabfea3b87557a5e",
        "label": "image-03 / 官方扫描图 03",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def db_sha256(path: Path) -> str:
    return sha256(path.resolve())


def project_root(db: Path) -> Path:
    resolved = db.resolve()
    if resolved.name != "research_index.sqlite" or resolved.parent.name != "data":
        raise ValueError(f"expected data/research_index.sqlite, got {resolved}")
    return resolved.parent.parent


def resolve_under_root(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes project root: {relative}") from exc
    return path


def parse_ocr(path: Path) -> tuple[str, int, float]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if "## 识别文本" not in raw:
        raise ValueError(f"OCR marker missing: {path}")
    text = raw.split("## 识别文本", 1)[1]
    if "## 明细" in text:
        text = text.split("## 明细", 1)[0]
    text = text.strip()
    if not text or text == "未识别出文字。":
        raise ValueError(f"OCR text is empty: {path}")
    scores = [
        float(value)
        for value in re.findall(
            r"\|\s*\d+\s*\|.*?\|\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*\|",
            raw,
        )
    ]
    if not scores:
        raise ValueError(f"OCR confidence table missing: {path}")
    return text, len(scores), sum(scores) / len(scores)


def bigramize(text: str) -> str:
    chunks = re.findall(r"[\u3400-\u9fff]+|[^\u3400-\u9fff]+", text)
    output: list[str] = []
    for chunk in chunks:
        if re.fullmatch(r"[\u3400-\u9fff]+", chunk):
            output.extend(chunk[index : index + 2] for index in range(len(chunk) - 1))
        else:
            output.append(chunk)
    return " ".join(item for item in output if item)


def load_candidate(conn: sqlite3.Connection, *, require_unlinked: bool) -> sqlite3.Row:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM domestic_candidates WHERE candidate_id=?", (CANDIDATE_ID,)
    ).fetchone()
    if row is None:
        raise RuntimeError(f"candidate not found: {CANDIDATE_ID}")
    if row["review_status"] != "accepted" or row["check_outcome"] != "pass":
        raise RuntimeError("candidate must remain accepted/pass")
    if require_unlinked and row["ingested_document_id"] is not None:
        raise RuntimeError(f"candidate already linked: {row['ingested_document_id']}")
    return row


def collect_pages(root: Path) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for item in PAGES:
        image = resolve_under_root(root, item["image"])
        ocr = resolve_under_root(root, item["ocr"])
        if not image.is_file() or not ocr.is_file():
            raise FileNotFoundError(f"missing image/OCR: {image} / {ocr}")
        image_sha = sha256(image)
        ocr_sha = sha256(ocr)
        if image_sha != item["image_sha256"]:
            raise RuntimeError(f"image SHA mismatch for page {item['index']}")
        if ocr_sha != item["ocr_sha256"]:
            raise RuntimeError(f"OCR SHA mismatch for page {item['index']}")
        text, lines, confidence = parse_ocr(ocr)
        prepared.append(
            {
                **item,
                "image_path": image,
                "ocr_path": ocr,
                "image_size": image.stat().st_size,
                "ocr_size": ocr.stat().st_size,
                "text": text,
                "ocr_lines": lines,
                "ocr_confidence": confidence,
            }
        )
    return prepared


def prepare(db: Path) -> dict[str, Any]:
    root = project_root(db)
    pages = collect_pages(root)
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        candidate = load_candidate(conn, require_unlinked=False)
        existing = conn.execute(
            "SELECT id, doc_key FROM documents WHERE doc_key=?", (DOC_KEY,)
        ).fetchone()
        linked_id = candidate["ingested_document_id"]
        if linked_id is not None and (existing is None or int(existing[0]) != int(linked_id)):
            raise RuntimeError("candidate/document link is inconsistent")
        status = "ALREADY_APPLIED" if linked_id is not None else "READY"
    return {
        "status": status,
        "candidate_id": CANDIDATE_ID,
        "candidate_title": candidate["title"],
        "document_key": DOC_KEY,
        "item_url": ITEM_URL,
        "formal_db": str(db.resolve()),
        "formal_db_sha256": db_sha256(db),
        "page_count": len(pages),
        "image_sha256": [page["image_sha256"] for page in pages],
        "ocr_sha256": [page["ocr_sha256"] for page in pages],
        "ocr_lines": [page["ocr_lines"] for page in pages],
        "ocr_mean_confidence": [round(page["ocr_confidence"], 4) for page in pages],
        "ocr_text_chars": [len(page["text"]) for page in pages],
        "existing_document": dict(existing) if existing else None,
        "citation_ready_pages": 0,
        "review_only_pages": len(pages),
        "evidence_level": "L1",
    }


def apply_import(db: Path, backup: Path, expected_db_sha: str) -> dict[str, Any]:
    actual_db = db.resolve()
    before_sha = db_sha256(actual_db)
    if before_sha != expected_db_sha:
        raise RuntimeError(f"database SHA mismatch: got {before_sha}, expected {expected_db_sha}")
    if backup.exists():
        raise FileExistsError(f"refusing to overwrite backup: {backup}")
    prepared = prepare(db)
    if prepared["status"] != "READY":
        raise RuntimeError(f"refusing to reapply: {prepared['status']}")
    root = project_root(db)
    pages = collect_pages(root)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    if db_sha256(backup) != before_sha:
        raise RuntimeError("formal DB backup SHA mismatch")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tags = ";".join(
        [
            "saac_scan",
            "source_kind=official_scan",
            "evidence_level=L1",
            "ocr_status=pilot",
            "citation_ready=false",
            "needs_human_review=true",
            "review_status=review_only",
            f"batch={BATCH_ID}",
            f"candidate_id={CANDIDATE_ID}",
        ]
    )
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        candidate = load_candidate(conn, require_unlinked=True)
        conn.execute(
            """INSERT INTO sources(source_type,source_id,title,origin_url,local_path)
               VALUES(?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET
                 title=excluded.title, origin_url=excluded.origin_url, local_path=excluded.local_path""",
            ("domestic_page_ocr", SOURCE_ID, SOURCE_TITLE, "https://www.saac.gov.cn/daj/gqzt/", None),
        )
        source_db_id = conn.execute(
            "SELECT id FROM sources WHERE source_id=?", (SOURCE_ID,)
        ).fetchone()[0]
        existing = conn.execute("SELECT id FROM documents WHERE doc_key=?", (DOC_KEY,)).fetchone()
        if existing:
            raise RuntimeError(f"document key unexpectedly exists: {DOC_KEY}")
        document_id = conn.execute(
            """INSERT INTO documents(
                 source_id,doc_key,volume_id,volume_title,doc_id,title,date_guess,url,
                 local_txt,hit_type,matched_terms,source_platform,ingested_candidate_id)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                source_db_id,
                DOC_KEY,
                "DOMESTIC-SAAC-1949-PCC",
                "中国人民政治协商会议第一届全体会议",
                CANDIDATE_ID,
                "中国人民政治协商会议第一届全体会议第一天会议记录（1949年9月21日）",
                "1949-09-21",
                ITEM_URL,
                pages[0]["image"],
                "saac_page_ocr",
                tags,
                "domestic",
                CANDIDATE_ID,
            ),
        ).lastrowid
        page_ids: list[int] = []
        for page in pages:
            page_url = f"{ITEM_URL}#image={page['index']:02d}"
            page_id = conn.execute(
                "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                (document_id, page["label"], page_url, page["text"]),
            ).lastrowid
            page_ids.append(page_id)
            conn.execute(
                "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-SAAC-1949-PCC", CANDIDATE_ID, SOURCE_TITLE, page["label"], tags, page["text"]),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-SAAC-1949-PCC", CANDIDATE_ID, SOURCE_TITLE, page["label"], tags, bigramize(page["text"])),
            )
            image_rel = page["image"]
            ocr_rel = page["ocr"]
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
                    image_rel,
                    page["image_sha256"],
                    page["image_size"],
                    None,
                    page["index"],
                    None,
                    image_rel,
                    page["image_sha256"],
                    ocr_rel,
                    page["ocr_sha256"],
                    "PaddleOCR 3.7.0",
                    "PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
                    "scan_page_paddleocr",
                    page["ocr_lines"],
                    page["ocr_confidence"],
                    len(page["text"]),
                    0,
                    1,
                    "review_only",
                    "手写档案的本地 PaddleOCR 草稿；错字、漏字和繁简识别误差明显，未逐字人工复核。",
                    None,
                    "1941-1949",
                    1949,
                    tags,
                    SOURCE_TITLE,
                    BATCH_ID,
                    now,
                    now,
                ),
            )
        conn.execute(
            """UPDATE domestic_candidates
               SET ingested_document_id=?,
                   review_note=COALESCE(review_note||'；','')||?
               WHERE candidate_id=? AND ingested_document_id IS NULL""",
            (document_id, f"saac_scan_ocr({BATCH_ID}) {now}", CANDIDATE_ID),
        )
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        pages_without_fts = conn.execute(
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE p.id IN (?,?,?) AND f.rowid IS NULL",
            tuple(page_ids),
        ).fetchone()[0]
        provenance_count = conn.execute(
            "SELECT COUNT(*) FROM page_provenance WHERE document_id=?", (document_id,)
        ).fetchone()[0]
        linked_id = conn.execute(
            "SELECT ingested_document_id FROM domestic_candidates WHERE candidate_id=?",
            (CANDIDATE_ID,),
        ).fetchone()[0]
    return {
        "status": "APPLIED",
        "document_id": document_id,
        "page_ids": page_ids,
        "candidate_id": CANDIDATE_ID,
        "before_db_sha256": before_sha,
        "after_db_sha256": db_sha256(actual_db),
        "backup": str(backup),
        "integrity_check": integrity,
        "foreign_key_violations": fk,
        "pages_without_fts": pages_without_fts,
        "page_provenance_count": provenance_count,
        "linked_candidate_document_id": linked_id,
        "citation_ready_pages": 0,
        "review_only_pages": len(page_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    if args.apply == args.dry_run:
        parser.error("choose exactly one of --dry-run or --apply")
    db = args.db.expanduser().resolve()
    prepared = prepare(db)
    if args.dry_run:
        print(json.dumps(prepared, ensure_ascii=False, indent=2))
        return 0
    if not args.expected_db_sha or not args.backup:
        parser.error("--apply requires --expected-db-sha and --backup")
    result = apply_import(db, args.backup.expanduser().resolve(), args.expected_db_sha)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
