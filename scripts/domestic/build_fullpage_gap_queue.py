#!/usr/bin/env python3
"""Build a conservative queue for domestic OCR drafts and formalization.

The queue distinguishes local OCR drafts from pages formally imported into
SQLite. A source with a complete local draft should be formalized and reviewed,
not OCRed again. It never modifies SQLite or source files.
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
    if "/gazette_scans/" in f"/{source_path}":
        return "A", "同期官方公报/原始扫描优先"
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
        draft = integer(row.get("ocr_draft_pages", "")) or 0
        indexed = integer(row.get("indexed_pages", "")) or 0
        if physical is None:
            unknown += 1
            state = "physical_page_count_unknown"
            ocr_needed = ""
            formalize = str(max(draft - indexed, 0))
        else:
            ocr_needed = str(max(physical - draft, 0))
            formalize = str(max(draft - indexed, 0))
            if indexed > physical:
                state = "formal_page_count_anomaly"
            elif physical == indexed:
                complete += 1
                state = "formal_page_complete"
            elif draft >= physical:
                state = "draft_ready_formal_gap"
            elif draft:
                state = "draft_partial_formal_gap"
            elif indexed:
                state = "indexed_partial_no_draft"
            else:
                state = "ocr_needed"
        band, rationale = priority(row["source_path"])
        if state != "formal_page_complete":
            queue.append(
                {
                    "priority": band,
                    "priority_rationale": rationale,
                    "coverage_state": state,
                    "source_path": row["source_path"],
                    "pdf_pages": row.get("pdf_pages", ""),
                    "ocr_draft_pages": row.get("ocr_draft_pages", "0"),
                    "indexed_pages": row.get("indexed_pages", "0"),
                    "ocr_pages_to_generate": ocr_needed,
                    "pages_to_formalize": formalize,
                    "sha256": row.get("sha256", ""),
                    "record_ids": row.get("record_ids", ""),
                    "indexed_titles": row.get("indexed_titles", ""),
                }
            )

    queue.sort(
        key=lambda row: (
            row["priority"],
            0 if row["coverage_state"] == "draft_ready_formal_gap" else 1,
            -(integer(row["pages_to_formalize"]) or 0),
            -(integer(row["ocr_pages_to_generate"]) or 0),
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
    draft_total = sum(integer(row.get("ocr_draft_pages", "")) or 0 for row in rows)
    indexed_total = sum(integer(row.get("indexed_pages", "")) or 0 for row in rows)
    ocr_needed_total = sum(
        max((integer(row.get("pdf_pages", "")) or 0) - (integer(row.get("ocr_draft_pages", "")) or 0), 0)
        for row in rows
    )
    formalize_total = sum(
        max((integer(row.get("ocr_draft_pages", "")) or 0) - (integer(row.get("indexed_pages", "")) or 0), 0)
        for row in rows
    )
    by_state = Counter(row["coverage_state"] for row in queue)
    by_priority = Counter(row["priority"] for row in queue)
    lines = [
        "# 国内来源 OCR 草稿与正式入库队列",
        "",
        "本报告区分本地 OCR 草稿和 SQLite 正式页层。完整 OCR 草稿优先进入 formalize/review，不重复 OCR；报告只读生成，不修改 SQLite 或原始文件。",
        "",
        f"- 来源文件：{len(rows)}",
        f"- 物理页总数（可识别）：{physical_total}",
        f"- 本地 OCR 草稿页总数：{draft_total}",
        f"- SQLite 入库页总数：{indexed_total}",
        f"- 仍需生成 OCR 草稿页：{ocr_needed_total}",
        f"- 已有 OCR 草稿但待正式化页：{formalize_total}",
        f"- 整本页完整：{complete}",
        f"- 待处理来源：{len(queue)}",
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
        "| 状态 | 文件数 |",
        "|---|---:|",
        f"| draft_ready_formal_gap | {by_state['draft_ready_formal_gap']} |",
        f"| draft_partial_formal_gap | {by_state['draft_partial_formal_gap']} |",
        f"| indexed_partial_no_draft | {by_state['indexed_partial_no_draft']} |",
        f"| formal_page_count_anomaly | {by_state['formal_page_count_anomaly']} |",
        "",
        "| 优先级 | 文件数 |",
        "|---|---:|",
        f"| A | {by_priority['A']} |",
        f"| B | {by_priority['B']} |",
        f"| C | {by_priority['C']} |",
        "",
        "## 下一步队列（前 20）",
        "",
    ]
    for row in queue[:20]:
        lines.append(
            f"- `{row['coverage_state']}` / `{row['priority']}`：`{row['source_path']}`（物理 {row['pdf_pages']}，OCR草稿 {row['ocr_draft_pages']}，正式入库 {row['indexed_pages']}，待OCR {row['ocr_pages_to_generate']}，待正式化 {row['pages_to_formalize']}）"
        )
    lines.extend(
        [
            "",
            "## 入库门控",
            "",
            "1. `draft_ready_formal_gap`：复核本地 OCR 草稿的来源 SHA256、页码映射和页级边界，再做 SQLite dry-run。",
            "2. `draft_partial_formal_gap`/`ocr_needed`：只对缺失页运行 PaddleOCR，保留页级 manifest。",
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
            "ocr_draft_pages": draft_total,
            "ocr_pages_to_generate": ocr_needed_total,
            "pages_to_formalize": formalize_total,
            "output_csv": str(args.output_csv),
            "output_md": str(args.output_md),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
