#!/usr/bin/env python3
"""Register only the explicitly reviewed MMHIST printed-page subset.

This is a narrow, idempotent metadata migration for 17 pages whose printed
page identity was visually reviewed and recorded in a body-free manifest.  It
does not register the proposed continuous ``pdf_page_no - 30`` offset for the
remaining pages, does not read or rewrite page text, does not run OCR, and does
not create a separate academic full-text source row.

``--apply`` requires both an expected current database SHA256 and a byte-
identical dated backup.  The database is the existing page-OCR document; only
``page_provenance.printed_page`` and its ``updated_at`` timestamp are changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_REVIEW = ROOT / "data" / "domestic" / "mmhist_1946_pcc_page_identity_review_20260822.json"
SOURCE_FILE = "data/domestic/sourcebooks/中国民主同盟历史文献_1941-1949_公开扫描.pdf"
SOURCE_SHA256 = "257bb7be70abe374be9864ec451b5a4a90e2442ae8c877b15f4e6bbb8bb30be3"
SOURCE_ID = "domestic-page-ocr/SRC-257bb7be70"
PROVENANCE_SOURCE_ID = "SRC-257bb7be70"
DOC_KEY = "domestic-page/SRC-257bb7be70"
EXPECTED_PAIRS = (
    (145, "115"),
    (147, "117"),
    (148, "118"),
    (149, "119"),
    (150, "120"),
    (151, "121"),
    (152, "122"),
    (153, "123"),
    (157, "127"),
    (158, "128"),
    (159, "129"),
    (160, "130"),
    (161, "131"),
    (162, "132"),
    (163, "133"),
    (164, "134"),
    (165, "135"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_review(path: Path) -> dict[str, Any]:
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"review manifest unreadable: {exc}") from exc
    if not isinstance(review, dict):
        raise SystemExit("review manifest must be an object")
    if review.get("schema") != "domestic_mmhist_1946_pcc_page_identity_review.v1":
        raise SystemExit("unexpected review manifest schema")
    if review.get("body_text_included") is not False or review.get("ocr_text_included") is not False:
        raise SystemExit("review manifest must remain body-free and OCR-free")
    if review.get("source_file") != SOURCE_FILE or review.get("source_sha256") != SOURCE_SHA256:
        raise SystemExit("review manifest source identity mismatch")
    pages = review.get("pages")
    if not isinstance(pages, list) or len(pages) != len(EXPECTED_PAIRS):
        raise SystemExit("review manifest must contain exactly the explicit subset")
    actual_pairs = []
    seen_ids: set[int] = set()
    for row in pages:
        if not isinstance(row, dict):
            raise SystemExit("review manifest page must be an object")
        page_id = int(row["page_id"])
        if page_id in seen_ids:
            raise SystemExit(f"duplicate review page id: {page_id}")
        seen_ids.add(page_id)
        actual_pairs.append((int(row["pdf_page_no"]), str(row["printed_page"])))
        for field in ("label", "page_image_path", "page_image_sha256"):
            if not str(row.get(field) or "").strip():
                raise SystemExit(f"review page {page_id} has no {field}")
    if tuple(actual_pairs) != EXPECTED_PAIRS:
        raise SystemExit("review manifest page mapping differs from the fixed explicit subset")
    return review


def resolve_relative(base: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"unsafe relative path in provenance: {relative_path}")
    return base / path


def validate_inputs(connection: sqlite3.Connection, db: Path, review: dict[str, Any]) -> dict[str, Any]:
    base = db.parents[1]
    source_file = resolve_relative(base, SOURCE_FILE)
    if not source_file.is_file():
        raise SystemExit(f"missing source PDF: {source_file}")
    if sha256(source_file) != SOURCE_SHA256:
        raise SystemExit("source PDF SHA256 mismatch")

    source_rows = connection.execute(
        "SELECT id, source_type, source_id, local_path FROM sources WHERE source_id=?",
        (SOURCE_ID,),
    ).fetchall()
    if len(source_rows) != 1:
        raise SystemExit(f"expected exactly one source row for {SOURCE_ID}, got {len(source_rows)}")
    source_row = source_rows[0]
    if source_row[1] != "domestic_page_ocr":
        raise SystemExit("source type is not domestic_page_ocr")

    document_rows = connection.execute(
        "SELECT id, source_id, doc_key FROM documents WHERE source_id=? AND doc_key=?",
        (source_row[0], DOC_KEY),
    ).fetchall()
    if len(document_rows) != 1:
        raise SystemExit(f"expected exactly one document row for {DOC_KEY}, got {len(document_rows)}")
    document_id = int(document_rows[0][0])

    pages = review["pages"]
    rows: list[dict[str, Any]] = []
    for target in pages:
        page_id = int(target["page_id"])
        row = connection.execute(
            """
            SELECT p.id, p.document_id, p.page_label, p.page_url,
                   pp.source_id, pp.source_file, pp.source_sha256,
                   pp.pdf_page_no, pp.physical_page_no, pp.printed_page,
                   pp.page_image_path, pp.page_image_sha256,
                   pp.citation_ready, pp.needs_human_review, pp.review_status,
                   pp.ocr_mode
              FROM pages AS p
              JOIN page_provenance AS pp ON pp.page_id=p.id
             WHERE p.id=?
            """,
            (page_id,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"missing page/provenance row: {page_id}")
        (
            _page_id,
            actual_document_id,
            page_label,
            _page_url,
            provenance_source_id,
            provenance_source_file,
            provenance_sha,
            pdf_page_no,
            physical_page_no,
            current_printed_page,
            image_path,
            image_sha,
            citation_ready,
            needs_human_review,
            review_status,
            ocr_mode,
        ) = row
        if int(actual_document_id) != document_id:
            raise SystemExit(f"page {page_id} belongs to another document")
        if provenance_source_id != PROVENANCE_SOURCE_ID or provenance_source_file != SOURCE_FILE:
            raise SystemExit(f"page {page_id} provenance source mismatch")
        if provenance_sha != SOURCE_SHA256:
            raise SystemExit(f"page {page_id} source SHA mismatch")
        if int(pdf_page_no) != int(target["pdf_page_no"]) or int(physical_page_no) != int(target["pdf_page_no"]):
            raise SystemExit(f"page {page_id} PDF/physical page mismatch")
        if page_label != target["label"]:
            raise SystemExit(f"page {page_id} page label differs from reviewed label")
        if image_path != target["page_image_path"] or image_sha != target["page_image_sha256"]:
            raise SystemExit(f"page {page_id} page-image provenance mismatch")
        image_file = resolve_relative(base, str(image_path))
        if not image_file.is_file() or sha256(image_file) != image_sha:
            raise SystemExit(f"page {page_id} page-image SHA mismatch")
        if int(citation_ready) != 1 or int(needs_human_review) != 0 or review_status != "human_verified":
            raise SystemExit(f"page {page_id} is not an explicitly reviewed citation-ready page")
        if ocr_mode != "page-by-page-real":
            raise SystemExit(f"page {page_id} has unexpected OCR mode: {ocr_mode}")
        expected_printed_page = str(target["printed_page"])
        if current_printed_page not in (None, expected_printed_page):
            raise SystemExit(f"page {page_id} has conflicting printed page: {current_printed_page}")
        rows.append(
            {
                "page_id": page_id,
                "pdf_page_no": int(pdf_page_no),
                "printed_page": expected_printed_page,
                "current_printed_page": current_printed_page,
            }
        )

    registered_rows = connection.execute(
        """
        SELECT pdf_page_no, printed_page
          FROM page_provenance
         WHERE document_id=? AND printed_page IS NOT NULL AND trim(printed_page)<>''
         ORDER BY pdf_page_no
        """,
        (document_id,),
    ).fetchall()
    current_pairs = tuple((int(row[0]), str(row[1])) for row in registered_rows)
    if current_pairs not in ((), EXPECTED_PAIRS):
        raise SystemExit(f"existing printed-page registration conflicts with explicit subset: {current_pairs}")
    if len({printed for _, printed in EXPECTED_PAIRS}) != len(EXPECTED_PAIRS):
        raise SystemExit("explicit printed pages are not unique")

    return {
        "source_id": SOURCE_ID,
        "document_id": document_id,
        "page_count": int(connection.execute("SELECT count(*) FROM pages WHERE document_id=?", (document_id,)).fetchone()[0]),
        "current_registered_pairs": [list(pair) for pair in current_pairs],
        "target_pairs": [list(pair) for pair in EXPECTED_PAIRS],
        "rows": rows,
        "already_applied": current_pairs == EXPECTED_PAIRS,
    }


def provenance_snapshot(connection: sqlite3.Connection, page_ids: list[int]) -> dict[int, tuple[Any, ...]]:
    placeholders = ",".join("?" for _ in page_ids)
    rows = connection.execute(
        f"""
        SELECT p.id, p.page_label, p.page_url,
               pp.source_id, pp.source_file, pp.source_sha256,
               pp.source_file_size, pp.pdf_page_no, pp.physical_page_no,
               pp.page_image_path, pp.page_image_sha256,
               pp.ocr_md_path, pp.ocr_md_sha256, pp.ocr_engine, pp.ocr_model,
               pp.ocr_mode, pp.ocr_lines, pp.ocr_mean_confidence,
               pp.text_chars, pp.citation_ready, pp.needs_human_review,
               pp.review_status, pp.machine_review_note, pp.human_review_note,
               pp.period, pp.year, pp.event_tags, pp.source_title, pp.batch_id
          FROM pages AS p
          JOIN page_provenance AS pp ON pp.page_id=p.id
         WHERE p.id IN ({placeholders})
        """,
        page_ids,
    ).fetchall()
    return {int(row[0]): tuple(row[1:]) for row in rows}


def validate_after(connection: sqlite3.Connection, document_id: int, expected_pairs: tuple[tuple[int, str], ...]) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT pdf_page_no, printed_page
          FROM page_provenance
         WHERE document_id=? AND printed_page IS NOT NULL AND trim(printed_page)<>''
         ORDER BY pdf_page_no
        """,
        (document_id,),
    ).fetchall()
    actual_pairs = tuple((int(row[0]), str(row[1])) for row in rows)
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_key_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if actual_pairs != expected_pairs or integrity != "ok" or foreign_key_violations:
        raise SystemExit(
            f"post-migration validation failed: pairs={actual_pairs}, integrity={integrity}, "
            f"foreign_keys={len(foreign_key_violations)}"
        )
    return {
        "printed_page_registered_count": len(actual_pairs),
        "integrity_check": integrity,
        "foreign_key_violations": len(foreign_key_violations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()

    db = args.db.resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")
    current_sha = sha256(db)
    review = load_review(args.review)

    if args.apply:
        if not args.expected_db_sha:
            raise SystemExit("--expected-db-sha is required with --apply")
        if current_sha != args.expected_db_sha:
            raise SystemExit(f"database SHA mismatch: expected {args.expected_db_sha}, got {current_sha}")
        if args.backup is None:
            raise SystemExit("--backup is required with --apply")
        backup = args.backup.resolve()
        if not backup.is_file() or sha256(backup) != current_sha:
            raise SystemExit("backup is missing or is not byte-identical to the current database")

        with sqlite3.connect(db) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            plan = validate_inputs(connection, db, review)
            page_ids = [int(row["page_id"]) for row in plan["rows"]]
            before = provenance_snapshot(connection, page_ids)
            connection.execute("BEGIN IMMEDIATE")
            now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
            for row in plan["rows"]:
                connection.execute(
                    "UPDATE page_provenance SET printed_page=?, updated_at=? WHERE page_id=?",
                    (row["printed_page"], now, row["page_id"]),
                )
            after = provenance_snapshot(connection, page_ids)
            if any(
                tuple(before[page_id]) != tuple(after[page_id])
                for page_id in page_ids
            ):
                raise SystemExit("non-printed-page provenance metadata changed unexpectedly")
            checks = validate_after(connection, int(plan["document_id"]), EXPECTED_PAIRS)
            connection.commit()

        after_sha = sha256(db)
        print(
            json.dumps(
                {
                    "status": "APPLIED",
                    "db_sha256_before": current_sha,
                    "db_sha256_after": after_sha,
                    "backup": str(backup),
                    "page_ids": page_ids,
                    "changed_page_count": sum(
                        row["current_printed_page"] != row["printed_page"] for row in plan["rows"]
                    ),
                    "body_text_changed": False,
                    "ocr_performed": False,
                    "new_formal_academic_source_rows": 0,
                    **checks,
                },
                ensure_ascii=False,
            )
        )
        return 0

    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
        plan = validate_inputs(connection, db, review)
    print(
        json.dumps(
            {
                "status": "READY",
                "db_sha256": current_sha,
                "source_sha256": SOURCE_SHA256,
                "document_id": plan["document_id"],
                "page_count": plan["page_count"],
                "current_registered_pairs": plan["current_registered_pairs"],
                "target_pairs": plan["target_pairs"],
                "planned_new_count": sum(
                    row["current_printed_page"] != row["printed_page"] for row in plan["rows"]
                ),
                "body_text_read": False,
                "ocr_performed": False,
                "new_formal_academic_source_rows": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
