#!/usr/bin/env python3
"""SAAC (中央档案馆) 60 个 OCR 候选的批量采集 + 入库。

流程:
1. 解析候选 evidence_locator, 转换详情页 URL (NN_NNN.html → content/NN/NN_NN.html)
2. 抓详情页 → 解析所有大图 (img/aNN/.../XX.jpg)
3. 下载大图 → data/domestic/raw/saac_scans/{sec_item}/XX.jpg
4. paddleocr 跑所有图片 → zhconv 转简体
5. 写入 documents + pages + page_fts + page_fts_bigram + page_provenance
6. 回填 domestic_candidates.ingested_document_id

入库模式与 lib_ingest.ingest_item 完全一致 (schema 5/6/16/31)。
doc_key 前缀: domestic-ocr/SAAC:{candidate_id}

支持:
  --limit N: 每批候选数 (默认 5)
  --offset M: 从第 M 个候选开始 (跳过已处理)
  --dry-run: 只读 manifest, 不下载不写库
  --resume: 跳过已 ingested 的候选 (默认就是 resume)

耗时估算: 60 候选 × ~100 张图 × 5-15 秒/张 OCR ≈ 5-30 分钟 (Mac M 系列 CPU)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/research_index.sqlite"
SCAN_DIR = ROOT / "data/domestic/raw/saac_scans"
PROGRESS = ROOT / "work/domestic/saac_ocr_progress.json"
MANIFEST = ROOT / "work/domestic/saac_ocr_manifest_v2.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
BATCH_ID = "saac-ocr-20260802"
SOURCE_ID = "saac-51koukou"
SOURCE_TITLE = "中央档案馆：从「五一口号」到开国大典档案文献专辑"
DOC_KEY_PREFIX = "domestic-ocr/SAAC:"
PLATFORM = "domestic"
PLATFORM_KIND = "DOMESTIC-PAGE"
SRC_KIND_TAG = "saac_page_ocr"

CJK_RE = re.compile(r"[\u3400-\u9fff]+")
OCR_CONF_MIN = 0.55


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch(url: str, timeout: int = 25) -> bytes | None:
    try:
        r = subprocess.run(
            ["curl", "-skL", "-A", UA,
             "--connect-timeout", "10", "--max-time", str(timeout), url],
            capture_output=True,
        )
        if r.returncode == 0 and r.stdout and b"404 Not Found" not in r.stdout[:300]:
            return r.stdout
        return None
    except Exception:
        return None


def old_to_new_url(old_url: str) -> str | None:
    """01_013.html -> content/01/01_13.html"""
    m = re.search(r"/(\d{2})_(\d{2,3})\.html", old_url)
    if not m:
        return None
    sec, item = m.group(1), m.group(2)
    return f"https://www.saac.gov.cn/daj/gqzt/content/{sec}/{sec}_{int(item):02d}.html"


def parse_image_urls(html: str) -> list[str]:
    imgs = re.findall(r'<img src="\.\./\.\./(img/a\d+/[^"]+\.jpg)"', html)
    return [i for i in imgs if not i.startswith("images")]


def bigramize(text: str) -> str:
    out: list[str] = []
    last = 0
    for m in CJK_RE.finditer(text):
        if m.start() > last:
            out.append(text[last:m.start()])
        seg = m.group(0)
        for i in range(len(seg) - 1):
            out.append(seg[i:i + 2])
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    return " ".join(p for p in out if p)


_ocr = None
def _get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(lang="ch")
    return _ocr


def ocr_image_text(path: Path) -> str:
    """OCR 跑一张图, 返回简体中文文本 (低置信度行过滤)."""
    import zhconv
    ocr = _get_ocr()
    res = ocr.predict(str(path))
    lines: list[str] = []
    if not res:
        return ""
    for r in res:
        rec_texts = r.get("rec_texts", [])
        rec_scores = r.get("rec_scores", [])
        for t, s in zip(rec_texts, rec_scores):
            if float(s) >= OCR_CONF_MIN and t and t.strip():
                lines.append(t.strip())
    full = "\n".join(lines)
    return zhconv.convert(full, "zh-cn")


def ensure_source(conn) -> int:
    existing = conn.execute("SELECT id FROM sources WHERE source_id=?", (SOURCE_ID,)).fetchone()
    if existing:
        return existing[0]
    cur = conn.execute(
        "INSERT INTO sources (source_type, source_id, title, origin_url, local_path) "
        "VALUES (?,?,?,?,?)",
        ("domestic_page_ocr", SOURCE_ID, SOURCE_TITLE,
         "https://www.saac.gov.cn/daj/gqzt/", None),
    )
    return cur.lastrowid


def _file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ingest_candidate(conn, cid: str, title: str, image_paths: list[Path], src_id: int) -> dict | None:
    """入库一个候选 → 1 document + N pages + FTS + provenance."""
    if not image_paths:
        return None
    page_texts: list[str] = []
    for img in image_paths:
        try:
            txt = ocr_image_text(img)
        except Exception as e:
            print(f"      OCR err {img.name}: {e}", file=sys.stderr)
            txt = ""
        page_texts.append(txt)

    # 至少必须有图片 (即使 OCR 失败也允许空文本, 用占位符入库)
    has_real_text = any(t.strip() for t in page_texts)
    if not has_real_text:
        return None  # 全部 OCR 无内容, 跳过

    now = now_iso()
    doc_key = f"{DOC_KEY_PREFIX}{cid}"

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

    # 文档 (幂等)
    existing_doc = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()
    if existing_doc:
        doc_id = existing_doc[0]
        old_pages = [r[0] for r in conn.execute("SELECT id FROM pages WHERE document_id=?", (doc_id,))]
        for pid in old_pages:
            conn.execute("DELETE FROM page_fts WHERE rowid=?", (pid,))
            conn.execute("DELETE FROM page_fts_bigram WHERE rowid=?", (pid,))
            conn.execute("DELETE FROM page_provenance WHERE page_id=?", (pid,))
        conn.execute("DELETE FROM pages WHERE document_id=?", (doc_id,))
        conn.execute(
            "UPDATE documents SET source_id=?, volume_id=?, volume_title=?, doc_id=?, title=?, "
            "date_guess=?, local_txt=?, hit_type=?, matched_terms=?, source_platform=? WHERE id=?",
            (src_id, PLATFORM_KIND, SOURCE_TITLE, SOURCE_ID, title, None,
             str(image_paths[0].relative_to(ROOT)), SRC_KIND_TAG, tags, PLATFORM, doc_id),
        )
        new_doc = False
    else:
        cur = conn.execute(
            "INSERT INTO documents (source_id, doc_key, volume_id, volume_title, doc_id, "
            "doc_number, title, date_guess, url, local_html, local_txt, hit_type, matched_terms, "
            "source_platform) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (src_id, doc_key, PLATFORM_KIND, SOURCE_TITLE, SOURCE_ID, None, title,
             None, None, None, str(image_paths[0].relative_to(ROOT)),
             SRC_KIND_TAG, tags, PLATFORM),
        )
        doc_id = cur.lastrowid
        new_doc = True

    n_pages = 0
    for i, (img, text) in enumerate(zip(image_paths, page_texts), start=1):
        page_label = f"page-{i:02d}"
        sha = _file_sha256(img)
        rel = str(img.relative_to(ROOT))
        page_url = f"file://{img.resolve()}"

        cur = conn.execute(
            "INSERT INTO pages (document_id, page_label, page_url, text) VALUES (?,?,?,?)",
            (doc_id, page_label, page_url, text),
        )
        pid = cur.lastrowid
        n_pages += 1

        conn.execute(
            "INSERT INTO page_fts (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid, PLATFORM_KIND, SOURCE_ID, title, page_label, tags, text),
        )
        conn.execute(
            "INSERT INTO page_fts_bigram (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid, PLATFORM_KIND, SOURCE_ID, title, page_label, tags, bigramize(text)),
        )

        try:
            file_size = img.stat().st_size
        except OSError:
            file_size = 0

        conn.execute(
            "INSERT INTO page_provenance (page_id, document_id, source_id, source_file, source_sha256, "
            "source_file_size, pdf_page_no, physical_page_no, printed_page, page_image_path, "
            "page_image_sha256, ocr_md_path, ocr_md_sha256, ocr_engine, ocr_model, ocr_mode, ocr_lines, "
            "ocr_mean_confidence, text_chars, citation_ready, needs_human_review, review_status, "
            "machine_review_note, human_review_note, period, year, event_tags, source_title, batch_id, "
            "created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,'review_only',NULL,NULL,?,?,?,?,?,?,?)",
            (pid, doc_id, SOURCE_ID, rel, sha, file_size, None, i, None,
             rel, sha, rel, sha, "paddleocr", "PP-OCRv6_medium", "real_page_ocr",
             sum(1 for ln in text.splitlines() if ln.strip()), None, len(text),
             "1941-1949", 1948, tags, SOURCE_TITLE, BATCH_ID, now, now),
        )

    # 回填候选 ingested_document_id
    conn.execute(
        "UPDATE domestic_candidates SET ingested_document_id=?, "
        "review_note=COALESCE(review_note||'；','')||? WHERE candidate_id=?",
        (doc_id, f"saac_ocr({BATCH_ID}) {now}", cid),
    )

    return {"document_id": doc_id, "pages": n_pages, "new_doc": new_doc}


def progress_load() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    return {"done": [], "errors": []}


def progress_save(p: dict) -> None:
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def process_one(conn, cand: dict, src_id: int) -> dict:
    cid = cand["candidate_id"]
    title = cand["title"]
    detail_url = cand["detail_url"]

    html_bytes = fetch(detail_url)
    if not html_bytes:
        return {"candidate_id": cid, "status": "detail_404"}
    html = html_bytes.decode("utf-8", errors="replace")
    img_rel = parse_image_urls(html)
    if not img_rel:
        return {"candidate_id": cid, "status": "no_image"}

    m_sec = re.search(r"content/(\d{2})/", detail_url)
    m_item = re.search(r"content/\d{2}/(\d{2})_(\d{2})\.html", detail_url)
    sec = m_sec.group(1) if m_sec else "00"
    item = f"{m_item.group(1)}-{m_item.group(2)}" if m_item else "00-00"
    save_dir = SCAN_DIR / f"sec{sec}_{item}"
    save_dir.mkdir(parents=True, exist_ok=True)

    local_imgs: list[Path] = []
    for ip in img_rel:
        # ip 形如 img/a02/02-04/01.jpg
        fname = ip.split("/")[-1]
        full_url = f"https://www.saac.gov.cn/daj/gqzt/{ip}"
        local_fp = save_dir / fname
        if not local_fp.exists():
            data = fetch(full_url)
            if data:
                local_fp.write_bytes(data)
        if local_fp.exists() and local_fp.stat().st_size > 1024:
            local_imgs.append(local_fp)

    if not local_imgs:
        return {"candidate_id": cid, "status": "image_dl_failed", "imgs_found": len(img_rel)}

    res = ingest_candidate(conn, cid, title, local_imgs, src_id)
    if not res:
        return {"candidate_id": cid, "status": "ocr_empty", "imgs": len(local_imgs)}
    return {"candidate_id": cid, "status": "ok", **res, "imgs": len(local_imgs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"Manifest missing: {MANIFEST}", file=sys.stderr)
        sys.exit(2)
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cands = [c for c in m["candidates"] if not c.get("note")]
    print(f"Total non-album SAAC candidates: {len(cands)}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # 跳过已入库
    done_ids = {r["candidate_id"] for r in conn.execute(
        "SELECT candidate_id FROM domestic_candidates "
        "WHERE candidate_id LIKE 'domestic:SAAC:%' AND ingested_document_id IS NOT NULL"
    )}
    print(f"Already ingested: {len(done_ids)}")
    remaining = [c for c in cands if c["candidate_id"] not in done_ids]
    print(f"Remaining to process: {len(remaining)}")

    if args.offset >= len(remaining):
        print("offset beyond remaining; nothing to do")
        return
    batch = remaining[args.offset:args.offset + args.limit]
    print(f"\nBatch: {len(batch)} candidates (offset {args.offset})")

    if args.dry_run:
        for c in batch[:6]:
            print(f"  would: {c['candidate_id']} -> {c['detail_url']}")
        print(f"  ... ({len(batch)} total in batch)")
        return

    progress = progress_load()
    src_id = ensure_source(conn)
    print(f"Source row id: {src_id}\n")

    batch_done: list[dict] = []
    batch_err: list[dict] = []
    t_start = time.time()

    for i, cand in enumerate(batch, 1):
        t0 = time.time()
        print(f"[{i}/{len(batch)}] {cand['candidate_id']} ...", flush=True)
        try:
            r = process_one(conn, cand, src_id)
            elapsed = time.time() - t0
            if r.get("status") == "ok":
                conn.commit()
                print(f"     ok ({elapsed:.1f}s): doc={r['document_id']} pages={r['pages']} imgs={r.get('imgs',0)}")
                batch_done.append(r)
                progress["done"].append({**r, "ts": now_iso(), "elapsed_s": round(elapsed, 1)})
            else:
                print(f"     {r['status']} ({elapsed:.1f}s)")
                batch_err.append(r)
                progress["errors"].append({**r, "ts": now_iso(), "elapsed_s": round(elapsed, 1)})
            progress_save(progress)
        except Exception as e:
            elapsed = time.time() - t0
            print(f"     EXCEPTION ({elapsed:.1f}s): {e}", file=sys.stderr)
            conn.rollback()
            batch_err.append({"candidate_id": cand["candidate_id"], "status": "exception", "error": str(e)})
            progress["errors"].append({"candidate_id": cand["candidate_id"], "err": str(e), "ts": now_iso()})
            progress_save(progress)

    total_elapsed = time.time() - t_start
    print(f"\n=== Batch summary ===")
    print(f"  OK   : {len(batch_done)}")
    print(f"  ERR  : {len(batch_err)}")
    print(f"  Total: {total_elapsed:.1f}s ({total_elapsed/max(1,len(batch)):.1f}s/candidate)")

    if batch_err:
        print(f"\n  Errors:")
        for e in batch_err:
            print(f"    - {e.get('candidate_id')}: {e.get('status')} {e.get('error','')}")


if __name__ == "__main__":
    main()
