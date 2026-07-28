#!/usr/bin/env python3
"""Render and OCR the cover/contents pages of the 12 verified Observer issues.

The complete issue PDFs remain untouched.  This intentionally starts with the
first two pages of each issue because those pages establish issue identity and
contents while keeping the first OCR batch bounded and restartable.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "work/domestic/OBSERVER_V3_ISSUE_MANIFEST_20260728.jsonl"
PADDLE_PYTHON = Path("/Users/cheer/Documents/民盟/knowledge_base/.venv-ocr/bin/python")
PDftoppm = Path("/Users/cheer/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm")
OCR_MODULE = ROOT / "scripts/ingest/ocr_paddle_local.py"


def render_pages(pdf: Path, image_dir: Path, dpi: int) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    expected = [image_dir / "page-01.png", image_dir / "page-02.png"]
    if all(path.is_file() for path in expected):
        return
    subprocess.run(
        [str(PDftoppm), "-r", str(dpi), "-png", "-f", "1", "-l", "2", str(pdf), str(image_dir / "page")],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--no-orientation", action="store_true")
    args = parser.parse_args()
    if not PADDLE_PYTHON.is_file():
        raise SystemExit(f"missing OCR runtime: {PADDLE_PYTHON}")
    import json

    rows = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    batch_root = ROOT / "work/domestic/observer_front_ocr_20260728"
    image_root = batch_root / "images"
    output_root = batch_root / "markdown"
    batch_root.mkdir(parents=True, exist_ok=True)
    for row in rows:
        issue = int(row["issue_number"])
        pdf = ROOT / row["derived_issue_pdf"]
        if not pdf.is_file():
            raise SystemExit(f"missing derived PDF: {pdf}")
        render_pages(pdf, image_root / f"issue{issue:02d}", args.dpi)

    from ocr_paddle_local import flatten, render
    from paddleocr import PaddleOCR

    engine = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=not args.no_orientation,
    )
    total = 0
    for issue_dir in sorted(image_root.glob("issue[0-9][0-9]")):
        out_dir = output_root / issue_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(issue_dir.glob("*.png")):
            target = out_dir / f"{source.stem}.ocr.md"
            if target.is_file() and target.stat().st_size > 100:
                print(f"skip existing {target}", flush=True)
                continue
            rows_out = []
            for result in engine.predict(str(source)):
                rows_out.extend(flatten(result))
            target.write_text(render(source, rows_out), encoding="utf-8")
            total += 1
            print(f"{source} -> {target} ({len(rows_out)} lines)", flush=True)
    print(f"completed_new_pages={total}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts/ingest"))
    raise SystemExit(main())
