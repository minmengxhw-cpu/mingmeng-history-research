#!/usr/bin/env python3
"""Non-destructive local PaddleOCR fallback for a bounded CYCLE_0003 batch.

The script consumes the Grok queue, renders only a bounded number of first
pages into a new staging directory, and writes page-level provenance. It never
touches the formal SQLite or existing OCR/source files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/01_GROK_CYCLE_0003/05_minimax_queue/MINIMAX_OCR_QUEUE_0003.jsonl"
DEFAULT_OUT = ROOT / "work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/03_MINIMAX_CYCLE_0003/02_local_paddle_batch"
DONE_MARK = "<!-- cycle-0003-local-fallback-complete -->"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def render_page(pdf: Path, page: int, out: Path) -> Path:
    prefix = out / "rendered" / pdf.stem[:80] / f"page-{page:04d}"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    candidates = sorted(prefix.parent.glob(f"{prefix.name}-*.png"))
    if candidates:
        return candidates[0]
    subprocess.run(
        ["pdftoppm", "-f", str(page), "-l", str(page), "-png", "-r", "180", str(pdf), str(prefix)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    candidates = sorted(prefix.parent.glob(f"{prefix.name}-*.png"))
    if not candidates:
        raise RuntimeError(f"rendered page missing: {prefix}")
    return candidates[0]


def write_ocr(out: Path, row: dict, pdf: Path, page: int, image: Path, texts: list[str], scores: list[float]) -> Path:
    target = out / "ocr" / row["queue_id"] / f"page-{page:04d}.ocr.md"
    if target.exists() and DONE_MARK in target.read_text(encoding="utf-8", errors="replace"):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    mean = sum(scores) / len(scores) if scores else 0.0
    body = [
        "# CYCLE_0003 本地 PaddleOCR staging 草稿",
        "",
        f"- queue_id：`{row['queue_id']}`",
        f"- 标题：{row.get('title', '')}",
        f"- 来源 PDF：`{row['local_path']}`",
        f"- 来源 SHA256：`{sha256(pdf)}`",
        f"- PDF 页号：{page}",
        f"- 页图：`{image.relative_to(ROOT)}`",
        f"- 页图 SHA256：`{sha256(image)}`",
        "- OCR 引擎：PaddleOCR 3.7.0",
        "- 模型：PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
        f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 识别行数：{len(texts)}",
        f"- 平均置信度：{mean:.6f}",
        "- citation_ready：false",
        "- human_verified：false",
        "",
        "## 识别文本",
        "",
        *(texts or ["未识别出文字。"]),
        "",
        DONE_MARK,
        "",
    ]
    part = target.with_suffix(target.suffix + ".part")
    part.write_text("\n".join(body), encoding="utf-8")
    part.replace(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in QUEUE.read_text(encoding="utf-8").splitlines() if line.strip()]
    # Queue order is intentionally preserved: B-layer and early 1941 entries first.
    rows = rows[: args.max_pages]
    from paddleocr import PaddleOCR

    engine = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
    )
    results: list[dict] = []
    for row in rows:
        pdf = ROOT / row["local_path"]
        if not pdf.is_file():
            results.append({**row, "status": "SOURCE_MISSING", "formal_db_written": False})
            continue
        actual_source_sha = sha256(pdf)
        if actual_source_sha != row.get("sha256"):
            results.append({**row, "status": "SOURCE_SHA_MISMATCH", "actual_source_sha256": actual_source_sha, "formal_db_written": False})
            continue
        page = 1
        t0 = time.time()
        image = render_page(pdf, page, out)
        texts: list[str] = []
        scores: list[float] = []
        for prediction in engine.predict(str(image)):
            data = dict(prediction)
            for text, score in zip(data.get("rec_texts") or [], data.get("rec_scores") or []):
                text = str(text).strip()
                if text:
                    texts.append(text)
                    scores.append(float(score))
        ocr_md = write_ocr(out, row, pdf, page, image, texts, scores)
        results.append({
            "queue_id": row["queue_id"],
            "canonical_key": row.get("canonical_key"),
            "source_pdf": row["local_path"],
            "source_pdf_sha256": actual_source_sha,
            "pdf_page_no": page,
            "page_image": str(image.relative_to(ROOT)),
            "page_image_sha256": sha256(image),
            "ocr_md": str(ocr_md.relative_to(ROOT)),
            "ocr_md_sha256": sha256(ocr_md),
            "line_count": len(texts),
            "mean_confidence": round(sum(scores) / len(scores), 6) if scores else 0.0,
            "elapsed_seconds": round(time.time() - t0, 2),
            "status": "LOCAL_PADDLE_OCR_COMPLETE",
            "citation_ready": False,
            "human_verified": False,
            "formal_db_written": False,
        })
    manifest = out / "LOCAL_PADDLE_OCR_MANIFEST.jsonl"
    manifest.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in results), encoding="utf-8")
    report = {
        "report": "CYCLE_0003_LOCAL_PADDLE_FALLBACK",
        "requested_pages": len(rows),
        "completed_pages": sum(item.get("status") == "LOCAL_PADDLE_OCR_COMPLETE" for item in results),
        "source_sha_mismatch": sum(item.get("status") == "SOURCE_SHA_MISMATCH" for item in results),
        "source_missing": sum(item.get("status") == "SOURCE_MISSING" for item in results),
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_written": False,
        "manifest": str(manifest.relative_to(ROOT)),
    }
    (out / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
