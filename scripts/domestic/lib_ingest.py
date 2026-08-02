#!/usr/bin/env python3
"""S3 补采入库核心：把 OCR 文章写入 documents/pages/FTS/provenance。

复用 apply_page_batch.py 的入库模式（document + pages + page_fts + provenance），
并额外同步 bigram FTS 表（S2 新增）。
"""
import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import zhconv

ROOT = Path(__file__).resolve().parent.parent.parent
CJK_RE = re.compile(r"[\u3400-\u9fff]+")
BATCH_ID = "s3-backfill-20260802"


def bigramize(text: str) -> str:
    out: list[str] = []
    last = 0
    for m in CJK_RE.finditer(text):
        if m.start() > last:
            out.append(text[last : m.start()])
        seg = m.group(0)
        for i in range(len(seg) - 1):
            out.append(seg[i : i + 2])
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    return " ".join(p for p in out if p)


def body_text(md_text: str) -> str:
    lines = []
    for ln in md_text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith(("#", ">", "*", "-", "|", "```")):
            continue
        if re.match(r"^(来源文件|OCR 引擎|运行方式|生成时间|OCR 识别结果)", s):
            continue
        lines.append(s)
    return "\n".join(lines)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ingest_item(conn: sqlite3.Connection, item: dict) -> dict:
    """入库一个候选。返回 {'doc_key','document_id','pages','new_doc'}。"""
    cid = item["candidate_id"]
    title = item["title"]
    date_guess = item.get("date")
    ocr_paths = item["ocr_paths"]
    if not ocr_paths:
        return {"document_id": None, "pages": 0, "new_doc": False, "error": "no_ocr"}

    # 收集所有 OCR 文本（一候选可能多页）
    page_rows = []
    for rel in ocr_paths:
        p = Path(rel)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            continue
        md_text = p.read_text(encoding="utf-8", errors="replace")
        text = zhconv.convert(body_text(md_text), "zh-cn")
        if not text:
            continue
        page_rows.append({
            "ocr_md": str(p.relative_to(ROOT)),
            "text": text,
            "label": p.stem.replace(".ocr", "") or "1",
        })
    if not page_rows:
        return {"document_id": None, "pages": 0, "new_doc": False, "error": "empty_ocr"}

    now = _now()
    doc_key = f"domestic-ocr/S3:{cid}"
    sid = f"s3:{cid}"

    # sources
    conn.execute(
        "INSERT INTO sources (source_type, source_id, title, origin_url, local_path) "
        "VALUES (?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET "
        "title=excluded.title, local_path=excluded.local_path",
        ("domestic_page_ocr", sid, title, item.get("source_url"), None),
    )
    src_id = conn.execute("SELECT id FROM sources WHERE source_id=?", (sid,)).fetchone()[0]

    tags = ",".join([
        "ocr_mode=page-by-page-real",
        "ocr_status=real_page_ocr",
        "citation_ready=false",
        "needs_human_review=true",
        "review_status=review_only",
        "source_kind=public_scan",
        f"batch={BATCH_ID}",
        f"candidate_id={cid}",
    ])

    existing = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()
    if existing:
        doc_id = existing[0]
        old_pages = [r[0] for r in conn.execute("SELECT id FROM pages WHERE document_id=?", (doc_id,))]
        for pid in old_pages:
            conn.execute("DELETE FROM page_fts WHERE rowid=?", (pid,))
            conn.execute("DELETE FROM page_fts_bigram WHERE rowid=?", (pid,))
            conn.execute("DELETE FROM page_provenance WHERE page_id=?", (pid,))
        conn.execute("DELETE FROM pages WHERE document_id=?", (doc_id,))
        conn.execute(
            "UPDATE documents SET source_id=?, volume_id=?, volume_title=?, doc_id=?, title=?, "
            "date_guess=?, local_txt=?, hit_type=?, matched_terms=?, source_platform=? WHERE id=?",
            (src_id, "DOMESTIC-PAGE", title, sid, title, date_guess,
             page_rows[0]["ocr_md"], "domestic_page_ocr", tags, "domestic", doc_id),
        )
        new_doc = False
    else:
        cur = conn.execute(
            "INSERT INTO documents (source_id, doc_key, volume_id, volume_title, doc_id, doc_number, "
            "title, date_guess, url, local_html, local_txt, hit_type, matched_terms, source_platform) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (src_id, doc_key, "DOMESTIC-PAGE", title, sid, None, title,
             date_guess, None, None, page_rows[0]["ocr_md"], "domestic_page_ocr", tags, "domestic"),
        )
        doc_id = cur.lastrowid
        new_doc = True

    pages_inserted = 0
    for i, pr in enumerate(page_rows, 1):
        text = pr["text"]
        page_label = pr["label"]
        md_rel = pr["ocr_md"]
        md_abs = (ROOT / md_rel).resolve()
        md_sha = hashlib.sha256(md_abs.read_bytes()).hexdigest()
        page_url = f"file://{md_abs}#text"
        cur = conn.execute(
            "INSERT INTO pages (document_id, page_label, page_url, text) VALUES (?,?,?,?)",
            (doc_id, page_label, page_url, text),
        )
        pid = cur.lastrowid
        conn.execute(
            "INSERT INTO page_fts (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid, "DOMESTIC-PAGE", sid, title, page_label, tags, text),
        )
        conn.execute(
            "INSERT INTO page_fts_bigram (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid, "DOMESTIC-PAGE", sid, title, page_label, tags, bigramize(text)),
        )
        conn.execute(
            "INSERT INTO page_provenance (page_id, document_id, source_id, source_file, source_sha256, "
            "source_file_size, pdf_page_no, physical_page_no, printed_page, page_image_path, "
            "page_image_sha256, ocr_md_path, ocr_md_sha256, ocr_engine, ocr_model, ocr_mode, ocr_lines, "
            "ocr_mean_confidence, text_chars, citation_ready, needs_human_review, review_status, "
            "machine_review_note, human_review_note, period, year, event_tags, source_title, batch_id, "
            "created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,'review_only',NULL,NULL,?,?,?,?,?,?,?)",
            (pid, doc_id, sid, md_rel, md_sha, None, None, i, None, None,
             None, md_rel, md_sha, "paddleocr", "3.7.0", "real_page_ocr",
             None, None, len(text),
             None, None, tags, title, BATCH_ID, now, now),
        )
        pages_inserted += 1

    conn.commit()
    return {"doc_key": doc_key, "document_id": doc_id, "pages": pages_inserted, "new_doc": new_doc}


def ingest_items(conn: sqlite3.Connection, items: list[dict]) -> list[dict]:
    results = []
    for it in items:
        results.append(ingest_item(conn, it))
    return results
