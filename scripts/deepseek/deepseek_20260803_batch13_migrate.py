#!/usr/bin/env python3
"""Batch 13 migrate: insert provenance stubs for 11 short pages; clear binary garbage text.

No OCR. No citation promotion.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from _guard import guard

guard()
BASE = Path(__file__).resolve().parents[2]
AN = BASE / "work/deepseek-20260803/02_analysis"
OUT = BASE / "work/deepseek-20260803/04_migration"
OUT.mkdir(parents=True, exist_ok=True)
DEFAULT_DB = BASE / "data" / "research_index.sqlite"
EXPECTED_SHA = "d8c4dcebddd11e7bc7d62fab9704e7da3bebfb1abc57021b4f62df6b97e65363"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def migrate(db: Path, apply: bool) -> dict:
    before = sha(db)
    if apply and before != EXPECTED_SHA:
        raise SystemExit(f"hash mismatch: expected {EXPECTED_SHA}, got {before}")

    stubs = list(csv.DictReader(open(AN / "batch13_missing_provenance_stubs.csv", encoding="utf-8-sig")))
    if len(stubs) != 11:
        raise SystemExit(f"expected 11 stubs, got {len(stubs)}")
    page_ids = [int(r["page_id"]) for r in stubs]
    if len(set(page_ids)) != 11:
        raise SystemExit("duplicate page_ids in stubs")

    target = db
    backup = None
    if not apply:
        target = OUT / "research_index.batch13.dryrun.sqlite"
        shutil.copy2(db, target)
    else:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = db.with_name(db.name + f".pre_deepseek_batch13_{stamp}.bak")
        shutil.copy2(db, backup)
        if sha(backup) != before:
            raise SystemExit("backup hash mismatch")

    now = datetime.now().isoformat(timespec="seconds")
    con = sqlite3.connect(target)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("BEGIN IMMEDIATE")
    stats: dict = {}
    try:
        # Must still lack provenance
        q = ",".join("?" * len(page_ids))
        existing = con.execute(
            f"SELECT page_id FROM page_provenance WHERE page_id IN ({q})", page_ids
        ).fetchall()
        if existing:
            raise RuntimeError(f"provenance already exists for {[r[0] for r in existing]}")

        live_pages = con.execute(
            f"SELECT id, document_id, length(trim(coalesce(text,''))) n FROM pages WHERE id IN ({q})",
            page_ids,
        ).fetchall()
        if len(live_pages) != 11:
            raise RuntimeError("page set changed")
        by_id = {int(r["id"]): r for r in live_pages}

        inserted = 0
        for r in stubs:
            pid = int(r["page_id"])
            doc_id = int(r["document_id"])
            if by_id[pid]["document_id"] != doc_id:
                raise RuntimeError(f"document_id mismatch page {pid}")
            source_file = (r["source_file"] or r["page_image_path"] or f"missing://page/{pid}").strip()
            # Deterministic locator hash of the URL/path string (NOT file bytes).
            # Marked via machine_review_note; citation_ready forced 0.
            source_sha = hashlib.sha256(f"batch13-stub-locator:{source_file}:{pid}".encode()).hexdigest()
            pdf_page = int(r["pdf_page_no"]) if str(r["pdf_page_no"]).strip().isdigit() else None
            # physical_page_no is NOT NULL in schema
            phys = int(r["physical_page_no"]) if str(r["physical_page_no"]).strip().isdigit() else (pdf_page or 0)
            con.execute(
                """
                INSERT INTO page_provenance (
                  page_id, document_id, source_id, source_file, source_sha256, source_file_size,
                  pdf_page_no, physical_page_no, printed_page,
                  page_image_path, page_image_sha256, ocr_md_path, ocr_md_sha256,
                  ocr_engine, ocr_model, ocr_mode, ocr_lines, ocr_mean_confidence, text_chars,
                  citation_ready, needs_human_review, review_status,
                  machine_review_note, human_review_note, period, year, event_tags,
                  source_title, batch_id, created_at, updated_at
                ) VALUES (
                  ?,?,?,?,?,NULL,
                  ?,?,?,
                  ?,NULL,NULL,NULL,
                  ?,NULL,?,NULL,NULL,?,
                  0,1,'review_only',
                  ?,NULL,?,NULL,NULL,
                  NULL,?,?,?
                )
                """,
                (
                    pid, doc_id, r["source_id"], source_file, source_sha,
                    pdf_page, phys, None,
                    r["page_image_path"] or source_file,
                    r["ocr_engine"], r["ocr_mode"], int(r["text_chars"] or 0),
                    r["machine_review_note"] + " | source_sha256=locator_stub_not_file_bytes",
                    r["period"],
                    r["batch_id"], now, now,
                ),
            )
            inserted += 1
        stats["stubs_inserted"] = inserted

        # Clear binary garbage text on page 20623 if still present
        bin_pages = [int(r["page_id"]) for r in stubs if r.get("clear_binary_text") == "yes"]
        cleared = 0
        for pid in bin_pages:
            row = con.execute("SELECT text FROM pages WHERE id=?", (pid,)).fetchone()
            text = row["text"] or ""
            if text.startswith("�PNG") or text.startswith("\x89PNG") or text[:4] == "PNG " or "PNG" in text[:8]:
                con.execute("UPDATE pages SET text='' WHERE id=?", (pid,))
                con.execute(
                    """
                    UPDATE page_provenance
                    SET text_chars=0,
                        machine_review_note = machine_review_note || ' | cleared binary pages.text',
                        updated_at=?
                    WHERE page_id=?
                    """,
                    (now, pid),
                )
                # FTS may lag; leave rebuild to later ops if needed.
                cleared += 1
        stats["binary_text_cleared"] = cleared

        # Post checks
        still_missing = con.execute(
            f"""
            SELECT count(*) FROM pages p
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE p.id IN ({q}) AND pp.page_id IS NULL
            """,
            page_ids,
        ).fetchone()[0]
        ready = con.execute(
            f"SELECT count(*) FROM page_provenance WHERE page_id IN ({q}) AND citation_ready=1",
            page_ids,
        ).fetchone()[0]
        stats["still_missing_after"] = still_missing
        stats["stubs_citation_ready"] = ready
        if still_missing or ready:
            raise RuntimeError(f"postcheck missing={still_missing} ready={ready}")

        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        integ = con.execute("PRAGMA integrity_check").fetchone()[0]
        stats["foreign_key_violations"] = len(fk)
        stats["integrity_check"] = integ
        if fk or integ != "ok":
            raise RuntimeError(f"validation failed fk={len(fk)} integrity={integ}")
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()

    after = sha(target)
    result = {
        "mode": "apply" if apply else "dry-run",
        "database": str(target),
        "source_sha256": before,
        "result_sha256": after,
        "backup": str(backup) if backup else None,
        "stats": stats,
        "timestamp": datetime.now().isoformat(),
    }
    name = "batch13_apply_result.json" if apply else "batch13_dryrun_result.json"
    (OUT / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(json.dumps(migrate(a.db, a.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
