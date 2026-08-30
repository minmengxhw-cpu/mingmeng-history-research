#!/usr/bin/env python3
"""Inventory the 1942/43 research-context layer without promoting it to primary evidence."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT_DIR = ROOT / "work/domestic/phase2_inventory_20260730/research_1942_1943"
ROWS_OUT = OUT_DIR / "RESEARCH_LAYER_1942_1943.jsonl"
REPORT_OUT = OUT_DIR / "REPORT.json"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    if DB.exists():
        with sqlite3.connect(DB) as conn:
            conn.row_factory = sqlite3.Row
            rows = [dict(row) for row in conn.execute(
                """SELECT external_id, title, author, institution, layer,
                          publication_date, research_type, quality_tier,
                          source_url, local_path, fulltext_status,
                          review_status, citation_ready, human_verified,
                          metadata_json
                   FROM domestic_research_materials
                   WHERE publication_date LIKE '%1942%'
                      OR publication_date LIKE '%1943%'
                      OR metadata_json LIKE '%1942%'
                      OR metadata_json LIKE '%1943%'
                   ORDER BY publication_date, external_id"""
            ).fetchall()]
    for row in rows:
        row.pop("metadata_json", None)
        local_path = str(row.get("local_path") or "")
        path = Path(local_path)
        if local_path and not path.is_absolute():
            path = ROOT / path
        content_status = "NO_LOCAL_FILE"
        extracted_chars = 0
        if path.exists() and path.is_file():
            raw = path.read_bytes()
            if raw.startswith(b"%PDF"):
                try:
                    import fitz
                    doc = fitz.open(path)
                    extracted_chars = sum(len(doc.load_page(i).get_text("text")) for i in range(doc.page_count))
                    doc.close()
                    content_status = "PDF_TEXT_EXTRACTABLE" if extracted_chars >= 1000 else "PDF_TEXT_FRAGMENT_NEEDS_OCR"
                except Exception:
                    content_status = "PDF_PRESENT_EXTRACTION_UNCHECKED"
            elif b"<html" in raw[:4096].lower():
                visible = re.sub(r"<[^>]+>", " ", raw.decode("utf-8", errors="ignore"))
                extracted_chars = len(" ".join(visible.split()))
                content_status = "HTML_BODY_CANDIDATE" if row.get("fulltext_status") == "FULLTEXT_HTML_CANDIDATE" and extracted_chars >= 1500 else "HTML_METADATA_OR_PROFILE"
            else:
                content_status = "LOCAL_FILE_UNCLASSIFIED"
        row["content_status"] = content_status
        row["extracted_chars"] = extracted_chars
    ROWS_OUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    report = {
        "report": "RESEARCH_LAYER_1942_1943_STATUS_20260730",
        "generated_on": date.today().isoformat(),
        "rows": len(rows),
        "layer_counts": dict(Counter(str(row.get("layer") or "unknown") for row in rows)),
        "research_type_counts": dict(Counter(str(row.get("research_type") or "unknown") for row in rows)),
        "quality_tier_counts": dict(Counter(str(row.get("quality_tier") or "unknown") for row in rows)),
        "fulltext_status_counts": dict(Counter(str(row.get("fulltext_status") or "unknown") for row in rows)),
        "content_status_counts": dict(Counter(str(row.get("content_status") or "unknown") for row in rows)),
        "citation_ready": sum(bool(row.get("citation_ready")) for row in rows),
        "human_verified": sum(bool(row.get("human_verified")) for row in rows),
        "local_fulltext": sum(bool(row.get("local_path")) for row in rows),
        "local_extractable_content": sum(row.get("content_status") in {"PDF_TEXT_EXTRACTABLE", "HTML_BODY_CANDIDATE"} for row in rows),
        "pdf_needs_ocr": sum(row.get("content_status") in {"PDF_TEXT_FRAGMENT_NEEDS_OCR", "PDF_IMAGE_ONLY_NEEDS_OCR"} for row in rows),
        "primary_originals_created": 0,
        "formal_db_written": False,
        "rule": "research context and official retrospectives are separate from 1942/43 primary originals; metadata-only rows cannot become citation-ready",
        "rows_path": str(ROWS_OUT),
    }
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
