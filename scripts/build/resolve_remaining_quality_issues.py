#!/usr/bin/env python3
"""Resolve the final low-volume translation quality issues."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "research_index.sqlite"
TRANSLATOR = "小班-quality-qc-2026-05-31"


PAGE_REPLACEMENTS = {
    668: [
        (
            "周恩来、Sif、Kutuz [化名，显然指刘少奇和朱德]以及任弼时",
            "周恩来、西夫、库图佐夫（化名，显然指刘少奇和朱德）以及任弼时",
        ),
    ],
    765: [
        ("由 David Wolff 译自俄文。出自 David Wolff 著", "由戴维·沃尔夫译自俄文。出自戴维·沃尔夫著"),
    ],
}


FIXED_TEXTS = {
    762: (
        "reference-summary",
        "【页面分隔符】本页为威尔逊中心镜像文本中的分页标记（--- page break ---），无可译档案正文。",
    ),
    763: (
        "reference-summary",
        "【页面分隔符】本页为威尔逊中心镜像文本中的分页标记（--- page break ---），无可译档案正文。",
    ),
    848: (
        "human-excerpt",
        """【相关段落摘译】

本页为《香港中国邮报》1948 年 2 月 3 日整期扫描的 OCR 片段，版面中混入广告、船期和其他新闻噪声。与本库主题直接相关的内容集中在“中国民主同盟被取缔后的地下工作”一段：

除南京政府军队内部外，被南京政府取缔的中国民主同盟地下工作者，正在全国范围内动员教授、学生、商界人士及普通民众，争取支持推翻现有政权。

关于中国共产党，沈先生（据上下文应为沈钧儒）表示，他个人不认为共产党会反对联合政府，因为共产党一贯主张联合政府。他补充说，联合政府并不必然排除国民党。

后文提到一项以中国民主同盟、中国国民党革命委员会等名义发表的政治行动或声明，但 OCR 残缺严重，无法可靠复原完整名单和句义。

【校订说明】后续大部分文字属于残缺版面、路透社杂讯、广告和船期信息，未逐行翻译；正式引用请回到原始影像核对版面位置。""",
    ),
}


def refresh_fts(conn: sqlite3.Connection, translation_id: int, page_id: int, text: str) -> None:
    try:
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (translation_id,))
        page = conn.execute(
            """
            SELECT d.title, p.page_label
            FROM pages p
            JOIN documents d ON d.id = p.document_id
            WHERE p.id=?
            """,
            (page_id,),
        ).fetchone()
        conn.execute(
            "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
            (translation_id, page[0], page[1] or "doc-level", text),
        )
    except sqlite3.OperationalError:
        pass


def upsert_translation(conn: sqlite3.Connection, page_id: int, text: str, status: str) -> None:
    row = conn.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (page_id,),
    ).fetchone()
    if row:
        translation_id = row[0]
        conn.execute(
            "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
            (text, status, TRANSLATOR, translation_id),
        )
    else:
        cur = conn.execute(
            "INSERT INTO translations(page_id, language, translator, status, text) VALUES (?, 'zh-CN', ?, ?, ?)",
            (page_id, TRANSLATOR, status, text),
        )
        translation_id = cur.lastrowid
    refresh_fts(conn, translation_id, page_id, text)
    conn.execute("DELETE FROM translation_quality_issues WHERE page_id=?", (page_id,))


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    changed = 0
    for page_id, replacements in PAGE_REPLACEMENTS.items():
        row = conn.execute(
            "SELECT text, status FROM translations WHERE page_id=? AND language='zh-CN'",
            (page_id,),
        ).fetchone()
        if not row:
            continue
        text, status = row
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            upsert_translation(conn, page_id, updated, status or "human-reviewed")
            changed += 1

    for page_id, (status, text) in FIXED_TEXTS.items():
        upsert_translation(conn, page_id, text.strip(), status)
        changed += 1

    conn.commit()
    conn.close()
    print(f"Resolved remaining quality issues on {changed} pages.")


if __name__ == "__main__":
    main()
