#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sqlite3
from collections import Counter
from pathlib import Path


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"
REPORT_PATH = Path.cwd() / "docs" / "document_classification_report.md"

CORE_PATTERNS = [
    ("组织定位", r"\b(members?|leaders?|chairman|headquarters|organization|party per se)\b"),
    ("政治纲领", r"\b(platform|program|manifesto|statement|petition|democratic reform|constitutional government|rule of law)\b"),
    ("政协/谈判", r"\b(PCC|Political Consultative|coalition government|peace talks|negotiations|State Council|National Assembly)\b"),
    ("压制/解散", r"\b(outlawry|illegal|dissolution|dissolve|treasonable|assassinations?|terrorism|refuge)\b"),
    ("新政协", r"\b(Preparatory Committee|standing committee|new PCC|Peiping)\b"),
]

DIRECT_ORG_RE = re.compile(
    r"China Democratic League|Chinese Democratic League|Democratic League|"
    r"Democratic Political League|Federation of Chinese Democratic Parties",
    re.IGNORECASE,
)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS document_classifications")
    conn.execute(
        """
        CREATE TABLE document_classifications (
            document_id INTEGER PRIMARY KEY REFERENCES documents(id),
            grade TEXT NOT NULL,
            score INTEGER NOT NULL,
            reason TEXT NOT NULL,
            needs_review INTEGER NOT NULL DEFAULT 0
        )
        """
    )


def classify(row: sqlite3.Row, full_text: str) -> tuple[str, int, str, int]:
    hit_type = row["hit_type"] or ""
    terms = row["matched_terms"] or ""
    text = full_text or ""
    reasons: list[str] = []
    score = 0

    if hit_type == "person_candidate":
        return "人物关联", 20, "由民盟重要人物异写触发，作为人物线索纳入资料库", 0

    org_mentions = len(DIRECT_ORG_RE.findall(text))
    if org_mentions:
        score += min(35, 15 + org_mentions * 5)
        reasons.append(f"组织词出现 {org_mentions} 次")

    if any(name in terms for name in ["Lo Lung", "Chang Lan", "Shen", "Huang", "Liang", "Shih", "Chang Po"]):
        score += 10
        reasons.append("命中民盟关键人物")

    matched_contexts = []
    for label, pattern in CORE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched_contexts.append(label)
    if matched_contexts:
        score += min(40, len(matched_contexts) * 12)
        reasons.append("涉及" + "、".join(matched_contexts))

    if len(text) >= 1200:
        score += 5
        reasons.append("文本信息量较高")

    if "Federation of Chinese Democratic Parties" in terms:
        score += 8
        reasons.append("命中民盟前身译名")

    if score >= 58:
        return "核心文献", score, "；".join(reasons), 0
    if score >= 30:
        return "相关文献", score, "；".join(reasons), 0
    return "背景材料", score, "组织词弱命中或上下文较少，作为背景线索保留", 0


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    docs = conn.execute(
        """
        SELECT documents.*, group_concat(pages.text, ' ') AS full_text
        FROM documents
        JOIN pages ON pages.document_id = documents.id
        GROUP BY documents.id
        ORDER BY documents.volume_id, CAST(documents.doc_number AS INTEGER)
        """
    ).fetchall()
    rows = []
    counts = Counter()
    for doc in docs:
        grade, score, reason, needs_review = classify(doc, doc["full_text"] or "")
        conn.execute(
            """
            INSERT INTO document_classifications(document_id, grade, score, reason, needs_review)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc["id"], grade, score, reason, needs_review),
        )
        counts[grade] += 1
        rows.append((doc, grade, score, reason, needs_review))
    conn.commit()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# FRUS 民盟文档自动分级报告",
        "",
        "自动分级用于整理检索入口，不用于排除资料。资料库以全面收录为主，所有命中文档均保留。",
        "",
        "## 统计",
        "",
        "| 等级 | 数量 |",
        "|---|---:|",
    ]
    for grade in ["核心文献", "相关文献", "人物关联", "背景材料"]:
        lines.append(f"| {grade} | {counts[grade]} |")

    lines.extend(["", "## 规则", ""])
    lines.append("- 核心文献：直接命中组织词，并且同时涉及组织、纲领、政协/谈判、压制/解散、新政协等高价值上下文。")
    lines.append("- 相关文献：直接命中组织词，但上下文较弱或主要为旁及。")
    lines.append("- 人物关联：由民盟重要人物异写触发，作为人物线索保留。")
    lines.append("- 背景材料：组织词弱命中或上下文较少，但仍保留为外围线索。")

    lines.extend(["", "## 样本", ""])
    for grade in ["核心文献", "相关文献", "人物关联", "背景材料"]:
        lines.append(f"### {grade}")
        sample = [r for r in rows if r[1] == grade][:12]
        if not sample:
            lines.append("- 无")
        for doc, _, score, reason, _ in sample:
            lines.append(f"- `{doc['doc_key']}` | {doc['date_guess']} | {score} | {reason}")
        lines.append("")

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    export_path = Path.cwd() / "data" / "document_classifications.csv"
    with export_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["doc_key", "grade", "score", "needs_review", "reason"])
        for doc, grade, score, reason, needs_review in rows:
            writer.writerow([doc["doc_key"], grade, score, needs_review, reason])

    conn.close()
    print(f"Classified {len(rows)} documents.")
    for grade in ["核心文献", "相关文献", "人物关联", "背景材料"]:
        print(f"{grade}: {counts[grade]}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {export_path}")


if __name__ == "__main__":
    main()
