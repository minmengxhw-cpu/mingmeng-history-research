#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit readability/structure of local OCR or derived text in staging.

This reads local text bodies only to compute machine quality signals. It does
not assert historical truth, extract claims, or promote citation status.
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
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def audit_text(path: Path, expected_sha: str | None) -> dict:
    reasons: list[str] = []
    actual_sha = sha256_file(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    chars = len(text)
    lines = text.splitlines()
    han = len(re.findall(r"[\u3400-\u9fff]", text))
    replacement = text.count("�")
    headings = len(re.findall(r"(?m)^\s{0,3}#{1,6}\s+", text))
    page_markers = len(re.findall(r"第\s*\d+\s*页|page[- _]?\d+", text, flags=re.I))
    date_signals = len(re.findall(r"(?:19|20)\d{2}", text))
    nonempty = sum(bool(line.strip()) for line in lines)
    if expected_sha and actual_sha != expected_sha:
        reasons.append("TEXT_SHA_MISMATCH")
    if chars < 80:
        reasons.append("TEXT_TOO_SHORT")
    if han < 20:
        reasons.append("LOW_HAN_CHARACTER_COUNT")
    if replacement and replacement / max(chars, 1) > 0.01:
        reasons.append("REPLACEMENT_CHARACTER_RATIO_HIGH")
    status = "TEXT_STRUCTURE_READY" if not reasons else "HOLD_TEXT_STRUCTURE"
    return {
        "text_path": str(path),
        "text_sha256": actual_sha,
        "char_count": chars,
        "line_count": len(lines),
        "nonempty_line_count": nonempty,
        "han_character_count": han,
        "replacement_character_count": replacement,
        "heading_count": headings,
        "page_marker_count": page_markers,
        "date_signal_count": date_signals,
        "quality_status": status,
        "quality_reasons": reasons,
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    source_rows = conn.execute("SELECT object_id,title,derived_text_path,derived_text_sha256,document_class,relation_status FROM local_source_objects ORDER BY object_id").fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS local_text_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id TEXT NOT NULL UNIQUE,
            text_path TEXT,
            text_sha256 TEXT,
            char_count INTEGER NOT NULL DEFAULT 0,
            line_count INTEGER NOT NULL DEFAULT 0,
            nonempty_line_count INTEGER NOT NULL DEFAULT 0,
            han_character_count INTEGER NOT NULL DEFAULT 0,
            replacement_character_count INTEGER NOT NULL DEFAULT 0,
            heading_count INTEGER NOT NULL DEFAULT 0,
            page_marker_count INTEGER NOT NULL DEFAULT 0,
            date_signal_count INTEGER NOT NULL DEFAULT 0,
            quality_status TEXT NOT NULL,
            quality_reasons_json TEXT NOT NULL,
            body_read_by_audit INTEGER NOT NULL DEFAULT 1,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    results = []
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    for row in source_rows:
        path = resolve(row["derived_text_path"])
        if path is None or not path.exists():
            audit = {
                "text_path": str(path) if path else None,
                "text_sha256": None,
                "char_count": 0,
                "line_count": 0,
                "nonempty_line_count": 0,
                "han_character_count": 0,
                "replacement_character_count": 0,
                "heading_count": 0,
                "page_marker_count": 0,
                "date_signal_count": 0,
                "quality_status": "HOLD_TEXT_PATH_MISSING",
                "quality_reasons": ["TEXT_PATH_MISSING"],
            }
        else:
            audit = audit_text(path, row["derived_text_sha256"])
        status_counts[audit["quality_status"]] += 1
        for reason in audit["quality_reasons"]:
            reason_counts[reason] += 1
        conn.execute(
            """
            INSERT INTO local_text_audit
            (object_id,text_path,text_sha256,char_count,line_count,nonempty_line_count,
             han_character_count,replacement_character_count,heading_count,
             page_marker_count,date_signal_count,quality_status,quality_reasons_json,
             body_read_by_audit,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,0,0)
            ON CONFLICT(object_id) DO UPDATE SET
              text_path=excluded.text_path,
              text_sha256=excluded.text_sha256,
              char_count=excluded.char_count,
              line_count=excluded.line_count,
              nonempty_line_count=excluded.nonempty_line_count,
              han_character_count=excluded.han_character_count,
              replacement_character_count=excluded.replacement_character_count,
              heading_count=excluded.heading_count,
              page_marker_count=excluded.page_marker_count,
              date_signal_count=excluded.date_signal_count,
              quality_status=excluded.quality_status,
              quality_reasons_json=excluded.quality_reasons_json,
              body_read_by_audit=1,
              citation_ready=0,
              human_verified=0
            """,
            (
                row["object_id"], audit["text_path"], audit["text_sha256"],
                audit["char_count"], audit["line_count"], audit["nonempty_line_count"],
                audit["han_character_count"], audit["replacement_character_count"],
                audit["heading_count"], audit["page_marker_count"], audit["date_signal_count"],
                audit["quality_status"], json.dumps(audit["quality_reasons"], ensure_ascii=False),
            ),
        )
        results.append({"object_id": row["object_id"], "title": row["title"], "document_class": row["document_class"], "relation_status": row["relation_status"], **audit, "citation_ready": False, "human_verified": False})
    conn.commit()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()

    output = OUT / "LOCAL_TEXT_STRUCTURE_AUDIT.jsonl"
    output.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in results) + ("\n" if results else ""), encoding="utf-8")
    report = {
        "report": "LOCAL_TEXT_STRUCTURE_AUDIT_20260730",
        "rows": len(results),
        "status_counts": dict(sorted(status_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "body_read_by_audit": True,
        "semantic_validation_done": 0,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "staging_db_written": True,
        "formal_db_written": False,
        "staging_integrity": integrity,
        "rule": "text structure/readability signals only; no historical truth or citation approval",
        "output": str(output),
    }
    (OUT / "LOCAL_TEXT_STRUCTURE_AUDIT_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
