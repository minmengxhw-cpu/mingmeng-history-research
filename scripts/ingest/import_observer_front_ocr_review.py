#!/usr/bin/env python3
"""Import the audited Observer front/contents OCR as non-citation search drafts.

The importer is additive and idempotent: it never deletes or overwrites local
files or existing SQLite rows. Existing document keys are reported and skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data/research_index.sqlite"
QA = ROOT / "work/domestic/OBSERVER_FRONT_OCR_QA_20260728.json"
PAGE_MANIFEST = ROOT / "work/domestic/OBSERVER_FRONT_OCR_MANIFEST_20260728.jsonl"
ISSUE_MANIFEST = ROOT / "work/domestic/OBSERVER_V3_ISSUE_MANIFEST_20260728.jsonl"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def recognized_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if "## 识别文本" in text:
        text = text.split("## 识别文本", 1)[1]
    if "## 明细" in text:
        text = text.split("## 明细", 1)[0]
    return text.strip()


def validate() -> tuple[list[dict], dict[int, dict]]:
    qa = json.loads(QA.read_text(encoding="utf-8"))
    if qa.get("gate") != "PASS":
        raise ValueError(f"OCR QA gate is not PASS: {qa.get('gate')}")
    pages = load(PAGE_MANIFEST)
    issues = {int(row["issue_number"]): row for row in load(ISSUE_MANIFEST)}
    if len(pages) != 24 or len(issues) != 12:
        raise ValueError(f"unexpected manifest sizes pages={len(pages)} issues={len(issues)}")
    for row in pages:
        ocr = ROOT / row["ocr_markdown"]
        if not ocr.is_file() or sha256(ocr) != row.get("ocr_markdown_sha256"):
            raise ValueError(f"OCR SHA gate failed: {row['record_id']}")
        if row.get("citation_ready") is not False:
            raise ValueError(f"citation_ready must be false: {row['record_id']}")
        issue = issues[int(row["issue_number"])]
        pdf = ROOT / issue["derived_issue_pdf"]
        if not pdf.is_file() or sha256(pdf) != issue["derived_issue_sha256"]:
            raise ValueError(f"derived PDF SHA gate failed: issue {row['issue_number']}")
        if row.get("source_pdf_sha256") != issue["derived_issue_sha256"]:
            raise ValueError(f"manifest PDF SHA mismatch: {row['record_id']}")
        if not recognized_text(ocr):
            raise ValueError(f"empty OCR text: {row['record_id']}")
    return pages, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--batch-id", default="observer-front-ocr-20260728")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    pages, issues = validate()
    grouped: dict[int, list[dict]] = {}
    for row in pages:
        grouped.setdefault(int(row["issue_number"]), []).append(row)
    report = {
        "batch_id": args.batch_id,
        "mode": "apply" if args.apply else "dry_run",
        "gate": "PASS",
        "issues": len(grouped),
        "ocr_pages": len(pages),
        "inserted_documents": 0,
        "inserted_pages": 0,
        "skipped_existing": [],
        "backup": None,
    }
    if args.apply:
        backup = args.db.with_name(args.db.name + "." + args.batch_id + ".pre.bak")
        if not backup.exists():
            shutil.copy2(args.db, backup)
        report["backup"] = str(backup)

    with sqlite3.connect(args.db) as conn:
        conn.row_factory = sqlite3.Row
        has_platform = "source_platform" in {row[1] for row in conn.execute("pragma table_info(documents)")}
        for issue_number in sorted(grouped):
            issue_rows = sorted(grouped[issue_number], key=lambda row: row["page_label"])
            issue = issues[issue_number]
            doc_key = f"domestic-ocr/NLC:observer-1947-v3n{issue_number:02d}-front-ocr"
            existing = conn.execute("select id from documents where doc_key=?", (doc_key,)).fetchone()
            if existing:
                report["skipped_existing"].append(doc_key)
                continue
            source_key = f"domestic-ocr:NLC:observer-1947-v3n{issue_number:02d}-front-ocr"
            source = conn.execute("select id from sources where source_id=?", (source_key,)).fetchone()
            pdf_path = str((ROOT / issue["derived_issue_pdf"]).resolve())
            source_title = f"《观察》第三卷第{issue_number}期封面/目录 OCR 草稿"
            if source:
                source_id = source[0]
            elif args.apply:
                source_id = conn.execute(
                    "insert into sources(source_type,source_id,title,origin_url,local_path) values(?,?,?,?,?)",
                    ("domestic_ocr_review", source_key, source_title, "https://commons.wikimedia.org/wiki/File:SSID-13679264_%E8%A7%82%E5%AF%9F_%E7%AC%AC3%E5%8D%B7%E7%AC%AC1-12%E6%9C%9F.pdf", pdf_path),
                ).lastrowid
            else:
                source_id = None
            matched = "observer,1947,front_matter,contents,ocr_draft,citation_ready=false,needs_human_review=true"
            columns = ["source_id", "doc_key", "volume_id", "volume_title", "doc_id", "doc_number", "title", "date_guess", "url", "local_txt", "hit_type", "matched_terms"]
            values = [source_id, doc_key, "NLC-OBS-V3", "《观察》第三卷", f"OBSERVER-V3N{issue_number:02d}-1947", f"第{issue_number}期", source_title, issue["document_date"], "https://commons.wikimedia.org/wiki/File:SSID-13679264_%E8%A7%82%E5%AF%9F_%E7%AC%AC3%E5%8D%B7第1-12期.pdf", pdf_path, "domestic_ocr_review_only", matched]
            if has_platform:
                columns.append("source_platform")
                values.append("domestic")
            if not args.apply:
                report["inserted_documents"] += 1
                report["inserted_pages"] += len(issue_rows)
                continue
            document_id = conn.execute(
                f"insert into documents({','.join(columns)}) values({','.join('?' for _ in columns)})", values
            ).lastrowid
            for row in issue_rows:
                ocr_path = ROOT / row["ocr_markdown"]
                text = recognized_text(ocr_path)
                page = conn.execute(
                    "insert into pages(document_id,page_label,page_url,text) values(?,?,?,?)",
                    (document_id, row["page_label"], str(ocr_path), text),
                )
                page_id = page.lastrowid
                conn.execute(
                    "insert into page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) values(?,?,?,?,?,?,?)",
                    (page_id, "NLC-OBS-V3", f"OBSERVER-V3N{issue_number:02d}-1947", source_title, row["page_label"], matched, text),
                )
                report["inserted_pages"] += 1
            report["inserted_documents"] += 1
        if args.apply:
            conn.commit()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report["applied_at"] = datetime.now().isoformat(timespec="seconds") if args.apply else None
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
