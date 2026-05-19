#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"
CSV_PATH = Path.cwd() / "data" / "translation_queue.csv"
JSONL_PATH = Path.cwd() / "data" / "translation_queue.jsonl"
REPORT_PATH = Path.cwd() / "docs" / "translation_queue_report.md"

GRADE_PRIORITY = {
    "核心文献": 1,
    "相关文献": 2,
    "人物关联": 3,
    "背景材料": 4,
}


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            pages.id AS page_id,
            pages.page_label,
            pages.page_url,
            length(pages.text) AS text_chars,
            pages.text,
            documents.doc_key,
            documents.volume_id,
            documents.doc_id,
            documents.date_guess,
            documents.title,
            documents.matched_terms,
            dc.grade,
            dc.score
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        WHERE translations.id IS NULL
        ORDER BY
            CASE dc.grade
                WHEN '核心文献' THEN 1
                WHEN '相关文献' THEN 2
                WHEN '人物关联' THEN 3
                WHEN '背景材料' THEN 4
                ELSE 9
            END,
            documents.volume_id,
            CAST(documents.doc_number AS INTEGER),
            pages.id
        """
    ).fetchall()

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "priority",
            "page_id",
            "doc_key",
            "grade",
            "date_guess",
            "page_label",
            "text_chars",
            "title",
            "matched_terms",
            "page_url",
        ])
        for row in rows:
            writer.writerow([
                GRADE_PRIORITY.get(row["grade"], 9),
                row["page_id"],
                row["doc_key"],
                row["grade"],
                row["date_guess"],
                row["page_label"],
                row["text_chars"],
                row["title"],
                row["matched_terms"],
                row["page_url"],
            ])

    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")

    by_grade = {}
    chars_by_grade = {}
    for row in rows:
        grade = row["grade"] or "未分级"
        by_grade[grade] = by_grade.get(grade, 0) + 1
        chars_by_grade[grade] = chars_by_grade.get(grade, 0) + (row["text_chars"] or 0)

    lines = [
        "# 待翻译队列",
        "",
        f"- 待翻译片段：{len(rows)}",
        f"- 估算英文字符数：{sum(row['text_chars'] or 0 for row in rows)}",
        f"- CSV：`{CSV_PATH}`",
        f"- JSONL：`{JSONL_PATH}`",
        "",
        "## 按等级",
        "",
        "| 等级 | 片段 | 英文字符 |",
        "|---|---:|---:|",
    ]
    for grade in ["核心文献", "相关文献", "人物关联", "背景材料", "未分级"]:
        if grade in by_grade:
            lines.append(f"| {grade} | {by_grade[grade]} | {chars_by_grade[grade]} |")
    lines.extend(["", "## 前 20 个待翻译片段", ""])
    for row in rows[:20]:
        page = row["page_label"] or "doc-level"
        lines.append(f"- `{row['doc_key']}` | {row['grade']} | {row['date_guess']} | {page} | {row['text_chars']} chars")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.close()

    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {JSONL_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Queued {len(rows)} segments.")


if __name__ == "__main__":
    main()
