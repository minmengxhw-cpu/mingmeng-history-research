#!/usr/bin/env python3
"""Record per-page provenance for the bounded Observer front-page OCR batch."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISSUES = ROOT / "work/domestic/OBSERVER_V3_ISSUE_MANIFEST_20260728.jsonl"
OUT = ROOT / "work/domestic/OBSERVER_FRONT_OCR_MANIFEST_20260728.jsonl"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    issue_rows = [json.loads(line) for line in ISSUES.read_text(encoding="utf-8").splitlines() if line.strip()]
    output = ROOT / "work/domestic/observer_front_ocr_20260728/markdown"
    rows = []
    for issue in issue_rows:
        number = int(issue["issue_number"])
        for page in (1, 2):
            path = output / f"issue{number:02d}" / f"page-{page:02d}.ocr.md"
            rows.append({
                "record_id": f"OBSERVER-V3N{number:02d}-1947-front-p{page:02d}",
                "issue_number": number,
                "document_date": issue["document_date"],
                "source_pdf": issue["derived_issue_pdf"],
                "source_pdf_sha256": issue["derived_issue_sha256"],
                "page_label": f"front-{page:02d}",
                "ocr_markdown": str(path.relative_to(ROOT)),
                "ocr_markdown_sha256": sha256(path) if path.is_file() else None,
                "ocr_exists": path.is_file(),
                "ocr_status": "draft" if path.is_file() else "pending",
                "citation_ready": False,
                "needs_human_review": True,
            })
    OUT.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"manifest": str(OUT), "rows": len(rows), "ocr_exists": sum(row["ocr_exists"] for row in rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
