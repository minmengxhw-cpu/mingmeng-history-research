#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path


ROOT = Path.cwd()
DB_PATH = ROOT / "data" / "research_index.sqlite"
CSV_PATH = ROOT / "data" / "translation_quality_issues.csv"
REPORT_PATH = ROOT / "docs" / "translation_quality_report.md"
GLOSSARY_PATH = ROOT / "data" / "translation_glossary.csv"


COMMON_ALLOWED_ENGLISH = {
    "FRUS",
    "PCC",
    "No",
    "Lot",
    "Document",
    "General",
    "Doctor",
    "Mr",
    "Mrs",
    "Dr",
    "Mission",
    "Files",
    "Nanking",
    "Peiping",
    "Chungking",
    "Kunming",
    "Shanghai",
    "Airgram",
    "Telegram",
    "RefDeptel",
    "Deptel",
    "Embtel",
    "Contel",
    "ReDeptel",
    "ReContel",
    "Mytels",
    "OffEmb",
    "Department",
    "Sent",
    "Canton",
    "Tientsin",
    "SWNCC",
    "UNRRA",
    "CNRRA",
    "ECA",
    "KmtRC",
    "Vol.ix",
    "April",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
}

BAD_TERMS = {
    "库蒙唐": "Kuomintang 应为国民党",
    "库明坦": "Kuomintang 应为国民党",
    "洛龙芝": "Lo Lung-chi 应为罗隆基",
    "洛龙志": "Lo Lung-chi 应为罗隆基",
    "罗龙志": "Lo Lung-chi 应为罗隆基",
    "张敦善": "Chang Tung-sun 通常应为张东荪",
    "延兴大学": "Yenching University 应为燕京大学",
    "唐恩宝": "Tang En-po 应为汤恩伯",
    "第三国际党": "Third Party / third party 不应译为第三国际党",
    "Mattle": "英文残留或模型误译",
    "Deplex": "英文残留或模型误译",
}


ACCEPTABLE_TRANSLATIONS = {
    "Democratic League": ["中国民主同盟", "民主同盟", "民盟"],
    "Chinese Democratic League": ["中国民主同盟", "民主同盟", "民盟"],
    "China Democratic League": ["中国民主同盟", "民主同盟", "民盟"],
    "Federation of Chinese Democratic Parties": ["中国民主政团同盟", "民主政团同盟", "民主同盟", "中国民主党派联合会"],
    "Political Consultative Council": ["政治协商会议", "政协", "协商会议", "PCC"],
    "Political Consultative Conference": ["政治协商会议", "政协", "协商会议", "PCC"],
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
    "T. V. Soong": ["宋子文", "宋"],
    "Wang Shihchieh": ["王世杰"],
    "Yu Ta-wei": ["俞大维"],
    "Tang En-po": ["汤恩伯"],
    "Miao Yun-tai": ["缪云台"],
    "Li Hwang": ["李璜"],
    "Chou En-lai": ["周恩来", "周将军"],
    "Chou Enlai": ["周恩来", "周将军"],
    "Li Tsung-jen": ["李宗仁"],
    "Shao Li-tzu": ["邵力子"],
    "Ma Yin-chu": ["马寅初"],
    "Pu Hsi-hsiu": ["浦熙修"],
    "Ye Tu-yi": ["叶笃义"],
    "Yenan": ["延安"],
    "Mukden": ["沈阳", "奉天", "满洲"],
    "Manchuria": ["满洲"],
    "Peiping": ["北平"],
    "Nanking": ["南京"],
    "Chungking": ["重庆"],
}


def compact(text: str, limit: int = 180) -> str:
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


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS translation_quality_issues;
        CREATE TABLE translation_quality_issues (
            id INTEGER PRIMARY KEY,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            issue_type TEXT NOT NULL,
            severity INTEGER NOT NULL,
            detail TEXT NOT NULL,
            snippet TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_translation_quality_page ON translation_quality_issues(page_id);
        CREATE INDEX IF NOT EXISTS idx_translation_quality_type ON translation_quality_issues(issue_type);
        CREATE INDEX IF NOT EXISTS idx_translation_quality_severity ON translation_quality_issues(severity);
        """
    )


def english_residue(text: str) -> list[str]:
    words = re.findall(r"\b[A-Z][A-Za-z][A-Za-z.-]{2,}\b", text or "")
    kept: list[str] = []
    for word in words:
        clean = word.strip(".,;:()[]")
        if clean in COMMON_ALLOWED_ENGLISH:
            continue
        if re.fullmatch(r"[IVXLCDM]+", clean):
            continue
        kept.append(clean)
    seen: list[str] = []
    for word in kept:
        if word not in seen:
            seen.append(word)
    return seen[:12]


def expected_translations(term: str, glossary_translation: str) -> list[str]:
    return ACCEPTABLE_TRANSLATIONS.get(term, [glossary_translation])


def source_contains_term(source: str, term: str) -> bool:
    pattern = re.compile(rf"(?<![A-Za-z]){re.escape(term)}(?![A-Za-z-])", re.IGNORECASE)
    return bool(pattern.search(source))


def insert_issue(
    conn: sqlite3.Connection,
    page_id: int,
    issue_type: str,
    severity: int,
    detail: str,
    snippet: str,
) -> None:
    conn.execute(
        """
        INSERT INTO translation_quality_issues(page_id, issue_type, severity, detail, snippet)
        VALUES (?, ?, ?, ?, ?)
        """,
        (page_id, issue_type, severity, detail, snippet),
    )


def analyze_row(conn: sqlite3.Connection, row: sqlite3.Row, glossary: list[tuple[str, str]]) -> int:
    count = 0
    page_id = row["page_id"]
    source = row["source_text"] or ""
    zh = row["zh_text"] or ""
    source_len = max(len(source), 1)
    zh_len = len(zh)

    if not zh.strip():
        insert_issue(conn, page_id, "missing_translation", 3, "缺少中文译文", compact(source))
        return 1

    ratio = zh_len / source_len
    if ratio < 0.12:
        insert_issue(conn, page_id, "length_too_short", 3, f"译文长度明显偏短，中文/英文字符比 {ratio:.2f}", compact(zh))
        count += 1
    elif ratio < 0.20:
        insert_issue(conn, page_id, "length_short", 2, f"译文可能偏短，中文/英文字符比 {ratio:.2f}", compact(zh))
        count += 1
    elif ratio > 1.80:
        insert_issue(conn, page_id, "length_long", 1, f"译文可能偏长，中文/英文字符比 {ratio:.2f}", compact(zh))
        count += 1

    for bad, detail in BAD_TERMS.items():
        if bad in zh:
            insert_issue(conn, page_id, "known_bad_term", 3, detail, compact(zh[zh.find(bad) - 70 : zh.find(bad) + 110]))
            count += 1

    residues = english_residue(zh)
    if residues:
        severity = 2 if len(residues) >= 4 else 1
        insert_issue(
            conn,
            page_id,
            "english_residue",
            severity,
            "译文仍保留英文词：" + "、".join(residues),
            compact(zh),
        )
        count += 1

    for term, translation in glossary:
        if len(term) < 5:
            continue
        if source_contains_term(source, term) and not any(expected in zh for expected in expected_translations(term, translation)):
            insert_issue(
                conn,
                page_id,
                "glossary_miss",
                2,
                f"原文含 {term}，译文未见统一译名“{translation}”",
                compact(zh),
            )
            count += 1
            break

    if row["grade"] == "核心文献" and row["status"] and "local" in row["status"]:
        insert_issue(conn, page_id, "core_machine_draft", 1, "核心文献仍为机器初稿，建议优先抽查", compact(zh))
        count += 1

    return count


def main() -> None:
    glossary = load_glossary()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    rows = conn.execute(
        """
        SELECT
            pages.id AS page_id,
            pages.text AS source_text,
            translations.text AS zh_text,
            translations.status,
            documents.doc_key,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language = 'zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        ORDER BY pages.id
        """
    ).fetchall()

    total = 0
    for row in rows:
        total += analyze_row(conn, row, glossary)
    conn.commit()

    issue_rows = conn.execute(
        """
        SELECT
            q.*,
            documents.doc_key,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade
        FROM translation_quality_issues q
        JOIN pages ON pages.id = q.page_id
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        ORDER BY q.severity DESC, documents.date_guess, q.page_id, q.issue_type
        """
    ).fetchall()

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["page_id", "doc_key", "grade", "date_guess", "issue_type", "severity", "detail", "snippet", "title"])
        for row in issue_rows:
            writer.writerow(
                [
                    row["page_id"],
                    row["doc_key"],
                    row["grade"],
                    row["date_guess"],
                    row["issue_type"],
                    row["severity"],
                    row["detail"],
                    row["snippet"],
                    row["title"],
                ]
            )

    by_type = conn.execute(
        "SELECT issue_type, severity, count(*) FROM translation_quality_issues GROUP BY issue_type, severity ORDER BY severity DESC, count(*) DESC"
    ).fetchall()
    by_grade = conn.execute(
        """
        SELECT COALESCE(dc.grade, '未分级') AS grade, count(*)
        FROM translation_quality_issues q
        JOIN pages ON pages.id = q.page_id
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        GROUP BY grade
        ORDER BY count(*) DESC
        """
    ).fetchall()

    report = [
        "# 译文质量检查报告",
        "",
        f"- 检查片段：{len(rows)}",
        f"- 风险提示：{total}",
        f"- CSV：`{CSV_PATH}`",
        "",
        "## 按问题类型",
        "",
        "| 问题类型 | 严重度 | 数量 |",
        "|---|---:|---:|",
    ]
    for issue_type, severity, count in by_type:
        report.append(f"| {issue_type} | {severity} | {count} |")
    report.extend(["", "## 按文献等级", "", "| 等级 | 数量 |", "|---|---:|"])
    for grade, count in by_grade:
        report.append(f"| {grade} | {count} |")
    report.extend(["", "## 前 30 个高优先级问题", "", "| 页片段 | 等级 | 问题 | 严重度 | 说明 |", "|---:|---|---|---:|---|"])
    for row in issue_rows[:30]:
        report.append(
            f"| {row['page_id']} | {row['grade']} | {row['issue_type']} | {row['severity']} | {row['detail']} |"
        )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    conn.close()
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Found {total} quality issues.")


if __name__ == "__main__":
    main()
