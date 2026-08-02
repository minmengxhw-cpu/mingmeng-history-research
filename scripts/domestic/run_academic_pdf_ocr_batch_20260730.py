#!/usr/bin/env python3
"""Run a bounded multi-page PaddleOCR staging batch for a local PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PDF = ROOT / "data/domestic/academic_public_20260730/pdf/中国民主同盟历史文献_1941-1949_marxists.pdf"
DEFAULT_OUT = ROOT / "work/domestic/academic_ocr_batch_pilot_20260730"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--pages", default="7,8,9,10", help="comma-separated 1-based PDF page numbers")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    pdf = args.pdf.expanduser()
    if not pdf.is_absolute():
        pdf = ROOT / pdf
    pages = sorted({int(value.strip()) for value in args.pages.split(",") if value.strip()})
    if not pages or min(pages) < 1:
        raise SystemExit("--pages must contain positive page numbers")
    if not pdf.exists():
        raise SystemExit(f"PDF not found: {pdf}")
    out = args.out.expanduser()
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    rendered: dict[int, Path] = {}
    for page in pages:
        prefix = out / f"render-{page:04d}"
        subprocess.run(
            ["pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", "180", str(pdf), str(prefix)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        candidates = sorted(out.glob(f"render-{page:04d}-*.png"))
        if not candidates:
            raise SystemExit(f"rendered image not found for page {page}")
        rendered[page] = candidates[0]

    from paddleocr import PaddleOCR

    engine = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
    )
    source_sha = sha256(pdf)
    results: list[dict] = []
    for page in pages:
        image = rendered[page]
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
        ocr_path = out / f"page-{page:04d}.ocr.md"
        image_sha = sha256(image)
        ocr_path.write_text(
            "\n".join([
                "# 学术 PDF OCR 批次结果（本地 PaddleOCR staging）",
                "",
                f"- 来源 PDF：`{pdf}`",
                f"- 来源 PDF SHA256：`{source_sha}`",
                f"- PDF 页码：{page}",
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
        results.append({
            "pdf_page_no": page,
            "page_image": str(image.relative_to(ROOT)),
            "page_image_sha256": image_sha,
            "ocr_md": str(ocr_path.relative_to(ROOT)),
            "line_count": len(texts),
            "mean_confidence": round(mean_confidence, 6),
            "status": "BATCH_PILOT_COMPLETE",
            "citation_ready": False,
            "human_verified": False,
        })

    manifest = out / "MANIFEST.jsonl"
    manifest.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results), encoding="utf-8")
    report = {
        "report": "ACADEMIC_PDF_OCR_BATCH_PILOT_20260730",
        "requested_pages": pages,
        "completed_pages": len(results),
        "line_counts": {str(row["pdf_page_no"]): row["line_count"] for row in results},
        "mean_confidences": {str(row["pdf_page_no"]): row["mean_confidence"] for row in results},
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_written": False,
        "source_pdf_sha256": source_sha,
        "manifest": str(manifest.relative_to(ROOT)),
    }
    (out / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
