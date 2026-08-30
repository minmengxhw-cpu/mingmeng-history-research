#!/usr/bin/env python3
"""Promote only visually verified NLC 1949 page identities to strict citation.

This migration deliberately does not add body text or OCR.  The promoted
records support page identity/scope citations only; the remaining selected
pages stay review_only until their body or image context is separately audited.
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
REVIEW_PATH = ROOT / "work" / "domestic" / "nlc_1949_conference_journal_page_identity_review_20260815.json"
SOURCE_FILE = "data/domestic/raw/public_sources/nlc_1949_first_plenary_conference_journal.pdf"
SOURCE_SHA256 = "20069c88dd8520e034f47beb614bca4c1c86ae6b8baf41aaf1988a13f95c7e4a"
EXPECTED_DB_SHA256 = "25624cc9b9713a72e3777c515571b26fc322444bf2101b0e9e72bcbe8802fee0"
AUDIT_RELATIVE = "work/domestic/nlc_1949_conference_journal_page_identity_review_20260815.json"

TARGETS = {
    20932: {
        "label": "pdf-001 / 会刊封面",
        "scope": "会刊题名、1949年出版信息及合刊范围的页级身份",
        "caveat": "只确认封面身份和可见范围，不据此宣称全套会议记录完整。",
    },
    20933: {
        "label": "pdf-017 / 开幕式程序",
        "scope": "第一届全体会议开幕式程序页的页级身份及1949-09-21日期线索",
        "caveat": "只确认程序页身份和日期，不逐字引用程序正文。",
    },
    20934: {
        "label": "pdf-030 / 主席团名单",
        "scope": "第一届全体会议主席团名单页的页级身份和名册版式",
        "caveat": "可作为名册页定位和可见姓名锚点；不据此完成逐人姓名、职务或代表资格校勘。",
    },
    20935: {
        "label": "pdf-031 / 议事规则-1",
        "scope": "第一届全体会议议事规则第一页的页级身份",
        "caveat": "只确认正式规则页身份，不逐字引用规则正文。",
    },
    20936: {
        "label": "pdf-032 / 议事规则-2",
        "scope": "第一届全体会议议事规则第二页的页级身份",
        "caveat": "只确认正式规则页身份，不逐字引用规则正文。",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolved_db() -> Path:
    return DB_PATH.resolve()


def replace_flag_terms(existing: str, *, page_id: int) -> str:
    prefixes = (
        "source_kind=",
        "evidence_level=",
        "body_text=",
        "ocr_status=",
        "citation_ready=",
        "needs_human_review=",
        "review_status=",
    )
    kept = [part for part in existing.split(";") if part and not part.startswith(prefixes)]
    kept.extend(
        [
            "source_kind=official_conference_journal_scan",
            "evidence_level=L1",
            "body_text=false",
            "ocr_status=not_performed",
            "citation_ready=true",
            "needs_human_review=false",
            "review_status=human_verified",
            f"identity_audit={AUDIT_RELATIVE}",
            f"page_id={page_id}",
        ]
    )
    return ";".join(kept)


def validate_inputs(connection: sqlite3.Connection, source_path: Path) -> list[dict[str, object]]:
    if not source_path.exists():
        raise SystemExit(f"missing source file: {source_path}")
    actual_source_sha = sha256(source_path)
    if actual_source_sha != SOURCE_SHA256:
        raise SystemExit(f"source SHA mismatch: expected {SOURCE_SHA256}, got {actual_source_sha}")
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    if review.get("source_sha256") != SOURCE_SHA256:
        raise SystemExit("visual review source SHA does not match migration source SHA")
    reviewed_ids = {int(item["page_id"]) for item in review.get("promoted_pages", [])}
    if reviewed_ids != set(TARGETS):
        raise SystemExit(f"visual review page set mismatch: {sorted(reviewed_ids)}")

    rows: list[dict[str, object]] = []
    for page_id, target in TARGETS.items():
        row = connection.execute(
            """
            SELECT p.id, p.page_label, p.text,
                   pp.source_file, pp.source_sha256, pp.pdf_page_no,
                   pp.review_status, pp.citation_ready, pp.needs_human_review,
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
            _old_label,
            text,
            source_file,
            source_sha,
            pdf_page_no,
            review_status,
            citation_ready,
            needs_human_review,
            ocr_mode,
            f_terms,
            b_terms,
        ) = row
        if source_file != SOURCE_FILE or source_sha != SOURCE_SHA256:
            raise SystemExit(f"page {page_id} provenance source mismatch")
        if review_status != "review_only" or citation_ready != 0 or needs_human_review != 1:
            raise SystemExit(f"page {page_id} is not an untouched review_only record")
        if text:
            raise SystemExit(f"page {page_id} unexpectedly contains body text; refusing promotion")
        if ocr_mode != "not_performed":
            raise SystemExit(f"page {page_id} OCR mode changed unexpectedly: {ocr_mode}")
        rows.append(
            {
                "page_id": page_id,
                "target": target,
                "old_fts_terms": f_terms,
                "old_bigram_terms": b_terms,
                "pdf_page_no": pdf_page_no,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha", default=EXPECTED_DB_SHA256)
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()

    db = resolved_db()
    source = db.parents[1] / SOURCE_FILE
    current_sha = sha256(db)
    if current_sha != args.expected_db_sha:
        raise SystemExit(f"database SHA mismatch: expected {args.expected_db_sha}, got {current_sha}")
    if not args.apply:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
            rows = validate_inputs(connection, source)
        print(json.dumps({"status": "READY", "db_sha256": current_sha, "promote_page_ids": [r["page_id"] for r in rows]}, ensure_ascii=False))
        return 0

    if args.backup is None:
        raise SystemExit("--backup is required with --apply")
    backup = args.backup if args.backup.is_absolute() else ROOT / args.backup
    if not backup.exists():
        raise SystemExit(f"missing backup: {backup}")
    backup_sha = sha256(backup)
    if backup_sha != current_sha:
        raise SystemExit(f"backup SHA mismatch: expected {current_sha}, got {backup_sha}")

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    with sqlite3.connect(db) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        rows = validate_inputs(connection, source)
        connection.execute("BEGIN IMMEDIATE")
        for row in rows:
            page_id = int(row["page_id"])
            target = row["target"]
            note = (
                f"审核者：codex-visual-audit-20260815；已查看本地PDF渲染页并核对来源SHA256、"
                f"物理页{int(row['pdf_page_no'])}和页级provenance。可作为{target['scope']}；"
                f"正文/OCR未核验，不转录正文。{target['caveat']}"
            )
            machine_note = (
                "page identity promoted from review_only; body_text remains empty; "
                "ocr_mode remains not_performed; see " + AUDIT_RELATIVE
            )
            connection.execute("UPDATE pages SET page_label = ? WHERE id = ?", (target["label"], page_id))
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
            connection.execute("UPDATE page_fts SET page_label=?, matched_terms=? WHERE rowid=?", (target["label"], f_terms, page_id))
            connection.execute("UPDATE page_fts_bigram SET page_label=?, matched_terms=? WHERE rowid=?", (target["label"], b_terms, page_id))
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        fk_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        pages_without_fts = connection.execute(
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL"
        ).fetchone()[0]
        if integrity != "ok" or fk_violations or pages_without_fts:
            connection.rollback()
            raise SystemExit(f"validation failed before commit: integrity={integrity}, fk={fk_violations}, pages_without_fts={pages_without_fts}")
        connection.commit()

    after_sha = sha256(db)
    print(
        json.dumps(
            {
                "status": "APPLIED",
                "db_sha256_before": current_sha,
                "db_sha256_after": after_sha,
                "backup": str(backup),
                "backup_sha256": backup_sha,
                "promoted_page_ids": [r["page_id"] for r in rows],
                "citation_ready_added": len(rows),
                "body_text_added": False,
                "ocr_performed": False,
                "integrity_check": integrity,
                "foreign_key_violations": len(fk_violations),
                "pages_without_fts": pages_without_fts,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
