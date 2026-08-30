#!/usr/bin/env python3
"""Prepare issue-level PDFs and provenance for 《观察》第三卷第1—12期.

The source PDF is immutable.  This script only creates derived issue PDFs
under work/domestic/ and records exact source/derived SHA256 values.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/domestic/press_scans/SSID-13679264_观察_第3卷第1-12期.pdf"
SOURCE_SHA256 = "d8f4dacfbf367f590d46344084fab8722d91d18fbb2d0b8cc241f7416d5f7f04"
OUTPUT_DIR = ROOT / "work/domestic/observer_issue_ocr_20260728"
MANIFEST = ROOT / "work/domestic/OBSERVER_V3_ISSUE_MANIFEST_20260728.jsonl"

# Boundaries were visually checked against the twelve cover pages on
# 2026-07-28.  PDF pages 1-2 are binding/front matter, not an issue.
ISSUES = [
    (1, "1947-08-30", 3, 26),
    (2, "1947-09-06", 27, 50),
    (3, "1947-09-13", 51, 74),
    (4, "1947-09-20", 75, 98),
    (5, "1947-09-27", 99, 122),
    (6, "1947-10-04", 123, 146),
    (7, "1947-10-11", 147, 174),
    (8, "1947-10-18", 175, 198),
    (9, "1947-10-25", 199, 218),
    (10, "1947-11-01", 219, 238),
    (11, "1947-11-08", 239, 258),
    (12, "1947-11-15", 259, 278),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if not SOURCE.is_file():
        raise SystemExit(f"missing source: {SOURCE}")
    actual_source_sha = sha256(SOURCE)
    if actual_source_sha != SOURCE_SHA256:
        raise SystemExit(f"source SHA256 mismatch: {actual_source_sha}")

    reader = PdfReader(str(SOURCE))
    if len(reader.pages) != 278:
        raise SystemExit(f"unexpected source page count: {len(reader.pages)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for issue, date, start, end in ISSUES:
        derived = OUTPUT_DIR / (
            f"观察_第三卷_第{issue:02d}期_{date}_pdf{start:04d}-{end:04d}.pdf"
        )
        if not derived.exists():
            writer = PdfWriter()
            for page_index in range(start - 1, end):
                writer.add_page(reader.pages[page_index])
            with derived.open("xb") as handle:
                writer.write(handle)

        derived_pages = len(PdfReader(str(derived)).pages)
        expected_pages = end - start + 1
        if derived_pages != expected_pages:
            raise SystemExit(
                f"derived page mismatch for issue {issue}: "
                f"{derived_pages} != {expected_pages}"
            )

        ocr_path = OUTPUT_DIR / f"{derived.stem}.ocr.md"
        rows.append(
            {
                "record_id": f"OBSERVER-V3N{issue:02d}-1947",
                "title": f"《观察》第三卷第{issue}期",
                "document_date": date,
                "issue_number": issue,
                "source_path": str(SOURCE.relative_to(ROOT)),
                "source_sha256": SOURCE_SHA256,
                "pdf_page_start": start,
                "pdf_page_end": end,
                "physical_pages": expected_pages,
                "derived_issue_pdf": str(derived.relative_to(ROOT)),
                "derived_issue_sha256": sha256(derived),
                "ocr_markdown": str(ocr_path.relative_to(ROOT)),
                "ocr_exists": ocr_path.is_file(),
                "boundary_status": "cover_verified",
                "ocr_status": "pilot",
                "citation_ready": False,
                "needs_human_review": True,
            }
        )

    MANIFEST.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "source": str(SOURCE),
                "source_sha256": SOURCE_SHA256,
                "issues": len(rows),
                "issue_pages": sum(int(row["physical_pages"]) for row in rows),
                "front_matter_pages_excluded": 2,
                "manifest": str(MANIFEST),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
