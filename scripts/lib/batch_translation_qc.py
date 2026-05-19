#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


ROOT = Path.cwd()
DB_PATH = ROOT / "data" / "research_index.sqlite"
GLOSSARY_PATH = ROOT / "data" / "translation_glossary.csv"
CSV_PATH = ROOT / "data" / "batch_translation_qc.csv"
REPORT_PATH = ROOT / "docs" / "batch_translation_qc_report.md"


ALLOWED_ENGLISH = {
    "FRUS",
    "ECA",
    "UNRRA",
    "CNRRA",
    "KmtRC",
    "SWNCC",
    "No",
    "Lot",
    "Document",
    "Files",
}

ACCEPTABLE_TRANSLATIONS = {
    "Democratic League": ["中国民主同盟", "民主同盟", "民盟"],
    "Chinese Democratic League": ["中国民主同盟", "民主同盟", "民盟"],
    "China Democratic League": ["中国民主同盟", "民主同盟", "民盟"],
    "Federation of Chinese Democratic Parties": ["中国民主政团同盟", "民主政团同盟", "民主同盟", "民盟"],
    "Political Consultative Council": ["政治协商会议", "政协", "协商会议"],
    "Political Consultative Conference": ["政治协商会议", "政协", "协商会议"],
    "People's Political Council": ["国民参政会", "参政会"],
    "Kuomintang": ["国民党"],
    "Generalissimo": ["委员长", "蒋介石", "蒋"],
    "General Marshall": ["马歇尔将军", "马歇尔"],
    "Lo Lung-chi": ["罗隆基"],
    "Lo Lung Chi": ["罗隆基"],
    "Liang Shu-ming": ["梁漱溟"],
    "Chang Lan": ["张澜"],
    "Chang Piao-fang": ["张澜"],
    "Shen Chun-ju": ["沈钧儒"],
    "Huang Yen-pei": ["黄炎培"],
    "Chang Po-chun": ["章伯钧"],
    "Shih Liang": ["史良"],
    "Carsun Chang": ["张君劢"],
    "Chang Chun": ["张群"],
    "Chang Tung-sun": ["张东荪"],
    "Chang Tung Sun": ["张东荪"],
    "Hsu Yung-chang": ["徐永昌"],
    "T. V. Soong": ["宋子文"],
    "Wang Shihchieh": ["王世杰"],
    "Yu Ta-wei": ["俞大维"],
    "Tang En-po": ["汤恩伯"],
    "Miao Yun-tai": ["缪云台"],
    "Li Hwang": ["李璜"],
    "Chou En-lai": ["周恩来"],
    "Chou Enlai": ["周恩来"],
    "Li Tsung-jen": ["李宗仁"],
    "Shao Li-tzu": ["邵力子"],
    "Ma Yin-chu": ["马寅初"],
    "Pu Hsi-hsiu": ["浦熙修"],
    "Ye Tu-yi": ["叶笃义"],
    "Peiping": ["北平"],
    "Nanking": ["南京"],
    "Chungking": ["重庆"],
    "Kweilin": ["桂林"],
    "Kunming": ["昆明"],
    "Yenan": ["延安"],
    "Mukden": ["沈阳", "奉天", "满洲"],
    "Manchuria": ["满洲"],
}

MANUAL_REPLACEMENTS = [
    ("中国阿盟", "中国民主同盟"),
    ("阿盟", "民盟"),
    ("民主联盟", "民主同盟"),
    ("洛龙芝", "罗隆基"),
    ("洛龙志", "罗隆基"),
    ("罗龙志", "罗隆基"),
    ("罗龙芝", "罗隆基"),
    ("洛隆基", "罗隆基"),
    ("张敦善", "张东荪"),
    ("张同孙", "张东荪"),
    ("张顿孙", "张东荪"),
    ("沉钧儒", "沈钧儒"),
    ("石良", "史良"),
    ("库蒙唐", "国民党"),
    ("库明坦", "国民党"),
    ("国明党", "国民党"),
    ("唐恩宝", "汤恩伯"),
    ("延兴大学", "燕京大学"),
    ("第三国际党", "第三党"),
    ("Generalissimo", "委员长"),
    ("General Marshall", "马歇尔将军"),
    ("Democratic League", "中国民主同盟"),
    ("Chinese Democratic League", "中国民主同盟"),
    ("China Democratic League", "中国民主同盟"),
    ("Political Consultative Council", "政治协商会议"),
    ("Political Consultative Conference", "政治协商会议"),
    ("People's Political Council", "国民参政会"),
    ("Kuomintang", "国民党"),
    ("Lo Lung-chi", "罗隆基"),
    ("Lo Lung Chi", "罗隆基"),
    ("Chang Tung-sun", "张东荪"),
    ("Chang Tung Sun", "张东荪"),
    ("Carsun Chang", "张君劢"),
    ("Chang Lan", "张澜"),
    ("Shen Chun-ju", "沈钧儒"),
    ("Shih Liang", "史良"),
    ("Huang Yen-pei", "黄炎培"),
    ("Chang Po-chun", "章伯钧"),
    ("Liang Shu-ming", "梁漱溟"),
    ("Chou En-lai", "周恩来"),
    ("Chou Enlai", "周恩来"),
    ("T. V. Soong", "宋子文"),
    ("Yu Ta-wei", "俞大维"),
    ("Peiping", "北平"),
    ("Nanking", "南京"),
    ("Chungking", "重庆"),
    ("Kunming", "昆明"),
    ("Yenan", "延安"),
    ("Mukden", "沈阳"),
]

BAD_TERMS = {
    "Mattle": "英文残留或模型误译",
    "Deplex": "英文残留或模型误译",
    "洛龙": "Lo Lung-chi 可能未统一为罗隆基",
    "库蒙": "Kuomintang 可能未统一为国民党",
    "库明": "Kuomintang 可能未统一为国民党",
}


@dataclass
class Decision:
    tier: str
    action: str
    reasons: list[str]
    hard_issues: list[str]
    changed: bool
    original_text: str
    updated_text: str


def compact(text: str, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def load_glossary() -> list[tuple[str, str]]:
    if not GLOSSARY_PATH.exists():
        return []
    rows: list[tuple[str, str]] = []
    with GLOSSARY_PATH.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            term = (row.get("term") or "").strip()
            translation = (row.get("translation") or "").strip()
            if term and translation:
                rows.append((term, translation))
    rows.sort(key=lambda item: len(item[0]), reverse=True)
    return rows


def replacements(glossary: list[tuple[str, str]]) -> list[tuple[str, str]]:
    merged = [(term, translation) for term, translation in glossary if len(term) >= 5]
    merged.extend(MANUAL_REPLACEMENTS)
    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for old, new in sorted(merged, key=lambda item: len(item[0]), reverse=True):
        key = (old, new)
        if key not in seen:
            seen.add(key)
            unique.append((old, new))
    return unique


def normalize_translation(text: str, glossary: list[tuple[str, str]]) -> str:
    updated = text or ""
    for old, new in replacements(glossary):
        updated = updated.replace(old, new)
    updated = re.sub(r"[ \t]+", " ", updated)
    updated = re.sub(r" *\n *", "\n", updated)
    return updated.strip()


def english_residue(text: str) -> list[str]:
    words = re.findall(r"\b[A-Z][A-Za-z][A-Za-z.-]{2,}\b", text or "")
    kept: list[str] = []
    for word in words:
        clean = word.strip(".,;:()[]")
        if clean in ALLOWED_ENGLISH:
            continue
        if re.fullmatch(r"[IVXLCDM]+", clean):
            continue
        if re.fullmatch(r"[A-Z]\.", clean):
            continue
        kept.append(clean)
    seen: list[str] = []
    for word in kept:
        if word not in seen:
            seen.append(word)
    return seen[:12]


def expected_translations(term: str, glossary_translation: str) -> list[str]:
    return ACCEPTABLE_TRANSLATIONS.get(term, [glossary_translation])


def hard_issues(source: str, zh: str, glossary: list[tuple[str, str]]) -> list[str]:
    issues: list[str] = []
    if not zh.strip():
        return ["缺少译文"]

    ratio = len(zh) / max(len(source), 1)
    if ratio < 0.18:
        issues.append(f"译文过短({ratio:.2f})")
    if ratio > 1.90:
        issues.append(f"译文过长({ratio:.2f})")

    residues = english_residue(zh)
    if residues:
        issues.append("英文残留：" + "、".join(residues))

    for bad, detail in BAD_TERMS.items():
        if bad in zh:
            issues.append(detail)

    source_lower = source.lower()
    for term, translation in glossary:
        if len(term) < 5:
            continue
        if term.lower() in source_lower and not any(expected in zh for expected in expected_translations(term, translation)):
            issues.append(f"术语缺失：{term}->{translation}")
            break

    return issues


def classify(row: sqlite3.Row, glossary: list[tuple[str, str]], max_chars: int) -> Decision:
    source = row["source_text"] or ""
    zh = row["zh_text"] or ""
    updated = normalize_translation(zh, glossary)
    issues = hard_issues(source, updated, glossary)
    issue_types = set((row["issue_types"] or "").split(","))
    source_l = source.lower()
    direct_core = any(
        token in source_l
        for token in [
            "lo lung-chi",
            "assassin",
            "assassination",
            "political consultative",
            "outlaw",
            "democratic league",
            "league leaders",
            "chang lan",
            "shen chun-ju",
            "shih liang",
        ]
    )

    reasons: list[str] = []
    if len(source) > max_chars:
        reasons.append(f"原文较长({len(source)}字)")
    if row["max_severity"] and row["max_severity"] >= 3:
        reasons.append("含严重问题")
    if direct_core and row["grade"] == "核心文献":
        reasons.append("核心主题页")
    if "length_short" in issue_types or "length_too_short" in issue_types:
        reasons.append("长度问题")

    changed = updated != zh.strip()
    if not issues and not reasons:
        return Decision("A-批量快校", "auto_pass", ["硬性检查通过"], issues, changed, zh, updated)
    if not issues and len(source) <= max_chars and row["max_severity"] and row["max_severity"] <= 2:
        return Decision("B-批量校订", "candidate", reasons or ["可批量抽查"], issues, changed, zh, updated)
    return Decision("C-人工精校", "manual", reasons or ["硬性检查未过"], issues, changed, zh, updated)


def fetch_queue(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        WITH issue_stats AS (
            SELECT
                page_id,
                count(*) AS issue_count,
                max(severity) AS max_severity,
                group_concat(DISTINCT issue_type) AS issue_types
            FROM translation_quality_issues
            GROUP BY page_id
        )
        SELECT
            pages.id AS page_id,
            pages.text AS source_text,
            pages.page_label,
            documents.doc_key,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade,
            translations.id AS translation_id,
            translations.text AS zh_text,
            translations.status AS zh_status,
            translations.translator AS translator,
            issue_stats.issue_count,
            issue_stats.max_severity,
            issue_stats.issue_types,
            (
                issue_stats.max_severity * 100
                + issue_stats.issue_count * 10
                + CASE COALESCE(dc.grade, '')
                    WHEN '核心文献' THEN 80
                    WHEN '相关文献' THEN 45
                    WHEN '人物关联' THEN 25
                    ELSE 0
                  END
            ) AS priority_score
        FROM issue_stats
        JOIN pages ON pages.id = issue_stats.page_id
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        ORDER BY priority_score DESC, documents.date_guess, pages.id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def update_translation_fts(conn: sqlite3.Connection, row: sqlite3.Row, text: str) -> None:
    if not row["translation_id"]:
        return
    conn.execute("DELETE FROM translation_fts WHERE rowid=?", (row["translation_id"],))
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
        (row["translation_id"], row["title"], row["page_label"] or "doc-level", text),
    )


def apply_decision(conn: sqlite3.Connection, row: sqlite3.Row, decision: Decision) -> None:
    if decision.changed and row["translation_id"]:
        conn.execute(
            """
            UPDATE translations
            SET text=?, translator='codex-batch-qc-v1'
            WHERE id=?
            """,
            (decision.updated_text, row["translation_id"]),
        )
        update_translation_fts(conn, row, decision.updated_text)

    if decision.action == "auto_pass" and row["translation_id"]:
        conn.execute(
            """
            UPDATE translations
            SET status='batch-qc-passed', translator='codex-batch-qc-v1'
            WHERE id=?
            """,
            (row["translation_id"],),
        )
        conn.execute("DELETE FROM translation_quality_issues WHERE page_id=?", (row["page_id"],))


def write_outputs(rows: list[tuple[sqlite3.Row, Decision]], applied: bool) -> None:
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "page_id",
                "tier",
                "action",
                "grade",
                "date",
                "doc_key",
                "issue_count",
                "issue_types",
                "changed",
                "reasons",
                "hard_issues",
                "title",
            ]
        )
        for row, decision in rows:
            writer.writerow(
                [
                    row["page_id"],
                    decision.tier,
                    decision.action,
                    row["grade"],
                    row["date_guess"],
                    row["doc_key"],
                    row["issue_count"],
                    row["issue_types"],
                    "yes" if decision.changed else "no",
                    "；".join(decision.reasons),
                    "；".join(decision.hard_issues),
                    row["title"],
                ]
            )

    counts: dict[str, int] = {}
    for _, decision in rows:
        counts[decision.action] = counts.get(decision.action, 0) + 1
    report = [
        "# 批量译文质检报告",
        "",
        f"- 模式：{'已写入数据库' if applied else '预演，未写入'}",
        f"- 检查页片段：{len(rows)}",
        f"- 自动通过：{counts.get('auto_pass', 0)}",
        f"- 批量候选：{counts.get('candidate', 0)}",
        f"- 保留人工精校：{counts.get('manual', 0)}",
        f"- 明细 CSV：`{CSV_PATH}`",
        "",
        "## 前 40 条分诊",
        "",
        "| 页片段 | 分层 | 动作 | 等级 | 问题 | 原因 |",
        "|---:|---|---|---|---|---|",
    ]
    for row, decision in rows[:40]:
        issue_text = "；".join(decision.hard_issues) or "通过"
        reason_text = "；".join(decision.reasons)
        report.append(
            f"| {row['page_id']} | {decision.tier} | {decision.action} | {row['grade']} | {issue_text} | {reason_text} |"
        )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch triage and low-risk QC pass for FRUS Chinese translations.")
    parser.add_argument("--limit", type=int, default=120, help="number of queued pages to inspect")
    parser.add_argument("--max-chars", type=int, default=2200, help="max source length for automatic pass")
    parser.add_argument("--apply", action="store_true", help="write low-risk fixes and auto-pass decisions")
    args = parser.parse_args()

    glossary = load_glossary()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    queue = fetch_queue(conn, args.limit)
    decisions = [(row, classify(row, glossary, args.max_chars)) for row in queue]

    if args.apply:
        for row, decision in decisions:
            if decision.action in {"auto_pass", "candidate"} and decision.changed and row["translation_id"]:
                apply_decision(conn, row, decision)
            elif decision.action == "auto_pass":
                apply_decision(conn, row, decision)
        conn.commit()

    write_outputs(decisions, args.apply)
    conn.close()

    total_auto = sum(1 for _, decision in decisions if decision.action == "auto_pass")
    total_candidate = sum(1 for _, decision in decisions if decision.action == "candidate")
    total_manual = sum(1 for _, decision in decisions if decision.action == "manual")
    print(f"Checked {len(decisions)} pages.")
    print(f"auto_pass={total_auto} candidate={total_candidate} manual={total_manual}")
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
