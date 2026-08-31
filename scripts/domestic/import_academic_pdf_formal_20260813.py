#!/usr/bin/env python3
"""Import locally verified, machine-readable academic PDFs into the formal index.

This importer is intentionally narrower than a primary-source importer:

* only S/A scholarly records with a SHA-matching local PDF are considered;
* Poppler page boundaries are retained as physical/PDF page numbers;
* all imported pages remain ``review_only`` and ``citation_ready=0``;
* image-only or nearly empty PDFs are held for OCR/visual review;
* dry-run is the default and apply requires an exact DB SHA plus a backup.

The PDF is never copied, moved, deleted, or treated as a formally reviewed
source.  The extracted page text is a searchable research aid only.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from import_academic_html_formal_20260813 import (
    bigramize,
    formal_sha,
    parse_metadata,
    resolve_source,
    sha256_file,
    stable_source_path,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FORMAL_DB = ROOT / "data/research_index.sqlite"
DEFAULT_STAGING_DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
DEFAULT_PDFTOTEXT = Path(
    "<local-user>/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftotext"
)
BATCH_ID = "academic-pdf-formal-20260813"
TIERS = {"S", "A"}


def find_pdftotext(value: Path | None) -> Path | None:
    candidates = [value] if value else []
    candidates.extend([DEFAULT_PDFTOTEXT, Path("/opt/homebrew/bin/pdftotext"), Path("/usr/local/bin/pdftotext")])
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    return None


def extract_pdf_pages(pdf: Path, pdftotext: Path) -> tuple[list[str], str | None]:
    try:
        result = subprocess.run(
            [str(pdftotext), "-layout", str(pdf), "-"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [], f"pdftotext_error:{exc}"
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", "replace").strip()[-400:]
        return [], f"pdftotext_exit_{result.returncode}:{error}"
    text = result.stdout.decode("utf-8", "replace")
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return [page.strip() for page in pages], None


def read_candidates(
    staging_db: Path, source_root: Path, pdftotext: Path | None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not staging_db.is_file():
        return [], [{"status": "blocked", "reason": "staging database missing", "path": str(staging_db)}]
    if pdftotext is None:
        return [], [{"status": "blocked", "reason": "pdftotext not found"}]
    with sqlite3.connect(f"file:{staging_db}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT external_id, title, author, institution, publication_date,
                      research_type, quality_tier, source_url, local_path,
                      sha256, fulltext_status, review_status, metadata_json
               FROM domestic_research_materials
               WHERE layer='SCHOLARLY_RESEARCH'
                 AND quality_tier IN ('S','A')
                 AND fulltext_status='FULLTEXT_PDF'
               ORDER BY quality_tier, external_id"""
        ).fetchall()
    selected: list[dict[str, Any]] = []
    holds: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        source_value = str(record.get("local_path") or "").strip()
        source = resolve_source(source_value, source_root)
        record["resolved_source"] = str(source)
        record["stable_source"] = stable_source_path(source, source_root)
        if not source.is_file():
            holds.append({"external_id": record["external_id"], "status": "hold_missing_file", "path": source_value})
            continue
        actual = sha256_file(source)
        record["sha256_actual"] = actual
        if len(str(record.get("sha256") or "")) != 64 or actual != str(record.get("sha256") or "").lower():
            holds.append({"external_id": record["external_id"], "status": "hold_sha_mismatch", "expected": record.get("sha256"), "actual": actual})
            continue
        pages, error = extract_pdf_pages(source, pdftotext)
        if error:
            holds.append({"external_id": record["external_id"], "status": "hold_extract_error", "reason": error})
            continue
        total_chars = sum(len(page) for page in pages)
        meaningful_pages = sum(1 for page in pages if len(page) >= 100)
        record["pages"] = pages
        record["page_count"] = len(pages)
        record["text_chars"] = total_chars
        record["meaningful_pages"] = meaningful_pages
        if total_chars < 500 or meaningful_pages == 0:
            holds.append({
                "external_id": record["external_id"],
                "status": "hold_no_extractable_text",
                "page_count": len(pages),
                "text_chars": total_chars,
                "meaningful_pages": meaningful_pages,
            })
            continue
        selected.append(record)
    return selected, holds


def existing_keys(db_path: Path, records: list[dict[str, Any]]) -> set[str]:
    keys = [f"domestic-academic/{row['external_id']}" for row in records]
    if not keys or not db_path.exists():
        return set()
    with sqlite3.connect(db_path) as conn:
        marks = ",".join("?" for _ in keys)
        rows = conn.execute(f"SELECT doc_key FROM documents WHERE doc_key IN ({marks})", keys).fetchall()
    return {str(row[0]) for row in rows}


def pdf_tags(record: dict[str, Any]) -> str:
    metadata = parse_metadata(str(record.get("metadata_json") or "{}"))
    events = metadata.get("events") if isinstance(metadata.get("events"), list) else []
    periods = metadata.get("historical_periods") if isinstance(metadata.get("historical_periods"), list) else []
    tags = [
        "academic_layer=scholarly_research",
        "evidence_role=secondary_interpretation",
        "source_kind=local_verified_pdf",
        "citation_ready=false",
        "needs_human_review=true",
        f"quality_tier={record.get('quality_tier') or 'unset'}",
        f"research_type={record.get('research_type') or 'unset'}",
        f"batch={BATCH_ID}",
    ]
    tags.extend(f"event={value}" for value in events[:8])
    tags.extend(f"period={value}" for value in periods[:8])
    return ",".join(tags)


def prepare(records: list[dict[str, Any]], db_path: Path) -> dict[str, Any]:
    present = existing_keys(db_path, records)
    new_records = [row for row in records if f"domestic-academic/{row['external_id']}" not in present]
    return {
        "db_path": str(db_path),
        "formal_db_sha256": formal_sha(db_path) if db_path.exists() else None,
        "selected_records": len(records),
        "new_records": len(new_records),
        "already_present": len(records) - len(new_records),
        "selected": [
            {
                "external_id": row["external_id"],
                "title": row["title"],
                "quality_tier": row["quality_tier"],
                "page_count": row["page_count"],
                "text_chars": row["text_chars"],
                "meaningful_pages": row["meaningful_pages"],
                "source_file": row["stable_source"],
                "source_sha256": row["sha256_actual"],
                "doc_key": f"domestic-academic/{row['external_id']}",
                "citation_ready": False,
                "review_status": "review_only",
            }
            for row in new_records
        ],
        "new_records_data": new_records,
    }


def apply(records: list[dict[str, Any]], db_path: Path, backup: Path) -> dict[str, Any]:
    actual_db = db_path.resolve()
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    imported: list[dict[str, Any]] = []
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        for record in records:
            doc_key = f"domestic-academic/{record['external_id']}"
            if conn.execute("SELECT 1 FROM documents WHERE doc_key=?", (doc_key,)).fetchone():
                continue
            source_key = f"domestic-academic-pdf:{record['external_id']}"
            conn.execute(
                """INSERT INTO sources(source_type,source_id,title,origin_url,local_path)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(source_id) DO UPDATE SET
                     title=excluded.title, origin_url=excluded.origin_url, local_path=excluded.local_path""",
                ("domestic_academic_fulltext", source_key, record["title"], record.get("source_url"), record["stable_source"]),
            )
            source_id = conn.execute("SELECT id FROM sources WHERE source_id=?", (source_key,)).fetchone()[0]
            tags = pdf_tags(record)
            document_id = conn.execute(
                """INSERT INTO documents(source_id,doc_key,volume_id,volume_title,doc_id,title,
                       date_guess,url,local_txt,hit_type,matched_terms,source_platform)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    source_id, doc_key, "DOMESTIC-ACADEMIC", "国内学术研究资料", record["external_id"],
                    record["title"], record.get("publication_date"), record.get("source_url"),
                    record["stable_source"], "domestic_academic_fulltext", tags, "domestic",
                ),
            ).lastrowid
            for page_no, page_text in enumerate(record["pages"], start=1):
                page_url = (record.get("source_url") or f"file://{record['stable_source']}") + f"#page={page_no}"
                page_id = conn.execute(
                    "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                    (document_id, str(page_no), page_url, page_text),
                ).lastrowid
                conn.execute(
                    "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                    (page_id, "DOMESTIC-ACADEMIC", record["external_id"], record["title"], str(page_no), tags, page_text),
                )
                conn.execute(
                    "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                    (page_id, "DOMESTIC-ACADEMIC", record["external_id"], record["title"], str(page_no), tags, bigramize(page_text)),
                )
                metadata = parse_metadata(str(record.get("metadata_json") or "{}"))
                periods = metadata.get("historical_periods") if isinstance(metadata.get("historical_periods"), list) else []
                year_match = re.search(r"(19|20)\d{2}", str(record.get("publication_date") or ""))
                year = int(year_match.group(0)) if year_match else None
                conn.execute(
                    """INSERT INTO page_provenance(
                        page_id,document_id,source_id,source_file,source_sha256,source_file_size,
                        pdf_page_no,physical_page_no,ocr_engine,ocr_mode,text_chars,
                        citation_ready,needs_human_review,review_status,machine_review_note,
                        period,year,event_tags,source_title,batch_id,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        page_id, document_id, source_key, record["stable_source"], record["sha256_actual"],
                        Path(record["resolved_source"]).stat().st_size, page_no, page_no, "poppler",
                        "electronic_pdf_import", len(page_text), 0, 1, "review_only",
                        "电子 PDF 文本已按物理页导入检索库；页面视觉、版本与引用位置尚未人工复核。",
                        "；".join(str(value) for value in periods[:8]), year, tags, record["title"],
                        BATCH_ID, now, now,
                    ),
                )
                imported.append({"external_id": record["external_id"], "document_id": document_id, "page_id": page_id, "page_no": page_no, "text_chars": len(page_text)})
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
        pages = conn.execute("SELECT count(*) FROM pages").fetchone()[0]
        fts = conn.execute("SELECT count(*) FROM page_fts").fetchone()[0]
        bigram = conn.execute("SELECT count(*) FROM page_fts_bigram").fetchone()[0]
    return {
        "imported": imported,
        "imported_records": len({item["external_id"] for item in imported}),
        "imported_pages": len(imported),
        "integrity_check": integrity,
        "foreign_key_violations": len(foreign_keys),
        "pages": pages,
        "page_fts": fts,
        "page_fts_bigram": bigram,
        "backup": str(backup),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-db", type=Path, default=DEFAULT_FORMAL_DB)
    parser.add_argument("--staging-db", type=Path, default=DEFAULT_STAGING_DB)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--pdftotext", type=Path)
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    pdftotext = find_pdftotext(args.pdftotext)
    selected, holds = read_candidates(args.staging_db, args.source_root.expanduser().resolve(), pdftotext)
    prepared = prepare(selected, args.formal_db)
    blocking_holds = [hold for hold in holds if hold.get("status") in {"blocked", "hold_missing_file", "hold_sha_mismatch", "hold_extract_error"}]
    report: dict[str, Any] = {
        "batch_id": BATCH_ID,
        "mode": "apply" if args.apply else "dry_run",
        "staging_db": str(args.staging_db),
        "source_root": str(args.source_root.expanduser().resolve()),
        "pdftotext": str(pdftotext) if pdftotext else None,
        "body_read": True,
        "source_files_copied": False,
        "holds": holds,
        "blocking_holds": blocking_holds,
        "gate": "BLOCKED" if blocking_holds else ("PASS" if not holds else "PASS_WITH_HOLDS"),
        **{key: value for key, value in prepared.items() if key != "new_records_data"},
    }
    if args.apply:
        if blocking_holds:
            raise SystemExit("--apply blocked by missing, mismatched, or unextractable source inputs")
        if not args.expected_db_sha or prepared["formal_db_sha256"] != args.expected_db_sha:
            raise SystemExit("--apply requires --expected-db-sha matching the current formal DB")
        if not args.backup:
            raise SystemExit("--apply requires --backup outside the repository")
        result = apply(prepared["new_records_data"], args.formal_db, args.backup.expanduser().resolve())
        report["apply_result"] = result
        report["formal_db_sha256_after"] = formal_sha(args.formal_db)
        report["gate"] = "PASS" if result["integrity_check"] == "ok" and result["foreign_key_violations"] == 0 else "FAIL"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    printable = {key: value for key, value in report.items() if key != "selected"}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0 if report["gate"] in {"PASS", "PASS_WITH_HOLDS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
