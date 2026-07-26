#!/usr/bin/env python3
"""Run the locally installed PaddleOCR engine without touching the formal DB.

The runtime is intentionally supplied by the caller, for example:
  /Users/cheer/Documents/民盟/knowledge_base/.venv-ocr/bin/python \
    scripts/ingest/ocr_paddle_local.py -i image.png -o work/domestic/ocr_pilot

This stage writes only auditable Markdown drafts. SQLite ingestion is a separate
reviewed step so a bad OCR run cannot silently contaminate the research index.
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Iterable


SUFFIXES = {".bmp", ".jpeg", ".jpg", ".pdf", ".png", ".tif", ".tiff", ".webp"}


def inputs(paths: list[Path], recursive: bool) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            for child in sorted(path.glob(pattern)):
                if child.is_file() and child.suffix.lower() in SUFFIXES:
                    yield child
        elif path.is_file() and path.suffix.lower() in SUFFIXES:
            yield path
        else:
            raise SystemExit(f"Unsupported or missing OCR input: {path}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def flatten(result: object) -> list[tuple[str, float | None]]:
    data = dict(result)
    texts = data.get("rec_texts") or []
    scores = data.get("rec_scores") or []
    rows: list[tuple[str, float | None]] = []
    for index, value in enumerate(texts):
        text = str(value).strip()
        if not text:
            continue
        score = scores[index] if index < len(scores) else None
        rows.append((text, float(score) if score is not None else None))
    return rows


def render(source: Path, rows: list[tuple[str, float | None]]) -> str:
    scores = [score for _text, score in rows if score is not None]
    avg = sum(scores) / len(scores) if scores else None
    lines = [
        "# OCR 识别结果（本地 PaddleOCR 草稿）",
        "",
        f"- 来源文件：`{source}`",
        f"- 来源 SHA256：`{sha256(source)}`",
        "- OCR 引擎：PaddleOCR 3.7.0",
        "- 模型：PP-OCRv6_medium_det + PP-OCRv6_medium_rec",
        "- 运行方式：本地 CPU",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 识别行数：{len(rows)}",
        f"- 平均置信度：{avg:.4f}" if avg is not None else "- 平均置信度：",
        "",
        "## 识别文本",
        "",
    ]
    lines.extend(text for text, _score in rows or [("未识别出文字。", None)])
    lines.extend(["", "## 明细", ""])
    if not rows:
        lines.append("无。")
    else:
        lines.extend(["| 序号 | 文本 | 置信度 |", "| --- | --- | --- |"])
        for index, (text, score) in enumerate(rows, 1):
            safe = text.replace("|", "\\|")
            shown = f"{score:.4f}" if score is not None else ""
            lines.append(f"| {index} | {safe} | {shown} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", action="append", required=True)
    parser.add_argument("--output", "-o", required=True, help="Markdown file for one input, directory for many")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--textline-orientation", action="store_true", help="enable PaddleOCR text-line orientation for vertical/rotated pages")
    args = parser.parse_args()

    sources = list(inputs([Path(value).expanduser() for value in args.input], args.recursive))
    if not sources:
        raise SystemExit("No supported OCR inputs found.")

    from paddleocr import PaddleOCR

    engine = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=args.textline_orientation,
    )
    output = Path(args.output).expanduser()
    multiple = len(sources) > 1
    for source in sources:
        rows: list[tuple[str, float | None]] = []
        for result in engine.predict(str(source)):
            rows.extend(flatten(result))
        target = output if output.suffix.lower() == ".md" and not multiple else output / f"{source.stem}.ocr.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(source, rows), encoding="utf-8")
        print(f"{source} -> {target} ({len(rows)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
