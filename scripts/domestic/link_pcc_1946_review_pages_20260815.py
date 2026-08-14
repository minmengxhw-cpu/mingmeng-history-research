#!/usr/bin/env python3
"""Link the imported 1946 PCC sourcebook pages to the topic index.

The links are navigation-only.  They deliberately accept only the exact
``review_only``/L2 pages imported by the companion importer and never change
page provenance or citation status.
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
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DOC_KEY = "domestic-ocr/NLC:pcc-1946-sourcebook-target-pages-ocr"
EVENT_ID = "domestic-1946-pcc"
EVENT_NAME = "1946年旧政协：民盟发言页、机关报交叉页与《政協文獻》档案目标地图"
BATCH_ID = "pcc-1946-sourcebook-event-links-20260815"
PAGE_LABELS = [
    "pdf-023 / printed-016 / 张澜开会词",
    "pdf-024 / adjacent-continuation",
    "pdf-052 / printed-045 / 张君劢闭会词",
    "pdf-062 / printed-055 / 罗隆基报告民主同盟意见",
    "pdf-063 / adjacent-continuation",
    "pdf-101 / printed-094 / 民主同盟的提案",
    "pdf-125 / printed-116 / 章伯钧说明民主同盟的意见",
    "pdf-126 / adjacent-continuation",
    "pdf-206 / printed-197 / 张澜三月二十一日谈话",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for label in PAGE_LABELS:
        row = conn.execute(
            """SELECT d.id AS document_id,d.doc_key,d.title,d.source_platform,
                      p.id AS page_id,p.page_label,p.page_url,
                      pp.source_sha256,pp.citation_ready,pp.needs_human_review,
                      pp.review_status,pp.event_tags
               FROM documents d
               JOIN pages p ON p.document_id=d.id AND p.page_label=?
               JOIN page_provenance pp ON pp.page_id=p.id
               WHERE d.doc_key=?""",
            (label, DOC_KEY),
        ).fetchone()
        if row is None:
            raise ValueError(f"missing formal page: {DOC_KEY} / {label}")
        if row["source_platform"] != "domestic":
            raise ValueError(f"non-domestic page: {label}")
        if row["review_status"] != "review_only" or int(row["citation_ready"] or 0) != 0 or int(row["needs_human_review"] or 0) != 1:
            raise ValueError(f"page is not review_only: {label}")
        rows.append(dict(row))
    return rows


def link_rows(rows: list[dict[str, object]]) -> list[tuple[object, ...]]:
    links = []
    for row in rows:
        links.append(
            (
                "topic",
                EVENT_ID,
                EVENT_NAME,
                row["page_id"],
                "1946",
                "1946",
                row["title"],
                "专题导航关联（仅导航层，非事实断言）：该页是 L2《政協文獻》汇编的页级 OCR 检索入口；正文与页界仍需人工复核，不能替代旧政协正式会议档案或独立原始记录。",
                "",
                "导航层;L2汇编;review_only;待人工复核",
                "",
                "",
                10,
            )
        )
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--expected-sha")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")
    before = sha256(db)
    if args.expected_sha and args.expected_sha != before:
        raise SystemExit(f"database SHA mismatch: expected={args.expected_sha} actual={before}")
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        rows = collect(conn)
        links = link_rows(rows)
        existing = conn.execute(
            "SELECT count(*) FROM research_events WHERE scope_slug=? AND page_id IN ({})".format(",".join("?" for _ in rows)),
            [EVENT_ID] + [row["page_id"] for row in rows],
        ).fetchone()[0]

    report: dict[str, object] = {
        "batch_id": BATCH_ID,
        "mode": "apply" if args.apply else "dry_run",
        "gate": "PASS",
        "body_read": False,
        "document_key": DOC_KEY,
        "event_id": EVENT_ID,
        "page_count": len(rows),
        "page_ids": [int(row["page_id"]) for row in rows],
        "existing_event_rows": int(existing),
        "before_sha256": before,
        "rows_inserted": 0,
    }
    if args.apply:
        if not args.expected_sha or args.expected_sha != before:
            raise SystemExit("--apply requires --expected-sha matching the current DB")
        if not args.backup:
            raise SystemExit("--apply requires --backup")
        backup = args.backup.expanduser().resolve()
        if backup.exists():
            raise SystemExit(f"refusing to overwrite existing backup: {backup}")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db, backup)
        if sha256(backup) != before:
            raise SystemExit("event-link backup SHA mismatch")
        with sqlite3.connect(db) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            for link in links:
                conn.execute(
                    """INSERT OR IGNORE INTO research_events(
                        scope_type,scope_slug,scope_name,page_id,event_date,event_year,
                        event_title,event_summary,actors,tags,places,organizations,importance)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    link,
                )
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
            if integrity != "ok" or fk:
                conn.rollback()
                raise SystemExit(f"validation failed: integrity={integrity}, foreign_keys={fk}")
            conn.commit()
            inserted = conn.total_changes
        report["rows_inserted"] = inserted
        report["backup"] = str(backup)
        report["integrity_check"] = "ok"
        report["foreign_key_violations"] = 0
        report["after_sha256"] = sha256(db)
    else:
        report["after_sha256"] = before
        report["next_action"] = "rerun with --apply and --expected-sha after reviewing the metadata-only link rows"

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
