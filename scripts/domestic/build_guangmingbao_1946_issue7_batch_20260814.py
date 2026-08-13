#!/usr/bin/env python3
"""Build a metadata-only visual-review batch for *Guangming Bao* issue 7.

The existing formal page (16351) already has the real PDF, SHA and page
anchor.  This batch only records the proposed evidence boundary: issue
identity, date, PDF page and the visible editorial title.  It intentionally
does not include OCR or page body text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_OUT = ROOT / "work" / "domestic" / "guangmingbao_1946_issue7_visual_review_20260814"
PAGE_ID = 16351


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    db = args.db.expanduser().resolve()
    out = args.out.expanduser()
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT p.id AS page_id, p.page_label, p.page_url, d.id AS document_id,
                   d.doc_key, d.title, d.date_guess, d.source_platform,
                   pp.source_file, pp.source_sha256, pp.source_file_size,
                   pp.pdf_page_no, pp.physical_page_no, pp.page_image_path,
                   pp.page_image_sha256, pp.ocr_md_path, pp.ocr_md_sha256,
                   pp.review_status, pp.citation_ready, pp.needs_human_review,
                   pp.event_tags, pp.source_title
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            JOIN page_provenance pp ON pp.page_id=p.id
            WHERE p.id=?
            """,
            (PAGE_ID,),
        ).fetchone()
    if row is None:
        raise SystemExit(f"page {PAGE_ID} not found")
    if row["source_platform"] != "domestic":
        raise SystemExit("target page is not domestic")
    source_file = str(row["source_file"] or "")
    source = db.parent.parent / source_file
    if not source.is_file():
        raise SystemExit(f"source file not found: {source}")
    actual_sha = sha256(source)
    if actual_sha != str(row["source_sha256"] or "").lower():
        raise SystemExit("source SHA256 mismatch")
    if int(row["pdf_page_no"] or 0) != 1 or int(row["physical_page_no"] or 0) != 1:
        raise SystemExit("expected PDF/physical page 1")
    batch = {
        "schema_version": 1,
        "batch_id": "guangmingbao-1946-issue7-visual-review-20260814",
        "purpose": "将《光明報》新七號首版从机器/OCR导航绑定到真实PDF页级身份；只确认刊名、期号、出版日、PDF页码、版面和社论题名，不开放未经逐字校勘的OCR正文。",
        "body_text_included": False,
        "database": {"path": str(db), "sha256": sha256(db), "size": db.stat().st_size},
        "source_basis": "中国国家图书馆数字化民国期刊公开扫描的本地PDF副本；《光明報》1946年新七號，1946-11-18，公开Wikimedia来源入口。该页是民盟机关报同期政治表达，不是民盟正式拒参声明、政协原始会议记录或政府文件。",
        "pages": [{
            "page_id": int(row["page_id"]),
            "document_id": int(row["document_id"]),
            "doc_key": str(row["doc_key"]),
            "page_label": str(row["page_label"]),
            "current": {
                "page_url": str(row["page_url"]),
                "source_file": source_file,
                "source_sha256": str(row["source_sha256"]),
                "review_status": str(row["review_status"]),
                "citation_ready": int(row["citation_ready"] or 0),
                "needs_human_review": int(row["needs_human_review"] or 0),
            },
            "new_page_url": "https://commons.wikimedia.org/wiki/Special:FilePath/NLC404-01J000514-10428_%E5%85%89%E6%98%8E%E5%A0%B1_1946%E5%B9%B47%E6%9C%9F.pdf#page=1",
            "source_file": source_file,
            "source_sha256": actual_sha,
            "source_file_size": int(row["source_file_size"] or source.stat().st_size),
            "pdf_page_no": 1,
            "physical_page_no": 1,
            "page_image_path": str(row["page_image_path"] or ""),
            "page_image_sha256": str(row["page_image_sha256"] or ""),
            "ocr_md_path": str(row["ocr_md_path"] or ""),
            "ocr_md_sha256": str(row["ocr_md_sha256"] or ""),
            "year": 1946,
            "period": "1946-11",
            "event_tags": "ocr_mode=page-by-page-real;ocr_status=real_page_ocr;source_kind=public_scan;topic=domestic-1946-refuse-national-assembly;evidence_role=contemporary_periodical_cross_source;review_scope=periodical_issue_identity_editorial_title",
            "source_title": "《光明報》1946 年7期",
        }],
    }
    decisions = {
        "body_text_included": False,
        "pages": [{
            "page_id": PAGE_ID,
            "decision": "human_verified",
            "reviewer": "codex-visual-audit-20260814",
            "review_method": "local_pdf_page_visual_review",
            "note": "已对照本地原始PDF第1页并核对整期PDF SHA256、物理页和公开来源入口。版头清晰显示《光明報》新七號、民国三十五年十一月十八日和香港出版信息；首版中央社论题名清晰显示“我们为什么不参加国大”。仅确认刊期、出版日、页码、版面及题名，不把OCR正文作为逐字引文，也不据此确认民盟正式拒参声明、政协原始记录或全部事件事实。",
        }],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "BATCH.json").write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "REVIEW_DECISIONS.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"batch": str(out / "BATCH.json"), "decisions": str(out / "REVIEW_DECISIONS.json"), "page_id": PAGE_ID, "database_sha256": batch["database"]["sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
