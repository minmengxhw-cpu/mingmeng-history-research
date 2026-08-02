#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register normalized local OCR document objects in the staging local layer.

This imports metadata pointers only. The OCR Markdown already exists at the
recorded local path; the script does not read its body, copy it, or modify the
formal database. All objects remain non-citation-ready until source review.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OBJECTS = ROOT / "work/domestic/local_private_ocr_metadata_20260730/LOCAL_DOCUMENT_OBJECTS.jsonl"
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730"


def period_value(signals: list[str]) -> str | None:
    return signals[0] if signals else None


def main() -> None:
    objects = [json.loads(line) for line in OBJECTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    domestic = [row for row in objects if row["scope"] != "overseas_out_of_domestic_scope"]
    conn = sqlite3.connect(DB)
    conn.execute("BEGIN")
    for row in domestic:
        if row["document_class"] == "historical_primary_candidate":
            relation = "OCR_ONLY_HISTORICAL_PRIMARY_CANDIDATE"
        elif row["document_class"] == "retrospective_local_history":
            relation = "OCR_ONLY_RETROSPECTIVE_REQUIRES_SOURCE_REVIEW"
        elif row["document_class"] == "catalog_or_cover":
            relation = "CATALOG_OR_COVER_NOT_ORIGINAL"
        else:
            relation = "OCR_ONLY_REQUIRES_SOURCE_REVIEW"
        conn.execute(
            """
            INSERT INTO local_source_objects
            (object_id,title,document_date,source_path,source_sha256,source_bytes,
             derived_text_path,derived_text_sha256,source_layer,document_class,
             relation_status,evidence_status,citation_ready,human_verified,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(object_id) DO UPDATE SET
              title=excluded.title,
              document_date=excluded.document_date,
              source_path=excluded.source_path,
              source_sha256=excluded.source_sha256,
              source_bytes=excluded.source_bytes,
              derived_text_path=excluded.derived_text_path,
              derived_text_sha256=excluded.derived_text_sha256,
              source_layer=excluded.source_layer,
              document_class=excluded.document_class,
              relation_status=excluded.relation_status,
              evidence_status=excluded.evidence_status,
              notes=excluded.notes
            """,
            (
                row["document_object_id"],
                row["title"],
                period_value(row.get("period_signals", [])),
                row["local_path"],
                row["sha256"],
                row["bytes"],
                row["local_path"],
                row["sha256"],
                row["source_layer"],
                row["document_class"],
                relation,
                "ocr_metadata_registered",
                0,
                0,
                "本地 OCR 元数据已登记；正文/原件来源尚未完成复核。",
            ),
        )
    conn.commit()
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    count = conn.execute("SELECT count(*) FROM local_source_objects").fetchone()[0]
    rows = conn.execute("SELECT document_class,relation_status,count(*) FROM local_source_objects GROUP BY document_class,relation_status").fetchall()
    conn.close()
    counts = {f"{row[0]}|{row[1]}": row[2] for row in rows}
    report = {
        "report": "LOCAL_OCR_OBJECTS_STAGING_20260730",
        "normalized_domestic_objects": len(domestic),
        "local_source_objects_total": count,
        "class_relation_counts": counts,
        "staging_integrity": integrity,
        "staging_db_written": True,
        "formal_db_written": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "body_read_by_import": False,
        "rule": "metadata pointer import only; OCR remains non-citation-ready",
    }
    (OUT / "LOCAL_OBJECTS_STAGING_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
