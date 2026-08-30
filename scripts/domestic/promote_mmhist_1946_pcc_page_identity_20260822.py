#!/usr/bin/env python3
"""Promote visually checked 1983 MMHIST reprint pages to page-level citation.

This migration changes only page identity/provenance flags.  It does not add
or rewrite body text, does not run OCR, and does not close the 1946 primary
archive gap.  A current database SHA and a byte-identical backup are required
for ``--apply``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "research_index.sqlite"
REVIEW_PATH = ROOT / "data" / "domestic" / "mmhist_1946_pcc_page_identity_review_20260822.json"
SOURCE_FILE = "data/domestic/sourcebooks/中国民主同盟历史文献_1941-1949_公开扫描.pdf"
SOURCE_SHA256 = "257bb7be70abe374be9864ec451b5a4a90e2442ae8c877b15f4e6bbb8bb30be3"
EXPECTED_DB_SHA256 = "1250e6ee3d20cc670bbfb5f53bf5a4a8a1658f35826617035bdb04c5cb59d3a3"
AUDIT_RELATIVE = "data/domestic/mmhist_1946_pcc_page_identity_review_20260822.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def replace_flag_terms(existing: str, *, page_id: int) -> str:
    prefixes = (
        "source_kind=",
        "evidence_level=",
        "body_text=",
        "ocr_status=",
        "ocr_page_status=",
        "citation_ready=",
        "needs_human_review=",
        "review_status=",
        "identity_audit=",
        "page_id=",
    )
    kept = [part for part in existing.split(";") if part and not part.startswith(prefixes)]
    kept.extend(
        [
            "source_kind=official_compilation_reprint",
            "evidence_level=L2",
            "body_text=ocr_not_quoted",
            "ocr_status=derived_search_only",
            "citation_ready=true",
            "needs_human_review=false",
            "review_status=human_verified",
            f"identity_audit={AUDIT_RELATIVE}",
            f"page_id={page_id}",
        ]
    )
    return ";".join(kept)


def load_review() -> dict:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    if review.get("schema") != "domestic_mmhist_1946_pcc_page_identity_review.v1":
        raise SystemExit("unexpected visual review schema")
    if review.get("source_file") != SOURCE_FILE or review.get("source_sha256") != SOURCE_SHA256:
        raise SystemExit("visual review source does not match migration source")
    pages = review.get("pages")
    if not isinstance(pages, list) or not pages:
        raise SystemExit("visual review has no pages")
    page_ids = [int(row["page_id"]) for row in pages]
    if len(page_ids) != len(set(page_ids)):
        raise SystemExit("visual review has duplicate page IDs")
    return review


def validate_inputs(connection: sqlite3.Connection, source_path: Path) -> list[dict[str, object]]:
    review = load_review()
    if not source_path.is_file():
        raise SystemExit(f"missing source file: {source_path}")
    if sha256(source_path) != SOURCE_SHA256:
        raise SystemExit("source SHA256 mismatch")

    rows: list[dict[str, object]] = []
    for target in review["pages"]:
        page_id = int(target["page_id"])
        row = connection.execute(
            """
            SELECT p.id, p.text, pp.source_file, pp.source_sha256, pp.pdf_page_no,
                   pp.physical_page_no, pp.page_image_path, pp.page_image_sha256,
                   pp.citation_ready, pp.needs_human_review, pp.review_status,
                   pp.ocr_mode, f.matched_terms, b.matched_terms
            FROM pages p
            JOIN page_provenance pp ON pp.page_id = p.id
            JOIN page_fts f ON f.rowid = p.id
            JOIN page_fts_bigram b ON b.rowid = p.id
            WHERE p.id = ?
            """,
            (page_id,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"missing page/provenance/FTS row: {page_id}")
        (
            _id,
            _text,
            source_file,
            source_sha,
            pdf_page_no,
            physical_page_no,
            image_path,
            image_sha,
            citation_ready,
            needs_human_review,
            review_status,
            ocr_mode,
            f_terms,
            b_terms,
        ) = row
        if source_file != SOURCE_FILE or source_sha != SOURCE_SHA256:
            raise SystemExit(f"page {page_id} provenance source mismatch")
        if int(pdf_page_no) != int(target["pdf_page_no"]) or int(physical_page_no) != int(target["pdf_page_no"]):
            raise SystemExit(f"page {page_id} PDF/physical page mismatch")
        if image_path != target["page_image_path"] or image_sha != target["page_image_sha256"]:
            raise SystemExit(f"page {page_id} page-image provenance mismatch")
        image_file = DB_PATH.resolve().parents[1] / image_path
        if not image_file.is_file() or sha256(image_file) != image_sha:
            raise SystemExit(f"page {page_id} page-image SHA mismatch")
        if citation_ready != 0 or needs_human_review != 0 or review_status != "machine_verified":
            raise SystemExit(f"page {page_id} is not an untouched machine-verified record")
        if ocr_mode != "page-by-page-real":
            raise SystemExit(f"page {page_id} unexpected OCR mode: {ocr_mode}")
        rows.append(
            {
                "page_id": page_id,
                "label": str(target["label"]),
                "pdf_page_no": int(target["pdf_page_no"]),
                "printed_page": str(target["printed_page"]),
                "image_sha": image_sha,
                "old_fts_terms": str(f_terms),
                "old_bigram_terms": str(b_terms),
            }
        )
    return rows


def validate_after(connection: sqlite3.Connection, page_ids: list[int]) -> dict[str, int | str]:
    placeholders = ",".join("?" for _ in page_ids)
    flags = connection.execute(
        f"""
        SELECT COUNT(*) FROM page_provenance
        WHERE page_id IN ({placeholders}) AND citation_ready=1
          AND needs_human_review=0 AND review_status='human_verified'
        """,
        page_ids,
    ).fetchone()[0]
    fts_flags = connection.execute(
        f"""
        SELECT COUNT(*) FROM page_fts
        WHERE rowid IN ({placeholders}) AND matched_terms LIKE '%citation_ready=true%'
          AND matched_terms LIKE '%review_status=human_verified%'
        """,
        page_ids,
    ).fetchone()[0]
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    fk_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    pages_without_fts = connection.execute(
        "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL"
    ).fetchone()[0]
    if flags != len(page_ids) or fts_flags != len(page_ids) or integrity != "ok" or fk_violations or pages_without_fts:
        raise SystemExit(
            f"validation failed: provenance={flags}, fts_flags={fts_flags}, integrity={integrity}, "
            f"fk={len(fk_violations)}, pages_without_fts={pages_without_fts}"
        )
    return {
        "integrity_check": integrity,
        "foreign_key_violations": len(fk_violations),
        "pages_without_fts": pages_without_fts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha", default=EXPECTED_DB_SHA256)
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()

    db = DB_PATH.resolve()
    current_sha = sha256(db)
    if current_sha != args.expected_db_sha:
        raise SystemExit(f"database SHA mismatch: expected {args.expected_db_sha}, got {current_sha}")
    source = db.parents[1] / SOURCE_FILE

    if not args.apply:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
            rows = validate_inputs(connection, source)
        print(json.dumps({"status": "READY", "db_sha256": current_sha, "page_ids": [r["page_id"] for r in rows]}, ensure_ascii=False))
        return 0

    if args.backup is None:
        raise SystemExit("--backup is required with --apply")
    backup = args.backup if args.backup.is_absolute() else ROOT / args.backup
    if not backup.is_file() or sha256(backup) != current_sha:
        raise SystemExit("backup is missing or is not byte-identical to the current database")

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    with sqlite3.connect(db) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        rows = validate_inputs(connection, source)
        connection.execute("BEGIN IMMEDIATE")
        for row in rows:
            page_id = int(row["page_id"])
            note = (
                "审核者：codex-visual-audit-20260822；已查看本地页图并核对标题/日期、"
                f"PDF第{row['pdf_page_no']}页、书内第{row['printed_page']}页、来源SHA256和页图SHA256。"
                "本页可作为1983年《中国民主同盟历史文献 1941—1949》汇编重刊的页级身份与范围引用；"
                "OCR仅用于检索，正文未逐字校读，不替代1946年政协正式会议记录或独立发言/提案原件。"
            )
            machine_note = (
                "page identity promoted from machine_verified; body/OCR text unchanged and not cleared for verbatim quotation; "
                f"see {AUDIT_RELATIVE}"
            )
            connection.execute("UPDATE pages SET page_label=? WHERE id=?", (row["label"], page_id))
            connection.execute(
                """
                UPDATE page_provenance
                SET citation_ready=1, needs_human_review=0, review_status='human_verified',
                    human_review_note=?, machine_review_note=?, updated_at=?
                WHERE page_id=?
                """,
                (note, machine_note, now, page_id),
            )
            f_terms = replace_flag_terms(str(row["old_fts_terms"]), page_id=page_id)
            b_terms = replace_flag_terms(str(row["old_bigram_terms"]), page_id=page_id)
            connection.execute("UPDATE page_fts SET page_label=?, matched_terms=? WHERE rowid=?", (row["label"], f_terms, page_id))
            connection.execute("UPDATE page_fts_bigram SET page_label=?, matched_terms=? WHERE rowid=?", (row["label"], b_terms, page_id))
        checks = validate_after(connection, [int(row["page_id"]) for row in rows])
        connection.commit()

    after_sha = sha256(db)
    print(
        json.dumps(
            {
                "status": "APPLIED",
                "db_sha256_before": current_sha,
                "db_sha256_after": after_sha,
                "backup": str(backup),
                "page_ids": [int(row["page_id"]) for row in rows],
                "citation_ready_added": len(rows),
                "body_text_changed": False,
                "ocr_performed": False,
                **checks,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
