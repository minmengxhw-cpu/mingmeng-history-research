#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


QUEUE_CSV = Path.cwd() / "data" / "translation_queue.csv"
QUEUE_JSONL = Path.cwd() / "data" / "translation_queue.jsonl"
DEFAULT_OUT_DIR = Path.cwd() / "data" / "translation_batches"


def load_queue() -> list[dict]:
    meta: dict[str, dict] = {}
    with QUEUE_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            meta[row["page_id"]] = row
    rows = []
    with QUEUE_JSONL.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            row.update(meta[str(row["page_id"])])
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Export translation queue into priority batches.")
    parser.add_argument("--max-chars", type=int, default=50000)
    parser.add_argument("--grade", default="", help="Optional grade filter, e.g. 核心文献")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    rows = load_queue()
    if args.grade:
        rows = [row for row in rows if row.get("grade") == args.grade]

    out_dir = args.out_dir
    report = out_dir / "translation_batches_report.md"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("batch_*.jsonl"):
        old.unlink()
    for old in out_dir.glob("batch_*.csv"):
        old.unlink()

    batches: list[list[dict]] = []
    current: list[dict] = []
    current_chars = 0
    for row in rows:
        chars = int(row.get("text_chars") or len(row.get("text") or ""))
        if current and current_chars + chars > args.max_chars:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(row)
        current_chars += chars
    if current:
        batches.append(current)

    report_lines = [
        "# 翻译批次导出",
        "",
        f"- 来源队列：`{QUEUE_CSV}`",
        f"- 等级筛选：{args.grade or '全部'}",
        f"- 每批目标字符数：{args.max_chars}",
        f"- 批次数：{len(batches)}",
        "",
        "## 批次",
        "",
        "| 批次 | 片段 | 英文字符 | 文件 |",
        "|---:|---:|---:|---|",
    ]
    for idx, batch in enumerate(batches, 1):
        jsonl_path = out_dir / f"batch_{idx:03d}.jsonl"
        csv_path = out_dir / f"batch_{idx:03d}.csv"
        with jsonl_path.open("w", encoding="utf-8") as f:
            for row in batch:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["page_id", "doc_key", "grade", "date_guess", "page_label", "title", "source_text", "zh_translation"])
            for row in batch:
                writer.writerow([
                    row["page_id"],
                    row["doc_key"],
                    row.get("grade", ""),
                    row.get("date_guess", ""),
                    row.get("page_label", ""),
                    row.get("title", ""),
                    row.get("text", ""),
                    "",
                ])
        char_count = sum(int(row.get("text_chars") or len(row.get("text") or "")) for row in batch)
        report_lines.append(f"| {idx} | {len(batch)} | {char_count} | `{jsonl_path}` / `{csv_path}` |")

    report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Exported {len(batches)} batches to {out_dir}")
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
