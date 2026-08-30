#!/usr/bin/env python3
"""Create a focused triage list for visible HathiTrust translation issues."""

from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"
CSV_OUT = ROOT / "data" / "hathitrust_quality_triage.csv"
REPORT_OUT = ROOT / "docs" / "_hathitrust-quality-triage.md"


def compact(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def triage_bucket(row: sqlite3.Row) -> tuple[str, str]:
    issue = row["issue_type"]
    detail = row["detail"] or ""
    original = row["original_text"] or ""
    zh = row["zh_text"] or ""
    original_len = len(original)
    zh_len = len(zh)
    if issue in {"length_too_short", "length_short"} and original_len > 8000:
        return "人工摘译", "报纸 OCR 或整版混栏较长，优先做民盟相关段落摘译并保留原文全文。"
    if issue in {"length_too_short", "length_short"}:
        return "需重译", "译文长度低于质量阈值，应优先补足中文译文。"
    if issue == "english_residue":
        return "术语/残留清理", "译文内保留英文词，应按术语表统一中文表述。"
    if issue == "glossary_miss":
        return "术语统一", detail or "原文命中术语但译文未见标准译名。"
    return "常规复核", detail or "保留在常规质量复核队列。"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            q.page_id,
            q.issue_type,
            q.severity,
            q.detail,
            q.snippet,
            d.doc_key,
            d.title,
            d.date_guess,
            d.url,
            p.page_label,
            p.page_url,
            p.text AS original_text,
            t.text AS zh_text,
            COALESCE(dc.grade, '') AS grade
        FROM translation_quality_issues q
        JOIN pages p ON p.id = q.page_id
        JOIN documents d ON d.id = p.document_id
        LEFT JOIN translations t ON t.page_id = p.id AND t.language = 'zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id = d.id
        WHERE d.source_platform = 'hathitrust'
          AND COALESCE(dc.grade, '') <> '前台不展示'
        ORDER BY q.severity DESC, d.date_guess, q.page_id, q.issue_type
        """
    ).fetchall()

    output_rows: list[dict[str, str]] = []
    for row in rows:
        bucket, next_action = triage_bucket(row)
        output_rows.append(
            {
                "page_id": str(row["page_id"]),
                "doc_key": row["doc_key"],
                "grade": row["grade"],
                "date_guess": row["date_guess"] or "",
                "title": row["title"] or "",
                "issue_type": row["issue_type"],
                "severity": str(row["severity"]),
                "bucket": bucket,
                "next_action": next_action,
                "snippet": compact(row["snippet"] or row["zh_text"] or row["original_text"]),
                "url": row["page_url"] or row["url"] or "",
            }
        )

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "page_id",
            "doc_key",
            "grade",
            "date_guess",
            "title",
            "issue_type",
            "severity",
            "bucket",
            "next_action",
            "snippet",
            "url",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    counts: dict[str, int] = {}
    for row in output_rows:
        counts[row["bucket"]] = counts.get(row["bucket"], 0) + 1

    report = [
        "# HathiTrust 译文质量分流",
        "",
        "本表只纳入前台展示的 HathiTrust / 港报材料；已下架或不展示材料不进入当前校订队列。",
        "",
        "## 总览",
        "",
    ]
    if counts:
        for bucket, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            report.append(f"- {bucket}：{count} 条")
    else:
        report.append("- 当前没有 HathiTrust 前台质量风险。")
    report.extend(
        [
            f"- CSV：`{CSV_OUT}`",
            "",
            "## 优先处理清单",
            "",
            "| 页片段 | 日期 | 等级 | 问题 | 分流 | 下一步 | 标题 |",
            "|---:|---|---|---|---|---|---|",
        ]
    )
    for row in output_rows[:40]:
        report.append(
            f"| {row['page_id']} | {row['date_guess']} | {row['grade']} | {row['issue_type']} / {row['severity']} | {row['bucket']} | {row['next_action']} | {row['title']} |"
        )
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {CSV_OUT}")
    print(f"Wrote {REPORT_OUT}")
    print(f"Found {len(output_rows)} visible HathiTrust quality issues.")
    conn.close()


if __name__ == "__main__":
    main()
