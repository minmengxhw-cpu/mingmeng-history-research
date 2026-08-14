#!/usr/bin/env python3
"""将 1941 成立宣言的公开转录快照以受限层级接入正式检索库。

这个批次只处理已有的电子文本快照，不 OCR、不复制原刊、不把转录升级为
一手原件。默认 dry-run；``--apply`` 时只新增 source/document/page/provenance
并建立候选反向链接，不删除或重写任何既有记录。
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

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
SOURCE_REL = (
    "data/domestic/official_research_public_20260730/html/"
    "GDC2-0087_中国民主政团同盟成立宣言_025.txt"
)
CANDIDATE_ID = "domestic:WS:democratic-league-declaration-1941"
OWNER_CANDIDATE_ID = "domestic:NLC:minmeng-wenxian-1946-formation-declaration"
SOURCE_ID = "domestic-public-transcription:GDC2-0087"
DOC_KEY = "domestic-text/WS:formation-declaration-1941"
SOURCE_URL = "https://zh.wikisource.org/zh-hans/中国民主政团同盟成立宣言"
TITLE = "中国民主政团同盟成立宣言（公开转录快照）"
BATCH_ID = "domestic-1941-transcription-review-20260815"
CJK_RE = re.compile(r"[\u3400-\u9fff]+")


def bigramize(text: str) -> str:
    """为中文 FTS 生成二字切分；避免把 OCR 依赖带入元数据导入器。"""
    out: list[str] = []
    last = 0
    for match in CJK_RE.finditer(text):
        if match.start() > last:
            out.append(text[last : match.start()])
        segment = match.group(0)
        out.extend(segment[index : index + 2] for index in range(len(segment) - 1))
        last = match.end()
    if last < len(text):
        out.append(text[last:])
    return " ".join(part for part in out if part)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_root_for(db_path: Path) -> Path:
    resolved = db_path.expanduser().resolve()
    return resolved.parent.parent


def extract_body(raw: str) -> str:
    start_marker = "中国民主政团同盟今次成立"
    end_marker = "本作品现时在"
    start = raw.find(start_marker)
    end = raw.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0 or end <= start:
        raise ValueError("无法从公开转录快照确定正文边界")
    body = " ".join(raw[start:end].split())
    if len(body) < 500:
        raise ValueError(f"正文过短，拒绝入库: {len(body)} chars")
    return body


def load_input(db_path: Path) -> dict[str, object]:
    project_root = project_root_for(db_path)
    source = (project_root / SOURCE_REL).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if not str(source).startswith(str(project_root) + "/"):
        raise ValueError("source path escaped project root")
    raw = source.read_text(encoding="utf-8", errors="replace")
    body = extract_body(raw)
    return {
        "project_root": project_root,
        "source": source,
        "source_rel": SOURCE_REL,
        "source_sha256": sha256(source),
        "source_size": source.stat().st_size,
        "body": body,
        "body_chars": len(body),
    }


def inspect(conn: sqlite3.Connection) -> dict[str, object]:
    candidate = conn.execute(
        "SELECT candidate_id, ingested_document_id, authenticity_level_accepted, "
        "review_status FROM domestic_candidates WHERE candidate_id=?",
        (CANDIDATE_ID,),
    ).fetchone()
    existing = conn.execute(
        "SELECT id, ingested_candidate_id FROM documents WHERE doc_key=?",
        (DOC_KEY,),
    ).fetchone()
    stale_link = conn.execute(
        "SELECT d.id, d.doc_key, d.ingested_candidate_id "
        "FROM domestic_candidates c JOIN documents d "
        "ON d.id=c.ingested_document_id WHERE c.candidate_id=?",
        (CANDIDATE_ID,),
    ).fetchone()
    owner = conn.execute(
        "SELECT candidate_id, ingested_document_id FROM domestic_candidates WHERE candidate_id=?",
        (OWNER_CANDIDATE_ID,),
    ).fetchone()
    return {
        "candidate_exists": candidate is not None,
        "candidate_link": candidate[1] if candidate else None,
        "candidate_level": candidate[2] if candidate else None,
        "candidate_review_status": candidate[3] if candidate else None,
        "document_exists": existing is not None,
        "existing_document_id": existing[0] if existing else None,
        "existing_document_candidate": existing[1] if existing else None,
        "stale_link_document_id": stale_link[0] if stale_link else None,
        "stale_link_doc_key": stale_link[1] if stale_link else None,
        "stale_link_document_candidate": stale_link[2] if stale_link else None,
        "owner_candidate_exists": owner is not None,
        "owner_candidate_document_id": owner[1] if owner else None,
    }


def validate_preconditions(state: dict[str, object]) -> None:
    if not state["candidate_exists"]:
        raise ValueError(f"candidate missing: {CANDIDATE_ID}")
    if not state["owner_candidate_exists"]:
        raise ValueError(f"owner candidate missing: {OWNER_CANDIDATE_ID}")
    if state["document_exists"]:
        raise ValueError(f"document key already exists: {DOC_KEY}")
    if state["candidate_link"] not in (None, ""):
        expected_stale = (
            state["candidate_link"] == state["stale_link_document_id"]
            and state["stale_link_document_candidate"] == CANDIDATE_ID
            and state["owner_candidate_document_id"] == state["stale_link_document_id"]
        )
        if not expected_stale:
            raise ValueError(f"candidate already linked to unexpected document: {state}")


def apply_import(
    db_path: Path,
    input_data: dict[str, object],
    backup: Path,
    state: dict[str, object],
) -> dict[str, object]:
    if backup.exists():
        raise FileExistsError(f"refusing to overwrite existing backup: {backup}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path.resolve(), backup)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_sha = str(input_data["source_sha256"])
    source_size = int(input_data["source_size"])
    source_rel = str(input_data["source_rel"])
    body = str(input_data["body"])
    tags = ";".join(
        (
            "event=domestic-1941-formation",
            "source_layer=later_transcription",
            "source_kind=public_transcription",
            "original_image=false",
            "citation_ready=false",
            "needs_human_review=true",
            f"batch={BATCH_ID}",
        )
    )
    with sqlite3.connect(db_path.resolve()) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        current_state = inspect(conn)
        validate_preconditions(current_state)
        conn.execute(
            "INSERT INTO sources(source_type,source_id,title,origin_url,local_path) "
            "VALUES(?,?,?,?,?)",
            ("domestic_public_transcription", SOURCE_ID, TITLE, SOURCE_URL, source_rel),
        )
        source_db_id = conn.execute(
            "SELECT id FROM sources WHERE source_id=?", (SOURCE_ID,)
        ).fetchone()[0]
        document_id = conn.execute(
            "INSERT INTO documents(source_id,doc_key,volume_id,volume_title,doc_id,title,"
            "date_guess,url,local_txt,hit_type,matched_terms,source_platform,"
            "ingested_candidate_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                source_db_id,
                DOC_KEY,
                "DOMESTIC-1941-TRANSCRIPTION",
                "1941 民盟成立文献公开转录",
                SOURCE_ID,
                TITLE,
                "1941-10-10",
                SOURCE_URL,
                source_rel,
                "domestic_public_transcription",
                tags,
                "domestic",
                CANDIDATE_ID,
            ),
        ).lastrowid
        page_id = conn.execute(
            "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
            (document_id, "electronic-text", SOURCE_URL, body),
        ).lastrowid
        conn.execute(
            "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) "
            "VALUES(?,?,?,?,?,?,?)",
            (page_id, "DOMESTIC-1941-TRANSCRIPTION", SOURCE_ID, TITLE, "electronic-text", tags, body),
        )
        conn.execute(
            "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) "
            "VALUES(?,?,?,?,?,?,?)",
            (
                page_id,
                "DOMESTIC-1941-TRANSCRIPTION",
                SOURCE_ID,
                TITLE,
                "electronic-text",
                tags,
                bigramize(body),
            ),
        )
        conn.execute(
            "INSERT INTO page_provenance(page_id,document_id,source_id,source_file,source_sha256,"
            "source_file_size,pdf_page_no,physical_page_no,printed_page,page_image_path,"
            "page_image_sha256,ocr_md_path,ocr_md_sha256,ocr_engine,ocr_model,ocr_mode,"
            "ocr_lines,ocr_mean_confidence,text_chars,citation_ready,needs_human_review,"
            "review_status,machine_review_note,human_review_note,period,year,event_tags,"
            "source_title,batch_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                page_id,
                document_id,
                SOURCE_ID,
                source_rel,
                source_sha,
                source_size,
                None,
                1,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                "electronic_text_snapshot",
                None,
                None,
                len(body),
                0,
                1,
                "review_only",
                "Wikisource公开转录快照；用于检索和版本追索，不是1941年《光明報》原刊影像；正文未作原刊逐字互校。",
                None,
                "1941",
                1941,
                tags,
                TITLE,
                BATCH_ID,
                now,
                now,
            ),
        )
        if state["stale_link_document_id"]:
            conn.execute(
                "UPDATE documents SET ingested_candidate_id=? WHERE id=?",
                (OWNER_CANDIDATE_ID, state["stale_link_document_id"]),
            )
        conn.execute(
            "UPDATE domestic_candidates SET ingested_document_id=? WHERE candidate_id=?",
            (document_id, CANDIDATE_ID),
        )
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        pages_without_fts = conn.execute(
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL"
        ).fetchone()[0]
        fts_without_pages = conn.execute(
            "SELECT COUNT(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL"
        ).fetchone()[0]
        result = {
            "document_id": document_id,
            "page_id": page_id,
            "candidate_id": CANDIDATE_ID,
            "rebound_existing_document_id": state["stale_link_document_id"],
            "rebound_existing_document_from": CANDIDATE_ID if state["stale_link_document_id"] else None,
            "rebound_existing_document_to": OWNER_CANDIDATE_ID if state["stale_link_document_id"] else None,
            "source_file": source_rel,
            "source_sha256": source_sha,
            "source_size": source_size,
            "text_chars": len(body),
            "citation_ready": False,
            "review_status": "review_only",
            "integrity_check": integrity,
            "foreign_key_violations": fk,
            "pages_without_fts": pages_without_fts,
            "fts_without_pages": fts_without_pages,
            "backup": str(backup),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    db_path = args.formal_db.expanduser().resolve()
    if not db_path.is_file():
        raise SystemExit(f"formal database missing: {db_path}")
    input_data = load_input(db_path)
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        state = inspect(conn)
    validate_preconditions(state)
    report: dict[str, object] = {
        "report": "IMPORT_1941_TRANSCRIPTION_REVIEW",
        "mode": "apply" if args.apply else "dry_run",
        "database": str(db_path),
        "candidate_id": CANDIDATE_ID,
        "document_key": DOC_KEY,
        "source_url": SOURCE_URL,
        "source_file": str(input_data["source_rel"]),
        "source_sha256": str(input_data["source_sha256"]),
        "source_size": int(input_data["source_size"]),
        "body_chars": int(input_data["body_chars"]),
        "body_read": True,
        "ocr": False,
        "citation_ready": False,
        "formal_db_written": bool(args.apply),
        "preconditions": state,
    }
    if args.apply:
        if args.backup is None:
            raise SystemExit("--apply requires --backup")
        result = apply_import(db_path, input_data, args.backup.expanduser(), state)
        report["result"] = result
    else:
        report["result"] = {"would_insert_documents": 1, "would_insert_pages": 1}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
