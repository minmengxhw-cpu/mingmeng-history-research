#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract conservative, locator-only semantic signals from local primary texts.

This is a machine triage layer for the local staging database. It does not
make historical claims, bind OCR to a physical page, or promote any object to
citation-ready/human-verified. Only bounded term counts and line locators are
stored; body excerpts are deliberately not persisted.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730/semantic_signals"

LEXICON = {
    "event": [
        "成立", "三中全会", "二中全会", "宣言", "声明", "解散", "政协", "内战",
        "宪政", "参政会", "政治报告", "统一战线", "新政协",
    ],
    "organization": [
        "中国民主同盟", "民盟", "国民党", "中国共产党", "国民参政会", "南京政府",
    ],
    "person": [
        "张澜", "沈钧儒", "章伯钧", "罗隆基", "闻一多", "李公朴", "杜斌丞",
        "周恩来", "毛泽东",
    ],
    "place": [
        "上海", "重庆", "昆明", "南京", "西安", "香港", "陕西", "北平", "北京",
    ],
}

DATE_RE = re.compile(r"(?:19|20)\d{2}(?:[年.\-/]\d{1,2}(?:[月.\-/]\d{1,2})?)?")
HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s+|[一二三四五六七八九十百]+、|（[一二三四五六七八九十]+）|\([一二三四五六七八九十]+\))")


def resolve(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(text: str) -> dict:
    lines = text.splitlines()
    headings = []
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped and HEADING_RE.search(line):
            headings.append({"line_no": line_no, "heading": stripped[:240]})
    headings = headings[:80]
    dates = []
    for line_no, line in enumerate(lines, start=1):
        for match in DATE_RE.finditer(line):
            dates.append({"line_no": line_no, "date": match.group(0)})
    dates = dates[:120]
    term_counts = {}
    term_locations = {}
    for category, terms in LEXICON.items():
        counts = Counter()
        locations = {}
        for term in terms:
            hits = [(line_no, line.find(term) + 1) for line_no, line in enumerate(lines, start=1) if term in line]
            if hits:
                counts[term] = len(hits)
                locations[term] = [{"line_no": n, "column": col} for n, col in hits[:20]]
        term_counts[category] = dict(counts)
        term_locations[category] = locations
    return {
        "line_count": len(lines),
        "nonempty_line_count": sum(bool(line.strip()) for line in lines),
        "heading_count": len(headings),
        "headings": headings,
        "date_signal_count": len(dates),
        "date_signals": dates,
        "term_counts": term_counts,
        "term_locations": term_locations,
        "machine_signal_status": "SIGNALS_EXTRACTED_REVIEW_REQUIRED",
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS local_semantic_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id TEXT NOT NULL UNIQUE,
            title TEXT,
            text_sha256 TEXT,
            signal_json TEXT NOT NULL,
            machine_signal_status TEXT NOT NULL,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    rows = conn.execute(
        """
        SELECT l.object_id, l.title, l.derived_text_path, l.derived_text_sha256,
               l.document_class, l.relation_status, a.quality_status
        FROM local_source_objects l
        LEFT JOIN local_text_audit a ON a.object_id=l.object_id
        WHERE l.document_class IN ('historical_primary_candidate', 'historical_primary_related_source')
        ORDER BY l.object_id
        """
    ).fetchall()
    records = []
    status_counts = Counter()
    for row in rows:
        path = resolve(row["derived_text_path"])
        record = {
            "object_id": row["object_id"],
            "title": row["title"],
            "document_class": row["document_class"],
            "relation_status": row["relation_status"],
            "text_path": str(path) if path else None,
            "expected_text_sha256": row["derived_text_sha256"],
            "text_read": False,
            "signal_status": "HOLD_TEXT_PATH_MISSING",
            "signals": {},
        }
        if path and path.exists() and row["quality_status"] == "TEXT_STRUCTURE_READY":
            text_sha = sha256_file(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            signals = extract(text)
            signals["text_sha256"] = text_sha
            record["text_read"] = True
            record["signal_status"] = signals["machine_signal_status"]
            record["signals"] = signals
            conn.execute(
                """
                INSERT INTO local_semantic_signals
                (object_id,title,text_sha256,signal_json,machine_signal_status,
                 semantic_validation_done,citation_ready,human_verified)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(object_id) DO UPDATE SET
                  title=excluded.title,
                  text_sha256=excluded.text_sha256,
                  signal_json=excluded.signal_json,
                  machine_signal_status=excluded.machine_signal_status,
                  semantic_validation_done=0,
                  citation_ready=0,
                  human_verified=0
                """,
                (row["object_id"], row["title"], text_sha, json.dumps(signals, ensure_ascii=False),
                 signals["machine_signal_status"], 0, 0, 0),
            )
        status_counts[record["signal_status"]] += 1
        records.append(record)
    conn.commit()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    total_terms = Counter()
    for record in records:
        for category, values in record.get("signals", {}).get("term_counts", {}).items():
            total_terms[category] += sum(values.values())
    report = {
        "run_id": "local_primary_semantic_signals_20260730",
        "scope": "local staging historical_primary_candidate and historical_primary_related_source only",
        "input_rows": len(rows),
        "signal_rows_written": sum(1 for r in records if r["text_read"]),
        "status_counts": dict(status_counts),
        "category_hit_totals": dict(total_terms),
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
        "staging_integrity": integrity,
    }
    (OUT / "LOCAL_PRIMARY_SEMANTIC_SIGNALS.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
    )
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
