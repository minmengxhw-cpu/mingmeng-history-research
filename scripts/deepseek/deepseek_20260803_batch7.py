#!/usr/bin/env python3
"""Batch 7: export and stratify short domestic pages for human quality review.

Read-only against the formal SQLite database. Produces only audit CSV/Markdown.
"""
from __future__ import annotations

import csv
import os
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from _guard import guard

guard()
BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "work/deepseek-20260803/02_analysis"
OUT.mkdir(parents=True, exist_ok=True)
DB = Path(os.environ.get(
    "DEEPSEEK_FORMAL_DB",
    "/Users/cheer/Documents/mm agent/mingmeng-history-research/data/research_index.sqlite",
))

CATALOG_MARKERS = ("目录", "书目", "档号", "全宗", "catalogue", "获取说明", "检索词")
OCR_MARKERS = ("ocr", "paddle", "识别")


def classify(page_label: str, hit_type: str, text: str, n: int) -> tuple[str, str, str]:
    blob = f"{page_label} {hit_type} {text[:500]}".lower()
    if not text.strip():
        return "Q0_EMPTY", "空文本", "修复导入或删除空页；不可引用"
    if "catalogue" in blob or any(x.lower() in blob for x in CATALOG_MARKERS):
        return "Q1_CATALOG", "目录/目录卡型短文本", "保留为目录线索；citation_ready=0"
    if page_label.lower() in {"cover", "front", "封面", "封底", "目录页"}:
        return "Q2_STRUCTURAL", "封面/结构页", "保留结构用途；不作正文引用"
    if any(x in blob for x in OCR_MARKERS) and n < 60:
        return "Q3_OCR_SUSPECT", "疑似 OCR 失败或截断", "人工对照影像；核验前不可引用"
    if n < 30:
        return "Q4_FRAGMENT", "极短片段", "人工判断标题/图注/截断；核验前不可引用"
    return "Q5_SHORT_REVIEW", "短正文待抽检", "人工对照影像确认完整性和定位"


def main() -> None:
    if not DB.exists() or DB.stat().st_size == 0:
        raise SystemExit(f"formal DB missing/empty: {DB}")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT p.id AS page_id, p.document_id, d.doc_key, d.title,
               d.hit_type, d.url AS document_url, p.page_label, p.page_url,
               length(trim(coalesce(p.text,''))) AS text_length,
               replace(replace(substr(trim(coalesce(p.text,'')),1,240), char(10),' '), char(13),' ') AS text_excerpt
        FROM pages p JOIN documents d ON d.id=p.document_id
        WHERE d.source_platform='domestic'
          AND length(trim(coalesce(p.text,''))) < 120
        ORDER BY d.id, p.id
    """).fetchall()
    con.close()

    out_rows = []
    for r in rows:
        text = r["text_excerpt"] or ""
        code, label, action = classify(r["page_label"] or "", r["hit_type"] or "", text, r["text_length"])
        out_rows.append({
            **dict(r),
            "quality_bucket": code,
            "audit_conclusion": label,
            "recommended_action": action,
            "citation_eligible": "no",
            "manual_review_status": "pending" if code in {"Q3_OCR_SUSPECT", "Q4_FRAGMENT", "Q5_SHORT_REVIEW"} else "not_required",
        })

    fields = list(out_rows[0]) if out_rows else []
    with (OUT / "short_pages_quality_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(out_rows)

    counts = Counter(r["quality_bucket"] for r in out_rows)
    by_hit = Counter(r["hit_type"] or "(empty)" for r in out_rows)
    docs = defaultdict(int)
    for r in out_rows:
        docs[r["doc_key"]] += 1
    top_docs = sorted(docs.items(), key=lambda x: (-x[1], x[0]))[:20]
    pending = sum(r["manual_review_status"] == "pending" for r in out_rows)

    report = [
        "# Batch 7 · 国内短页面质量审计（text < 120）", "",
        f"- 正式库只读路径：`{DB}`", f"- 短页面总数：**{len(out_rows)}**", f"- 涉及文档：**{len(docs)}**",
        f"- 需人工影像抽检：**{pending}**", "- 门禁原则：本批全部预设 `citation_eligible=no`，直至人工核验完成。", "",
        "## 分层结果", "", "| 分层 | 数量 |", "|---|---:|",
    ]
    for k, v in sorted(counts.items()): report.append(f"| {k} | {v} |")
    report += ["", "## hit_type 分布（Top 20）", "", "| hit_type | 数量 |", "|---|---:|"]
    for k, v in by_hit.most_common(20): report.append(f"| {k} | {v} |")
    report += ["", "## 短页面最多的文档（Top 20）", "", "| doc_key | 数量 |", "|---|---:|"]
    for k, v in top_docs: report.append(f"| {k} | {v} |")
    report += ["", "## 处置规则", "", "1. Q0/Q3/Q4/Q5 在人工对照影像前禁止引用。", "2. Q1 仅作目录线索，不得冒充全文。", "3. Q2 可保留版式/结构用途，但不作为正文证据。", "4. 本批未执行 OCR、未修改页面、未写正式 SQLite。", ""]
    (OUT / "batch7_short_pages_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"short pages={len(out_rows)}, docs={len(docs)}, pending={pending}")
    print(dict(sorted(counts.items())))


if __name__ == "__main__":
    main()
