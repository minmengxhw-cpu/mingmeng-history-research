#!/usr/bin/env python3
"""Apply a bounded, body-free visual review for six 1947 NLC pages.

The selected records already have OCR pages in the formal index, but their
provenance pointed only at OCR markdown.  This batch binds each reviewed page
to the local source PDF and rendered page image, corrects the PDF/physical page
numbers, and opens the strict citation gate only after an explicit visual
review note.  It never changes page text and never deletes or rewrites source
assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_BATCH = ROOT / "work" / "domestic" / "nlc_1947_visual_review_20260814" / "BATCH.json"
DEFAULT_DECISIONS = ROOT / "work" / "domestic" / "nlc_1947_visual_review_20260814" / "REVIEW_DECISIONS.json"
DEFAULT_REPORT = ROOT / "work" / "domestic" / "nlc_1947_visual_review_20260814" / "APPLY_REPORT.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_root_for(db_path: Path) -> Path:
    return db_path.resolve().parent.parent


def resolve_source(root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def load_decisions(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("pages"), list):
        return payload["pages"]
    raise ValueError("decision file must be a list or an object with pages")


STRICT_SQL = """citation_ready=1 AND needs_human_review=0
                   AND review_status='human_verified'
                   AND trim(COALESCE(human_review_note,''))<>''"""


def strict_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute(f"SELECT count(*) FROM page_provenance WHERE {STRICT_SQL}").fetchone()[0])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    expected_db_sha = str(batch.get("database", {}).get("sha256") or "").lower()
    actual_db_sha = sha256_file(args.db)
    if expected_db_sha != actual_db_sha:
        raise SystemExit(f"database SHA mismatch: expected {expected_db_sha}, got {actual_db_sha}")

    batch_pages = {int(item["page_id"]): item for item in batch.get("pages", [])}
    decisions = load_decisions(args.decisions)
    errors: list[str] = []
    accepted: list[dict[str, object]] = []
    seen: set[int] = set()
    source_root = source_root_for(args.db)
    forbidden_body_keys = {"text", "page_text", "ocr_text", "body", "body_text", "transcript"}

    with sqlite3.connect(args.db) as conn:
        conn.row_factory = sqlite3.Row
        for decision in decisions:
            try:
                page_id = int(decision["page_id"])
            except (KeyError, TypeError, ValueError):
                errors.append("decision without integer page_id")
                continue
            if page_id in seen:
                errors.append(f"duplicate decision page_id={page_id}")
                continue
            seen.add(page_id)
            item = batch_pages.get(page_id)
            if not item:
                errors.append(f"page_id={page_id} is not in batch")
                continue
            if forbidden_body_keys.intersection(decision):
                errors.append(f"page_id={page_id} decision contains body text key")
            if str(decision.get("decision") or "") != "human_verified":
                continue
            reviewer = str(decision.get("reviewer") or "").strip()
            note = str(decision.get("note") or "").strip()
            if not reviewer or len(note) < 20:
                errors.append(f"page_id={page_id} requires reviewer and a 20+ character note")
                continue

            source_path = resolve_source(source_root, str(item["target_source_file"]))
            image_path = resolve_source(source_root, str(item["page_image_path"]))
            if not source_path.is_file() or sha256_file(source_path) != str(item["target_source_sha256"]).lower():
                errors.append(f"page_id={page_id} target PDF hash/file check failed")
            if not image_path.is_file() or sha256_file(image_path) != str(item["page_image_sha256"]).lower():
                errors.append(f"page_id={page_id} page image hash/file check failed")
            if source_path.suffix.lower() != ".pdf" or image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
                errors.append(f"page_id={page_id} target asset type is not PDF plus image")

            row = conn.execute(
                """
                SELECT p.id, p.page_label, p.page_url, p.text,
                       d.doc_key, d.source_platform,
                       pp.source_id, pp.source_file, pp.source_sha256,
                       pp.page_image_path, pp.page_image_sha256,
                       pp.pdf_page_no, pp.physical_page_no,
                       pp.ocr_md_path, pp.ocr_md_sha256,
                       pp.citation_ready, pp.review_status
                FROM pages p
                JOIN documents d ON d.id=p.document_id
                JOIN page_provenance pp ON pp.page_id=p.id
                WHERE p.id=?
                """,
                (page_id,),
            ).fetchone()
            if row is None:
                errors.append(f"page_id={page_id} provenance row missing")
                continue
            checks = {
                "source_platform": (str(row["source_platform"] or ""), "domestic"),
                "doc_key": (str(row["doc_key"] or ""), str(item["doc_key"])),
                "page_label": (str(row["page_label"] or ""), str(item["page_label"])),
                "current_page_url": (str(row["page_url"] or ""), str(item["current_page_url"])),
                "source_id": (str(row["source_id"] or ""), str(item["source_id"])),
                "current_source_file": (str(row["source_file"] or ""), str(item["current_source_file"])),
                "current_source_sha256": (str(row["source_sha256"] or "").lower(), str(item["current_source_sha256"]).lower()),
            }
            for name, (actual, expected) in checks.items():
                if actual != expected:
                    errors.append(f"page_id={page_id} {name} differs from batch")
            accepted.append({
                "page_id": page_id,
                "reviewer": reviewer,
                "note": note,
                "target_page_url": str(item["target_page_url"]),
                "target_source_file": str(item["target_source_file"]),
                "target_source_sha256": str(item["target_source_sha256"]).lower(),
                "target_source_file_size": int(item["target_source_file_size"]),
                "page_image_path": str(item["page_image_path"]),
                "page_image_sha256": str(item["page_image_sha256"]).lower(),
                "pdf_page_no": int(item["pdf_page_no"]),
                "physical_page_no": int(item["physical_page_no"]),
                "year": int(item["year"]),
                "period": str(item["period"]),
                "event_tags": str(item["event_tags"]),
            })

        before = strict_count(conn)
        page_count_before = int(conn.execute("SELECT count(*) FROM pages").fetchone()[0])
        if args.apply and errors:
            raise SystemExit("validation failed:\n- " + "\n- ".join(errors))
        if args.apply and not args.backup:
            raise SystemExit("--backup is required with --apply")
        if args.apply and args.backup.exists():
            raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")

        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.db, args.backup)
            if sha256_file(args.backup) != actual_db_sha:
                raise SystemExit("backup verification failed")
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN IMMEDIATE")
            try:
                for item in accepted:
                    stored_note = f"审核者：{item['reviewer']}；{item['note']}"
                    conn.execute("UPDATE pages SET page_url=? WHERE id=?", (item["target_page_url"], item["page_id"]))
                    conn.execute(
                        """
                        UPDATE page_provenance
                           SET source_file=?, source_sha256=?, source_file_size=?,
                               pdf_page_no=?, physical_page_no=?, page_image_path=?,
                               page_image_sha256=?, citation_ready=1, needs_human_review=0,
                               review_status='human_verified', human_review_note=?,
                               period=?, year=?, event_tags=?, batch_id=?, updated_at=?
                         WHERE page_id=?
                        """,
                        (
                            item["target_source_file"], item["target_source_sha256"], item["target_source_file_size"],
                            item["pdf_page_no"], item["physical_page_no"], item["page_image_path"],
                            item["page_image_sha256"], stored_note, item["period"], item["year"],
                            item["event_tags"], batch["batch_id"], now, item["page_id"],
                        ),
                    )
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
                page_count_after = int(conn.execute("SELECT count(*) FROM pages").fetchone()[0])
                fts_missing = int(conn.execute("SELECT count(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL").fetchone()[0])
                fts_extra = int(conn.execute("SELECT count(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL").fetchone()[0])
                if integrity != "ok" or foreign_keys or page_count_after != page_count_before or fts_missing or fts_extra:
                    raise RuntimeError(f"SQLite validation failed: integrity={integrity}; fk={len(foreign_keys)}; pages={page_count_before}->{page_count_after}; fts_missing={fts_missing}; fts_extra={fts_extra}")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        after = strict_count(conn)

    final_db_sha = sha256_file(args.db)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": actual_db_sha,
        "database_sha_after": final_db_sha,
        "batch_sha": expected_db_sha,
        "decisions": len(decisions),
        "accepted_decisions": len(accepted),
        "validation_errors": errors,
        "strict_citation_count_before": before,
        "strict_citation_count_after": after,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "body_text_included": False,
        "page_text_modified": False,
        "source_assets_modified": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
