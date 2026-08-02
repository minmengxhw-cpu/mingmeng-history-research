#!/usr/bin/env python3
"""Run one-page local PaddleOCR staging pilot on an image-based academic PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PDF = ROOT / "data/domestic/academic_public_20260730/pdf/中国民主同盟历史文献_1941-1949_marxists.pdf"
DEFAULT_OUT = ROOT / "work/domestic/academic_ocr_pilot_20260730"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--page", type=int, default=4, help="1-based PDF page to render")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    pdf = args.pdf.expanduser()
    if not pdf.is_absolute():
        pdf = ROOT / pdf
    if not pdf.exists():
        raise SystemExit(f"PDF not found: {pdf}")
    if args.page < 1:
        raise SystemExit("--page must be >= 1")

    out = args.out.expanduser()
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    render_prefix = out / f"page-{args.page:04d}"
    subprocess.run(
        ["pdftoppm", "-f", str(args.page), "-l", str(args.page), "-png", "-r", "180", str(pdf), str(render_prefix)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    image = out / f"page-{args.page:04d}-{args.page:04d}.png"
    if not image.exists():
        # Poppler names a single rendered page with the requested page number.
        alternatives = sorted(out.glob(f"page-{args.page:04d}-*.png"))
        if alternatives:
            image = alternatives[0]
    if not image.exists():
        raise SystemExit(f"rendered image not found under {out}")

    from paddleocr import PaddleOCR

    engine = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
    )
    texts: list[str] = []
    scores: list[float] = []
    for prediction in engine.predict(str(image)):
        data = dict(prediction)
        for text, score in zip(data.get("rec_texts") or [], data.get("rec_scores") or []):
            text = str(text).strip()
            if text:
                texts.append(text)
                scores.append(float(score))
    mean_confidence = sum(scores) / len(scores) if scores else 0.0
    source_sha = sha256(pdf)
    image_sha = sha256(image)
    ocr_path = out / f"page-{args.page:04d}.ocr.md"
    ocr_path.write_text(
        "\n".join([
            "# 学术 PDF OCR 单页试跑（本地 PaddleOCR staging）",
            "",
            f"- 来源 PDF：`{pdf}`",
            f"- 来源 PDF SHA256：`{source_sha}`",
            f"- PDF 页码：{args.page}",
            f"- 页图：`{image}`",
            f"- 页图 SHA256：`{image_sha}`",
            "- OCR 引擎：本地 PaddleOCR 3.7.0",
            "- citation_ready：false",
            "- human_verified：false",
            f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
            f"- 识别行数：{len(texts)}",
            f"- 平均置信度：{mean_confidence:.4f}",
            "",
            "## 识别文本",
            "",
            *(texts or ["未识别出文字。"]),
            "",
        ]),
        encoding="utf-8",
    )
    manifest_row = {
        "source_pdf": str(pdf),
        "source_pdf_sha256": source_sha,
        "pdf_page_no": args.page,
        "page_image": str(image.relative_to(ROOT)),
        "page_image_sha256": image_sha,
        "ocr_md": str(ocr_path.relative_to(ROOT)),
        "line_count": len(texts),
        "mean_confidence": round(mean_confidence, 6),
        "status": "PILOT_COMPLETE",
        "citation_ready": False,
        "human_verified": False,
    }
    (out / "MANIFEST.jsonl").write_text(json.dumps(manifest_row, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "report": "ACADEMIC_PDF_OCR_PILOT_20260730",
        "requested_pages": 1,
        "completed_pages": 1,
        "page": args.page,
        "line_count": len(texts),
        "mean_confidence": round(mean_confidence, 6),
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_written": False,
        "source_pdf_sha256": source_sha,
        "manifest": str((out / "MANIFEST.jsonl").relative_to(ROOT)),
    }
    (out / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
