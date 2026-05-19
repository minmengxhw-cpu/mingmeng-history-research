#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"

SAMPLE_TRANSLATIONS = {
    ("frus1946v09", "d735", ""): """893.00/8-646：电报。[第735号文件] 驻华大使（司徒雷登）致国务卿。南京，1946年8月6日上午10时；8月6日上午4时25分收到。

1270。最近同中国民主同盟成员的谈话，包括若干曾在昆明领事馆避难者，显示出民盟内部因昆明暗杀事件而普遍恐惧。无论暗杀责任究竟归属何方，其结果都暴露了民盟作为一个政治党派本身的薄弱，也显示它难以成为凝聚中国内部政治的力量。民盟一些重要领导人现在意识到组织能力有限，或受到暗杀事件惊吓，认为自己面临三种选择：（1）公开悔过或退让；（2）出国；（3）加入共产党。

目前，教育部正安排几位民盟成员中的知名教授，以各种学术身份前往澳大利亚和美国。另有一些人已经公开表示今后只从事学术工作，以此作出退让。

看来多数民盟领导人可能会接受第一种选择。当前报刊关于政府可能在没有共产党参加的情况下进行改组的评论，也许是在为向民盟成员提供官方职位作铺垫。这样做除了在国外具有重要宣传价值外，可能还会有效消除对国民党政策的自由派反对。若有机会，最著名的一些教授可能会接受第二种选择；从实际效果看，流亡与暗杀同样能够达到排除其影响的目的。""",
    ("frus1946v09", "d735", "1452"): """预计只有少数民盟领导人会前往共产党地区；一位著名的民盟教授已经向使馆含蓄表达了前往延安的愿望。不过可以预期，学生，尤其是受暗杀事件影响的大学中的学生，前往延安、张家口或其他共产党控制地点的情况会增加。许多教授和知识分子不愿前往共产党地区，是因为担心自己只会被共产党用于宣传目的。

司徒雷登""",
}


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            language TEXT NOT NULL,
            translator TEXT,
            status TEXT,
            text TEXT NOT NULL,
            UNIQUE(page_id, language)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS translation_fts USING fts5(
            language,
            title,
            page_label,
            text
        );
        """
    )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)

    inserted = 0
    for (volume_id, doc_id, page_label), zh_text in SAMPLE_TRANSLATIONS.items():
        row = conn.execute(
            """
            SELECT pages.id, documents.title
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            WHERE documents.volume_id=? AND documents.doc_id=? AND pages.page_label=?
            """,
            (volume_id, doc_id, page_label),
        ).fetchone()
        if not row:
            raise RuntimeError(f"Missing page segment: {volume_id}/{doc_id} page={page_label!r}")
        page_id, title = row
        existing = conn.execute(
            "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
            (page_id,),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM translation_fts WHERE rowid=?", (existing[0],))
            conn.execute("DELETE FROM translations WHERE id=?", (existing[0],))
        cur = conn.execute(
            """
            INSERT INTO translations(page_id, language, translator, status, text)
            VALUES (?, 'zh-CN', 'manual-demo', 'sample-review-needed', ?)
            """,
            (page_id, zh_text),
        )
        conn.execute(
            "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, ?, ?, ?, ?)",
            (cur.lastrowid, "zh-CN", title, page_label or "doc-level", zh_text),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} sample translation segments into {DB_PATH}")


if __name__ == "__main__":
    main()
