#!/usr/bin/env python3
"""Build the metadata-only review batch for the 1945 official compilation pages.

The batch binds the real NLC 1946 sourcebook PDF to the existing OCR navigation
rows for the 1945 platform and temporary national congress declaration.  It
contains metadata and review notes only; it never copies page text.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "research_index.sqlite"
OUT = ROOT / "work/domestic/minmeng_wenxian_1945_program_review_20260814"
SOURCE_REL = "data/domestic/sourcebooks/NLC416-01jh004281-12557_民主同盟文獻_1946.pdf"
SOURCE = DB.resolve().parent.parent / SOURCE_REL
SOURCE_URL = (
    "https://commons.wikimedia.org/wiki/"
    "File:NLC416-01jh004281-12557_%E6%B0%91%E4%B8%BB%E5%90%8C%E7%9B%9F%E6%96%87%E7%8D%BB.pdf"
)
BATCH_ID = "minmeng-wenxian-1945-program-visual-20260814"
REVIEWER = "codex-visual-audit-20260814"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    db_sha = sha256(DB)
    source_sha = sha256(SOURCE)
    source_size = SOURCE.stat().st_size
    pages = []
    decisions = []
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT p.id, p.document_id, p.page_label, p.page_url,
                   d.doc_key, d.title, d.date_guess,
                   pp.source_file, pp.source_sha256, pp.review_status,
                   pp.citation_ready, pp.needs_human_review, pp.ocr_md_path,
                   pp.ocr_md_sha256
            FROM pages p
            JOIN documents d ON d.id = p.document_id
            JOIN page_provenance pp ON pp.page_id = p.id
            WHERE p.id BETWEEN 20149 AND 20179
            ORDER BY p.id
            """
        ).fetchall()
    expected_ids = list(range(20149, 20180))
    if [int(row["id"]) for row in rows] != expected_ids:
        raise SystemExit("expected contiguous page ids 20149..20179")

    for row in rows:
        page_id = int(row["id"])
        pdf_page = page_id - 20101
        platform_pages = page_id <= 20173
        period = "1945-10" if platform_pages else "1945-10-16"
        title = "中国民主同盟纲领" if platform_pages else "中国民主同盟临时全国代表大会宣言"
        role = "official_compilation_of_1945_text"
        topic = "domestic-1945-first-congress"
        event_tags = ";".join(
            [
                "ocr_mode=page-by-page-real",
                "ocr_status=real_page_ocr",
                "citation_ready=true",
                "needs_human_review=false",
                "review_status=human_verified",
                "source_kind=official_compilation",
                "batch=s3-backfill-20260802",
                f"review_batch={BATCH_ID}",
                f"topic={topic}",
                f"evidence_role={role}",
                "review_scope=compiled_text_title_date_page_identity",
            ]
        )
        pages.append(
            {
                "page_id": page_id,
                "document_id": int(row["document_id"]),
                "doc_key": row["doc_key"],
                "page_label": row["page_label"],
                "title": title,
                "date_guess": period,
                "current": {
                    "page_url": row["page_url"],
                    "source_file": row["source_file"],
                    "source_sha256": row["source_sha256"],
                    "review_status": row["review_status"],
                    "citation_ready": int(row["citation_ready"]),
                    "needs_human_review": int(row["needs_human_review"]),
                },
                "new_page_url": f"{SOURCE_URL}#page={pdf_page}",
                "source_file": SOURCE_REL,
                "source_sha256": source_sha,
                "source_file_size": source_size,
                "pdf_page_no": pdf_page,
                "physical_page_no": pdf_page,
                "period": period,
                "year": 1945,
                "event_tags": event_tags,
                "source_title": "《民主同盟文獻》1946（民盟总部编印）",
                "batch_id": BATCH_ID,
                "ocr_md_path": row["ocr_md_path"],
                "ocr_md_sha256": row["ocr_md_sha256"],
            }
        )
        if platform_pages:
            note = (
                f"已对照本地《民主同盟文獻》1946原始PDF第{pdf_page}页，并核对第48—72页连续页序、"
                "篇名页与收束页。该页仅确认官方汇编中的《纲领》版本、标注日期、PDF页码和页界；"
                "不确认独立1945原件、底本关系或OCR正文逐字准确。"
            )
        else:
            note = (
                f"已对照本地《民主同盟文獻》1946原始PDF第{pdf_page}页，并核对第73—78页连续页序、"
                "篇名页与宣言收束页。该页仅确认官方汇编中的《临时全国代表大会宣言》版本、"
                "标注日期、PDF页码和页界；不确认独立1945原件、底本关系或OCR正文逐字准确。"
            )
        decisions.append(
            {
                "page_id": page_id,
                "decision": "human_verified",
                "reviewer": REVIEWER,
                "review_method": "local_pdf_page_visual_review",
                "note": note,
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    batch = {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "purpose": (
            "将《民主同盟文獻》1946年官方汇编中的《中国民主同盟纲领》和《临时全国代表大会宣言》"
            "31页从OCR-only导航记录绑定到真实PDF页级provenance；只确认汇编版本、篇名、标注日期、"
            "PDF页码和连续页界，不确认独立1945原件、底本关系或未经校勘的OCR正文。"
        ),
        "body_text_included": False,
        "database": {"path": str(DB), "sha256": db_sha, "size": DB.stat().st_size},
        "source_basis": (
            "中国国家图书馆标识NLC416-01jh004281-12557的公开扫描；1946年民盟总部编印本，"
            "真实PDF共176页。第48—72页为《纲领》，第73—78页为《临时全国代表大会宣言》。"
            "本批是官方汇编/再编载体，不是独立的1945大会档案原件。"
        ),
        "pages": pages,
    }
    decisions_payload = {
        "schema_version": 1,
        "batch_id": BATCH_ID,
        "body_text_included": False,
        "pages": decisions,
    }
    (OUT / "BATCH.json").write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "REVIEW_DECISIONS.json").write_text(
        json.dumps(decisions_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"batch": str(OUT / "BATCH.json"), "decisions": str(OUT / "REVIEW_DECISIONS.json"), "pages": len(pages), "database_sha": db_sha, "source_sha": source_sha}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
