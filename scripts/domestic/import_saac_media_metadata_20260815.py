#!/usr/bin/env python3
"""Register one official SAAC media item as a review-only research record.

The National Archives Administration item for Zhang Lan's 1949-09-21 speech
publishes an official video entry, not a page-image scan or a public transcript.
This importer therefore indexes the local video and its official item page as
media metadata only.  It deliberately does *not* create a citable transcript.

Safety:
* default mode is a read-only dry run;
* ``--apply`` requires the exact current database SHA and a new backup path;
* the local media file must match the expected SHA256;
* only one exact candidate/document pair may be changed;
* existing files and documents are never deleted or overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
CANDIDATE_ID = "domestic:SAAC:1949-09-21-05"
DOC_KEY = "domestic-media/SAAC:domestic:SAAC:1949-09-21-05"
SOURCE_ID = "saac-51koukou-media"
SOURCE_TITLE = "国家档案局：张澜在中国人民政治协商会议第一届全体会议上的讲话（官方视频）"
ITEM_URL = "https://www.saac.gov.cn/daj/gqzt/content/05/05_11.html"
MEDIA_URL = "https://www.saac.gov.cn/daj/gqzt/sp/5-11.mp4"
DEFAULT_MEDIA_REL = (
    "data/domestic/raw/saac_media/SAAC-1949-09-21-zhanglan-5-11.mp4"
)
EXPECTED_MEDIA_SHA256 = "474c4e44f04b031c99b3e95cb2ff71d2f964bc75b5dae39c88461d4c269f33f7"
BATCH_ID = "saac-media-metadata-20260815"


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
        raise ValueError(f"expected a data/research_index.sqlite path, got {resolved}")
    return resolved.parent.parent


def probe_media(path: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size,format_name:stream=index,codec_name,codec_type,width,height,channels,sample_rate",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"ffprobe failed for {path}: {exc}") from exc
    return json.loads(result.stdout)


def metadata_text(media_rel: str, media_sha: str, media_size: int, probe: dict[str, Any]) -> str:
    fmt = probe.get("format") or {}
    streams = probe.get("streams") or []
    stream_summary = []
    for stream in streams:
        kind = stream.get("codec_type")
        codec = stream.get("codec_name")
        if kind == "video":
            stream_summary.append(
                f"video/{codec} {stream.get('width')}x{stream.get('height')}"
            )
        elif kind == "audio":
            stream_summary.append(
                f"audio/{codec} {stream.get('sample_rate')}Hz/{stream.get('channels')}ch"
            )
        else:
            stream_summary.append(f"{kind}/{codec}")
    return "\n".join(
        [
            "【资料状态】官方媒体原件已保存；正文/逐字稿尚未取得。",
            "【证据等级】L1 条目级官方媒体入口；本页不是逐字引文页。",
            "【题名】中国民主同盟主席张澜在中国人民政治协商会议第一届全体会议上的讲话",
            "【形成者】张澜；中国民主同盟",
            "【日期】1949-09-21",
            "【官方条目页】" + ITEM_URL,
            "【官方媒体地址】" + MEDIA_URL,
            "【本地原件】" + media_rel,
            f"【本地 SHA256】{media_sha}",
            f"【本地大小】{media_size} bytes",
            f"【媒体技术信息】{fmt.get('format_name', 'unknown')}；时长 {fmt.get('duration', 'unknown')} 秒；" + "；".join(stream_summary),
            "【使用边界】可用于来源发现、媒体观看、题名/日期/形成者核对；未完成人工核听或官方逐字稿核对前，不得把自动转写或本页元数据当作正式引文。",
        ]
    )


def load_candidate(conn: sqlite3.Connection, *, require_unlinked: bool = True) -> sqlite3.Row:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM domestic_candidates WHERE candidate_id=?", (CANDIDATE_ID,)
    ).fetchone()
    if row is None:
        raise RuntimeError(f"candidate not found: {CANDIDATE_ID}")
    if row["review_status"] != "accepted" or row["check_outcome"] != "pass":
        raise RuntimeError("candidate must remain accepted/pass before media import")
    if require_unlinked and row["ingested_document_id"] is not None:
        raise RuntimeError(
            f"candidate already linked to document {row['ingested_document_id']}"
        )
    return row


def prepare(db: Path, media: Path) -> dict[str, Any]:
    if not media.is_file():
        raise FileNotFoundError(f"media file missing: {media}")
    media_sha = sha256(media)
    if media_sha != EXPECTED_MEDIA_SHA256:
        raise RuntimeError(
            f"media SHA mismatch: got {media_sha}, expected {EXPECTED_MEDIA_SHA256}"
        )
    root = project_root(db)
    try:
        media_rel = str(media.resolve().relative_to(root))
    except ValueError as exc:
        raise RuntimeError(f"media must be under formal project root {root}: {media}") from exc
    probe = probe_media(media)
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        existing = conn.execute(
            "SELECT id, doc_key FROM documents WHERE doc_key=?", (DOC_KEY,)
        ).fetchone()
        row = load_candidate(conn, require_unlinked=False)
        linked_id = row["ingested_document_id"]
        if linked_id is not None and (existing is None or int(existing[0]) != int(linked_id)):
            raise RuntimeError(
                f"candidate is linked to {linked_id}, but expected document {DOC_KEY} is absent or different"
            )
        if linked_id is not None:
            return {
                "status": "ALREADY_APPLIED",
                "candidate_id": CANDIDATE_ID,
                "candidate_title": row["title"],
                "candidate_source_url": row["source_url"],
                "document_key": DOC_KEY,
                "source_id": SOURCE_ID,
                "item_url": ITEM_URL,
                "media_url": MEDIA_URL,
                "formal_db": str(db.resolve()),
                "formal_db_sha256": db_sha256(db),
                "media_file": media_rel,
                "media_sha256": media_sha,
                "media_size": media.stat().st_size,
                "media_probe": probe,
                "existing_document": dict(existing) if existing else None,
                "citation_ready_pages": 0,
                "review_only_pages": 1,
                "body_transcript_status": "not_acquired",
                "evidence_level": "L1",
            }
    return {
        "status": "READY",
        "candidate_id": CANDIDATE_ID,
        "candidate_title": row["title"],
        "candidate_source_url": row["source_url"],
        "document_key": DOC_KEY,
        "source_id": SOURCE_ID,
        "item_url": ITEM_URL,
        "media_url": MEDIA_URL,
        "formal_db": str(db.resolve()),
        "formal_db_sha256": db_sha256(db),
        "media_file": media_rel,
        "media_sha256": media_sha,
        "media_size": media.stat().st_size,
        "media_probe": probe,
        "existing_document": dict(existing) if existing else None,
        "citation_ready_pages": 0,
        "review_only_pages": 1,
        "body_transcript_status": "not_acquired",
        "evidence_level": "L1",
    }


def apply_import(db: Path, media: Path, backup: Path, expected_db_sha: str) -> dict[str, Any]:
    actual_db = db.resolve()
    before_sha = db_sha256(actual_db)
    if before_sha != expected_db_sha:
        raise RuntimeError(f"database SHA mismatch: got {before_sha}, expected {expected_db_sha}")
    if backup.exists():
        raise FileExistsError(f"refusing to overwrite existing backup: {backup}")
    prepared = prepare(db, media)
    if prepared.get("status") != "READY":
        raise RuntimeError(f"refusing to apply an already-linked media record: {prepared.get('status')}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    if db_sha256(backup) != before_sha:
        raise RuntimeError("formal DB backup SHA mismatch")

    root = project_root(db)
    media_rel = prepared["media_file"]
    media_sha = prepared["media_sha256"]
    media_size = prepared["media_size"]
    probe = prepared["media_probe"]
    text = metadata_text(media_rel, media_sha, media_size, probe)
    tags = ";".join(
        [
            "official_media",
            "media_original=official_video",
            "body_transcript_status=not_acquired",
            "evidence_level=L1",
            "citation_ready=false",
            "needs_human_review=true",
            "review_status=review_only",
            f"batch={BATCH_ID}",
            f"candidate_id={CANDIDATE_ID}",
        ]
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        candidate = load_candidate(conn, require_unlinked=True)
        conn.execute(
            """INSERT INTO sources(source_type,source_id,title,origin_url,local_path)
               VALUES(?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET
                 title=excluded.title, origin_url=excluded.origin_url, local_path=excluded.local_path""",
            ("domestic_official_media", SOURCE_ID, SOURCE_TITLE, ITEM_URL, media_rel),
        )
        source_db_id = conn.execute(
            "SELECT id FROM sources WHERE source_id=?", (SOURCE_ID,)
        ).fetchone()[0]
        existing = conn.execute("SELECT id FROM documents WHERE doc_key=?", (DOC_KEY,)).fetchone()
        if existing:
            raise RuntimeError(f"document key unexpectedly already exists: {DOC_KEY}")
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
                "中国民主同盟主席张澜在中国人民政治协商会议第一届全体会议上的讲话（1949年9月21日）",
                "1949-09-21",
                ITEM_URL,
                media_rel,
                "saac_official_media",
                tags,
                "domestic",
                CANDIDATE_ID,
            ),
        ).lastrowid
        page_id = conn.execute(
            "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
            (document_id, "media-recording", ITEM_URL, text),
        ).lastrowid
        conn.execute(
            "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
            (page_id, "DOMESTIC-SAAC-1949-PCC", CANDIDATE_ID, SOURCE_TITLE, "media-recording", tags, text),
        )
        cjk = "".join(ch if "\u3400" <= ch <= "\u9fff" else " " for ch in text)
        bigrams = " ".join(cjk[i : i + 2] for i in range(len(cjk) - 1) if cjk[i] != " " and cjk[i + 1] != " ")
        conn.execute(
            "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
            (page_id, "DOMESTIC-SAAC-1949-PCC", CANDIDATE_ID, SOURCE_TITLE, "media-recording", tags, bigrams),
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
                media_rel,
                media_sha,
                media_size,
                None,
                1,
                None,
                None,
                None,
                None,
                None,
                "not_applicable",
                "official_saac_video",
                "media_metadata_only",
                0,
                None,
                len(text),
                0,
                1,
                "review_only",
                "官方条目页挂载视频；本页仅为媒体元数据和检索定位，未取得逐字稿，不能直接作正式引文。",
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
                   evidence_type='digital_media',
                   evidence_locator='官方条目页标题、日期和视频入口',
                   review_note=COALESCE(review_note||'；','')||?
               WHERE candidate_id=? AND ingested_document_id IS NULL""",
            (document_id, f"official_media_registered({BATCH_ID}) {now}", CANDIDATE_ID),
        )
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        page_fts_missing = conn.execute(
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE p.id=? AND f.rowid IS NULL",
            (page_id,),
        ).fetchone()[0]
        provenance_count = conn.execute(
            "SELECT COUNT(*) FROM page_provenance WHERE page_id=?", (page_id,)
        ).fetchone()[0]
        linked_candidate = conn.execute(
            "SELECT ingested_document_id FROM domestic_candidates WHERE candidate_id=?",
            (CANDIDATE_ID,),
        ).fetchone()[0]
    after_sha = db_sha256(actual_db)
    return {
        "status": "APPLIED",
        "document_id": document_id,
        "page_id": page_id,
        "candidate_id": CANDIDATE_ID,
        "media_file": media_rel,
        "media_sha256": media_sha,
        "before_db_sha256": before_sha,
        "after_db_sha256": after_sha,
        "backup": str(backup),
        "integrity_check": integrity,
        "foreign_key_violations": fk,
        "page_fts_missing": page_fts_missing,
        "page_provenance_count": provenance_count,
        "linked_candidate_document_id": linked_candidate,
        "citation_ready_pages": 0,
        "review_only_pages": 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--media", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    if args.apply == args.dry_run:
        parser.error("choose exactly one of --dry-run or --apply")
    db = args.db.expanduser().resolve()
    root = project_root(db)
    media = (args.media.expanduser() if args.media else root / DEFAULT_MEDIA_REL).resolve()
    prepared = prepare(db, media)
    if args.dry_run:
        print(json.dumps({"status": "PASS", **prepared}, ensure_ascii=False, indent=2))
        return 0
    if not args.expected_db_sha:
        parser.error("--apply requires --expected-db-sha")
    if not args.backup:
        parser.error("--apply requires --backup")
    result = apply_import(db, media, args.backup.expanduser().resolve(), args.expected_db_sha)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
