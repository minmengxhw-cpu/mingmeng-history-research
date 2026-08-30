#!/usr/bin/env python3
"""Finalize remaining 24 html candidates:

Strategy:
- 14 candidates whose source_url fetched 200 → process (download + extract + ingest)
- 4 candidates with HTTP 404/521/SSL errors → mark lead_only
- Some may have been collected already by loop worker; skip those.

Uses import_domestic_web_batch.py importer semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/research_index.sqlite"
RAW_DIR = ROOT / "data/domestic/raw/public_sources"
TXT_DIR = ROOT / "work/domestic/public_web_extracted_20260728"
MANIFEST = ROOT / "work/domestic/S3_HTML_COLLECTION_QUEUE.json"
BATCH_ID = "html-finalize-20260802"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0"
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_bytes(url, timeout=15):
    r = subprocess.run(
        ["curl", "-skL", "-A", UA, "--connect-timeout", "10", "--max-time", str(timeout), url],
        capture_output=True,
    )
    if r.returncode == 0 and r.stdout:
        return r.returncode, r.stdout
    return r.returncode, r.stdout


def http_status(url, timeout=12):
    """Return (code, body) using HEAD-like probe."""
    r = subprocess.run(
        ["curl", "-skL", "-A", UA, "-o", "/dev/null",
         "-w", "%{http_code}", "--connect-timeout", "8", "--max-time", str(timeout), url],
        capture_output=True,
    )
    try:
        return int(r.stdout.decode().strip())
    except Exception:
        return -1


def html_to_text(html: bytes) -> str:
    """Simple HTML to plain text."""
    s = html.decode("utf-8", errors="replace")
    # Remove script/style
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S | re.I)
    # Drop tags
    s = re.sub(r"<[^>]+>", " ", s)
    # Unescape
    s = unescape(s)
    # Whitespace
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n[ \t]+", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def get_next_dl_id(conn) -> str:
    """Find next unused DL-YYYYMMDD-NNN id."""
    n = 1
    today = datetime.now().strftime("%Y%m%d")
    while True:
        did = f"DL-{today}-{n:03d}"
        existing = conn.execute(
            "SELECT id FROM sources WHERE source_id=?", (f"domestic-web:{did}",)
        ).fetchone()
        if not existing:
            return did
        n += 1


def ingest_one(conn, cid: str, title: str, url: str, html: bytes) -> dict:
    """One candidate: download + extract + ingest (documents/pages/provenance)."""
    dl_id = get_next_dl_id(conn)
    text = html_to_text(html)
    if len(text) < 50:
        return {"status": "no_content", "chars": len(text)}

    # Save files
    slug = re.sub(r"[^a-z0-9]+", "_", cid.lower()).strip("_")[:60]
    raw_fp = RAW_DIR / f"{dl_id}_{slug}.html"
    raw_fp.write_bytes(html)
    txt_fp = TXT_DIR / f"{dl_id}.txt"
    txt_fp.write_text(text, encoding="utf-8")

    sha = hashlib.sha256(html).hexdigest()
    src_id = f"domestic-web:{dl_id}"

    # sources
    conn.execute(
        "INSERT INTO sources (source_type, source_id, title, origin_url, local_path) VALUES (?,?,?,?,?)",
        ("domestic_public_web", src_id, title, url, str(raw_fp.relative_to(ROOT))),
    )

    # documents (idempotent)
    doc_key = f"domestic-web/{dl_id}"
    existing_doc = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()
    tags = ",".join([
        "国内盟史", "公开网页",
        "evidence_level=secondary",
        "source_kind=public_web",
        "citation_ready=false",
        "needs_human_review=true",
        f"batch={BATCH_ID}",
        f"candidate_id={cid}",
    ])
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
            "date_guess=?, url=?, local_html=?, local_txt=?, hit_type=?, matched_terms=?, source_platform=? WHERE id=?",
            (conn.execute("SELECT id FROM sources WHERE source_id=?", (src_id,)).fetchone()[0],
             "MMHIST-WEB", "国内公开网页资料", dl_id, title, None, url,
             str(raw_fp.relative_to(ROOT)), str(txt_fp.relative_to(ROOT)),
             "domestic_public_web", tags, "domestic", doc_id),
        )
    else:
        doc_id = conn.execute(
            "INSERT INTO documents (source_id, doc_key, volume_id, volume_title, doc_id, "
            "doc_number, title, date_guess, url, local_html, local_txt, hit_type, matched_terms, "
            "source_platform) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (conn.execute("SELECT id FROM sources WHERE source_id=?", (src_id,)).fetchone()[0],
             doc_key, "MMHIST-WEB", "国内公开网页资料", dl_id, None, title,
             None, url, str(raw_fp.relative_to(ROOT)), str(txt_fp.relative_to(ROOT)),
             "domestic_public_web", tags, "domestic"),
        ).lastrowid

    pid = conn.execute(
        "INSERT INTO pages (document_id, page_label, page_url, text) VALUES (?,?,?,?)",
        (doc_id, "full-text", url, text),
    ).lastrowid

    # FTS
    conn.execute(
        "INSERT INTO page_fts (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
        "VALUES (?,?,?,?,?,?,?)",
        (pid, "MMHIST-WEB", dl_id, title, "full-text", tags, text),
    )
    # bigram FTS
    CJK = re.compile(r"[\u3400-\u9fff]+")
    out = []
    last = 0
    for m in CJK.finditer(text):
        if m.start() > last:
            out.append(text[last:m.start()])
        seg = m.group(0)
        for i in range(len(seg) - 1):
            out.append(seg[i:i + 2])
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    bg = " ".join(p for p in out if p)
    conn.execute(
        "INSERT INTO page_fts_bigram (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
        "VALUES (?,?,?,?,?,?,?)",
        (pid, "MMHIST-WEB", dl_id, title, "full-text", tags, bg),
    )

    # provenance
    conn.execute(
        "INSERT INTO page_provenance (page_id, document_id, source_id, source_file, source_sha256, "
        "source_file_size, pdf_page_no, physical_page_no, printed_page, page_image_path, "
        "page_image_sha256, ocr_md_path, ocr_md_sha256, ocr_engine, ocr_model, ocr_mode, ocr_lines, "
        "ocr_mean_confidence, text_chars, citation_ready, needs_human_review, review_status, "
        "machine_review_note, human_review_note, period, year, event_tags, source_title, batch_id, "
        "created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,'review_only',NULL,NULL,?,?,?,?,?,?,?)",
        (pid, doc_id, src_id, str(raw_fp.relative_to(ROOT)), sha, len(html), None, 1, None,
         None, None, None, None, None, None, None, None, None, len(text),
         "1941-1949", 1948, tags, title, BATCH_ID, NOW, NOW),
    )

    # 回填 ingest
    conn.execute(
        "UPDATE domestic_candidates SET ingested_document_id=?, "
        "review_note=COALESCE(review_note||'；','')||? WHERE candidate_id=?",
        (doc_id, f"html-finalize({BATCH_ID}) {NOW}", cid),
    )
    return {"status": "ok", "document_id": doc_id, "chars": len(text), "download_id": dl_id}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT candidate_id, title, source_url FROM domestic_candidates
        WHERE check_outcome='pass' AND online_availability='full_item_online'
        AND ingested_document_id IS NULL
        AND source_url NOT LIKE '%saac%' AND source_url NOT LIKE '%upload.wikimedia%'
        AND source_url NOT LIKE '%wiki/File:%'
        ORDER BY candidate_id
    """).fetchall()
    print(f"Remaining HTML candidates: {len(rows)}")

    print("\n=== Probe HTTP ===")
    accessible: list[tuple] = []
    blocked: list[tuple] = []
    for r in rows:
        code = http_status(r["source_url"])
        if code == 200:
            accessible.append(r)
            print(f"  200  {r['candidate_id'][:42]:42s}  {r['source_url'][:60]}")
        else:
            blocked.append((r, code))
            print(f"  {code:4d} {r['candidate_id'][:42]:42s}  {r['source_url'][:60]}")

    print(f"\nAccessible: {len(accessible)}, Blocked: {len(blocked)}")

    if args.dry_run:
        print(f"\nWould ingest {len(accessible)} accessible; would mark lead_only {len(blocked)} blocked.")
        return

    # Process accessible
    print("\n=== Ingesting accessible ===")
    ok_count = 0
    for r in accessible:
        rc, html = fetch_bytes(r["source_url"])
        if rc != 0 or not html or b"404" in html[:300] or b"502" in html[:300]:
            print(f"  fetch fail: {r['candidate_id']}")
            blocked.append((r, "fetch_fail"))
            continue
        try:
            res = ingest_one(conn, r["candidate_id"], r["title"], r["source_url"], html)
            conn.commit()
            if res["status"] == "ok":
                ok_count += 1
                print(f"  ok  {r['candidate_id'][:42]:42s} doc={res['document_id']} chars={res['chars']}")
            else:
                print(f"  {res['status']}  {r['candidate_id'][:42]:42s} chars={res['chars']}")
                blocked.append((r, res["status"]))
        except Exception as e:
            conn.rollback()
            print(f"  EXC  {r['candidate_id']}: {e}", file=sys.stderr)
            blocked.append((r, "exception"))

    # Mark blocked as lead_only
    print("\n=== Demoting blocked → lead_only ===")
    demote_count = 0
    for r, code in blocked:
        conn.execute(
            "UPDATE domestic_candidates SET check_outcome='lead_only', "
            "review_note=COALESCE(review_note||'；','')||? "
            "WHERE candidate_id=? AND ingested_document_id IS NULL",
            (f"网页 2026-08-02 不可采 (HTTP {code}) {NOW}", r["candidate_id"]),
        )
        demote_count += 1
    conn.commit()
    print(f"  demoted: {demote_count}")

    # Final stats
    final = conn.execute("""
        SELECT
          SUM(CASE WHEN ingested_document_id IS NOT NULL THEN 1 ELSE 0 END) as ingested,
          SUM(CASE WHEN check_outcome='lead_only' THEN 1 ELSE 0 END) as lead_only,
          SUM(CASE WHEN check_outcome='pass' AND ingested_document_id IS NULL THEN 1 ELSE 0 END) as remain
        FROM domestic_candidates
        WHERE check_outcome IN ('pass', 'lead_only')
    """).fetchone()
    print(f"\nFinal pass+lead_only: ingested={final[0]}, lead_only={final[1]}, remaining pass={final[2]}")
    print(f"Integrity: {conn.execute('PRAGMA integrity_check').fetchone()[0]}")


if __name__ == "__main__":
    main()
