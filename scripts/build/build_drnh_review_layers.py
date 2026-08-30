#!/usr/bin/env python3
"""Build DRNH auto-converted review layers.

The script is intentionally read-only for the SQLite database. It produces a
Markdown report plus a CSV queue so the DRNH auto-converted records can be
reviewed in priority order without mutating translation status.
"""

from __future__ import annotations

import csv
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
REPORT = ROOT / "docs" / "_drnh-auto-summary-review-layers.md"
CSV_OUT = ROOT / "data" / "drnh_review_layers.csv"

DIRECT_ORG_TERMS = ("中国民主同盟", "民主同盟", "民主政团同盟", "民盟")
LEADER_TERMS = (
    "张澜",
    "沈钧儒",
    "罗隆基",
    "章伯钧",
    "张君劢",
    "左舜生",
    "黄炎培",
    "梁漱溟",
    "黄任之",
    "李公朴",
    "闻一多",
)
CORE_EVENT_TERMS = (
    "政治协商",
    "政协",
    "国民参政会",
    "国民大会",
    "制宪",
    "宪法",
    "改组政府",
    "联合政府",
    "非法",
    "解散",
    "取缔",
    "调解国共",
    "停战",
    "内战",
    "赫尔利",
    "马歇尔",
)
STATE_SECURITY_TERMS = ("戴笠", "军统", "特务", "侍从室", "蒋中正", "情报", "密报", "保密局")


def year_score(date_guess: str) -> tuple[int, str]:
    year = ""
    for token in (date_guess or "").split("/"):
        if token.isdigit() and len(token) == 4:
            year = token
            break
    if not year:
        return (0, "")
    y = int(year)
    if 1945 <= y <= 1947:
        return (10, year)
    if 1948 <= y <= 1949:
        return (6, year)
    if 1941 <= y <= 1944:
        return (4, year)
    return (1, year)


def hits(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in text]


def score_row(row: sqlite3.Row) -> dict[str, object]:
    title = row["title"] or ""
    matched_terms = row["matched_terms"] or ""
    haystack = title + " " + matched_terms

    direct_hits = hits(haystack, DIRECT_ORG_TERMS)
    leader_hits = hits(haystack, LEADER_TERMS)
    event_hits = hits(haystack, CORE_EVENT_TERMS)
    security_hits = hits(haystack, STATE_SECURITY_TERMS)
    y_score, year = year_score(row["date_guess"] or "")

    score = int(row["class_score"] or 0)
    score += 25 if direct_hits else 0
    score += min(len(leader_hits) * 3, 15)
    score += min(len(event_hits) * 4, 20)
    score += min(len(security_hits) * 3, 15)
    score += y_score

    if row["grade"] == "A" and score >= 110:
        tier = "重点校订"
    elif row["grade"] == "A" or score >= 85:
        tier = "常规校订"
    else:
        tier = "背景保留"

    reasons = []
    if direct_hits:
        reasons.append("组织直接命中：" + "、".join(direct_hits[:3]))
    if leader_hits:
        reasons.append("人物：" + "、".join(leader_hits[:5]))
    if event_hits:
        reasons.append("事件：" + "、".join(event_hits[:5]))
    if security_hits:
        reasons.append("机关/情报：" + "、".join(security_hits[:4]))
    if year:
        reasons.append("年份：" + year)

    return {
        "doc_id": row["doc_id"],
        "page_id": row["page_id"],
        "doc_key": row["doc_key"],
        "title": title,
        "date_guess": row["date_guess"] or "",
        "grade": row["grade"],
        "class_score": row["class_score"],
        "translation_status": row["translation_status"],
        "review_score": score,
        "tier": tier,
        "reason": "；".join(reasons) or row["class_reason"],
        "url": row["url"] or "",
    }


def load_rows() -> list[dict[str, object]]:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
          d.id AS doc_id,
          p.id AS page_id,
          d.doc_key,
          d.title,
          d.date_guess,
          d.url,
          d.matched_terms,
          dc.grade,
          dc.score AS class_score,
          dc.reason AS class_reason,
          t.status AS translation_status
        FROM documents d
        JOIN document_classifications dc ON dc.document_id = d.id
        JOIN pages p ON p.document_id = d.id
        JOIN translations t ON t.page_id = p.id
        WHERE d.source_platform = 'drnh'
          AND t.status = 'auto-converted'
        ORDER BY dc.grade ASC, dc.score DESC, d.date_guess ASC, d.id ASC
        """
    ).fetchall()
    return [score_row(row) for row in rows]


def write_csv(rows: list[dict[str, object]]) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "tier",
        "review_score",
        "grade",
        "class_score",
        "doc_id",
        "page_id",
        "date_guess",
        "title",
        "reason",
        "doc_key",
        "url",
    ]
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (-int(r["review_score"]), str(r["date_guess"]), int(r["doc_id"]))):
            writer.writerow({field: row[field] for field in fields})


def sample_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_tier: dict[str, list[dict[str, object]]] = {
        tier: [r for r in rows if r["tier"] == tier]
        for tier in ("重点校订", "常规校订", "背景保留")
    }
    sample: list[dict[str, object]] = []
    sample.extend(sorted(by_tier["重点校订"], key=lambda r: -int(r["review_score"]))[:12])
    sample.extend(sorted(by_tier["常规校订"], key=lambda r: -int(r["review_score"]))[:5])
    sample.extend(sorted(by_tier["背景保留"], key=lambda r: -int(r["review_score"]))[:3])
    return sample


def write_report(rows: list[dict[str, object]]) -> None:
    counts = Counter(row["tier"] for row in rows)
    grade_counts = Counter(row["grade"] for row in rows)
    samples = sample_rows(rows)

    lines = [
        "# DRNH 自动转写档案校订分层",
        "",
        "本报告由 `scripts/build/build_drnh_review_layers.py` 生成。脚本只读数据库，不修改翻译状态。",
        "",
        "## 总览",
        "",
        f"- DRNH `auto-converted` 档案：{len(rows)} 篇",
        f"- A 档：{grade_counts.get('A', 0)} 篇",
        f"- B 档：{grade_counts.get('B', 0)} 篇",
        f"- 重点校订：{counts.get('重点校订', 0)} 篇",
        f"- 常规校订：{counts.get('常规校订', 0)} 篇",
        f"- 背景保留：{counts.get('背景保留', 0)} 篇",
        f"- CSV 队列：`{CSV_OUT.relative_to(ROOT)}`",
        "",
        "## 分层规则",
        "",
        "- 基础分来自 `document_classifications.score`。",
        "- 题名或命中词直接出现民盟组织名，加权最高。",
        "- 民盟核心人物、政协/制宪/停战/非法化等事件词、戴笠/侍从室/情报系统词分别加权。",
        "- 1945-1947 年为核心窗口，1948-1949 年次之，1941-1944 年作为前史窗口。",
        "- `重点校订` 用于优先人工核验摘要和题名释读；`常规校订` 保持入库但延后复核；`背景保留` 暂作检索补充。",
        "",
        "## 人工抽检建议",
        "",
        "| 层级 | 分数 | 日期 | 标题 | 理由 |",
        "|---|---:|---|---|---|",
    ]
    for row in samples:
        title = str(row["title"]).replace("|", "｜")
        reason = str(row["reason"]).replace("|", "｜")
        lines.append(
            f"| {row['tier']} | {row['review_score']} | {row['date_guess']} | {title} | {reason} |"
        )

    lines.extend([
        "",
        "## 下一步",
        "",
        "1. 先校订 `重点校订` 前 20 篇，检查案由是否能支持摘要表述。",
        "2. 对 `常规校订` 抽查 10 篇，确认分层规则没有系统性误判。",
        "3. `背景保留` 暂不逐篇精修，只在专题检索命中时再回到原始案由核验。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    write_csv(rows)
    write_report(rows)
    print(f"DRNH auto-converted: {len(rows)}")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    print(f"CSV: {CSV_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
