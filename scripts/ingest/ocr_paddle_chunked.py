#!/usr/bin/env python3
"""Chunked OCR for large PDFs (>100 pages) using PaddleOCR.

Splits a PDF into N-page chunks via pypdf, OCRs each chunk with a single
PaddleOCR engine instance (loaded once), and writes one .ocr.md per chunk.
This avoids the "all-in-memory" write-once-at-end failure mode of the parent
ocr_paddle_local.py for very large files (622p/789p).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


VENV_PY = "/Users/cheer/Documents/民盟/knowledge_base/.venv-ocr/bin/python"
OCR_SCRIPT = Path(__file__).resolve().parent / "ocr_paddle_local.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_pdf(src: Path, tmp: Path, start: int, end: int) -> Path:
    """Split src PDF pages [start, end] (1-based, inclusive) into tmp/{start}-{end}.pdf."""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(src))
    writer = PdfWriter()
    total = len(reader.pages)
    end = min(end, total)
    for page_num in range(start - 1, end):
        writer.add_page(reader.pages[page_num])
    out = tmp / f"chunk_{start:04d}_{end:04d}.pdf"
    with out.open("wb") as handle:
        writer.write(handle)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", required=True, help="Source PDF")
    parser.add_argument("--output-dir", "-o", required=True, help="Output dir for chunk .ocr.md files")
    parser.add_argument("--chunk-size", type=int, default=100, help="Pages per chunk (default 100)")
    parser.add_argument("--start", type=int, default=1, help="First page (1-based, default 1)")
    parser.add_argument("--end", type=int, default=0, help="Last page (0 = till end)")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.is_file() or src.suffix.lower() != ".pdf":
        print(f"ERROR: not a PDF: {src}", file=sys.stderr)
        return 2

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    from pypdf import PdfReader
    total = len(PdfReader(str(src)).pages)
    start = max(1, args.start)
    end = args.end if args.end >= 1 else total
    end = min(end, total)
    if start > end:
        print(f"ERROR: start {start} > end {end}", file=sys.stderr)
        return 2

    digest = sha256(src)
    stem = src.stem
    print(f"[chunked] src={src.name} sha256={digest[:12]}.. total={total}p start={start} end={end} chunk={args.chunk_size}")

    tmp = Path(tempfile.mkdtemp(prefix=f"ocr_chunk_{stem[:20]}_"))
    print(f"[chunked] tmp dir: {tmp}")

    try:
        chunk = args.chunk_size
        n_chunks = 0
        for chunk_start in range(start, end + 1, chunk):
            chunk_end = min(chunk_start + chunk - 1, end)
            print(f"[chunked] === pages {chunk_start}-{chunk_end} ===")
            sub_pdf = split_pdf(src, tmp, chunk_start, chunk_end)
            out_md = out_dir / f"{stem}_p{chunk_start:04d}-{chunk_end:04d}.ocr.md"
            # Call the existing single-PDF script on the chunk
            cmd = [
                VENV_PY,
                str(OCR_SCRIPT),
                "-i", str(sub_pdf),
                "-o", str(out_md),
            ]
            print(f"[chunked] run: {' '.join(cmd)}")
            t0 = datetime.now()
            result = subprocess.run(cmd, capture_output=True, text=True)
            t1 = datetime.now()
            print(f"[chunked] elapsed={t1 - t0}")
            if result.returncode != 0:
                print(f"[chunked] FAILED rc={result.returncode}")
                print(f"  stdout: {result.stdout[-500:]}")
                print(f"  stderr: {result.stderr[-500:]}")
                return 1
            if not out_md.is_file():
                print(f"[chunked] FAILED: no output file at {out_md}")
                return 1
            n_chunks += 1
            print(f"[chunked] ✓ {out_md.name}")
        print(f"[chunked] DONE: {n_chunks} chunks, pages {start}-{end} of {total}, output dir: {out_dir}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
