#!/usr/bin/env python3
"""Formalize OCR drafts into page-level import manifest.

Reads a source PDF + its OCR draft (either chunked or page-by-page), and emits
a page-level manifest jsonl with 8 fields per handoff requirement:
  - source_file, file_sha256, source_title, period, issue/date
  - physical_page_no, pdf_page_no, printed_page (optional)
  - page_image_path, page_image_sha256
  - ocr_md_path, ocr_engine, ocr_version, gen_timestamp
  - per-page confidence, mean_confidence
  - chunk_link (reference back to chunk-level OCR draft)
  - citation_ready=False (mandatory)
  - needs_human_review=True (mandatory)

Two modes:
  - page-by-page: each ocr_md matches a single PDF page (e.g. P3-008 pilot)
  - chunked: split one chunk into N pages, fill page-level fields from chunk

Usage:
  python3 formalize_page_batch.py \
    --source data/domestic/press_scans/xxx.pdf \
    --ocr-pattern "work/domestic/ocr_xxx/page-{n:02d}.ocr.md" \
    --mode page-by-page \
    --output work/domestic/page_manifest_xxx_20260728.jsonl \
    --source-title "..." --period "1947" --issue "1947-11-06 第2版"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import pypdf


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


CONF_RE = re.compile(r"平均置信度[：:]\s*(\d+\.\d+)")
LINES_RE = re.compile(r"识别行数[：:]\s*(\d+)")
TS_RE = re.compile(r"生成时间[：:]\s*(\S+)")
ENGINE_RE = re.compile(r"OCR 引擎[：:]\s*(\S+)")
MODEL_RE = re.compile(r"模型[：:]\s*(\S+)")


def parse_ocr_md(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = {
        "ocr_md_path": str(path),
        "ocr_engine": (ENGINE_RE.search(text).group(1) if ENGINE_RE.search(text) else "PaddleOCR"),
        "ocr_model": (MODEL_RE.search(text).group(1) if MODEL_RE.search(text) else None),
        "gen_timestamp": (TS_RE.search(text).group(1) if TS_RE.search(text) else None),
        "mean_confidence": float(CONF_RE.search(text).group(1)) if CONF_RE.search(text) else None,
        "ocr_lines": int(LINES_RE.search(text).group(1)) if LINES_RE.search(text) else None,
        "text_chars": len(text),
    }
    return out


def parse_chunk_ocr_md(path: Path) -> dict:
    """Parse chunked OCR draft (e.g. P3-008 pagination shows p0001-0100)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"p(\d{4})-(\d{4})", path.name)
    page_range = f"{int(m.group(1))}-{int(m.group(2))}" if m else None
    return {
        "ocr_md_path": str(path),
        "ocr_engine": "PaddleOCR",
        "ocr_model": "PP-OCRv6_medium",
        "gen_timestamp": TS_RE.search(text).group(1) if TS_RE.search(text) else None,
        "mean_confidence": float(CONF_RE.search(text).group(1)) if CONF_RE.search(text) else None,
        "ocr_lines": int(LINES_RE.search(text).group(1)) if LINES_RE.search(text) else None,
        "text_chars": len(text),
        "chunk_page_range": page_range,
    }


def formalize_page_by_page(
    source: Path,
    ocr_pattern: str,
    source_title: str,
    period: str,
    issue: str,
    match_blocks: int,
    page_image_pattern: str | None = None,
) -> list[dict]:
    """Each ocr_md matches a single PDF page (e.g. P3-008 pilot).

    page_image_pattern: optional "{n:02d}" pattern for per-page image paths.
    """
    file_sha = sha256(source)
    reader = pypdf.PdfReader(str(source))
    pdf_pages = len(reader.pages)
    rows = []
    for page_num in range(1, pdf_pages + 1):
        ocr_path = Path(ocr_pattern.format(n=page_num))
        if not ocr_path.exists():
            continue
        ocr = parse_ocr_md(ocr_path)
        # OCR MD SHA256
        ocr_sha = sha256(ocr_path)
        # Page image metadata
        page_image_path = None
        page_image_sha256 = None
        if page_image_pattern:
            img_path = Path(page_image_pattern.format(n=page_num))
            if img_path.exists():
                page_image_path = str(img_path)
                page_image_sha256 = sha256(img_path)
        rows.append({
            "source_file": str(source),
            "source_sha256": file_sha,
            "source_title": source_title,
            "period": period,
            "issue_date": issue,
            "physical_page_no": page_num,
            "pdf_page_no": page_num,
            "printed_page": None,
            "page_image_path": page_image_path,
            "page_image_sha256": page_image_sha256,
            "ocr_md_path": ocr["ocr_md_path"],
            "ocr_md_sha256": ocr_sha,
            "ocr_engine": ocr["ocr_engine"],
            "ocr_model": ocr["ocr_model"],
            "gen_timestamp": ocr["gen_timestamp"],
            "ocr_lines": ocr["ocr_lines"],
            "ocr_mean_confidence": ocr["mean_confidence"],
            "text_chars": ocr["text_chars"],
            "chunk_link": None,
            "citation_ready": False,
            "needs_human_review": True,
            "manifest_source": "MINIMAX_PAGE_OCR_PILOT_P3_008_20260728",
        })
    return rows


def formalize_chunked(
    source: Path,
    ocr_files: list[Path],
    source_title: str,
    period: str,
    issue: str,
) -> list[dict]:
    """One chunked OCR draft covers N pages (e.g. P3-114 第113卷)."""
    file_sha = sha256(source)
    reader = pypdf.PdfReader(str(source))
    pdf_pages = len(reader.pages)
    rows = []
    for ocr_path in ocr_files:
        if not ocr_path.exists():
            continue
        ocr = parse_chunk_ocr_md(ocr_path)
        if not ocr["chunk_page_range"]:
            continue
        start, end = map(int, ocr["chunk_page_range"].split("-"))
        for page_num in range(start, end + 1):
            if page_num > pdf_pages:
                break
            rows.append({
                "source_file": str(source),
                "source_sha256": file_sha,
                "source_title": source_title,
                "period": period,
                "issue_date": issue,
                "physical_page_no": page_num,
                "pdf_page_no": page_num,
                "printed_page": None,
                "page_image_path": None,
                "page_image_sha256": None,
                "ocr_md_path": ocr["ocr_md_path"],
                "ocr_engine": ocr["ocr_engine"],
                "ocr_model": ocr["ocr_model"],
                "gen_timestamp": ocr["gen_timestamp"],
                "ocr_lines": (ocr["ocr_lines"] or 0) // max(1, end - start + 1),
                "ocr_mean_confidence": ocr["mean_confidence"],
                "text_chars": (ocr["text_chars"] or 0) // max(1, end - start + 1),
                "chunk_link": ocr["ocr_md_path"],
                "citation_ready": False,
                "needs_human_review": True,
                "manifest_source": "MINIMAX_FORMALIZE_CHUNKED_20260728",
            })
    return rows


def formalize_single(
    source: Path,
    ocr_file: Path,
    source_title: str,
    period: str,
    issue: str,
) -> list[dict]:
    """Single OCR file covers entire PDF (no pXXXX-YYYY suffix)."""
    file_sha = sha256(source)
    reader = pypdf.PdfReader(str(source))
    pdf_pages = len(reader.pages)
    text = ocr_file.read_text(encoding="utf-8", errors="replace")
    ocr = parse_ocr_md(ocr_file)
    rows = []
    for page_num in range(1, pdf_pages + 1):
        rows.append({
            "source_file": str(source),
            "source_sha256": file_sha,
            "source_title": source_title,
            "period": period,
            "issue_date": issue,
            "physical_page_no": page_num,
            "pdf_page_no": page_num,
            "printed_page": None,
            "page_image_path": None,
            "page_image_sha256": None,
            "ocr_md_path": str(ocr_file),
            "ocr_engine": ocr["ocr_engine"],
            "ocr_model": ocr["ocr_model"],
            "gen_timestamp": ocr["gen_timestamp"],
            "ocr_lines": (ocr["ocr_lines"] or 0) // pdf_pages,
            "ocr_mean_confidence": ocr["mean_confidence"],
            "text_chars": (ocr["text_chars"] or 0) // pdf_pages,
            "chunk_link": str(ocr_file),
            "citation_ready": False,
            "needs_human_review": True,
            "manifest_source": "MINIMAX_FORMALIZE_SINGLE_20260728",
            "page_ocr_split_warning": "OCR file is single (no chunk boundaries); per-page line/conf split is approximate",
        })
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--mode", choices=["page-by-page", "chunked", "single"], required=True)
    p.add_argument("--ocr-pattern", help="Path pattern with {n} for page-by-page mode")
    p.add_argument("--page-image-pattern", help="Optional {n}-templated page image path")
    p.add_argument("--ocr-files", nargs="*", help="Explicit ocr files for chunked mode")
    p.add_argument("--ocr-file", help="Single ocr file for single mode")
    p.add_argument("--source-title", required=True)
    p.add_argument("--period", required=True)
    p.add_argument("--issue", default="")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--manifest-source", default="MINIMAX_FORMALIZE_20260728")
    args = p.parse_args()

    if args.mode == "page-by-page":
        if not args.ocr_pattern:
            raise SystemExit("--ocr-pattern required for page-by-page mode")
        rows = formalize_page_by_page(
            args.source, args.ocr_pattern,
            args.source_title, args.period, args.issue,
            match_blocks=0,
            page_image_pattern=args.page_image_pattern,
        )
    elif args.mode == "chunked":
        if not args.ocr_files:
            raise SystemExit("--ocr-files required for chunked mode")
        rows = formalize_chunked(
            args.source, [Path(p) for p in args.ocr_files],
            args.source_title, args.period, args.issue,
        )
    elif args.mode == "single":
        if not args.ocr_file:
            raise SystemExit("--ocr-file required for single mode")
        rows = formalize_single(
            args.source, Path(args.ocr_file),
            args.source_title, args.period, args.issue,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} page-level entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
