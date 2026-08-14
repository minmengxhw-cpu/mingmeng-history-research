#!/usr/bin/env python3
"""Import an explicit batch of SAAC scan/OCR pages as review-only records.

The manifest is the write boundary: every candidate, document key, image,
OCR draft, and SHA must be listed there.  The importer does not infer title
matches and never promotes machine OCR to a formal citation.

Default mode is read-only.  ``--apply`` requires the exact current formal DB
SHA and a new backup path.  Existing documents, candidate links, and local
files are never overwritten or deleted.
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
DEFAULT_MANIFEST = ROOT / "data" / "domestic" / "saac_scan_manifest_1949_pcc_chain_20260815.json"
OCR_ENGINE = "PaddleOCR 3.7.0"
OCR_MODEL = "PP-OCRv6_medium_det + PP-OCRv6_medium_rec"


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


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "domestic_saac_scan_batch_manifest.v1":
        raise ValueError("unexpected manifest schema")
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("manifest items must be a non-empty list")
    candidate_ids = [str(item.get("candidate_id") or "") for item in items]
    doc_keys = [str(item.get("doc_key") or "") for item in items]
    if len(set(candidate_ids)) != len(candidate_ids) or any(not value for value in candidate_ids):
        raise ValueError("candidate IDs must be unique and non-empty")
    if len(set(doc_keys)) != len(doc_keys) or any(not value for value in doc_keys):
        raise ValueError("document keys must be unique and non-empty")
    for item in items:
        pages = item.get("pages")
        if not isinstance(pages, list) or not pages:
            raise ValueError(f"item has no pages: {item.get('candidate_id')}")
        numbers = [int(page.get("physical_page")) for page in pages]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"pages must be sequential from 1: {item.get('candidate_id')}")
    return payload


def prepare(db: Path, manifest_path: Path) -> dict[str, Any]:
    root = project_root(db)
    manifest = load_manifest(manifest_path)
    prepared_items: list[dict[str, Any]] = []
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        for item in manifest["items"]:
            candidate = conn.execute(
                "SELECT * FROM domestic_candidates WHERE candidate_id=?",
                (item["candidate_id"],),
            ).fetchone()
            if candidate is None:
                raise RuntimeError(f"candidate not found: {item['candidate_id']}")
            if candidate["review_status"] != "accepted" or candidate["check_outcome"] != "pass":
                raise RuntimeError(f"candidate is not accepted/pass: {item['candidate_id']}")
            existing = conn.execute(
                "SELECT id, doc_key FROM documents WHERE doc_key=?", (item["doc_key"],)
            ).fetchone()
            linked_id = candidate["ingested_document_id"]
            if linked_id is not None and (existing is None or int(existing[0]) != int(linked_id)):
                raise RuntimeError(f"candidate/document link conflict: {item['candidate_id']}")
            if existing is not None and linked_id is None:
                raise RuntimeError(f"document exists without candidate link: {item['doc_key']}")
            page_rows: list[dict[str, Any]] = []
            for page in item["pages"]:
                image = resolve_under_root(root, page["image"])
                ocr = resolve_under_root(root, page["ocr"])
                if not image.is_file() or not ocr.is_file():
                    raise FileNotFoundError(f"missing image/OCR: {image} / {ocr}")
                image_sha = sha256(image)
                ocr_sha = sha256(ocr)
                if image_sha != page["image_sha256"]:
                    raise RuntimeError(f"image SHA mismatch: {page['image']}")
                if ocr_sha != page["ocr_sha256"]:
                    raise RuntimeError(f"OCR SHA mismatch: {page['ocr']}")
                text, lines, confidence = parse_ocr(ocr)
                if int(page["ocr_lines"]) != lines:
                    raise RuntimeError(f"OCR line count mismatch: {page['ocr']}")
                if abs(float(page["ocr_mean_confidence"]) - confidence) > 0.001:
                    raise RuntimeError(f"OCR confidence mismatch: {page['ocr']}")
                page_rows.append(
                    {
                        **page,
                        "image_path": image,
                        "ocr_path": ocr,
                        "image_size": image.stat().st_size,
                        "text": text,
                        "ocr_lines_actual": lines,
                        "ocr_confidence_actual": confidence,
                    }
                )
            prepared_items.append(
                {
                    **item,
                    "candidate": dict(candidate),
                    "existing_document": dict(existing) if existing else None,
                    "page_rows": page_rows,
                    "status": "ALREADY_APPLIED" if linked_id is not None else "READY",
                }
            )
    statuses = {str(item["status"]) for item in prepared_items}
    overall = "ALREADY_APPLIED" if statuses == {"ALREADY_APPLIED"} else "READY" if statuses == {"READY"} else "MIXED"
    return {
        "status": overall,
        "manifest": str(manifest_path.resolve()),
        "batch_id": manifest["batch_id"],
        "source_id": manifest["source_id"],
        "formal_db": str(db.resolve()),
        "formal_db_sha256": db_sha256(db),
        "item_count": len(prepared_items),
        "page_count": sum(len(item["page_rows"]) for item in prepared_items),
        "items": prepared_items,
    }


def summary(prepared: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": prepared["status"],
        "manifest": prepared["manifest"],
        "batch_id": prepared["batch_id"],
        "source_id": prepared["source_id"],
        "formal_db": prepared["formal_db"],
        "formal_db_sha256": prepared["formal_db_sha256"],
        "item_count": prepared["item_count"],
        "page_count": prepared["page_count"],
        "items": [
            {
                "candidate_id": item["candidate_id"],
                "doc_key": item["doc_key"],
                "status": item["status"],
                "existing_document": item["existing_document"],
                "page_count": len(item["page_rows"]),
                "ocr_mean_confidence": [round(page["ocr_confidence_actual"], 4) for page in item["page_rows"]],
            }
            for item in prepared["items"]
        ],
    }


def apply_import(db: Path, manifest_path: Path, backup: Path, expected_db_sha: str) -> dict[str, Any]:
    actual_db = db.resolve()
    before_sha = db_sha256(actual_db)
    if before_sha != expected_db_sha:
        raise RuntimeError(f"database SHA mismatch: got {before_sha}, expected {expected_db_sha}")
    if backup.exists():
        raise FileExistsError(f"refusing to overwrite backup: {backup}")
    prepared = prepare(db, manifest_path)
    if prepared["status"] != "READY":
        raise RuntimeError(f"refusing to apply status {prepared['status']}")
    manifest = load_manifest(manifest_path)
    root = project_root(db)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    if db_sha256(backup) != before_sha:
        raise RuntimeError("formal DB backup SHA mismatch")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    document_ids: dict[str, int] = {}
    page_ids: list[int] = []
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        for item, prepared_item in zip(manifest["items"], prepared["items"]):
            candidate = prepared_item["candidate"]
            conn.execute(
                """INSERT INTO sources(source_type,source_id,title,origin_url,local_path)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(source_id) DO UPDATE SET
                     title=excluded.title, origin_url=excluded.origin_url""",
                (
                    "domestic_page_ocr",
                    manifest["source_id"],
                    manifest["source_title"],
                    "https://www.saac.gov.cn/daj/gqzt/",
                    None,
                ),
            )
            source_db_id = conn.execute(
                "SELECT id FROM sources WHERE source_id=?", (manifest["source_id"],)
            ).fetchone()[0]
            tags = ";".join(
                [
                    "saac_scan",
                    "source_kind=official_scan",
                    "evidence_level=L1",
                    "ocr_status=pilot",
                    "citation_ready=false",
                    "needs_human_review=true",
                    "review_status=review_only",
                    f"batch={manifest['batch_id']}",
                    f"candidate_id={item['candidate_id']}",
                ]
                + [f"event={tag}" for tag in item.get("event_tags", [])]
            )
            document_id = conn.execute(
                """INSERT INTO documents(
                     source_id,doc_key,volume_id,volume_title,doc_id,title,date_guess,url,
                     local_txt,hit_type,matched_terms,source_platform,ingested_candidate_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    source_db_id,
                    item["doc_key"],
                    "DOMESTIC-SAAC-1949-PCC",
                    "中国人民政治协商会议第一届全体会议",
                    item["candidate_id"],
                    item["title"],
                    item["date_guess"],
                    item["item_url"],
                    item["pages"][0]["image"],
                    "saac_page_ocr",
                    tags,
                    "domestic",
                    item["candidate_id"],
                ),
            ).lastrowid
            document_ids[item["candidate_id"]] = int(document_id)
            for page, prepared_page in zip(item["pages"], prepared_item["page_rows"]):
                page_url = f"{item['item_url']}#image={int(page['physical_page']):02d}"
                page_id = conn.execute(
                    "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                    (document_id, f"image-{int(page['physical_page']):02d} / 官方扫描图 {int(page['physical_page']):02d}", page_url, prepared_page["text"]),
                ).lastrowid
                page_ids.append(int(page_id))
                conn.execute(
                    "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                    (page_id, "DOMESTIC-SAAC-1949-PCC", item["candidate_id"], manifest["source_title"], f"image-{int(page['physical_page']):02d}", tags, prepared_page["text"]),
                )
                conn.execute(
                    "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                    (page_id, "DOMESTIC-SAAC-1949-PCC", item["candidate_id"], manifest["source_title"], f"image-{int(page['physical_page']):02d}", tags, bigramize(prepared_page["text"])),
                )
                image_rel = page["image"]
                ocr_rel = page["ocr"]
                mode = "scan_page_paddleocr_rotate270" if int(page.get("ocr_rotation_degrees") or 0) else "scan_page_paddleocr"
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
                        manifest["source_id"],
                        image_rel,
                        page["image_sha256"],
                        prepared_page["image_size"],
                        None,
                        int(page["physical_page"]),
                        None,
                        image_rel,
                        page["image_sha256"],
                        ocr_rel,
                        page["ocr_sha256"],
                        OCR_ENGINE,
                        OCR_MODEL,
                        mode,
                        prepared_page["ocr_lines_actual"],
                        prepared_page["ocr_confidence_actual"],
                        len(prepared_page["text"]),
                        0,
                        1,
                        "review_only",
                        "官方扫描图的本地 PaddleOCR 草稿；识别存在错字、漏字和排版方向误差，未逐字人工复核。",
                        None,
                        "1941-1949",
                        int(item["date_guess"][:4]),
                        tags,
                        manifest["source_title"],
                        manifest["batch_id"],
                        now,
                        now,
                    ),
                )
            conn.execute(
                """UPDATE domestic_candidates
                   SET ingested_document_id=?,
                       review_note=COALESCE(review_note||'；','')||?
                   WHERE candidate_id=? AND ingested_document_id IS NULL""",
                (document_id, f"saac_scan_batch({manifest['batch_id']}) {now}", item["candidate_id"]),
            )
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        placeholders = ",".join("?" for _ in page_ids)
        pages_without_fts = conn.execute(
            f"SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE p.id IN ({placeholders}) AND f.rowid IS NULL",
            page_ids,
        ).fetchone()[0]
        provenance_count = conn.execute(
            f"SELECT COUNT(*) FROM page_provenance WHERE page_id IN ({placeholders})", page_ids
        ).fetchone()[0]
        citation_ready = conn.execute(
            f"SELECT COUNT(*) FROM page_provenance WHERE page_id IN ({placeholders}) AND citation_ready=1", page_ids
        ).fetchone()[0]
    return {
        "status": "APPLIED",
        "batch_id": manifest["batch_id"],
        "candidate_document_ids": document_ids,
        "page_ids": page_ids,
        "before_db_sha256": before_sha,
        "after_db_sha256": db_sha256(actual_db),
        "backup": str(backup),
        "integrity_check": integrity,
        "foreign_key_violations": fk,
        "pages_without_fts": pages_without_fts,
        "page_provenance_count": provenance_count,
        "citation_ready_pages": citation_ready,
        "review_only_pages": len(page_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    if args.apply == args.dry_run:
        parser.error("choose exactly one of --dry-run or --apply")
    db = args.db.expanduser().resolve()
    manifest = args.manifest.expanduser().resolve()
    prepared = prepare(db, manifest)
    if args.dry_run:
        print(json.dumps(summary(prepared), ensure_ascii=False, indent=2))
        return 0
    if not args.expected_db_sha or not args.backup:
        parser.error("--apply requires --expected-db-sha and --backup")
    result = apply_import(db, manifest, args.backup.expanduser().resolve(), args.expected_db_sha)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
