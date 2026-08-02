#!/usr/bin/env python3
"""Retry W1 low-confidence pages into a new, non-destructive OCR staging batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRIAGE = ROOT / "work" / "domestic" / "minimax_two_month_20260730" / "w1" / "UNREADABLE_TRIAGE.jsonl"
DEFAULT_OUT = ROOT / "work" / "domestic" / "minimax_two_month_20260730" / "w2" / "retry_ocr"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_queue(limit: int = 0) -> list[dict]:
    rows = [json.loads(line) for line in TRIAGE.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [row for row in rows if row.get("triage") == "RETRY_OCR"]
    return rows[:limit] if limit else rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offset", type=int, default=0, help="skip this many RETRY_OCR rows before applying --limit")
    parser.add_argument("--limit", type=int, default=0, help="0 = all retry pages")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    all_queue = load_queue()
    queue = all_queue[args.offset:]
    if args.limit:
        queue = queue[:args.limit]
    if not queue:
        raise SystemExit("No RETRY_OCR rows found")

    # Import only after queue validation so a missing local OCR runtime does
    # not alter any staging files.
    from paddleocr import PaddleOCR

    engine = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
    )
    out_dir = args.out.expanduser()
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    for row in queue:
        image = ROOT / row["page_image_path"]
        if not image.exists():
            results.append({**row, "status": "SOURCE_IMAGE_MISSING"})
            continue
        image_sha = sha256(image)
        texts: list[str] = []
        scores: list[float] = []
        for prediction in engine.predict(str(image)):
            data = dict(prediction)
            for text, score in zip(data.get("rec_texts") or [], data.get("rec_scores") or []):
                text = str(text).strip()
                if text:
                    texts.append(text)
                    scores.append(float(score))
        avg = sum(scores) / len(scores) if scores else 0.0
        source_id = row.get("source_id", "unknown")
        page_id = row.get("page_id", "unknown")
        target = out_dir / source_id / f"page-{int(str(row['page_image_path']).split('page-')[-1].split('.')[0]):04d}.retry.ocr.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        body = [
            "# OCR 重跑结果（本地 PaddleOCR staging 草稿）",
            "",
            f"- page_id：{page_id}",
            f"- 来源文件：`{row.get('source_file', '')}`",
            f"- 来源 SHA256（原数据库）：`{row.get('source_sha256_db', '')}`",
            f"- 页图：`{row['page_image_path']}`",
            f"- 页图 SHA256：`{image_sha}`",
            f"- 物理页号：{row.get('page_image_path', '').split('page-')[-1].split('.')[0]}",
            "- OCR 引擎：PaddleOCR 3.7.0",
            "- 运行方式：本地 CPU；textline orientation=True",
            f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
            f"- 识别行数：{len(texts)}",
            f"- 平均置信度：{avg:.4f}",
            "",
            "## 识别文本",
            "",
            *(texts or ["未识别出文字。"]),
            "",
        ]
        target.write_text("\n".join(body), encoding="utf-8")
        results.append({
            "page_id": page_id,
            "source_id": source_id,
            "source_file": row.get("source_file", ""),
            "page_image_path": row["page_image_path"],
            "page_image_sha256": image_sha,
            "retry_ocr_md": str(target.relative_to(ROOT)),
            "line_count": len(texts),
            "mean_confidence": round(avg, 6),
            "status": "RETRY_OCR_COMPLETE",
            "citation_ready": False,
            "human_verified": False,
        })

    manifest = out_dir / "RETRY_OCR_MANIFEST.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    report = {
        "report": "RETRY_OCR_STAGING_20260730",
        "requested": len(queue),
        "completed": sum(r.get("status") == "RETRY_OCR_COMPLETE" for r in results),
        "missing": sum(r.get("status") == "SOURCE_IMAGE_MISSING" for r in results),
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_written": False,
        "manifest": str(manifest.relative_to(ROOT)),
    }
    (out_dir / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
