#!/usr/bin/env python3
"""Build a search-draft import manifest from locally validated OCR chunks.

This intentionally creates one searchable unit per OCR chunk, not one formal
page per physical page. Every row remains ``citation_ready=false`` and
``needs_human_review=true`` until page boundaries and the original image are
reviewed. Low-confidence records marked ``phase5_search_usable=false`` are
excluded from the automatic search-draft batch.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RANGE_RE = re.compile(r"_p(\d{4})-(\d{4})\.ocr\.md$")


def resolve(value: str, project: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else project / path


def chunk_label(path: Path, physical_pages: int) -> str:
    match = RANGE_RE.search(path.name)
    if match:
        return f"ocr-chunk-p{match.group(1)}-p{match.group(2)}"
    return f"full-draft-p0001-p{physical_pages:04d}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("work/domestic/CLAUDE_B_OCR_MANIFEST_NORMALIZED_20260726.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("work/domestic/DOMESTIC_FULL_DRAFT_IMPORT_MANIFEST_20260728.jsonl"),
    )
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    output_path = args.output if args.output.is_absolute() else ROOT / args.output

    selected: list[dict] = []
    skipped: list[dict] = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        usable = row.get("phase5_search_usable") in {"true", "true_with_caution"}
        source = resolve(str(row.get("rel_path", "")), ROOT)
        chunks = row.get("ocr_output_paths") or row.get("chunk_paths") or []
        if not chunks and row.get("ocr_md_path_actual"):
            chunks = [row["ocr_md_path_actual"]]
        chunk_paths = [resolve(str(value), ROOT) for value in chunks]
        physical_pages = int(row.get("page_count") or row.get("pdf_pages_actual") or 0)
        reason = ""
        if not usable:
            reason = "phase5_search_usable=false"
        elif not source.is_file():
            reason = "source_missing"
        elif not chunk_paths or not all(path.is_file() for path in chunk_paths):
            reason = "ocr_chunk_missing"
        elif not physical_pages:
            reason = "physical_page_count_missing"
        if reason:
            skipped.append({"file_id": row.get("file_id", ""), "reason": reason})
            continue

        file_id = str(row["file_id"])
        title = str(row.get("filename") or source.stem)
        pages = []
        for chunk in chunk_paths:
            pages.append(
                {
                    "page_label": chunk_label(chunk, physical_pages),
                    "page_url": "",
                    "ocr_markdown": str(chunk.relative_to(ROOT)),
                    "mean_confidence": row.get("mean_confidence_manifest") or row.get("mean_confidence", ""),
                    "ocr_status": "needs_human_review",
                    "page_scope": "ocr_chunk_not_physical_page",
                }
            )
        selected.append(
            {
                "record_id": f"LOCALFULL:{file_id}",
                "title": f"{title} · OCR检索草稿",
                "document_date": row.get("document_date", ""),
                "collection": row.get("priority_source_kind") or "domestic-source",
                "source_kind": "public_scan",
                "source_path": str(source.relative_to(ROOT)),
                "source_sha256": row.get("sha256_actual") or row.get("sha256", ""),
                "source_url": row.get("source_url", ""),
                "event_tags": ["国内史料", "OCR检索草稿", "citation_ready=false"],
                "citation_ready": False,
                "needs_human_review": True,
                "physical_pdf_pages": physical_pages,
                "ocr_search_usable": row.get("phase5_search_usable"),
                "ocr_chunks": len(pages),
                "pages": pages,
            }
        )

    selected.sort(key=lambda row: row["record_id"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "selected_records": len(selected),
                "selected_chunks": sum(len(row["pages"]) for row in selected),
                "selected_physical_pages": sum(row["physical_pdf_pages"] for row in selected),
                "skipped_records": len(skipped),
                "skipped": skipped,
                "output": str(output_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
