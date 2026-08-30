#!/usr/bin/env python3
"""Import verified local academic HTML full-text pointers into the formal index.

The importer is deliberately narrow:

* only S/A scholarly records with an existing, SHA-matching local HTML file;
* one searchable full-text page per HTML item;
* ``review_only`` and ``citation_ready=0`` are hard-coded;
* no source file is copied, moved, deleted, or exposed through a public route;
* dry-run is the default and apply requires an exact formal-DB SHA plus a
  caller-supplied backup path.

This makes academic research searchable without confusing a later scholarly
HTML reproduction with a page-level primary source.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FORMAL_DB = ROOT / "data/research_index.sqlite"
DEFAULT_STAGING_DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
HTML_STATUSES = {"FULLTEXT_HTML_CANDIDATE", "FULLTEXT_HTML", "ACQUIRED_PUBLIC_HTML"}
TIERS = {"S", "A"}
BATCH_ID = "academic-html-formal-20260813"


class VisibleTextParser(HTMLParser):
    """Small HTML-to-text parser that drops navigation and non-content tags."""

    SKIP = {"script", "style", "noscript", "svg", "nav", "header", "footer", "form"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP:
            self.depth += 1
        elif not self.depth and tag.lower() in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP and self.depth:
            self.depth -= 1
        elif not self.depth and tag.lower() in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.depth:
            self.parts.append(data)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def html_text(path: Path) -> str:
    parser = VisibleTextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    text = html.unescape("".join(parser.parts))
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def resolve_source(value: str, source_root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else source_root / path


def stable_source_path(path: Path, source_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(source_root.resolve()))
    except ValueError:
        return str(path.resolve())


def parse_metadata(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def read_candidates(staging_db: Path, source_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not staging_db.is_file():
        return [], [{"status": "blocked", "reason": "staging database missing", "path": str(staging_db)}]
    with sqlite3.connect(f"file:{staging_db}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT external_id, title, author, institution, publication_date,
                      research_type, quality_tier, source_url, local_path,
                      sha256, fulltext_status, review_status, metadata_json
               FROM domestic_research_materials
               WHERE layer='SCHOLARLY_RESEARCH'
                 AND quality_tier IN ('S','A')
                 AND fulltext_status IN ('FULLTEXT_HTML_CANDIDATE','FULLTEXT_HTML','ACQUIRED_PUBLIC_HTML')
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
        expected = str(record.get("sha256") or "").lower()
        actual = sha256_file(source)
        record["sha256_actual"] = actual
        if len(expected) != 64 or actual != expected:
            holds.append({"external_id": record["external_id"], "status": "hold_sha_mismatch", "expected": expected, "actual": actual})
            continue
        text = html_text(source)
        record["text_chars"] = len(text)
        if len(text) < 500:
            holds.append({"external_id": record["external_id"], "status": "hold_short_text", "text_chars": len(text)})
            continue
        record["_text"] = text
        selected.append(record)
    return selected, holds


def formal_sha(db_path: Path) -> str:
    return sha256_file(db_path.resolve())


def existing_keys(db_path: Path, records: list[dict[str, Any]]) -> set[str]:
    if not db_path.exists():
        return set()
    keys = [f"domestic-academic/{row['external_id']}" for row in records]
    with sqlite3.connect(db_path) as conn:
        placeholders = ",".join("?" for _ in keys)
        rows = conn.execute(f"SELECT doc_key FROM documents WHERE doc_key IN ({placeholders})", keys).fetchall() if keys else []
    return {str(row[0]) for row in rows}


def tags_for(record: dict[str, Any]) -> str:
    metadata = parse_metadata(str(record.get("metadata_json") or "{}"))
    events = metadata.get("events") if isinstance(metadata.get("events"), list) else []
    periods = metadata.get("historical_periods") if isinstance(metadata.get("historical_periods"), list) else []
    tags = [
        "academic_layer=scholarly_research",
        "evidence_role=secondary_interpretation",
        "source_kind=local_verified_html",
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
    keys = existing_keys(db_path, records)
    new_records = [row for row in records if f"domestic-academic/{row['external_id']}" not in keys]
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
                "fulltext_status": row["fulltext_status"],
                "text_chars": row["text_chars"],
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


def bigramize(text: str) -> str:
    cjk = re.compile(r"[\u3400-\u9fff]+")
    output: list[str] = []
    last = 0
    for match in cjk.finditer(text):
        if match.start() > last:
            output.append(text[last : match.start()])
        segment = match.group(0)
        output.extend(segment[index : index + 2] for index in range(len(segment) - 1))
        last = match.end()
    if last < len(text):
        output.append(text[last:])
    return " ".join(part for part in output if part)


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
            source_key = f"domestic-academic:{record['external_id']}"
            conn.execute(
                """INSERT INTO sources(source_type,source_id,title,origin_url,local_path)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(source_id) DO UPDATE SET
                     title=excluded.title, origin_url=excluded.origin_url, local_path=excluded.local_path""",
                ("domestic_academic_fulltext", source_key, record["title"], record.get("source_url"), record["stable_source"]),
            )
            source_id = conn.execute("SELECT id FROM sources WHERE source_id=?", (source_key,)).fetchone()[0]
            tags = tags_for(record)
            document_id = conn.execute(
                """INSERT INTO documents(source_id,doc_key,volume_id,volume_title,doc_id,title,
                       date_guess,url,local_html,hit_type,matched_terms,source_platform)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    source_id,
                    doc_key,
                    "DOMESTIC-ACADEMIC",
                    "国内学术研究资料",
                    record["external_id"],
                    record["title"],
                    record.get("publication_date"),
                    record.get("source_url"),
                    record["stable_source"],
                    "domestic_academic_fulltext",
                    tags,
                    "domestic",
                ),
            ).lastrowid
            page_url = record.get("source_url") or f"file://{record['stable_source']}#text"
            page_id = conn.execute(
                "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                (document_id, "full-text", page_url, record["_text"]),
            ).lastrowid
            conn.execute(
                "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-ACADEMIC", record["external_id"], record["title"], "full-text", tags, record["_text"]),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "DOMESTIC-ACADEMIC", record["external_id"], record["title"], "full-text", tags, bigramize(record["_text"])),
            )
            metadata = parse_metadata(str(record.get("metadata_json") or "{}"))
            periods = metadata.get("historical_periods") if isinstance(metadata.get("historical_periods"), list) else []
            publication_match = re.search(r"(19|20)\d{2}", str(record.get("publication_date") or ""))
            year = int(publication_match.group(0)) if publication_match else None
            conn.execute(
                """INSERT INTO page_provenance(
                    page_id,document_id,source_id,source_file,source_sha256,source_file_size,
                    physical_page_no,ocr_md_path,ocr_md_sha256,ocr_mode,text_chars,
                    citation_ready,needs_human_review,review_status,machine_review_note,
                    period,year,event_tags,source_title,batch_id,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    page_id,
                    document_id,
                    source_key,
                    record["stable_source"],
                    record["sha256_actual"],
                    Path(record["resolved_source"]).stat().st_size,
                    1,
                    None,
                    None,
                    "electronic_html_import",
                    record["text_chars"],
                    0,
                    1,
                    "review_only",
                    "学术 HTML 正文已入检索库；它是解释层材料，尚未完成页级/版本/引用复核。",
                    "；".join(str(value) for value in periods[:8]),
                    year,
                    tags,
                    record["title"],
                    BATCH_ID,
                    now,
                    now,
                ),
            )
            imported.append({"external_id": record["external_id"], "document_id": document_id, "page_id": page_id, "text_chars": record["text_chars"]})
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
        pages = conn.execute("SELECT count(*) FROM pages").fetchone()[0]
        fts = conn.execute("SELECT count(*) FROM page_fts").fetchone()[0]
        bigram = conn.execute("SELECT count(*) FROM page_fts_bigram").fetchone()[0]
    return {
        "imported": imported,
        "imported_records": len(imported),
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
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    selected, holds = read_candidates(args.staging_db, args.source_root.expanduser().resolve())
    prepared = prepare(selected, args.formal_db)
    blocking_holds = [
        hold for hold in holds if hold.get("status") in {"blocked", "hold_missing_file", "hold_sha_mismatch"}
    ]
    report: dict[str, Any] = {
        "batch_id": BATCH_ID,
        "mode": "apply" if args.apply else "dry_run",
        "staging_db": str(args.staging_db),
        "source_root": str(args.source_root.expanduser().resolve()),
        "body_read": True,
        "source_files_copied": False,
        "holds": holds,
        "gate": "BLOCKED" if blocking_holds else ("PASS" if not holds else "PASS_WITH_HOLDS"),
        "blocking_holds": blocking_holds,
        **{key: value for key, value in prepared.items() if key != "new_records_data"},
    }
    if args.apply:
        if blocking_holds:
            raise SystemExit("--apply blocked by missing or SHA-mismatched source inputs")
        if not args.expected_db_sha or prepared["formal_db_sha256"] != args.expected_db_sha:
            raise SystemExit("--apply requires --expected-db-sha matching the current formal DB")
        if not args.backup:
            raise SystemExit("--apply requires --backup outside the repository")
        result = apply(prepared["new_records_data"], args.formal_db, args.backup.expanduser().resolve())
        report["apply_result"] = result
        report["formal_db_sha256_after"] = formal_sha(args.formal_db)
        report["gate"] = (
            "PASS"
            if result["integrity_check"] == "ok" and result["foreign_key_violations"] == 0
            else "FAIL"
        )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    printable = {key: value for key, value in report.items() if key != "selected"}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0 if report["gate"] in {"PASS", "PASS_WITH_HOLDS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
