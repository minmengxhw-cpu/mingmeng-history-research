#!/usr/bin/env python3
"""Build a conservative queue for domestic sources whose OCR is not page-complete.

The existing coverage inventory treats any indexed page as ``indexed``. This
report adds the stricter physical-page comparison so selected-page OCR cannot
be mistaken for whole-file coverage. It never modifies SQLite or source files.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def integer(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def priority(source_path: str) -> tuple[str, str]:
    if "/press_scans/" in f"/{source_path}":
        return "A", "同期报刊/原始扫描优先"
    if "/sourcebooks/" in f"/{source_path}":
        return "B", "文献汇编/来源书，先做导航和关键页"
    return "C", "其他国内来源"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    with args.input_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    queue: list[dict[str, str]] = []
    complete = 0
    unknown = 0
    for row in rows:
        physical = integer(row.get("pdf_pages", ""))
        manifest = integer(row.get("manifest_pages", "")) or 0
        indexed = integer(row.get("indexed_pages", "")) or 0
        if physical is None:
            unknown += 1
            state = "physical_page_count_unknown"
            missing = ""
        else:
            missing_count = max(physical - manifest, 0)
            if physical == manifest == indexed:
                complete += 1
                state = "page_complete"
            elif indexed == 0:
                state = "not_indexed"
            else:
                state = "partial_selected_pages"
            missing = str(missing_count)
        band, rationale = priority(row["source_path"])
        if state != "page_complete":
            queue.append(
                {
                    "priority": band,
                    "priority_rationale": rationale,
                    "coverage_state": state,
                    "source_path": row["source_path"],
                    "pdf_pages": row.get("pdf_pages", ""),
                    "manifest_pages": row.get("manifest_pages", "0"),
                    "indexed_pages": row.get("indexed_pages", "0"),
                    "missing_pages": missing,
                    "sha256": row.get("sha256", ""),
                    "record_ids": row.get("record_ids", ""),
                    "indexed_titles": row.get("indexed_titles", ""),
                }
            )

    queue.sort(
        key=lambda row: (
            row["priority"],
            -(integer(row["missing_pages"]) or 0),
            row["source_path"],
        )
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    fields = list(queue[0]) if queue else ["source_path"]
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(queue)

    physical_total = sum(integer(row.get("pdf_pages", "")) or 0 for row in rows)
    manifest_total = sum(integer(row.get("manifest_pages", "")) or 0 for row in rows)
    indexed_total = sum(integer(row.get("indexed_pages", "")) or 0 for row in rows)
    missing_total = sum(
        max((integer(row.get("pdf_pages", "")) or 0) - (integer(row.get("manifest_pages", "")) or 0), 0)
        for row in rows
    )
    overcount_total = sum(
        max((integer(row.get("manifest_pages", "")) or 0) - (integer(row.get("pdf_pages", "")) or 0), 0)
        for row in rows
    )
    by_priority = Counter(row["priority"] for row in queue)
    lines = [
        "# 国内来源整本页覆盖缺口队列",
        "",
        "本报告对比 PDF 物理页数、OCR manifest 页数和 SQLite 已入库页数。`indexed` 不代表整本完成；只有三者相等才标记为 `page_complete`。报告只读生成，不修改原始文件或 SQLite。",
        "",
        f"- 来源 PDF：{len(rows)}",
        f"- 物理页总数（可识别）：{physical_total}",
        f"- manifest 页总数：{manifest_total}",
        f"- SQLite 入库页总数：{indexed_total}",
        f"- 待补物理页（逐文件正缺口合计）：{missing_total}",
        f"- manifest 超出 pdfinfo 页数：{overcount_total}",
        f"- 整本页完整：{complete}",
        f"- 选页/部分 OCR：{len(queue) - unknown}",
        f"- 物理页数未知：{unknown}",
        "",
        "## 优先级定义",
        "",
        "- `A`：同期报刊/原始扫描，优先补齐整本页覆盖；补齐前仍只视为检索草稿。",
        "- `B`：文献汇编或来源书，先补目录、序言、关键文献和可定位页；不能替代同期原件。",
        "- `C`：其他国内来源，按证据价值另行处理。",
        "",
        "## 队列统计",
        "",
        "| 优先级 | 文件数 |",
        "|---|---:|",
        f"| A | {by_priority['A']} |",
        f"| B | {by_priority['B']} |",
        f"| C | {by_priority['C']} |",
        "",
        "## 最大页缺口（前 20）",
        "",
    ]
    for row in sorted(queue, key=lambda r: -(integer(r["missing_pages"]) or 0))[:20]:
        lines.append(
            f"- `{row['priority']}` 缺 {row['missing_pages']} 页：`{row['source_path']}`（物理 {row['pdf_pages']}，manifest {row['manifest_pages']}，入库 {row['indexed_pages']}）"
        )
    lines.extend(
        [
            "",
            "## 入库门控",
            "",
            "1. 先按 `A` 队列逐份保留原 PDF SHA256 和页码映射。",
            "2. 以页为单位运行 PaddleOCR；OCR 结果只能先进入检索草稿层。",
            "3. 关键页必须记录原图定位、版面复核和人工审校结果。",
            "4. 仅在 manifest、pages、page_fts 对齐且证据门控通过后，才提升为引用候选。",
        ]
    )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        {
            "sources": len(rows),
            "queue": len(queue),
            "page_complete": complete,
            "physical_pages": physical_total,
            "manifest_pages": manifest_total,
            "missing_pages": missing_total,
            "output_csv": str(args.output_csv),
            "output_md": str(args.output_md),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
