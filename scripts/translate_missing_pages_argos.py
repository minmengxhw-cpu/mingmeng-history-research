#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"
GLOSSARY_PATH = Path.cwd() / "data" / "translation_glossary.csv"


def require_argos():
    try:
        from argostranslate import translate
    except ImportError:
        print("argostranslate is not installed. Use .venv/bin/python for this script.", file=sys.stderr)
        raise
    return translate


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


def iter_chunks(text: str, max_chars: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return [text] if text else []

    parts = re.split(r"(?<=[.!?;:])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for part in parts:
        if not part:
            continue
        if len(part) > max_chars:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_len = 0
            for start in range(0, len(part), max_chars):
                chunks.append(part[start : start + max_chars])
            continue
        if current and current_len + len(part) + 1 > max_chars:
            chunks.append(" ".join(current))
            current = [part]
            current_len = len(part)
        else:
            current.append(part)
            current_len += len(part) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def glossary_postedit(text: str, glossary: list[tuple[str, str]]) -> str:
    # Argos sometimes leaves romanized names or English organization names in output.
    # Apply only exact surviving English terms so Chinese prose is otherwise untouched.
    for term, translation in glossary:
        text = re.sub(re.escape(term), translation, text, flags=re.IGNORECASE)
    replacements = {
        "中国民主党联盟": "中国民主同盟",
        "中国民主联盟": "中国民主同盟",
        "民主联盟": "民主同盟",
        "民主联军": "民主同盟",
        "民主党派联合会": "中国民主政团同盟",
        "中国民主党派联合会": "中国民主政团同盟",
        "中国民主政党联盟": "中国民主政团同盟",
        "库蒙唐": "国民党",
        "库明坦": "国民党",
        "库民坦": "国民党",
        "库明堂": "国民党",
        "库姆宁唐": "国民党",
        "库姆林唐": "国民党",
        "库明唐": "国民党",
        "国民党党": "国民党",
        "蒋介石将军": "蒋介石",
        "Marshall将军": "马歇尔将军",
        "Marshall 马歇尔将军": "马歇尔将军",
        "Mattle of meeting Mattle 马歇尔将军": "马歇尔将军会谈纪要",
        "Mattle of 马歇尔将军": "马歇尔将军会谈纪要",
        "Mattle": "会谈纪要",
        "Third International Party Deplex": "第三方面代表",
        "罗龙志": "罗隆基",
        "罗龙基": "罗隆基",
        "罗龙芝": "罗隆基",
        "罗龙奇": "罗隆基",
        "罗龙chi": "罗隆基",
        "乐龙志": "罗隆基",
        "乐龙芝": "罗隆基",
        "乐龙奇": "罗隆基",
        "洛龙芝": "罗隆基",
        "洛龙志": "罗隆基",
        "洛龙奇": "罗隆基",
        "洛龙chi": "罗隆基",
        "洛医生": "罗博士",
        "洛博士": "罗博士",
        "Lo博士": "罗博士",
        "Lo入室": "罗隆基入室",
        "Lo说": "罗隆基说",
        "Lo ": "罗隆基 ",
        "张敦善": "张东荪",
        "张敦山": "张东荪",
        "常敦善": "张东荪",
        "长敦善": "张东荪",
        "张通善": "张东荪",
        "长通善": "张东荪",
        "长曾敦善": "张东荪",
        "常兰": "张澜",
        "长兰": "张澜",
        "常宝ch": "章伯钧",
        "长宝春": "章伯钧",
        "长宝钧": "章伯钧",
        "熊延培": "黄炎培",
        "黄延培": "黄炎培",
        "梁书明": "梁漱溟",
        "梁舒明": "梁漱溟",
        "沈春珠": "沈钧儒",
        "沈春菊": "沈钧儒",
        "石良": "史良",
        "李黄": "李璜",
        "李煌": "李璜",
        "缪云台": "缪云台",
        "嘉善昌": "张君劢",
        "卡森·昌": "张君劢",
        "卡森昌": "张君劢",
        "昌博士": "张君劢博士",
        "延兴大学": "燕京大学",
        "孙福": "孙科",
        "孙亚臣夫人": "孙夫人",
        "王世芝": "王世杰",
        "陈程": "陈诚",
        "唐恩宝": "汤恩伯",
        "唐恩波": "汤恩伯",
        "汤陶伟": "俞大维",
        "余田伟": "俞大维",
        "于太卫": "俞大维",
        "于大伟": "俞大维",
        "余太卫": "俞大维",
        "第三国际党": "第三方面",
        "第三国际方面": "第三方面",
        "第三国党": "第三方面",
        "第三方集团": "第三方面",
        "五元": "五院",
        "控制院": "监察院",
        "考核院": "考试院",
        "考核袁": "考试院",
        "行政,立法,司法,控制和考试院世凯主席": "行政院、立法院、司法院、监察院和考试院院长",
        "行政、立法、司法、控制和考试院世凯主席": "行政院、立法院、司法院、监察院和考试院院长",
        "袁世凯主席": "院院长",
        "临时国民委员会": "临时全国委员会",
        "国家临时委员会": "临时全国委员会",
        "共产党员提名": "共产党提名",
        "佩平": "北平",
        "裴平": "北平",
        "培平": "北平",
        "培田": "北平",
        "钟京": "重庆",
        "钟庆": "重庆",
        "琼京": "重庆",
        "中京": "重庆",
        "清廷": "重庆",
        "热霍尔": "热河",
        "遂永": "绥远",
        "霍普": "河北",
        "沈西": "陕西",
        "霍南": "河南",
        "耶南": "延安",
        "叶南": "延安",
        "淮南": "延安",
        "南基": "南京",
        "满洲国": "满洲",
        "穆克登": "沈阳",
        "Mukden": "沈阳",
        "Hupeh": "湖北",
        "Hunan": "湖南",
        "Honan": "河南",
        "Shantung": "山东",
        "Shansi": "山西",
        "Shensi": "陕西",
        "库林": "牯岭",
        "Kuling": "牯岭",
        "国务大臣": "国务卿",
        "驻南京国务卿": "驻南京国务卿",
        "民主团体": "民主同盟",
        "民主同盟8号准将叶图义": "民主同盟人士叶笃义",
        "叶图毅": "叶笃义",
        "叶图义": "叶笃义",
        "叶玉怡": "叶笃义",
        "叶赫": "叶笃义",
        "李鹤珍": "李宗仁",
        "李鹤贞": "李宗仁",
        "肖立策": "邵力子",
        "张其ung": "张群",
        "马殷楚": "马寅初",
        "浦希鲁": "浦熙修",
        "浦希秀": "浦熙修",
        "Pu Hsi-hsiu": "浦熙修",
        "Map Sen": "毛森",
        "蒋清国": "蒋经国",
        "富基安": "福建",
        "关西": "广西",
        "宽东": "广东",
        "光东": "广东",
        "成图": "成都",
        "波塞": "百色",
        "史都华": "司徒雷登",
        "斯图尔特": "司徒雷登",
        "俱乐部b": "柯乐博",
        "俱乐部": "柯乐博",
        "卡博特": "卡伯特",
        "霍伯": "霍珀",
        "史密思": "史密斯",
        "麦科诺伊": "麦康纳",
        "杜鲁门·南京总统": "杜鲁门总统",
        "Druman": "Truman",
        "Marshall General to President Truman": "马歇尔将军致杜鲁门总统",
        "Marshall General": "马歇尔将军",
        "President Truman": "杜鲁门总统",
        "Marshall Mission Files": "马歇尔使华档案",
        "周世宗": "周恩来",
        "Chou将军": "周将军",
        "Chou En-Lai": "周恩来",
        "Chou En-lai": "周恩来",
        "Chou教授": "周教授",
        "Gen. 周": "周将军",
        "Gen.": "将军",
        "周将军恩来": "周恩来将军",
        "周将军 to": "周将军",
        "前赫派": "执行总部",
        "Ex.Hq.": "执行总部",
        "黄河保税委员会": "黄河水利委员会",
        "黄河战地小组": "黄河实地小组",
        "李公普": "李公朴",
        "文一托": "闻一多",
        "库楚通": "顾祝同",
        "库尔明": "昆明",
        "云南嘉里森总部": "云南警备司令部",
        "Garrison总部": "警备司令部",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()


def translate_text(translate_module, text: str, glossary: list[tuple[str, str]], max_chunk_chars: int) -> str:
    pieces = []
    for chunk in iter_chunks(text, max_chunk_chars):
        translated = translate_module.translate(chunk, "en", "zh")
        pieces.append(glossary_postedit(translated, glossary))
    return "\n\n".join(piece for piece in pieces if piece)


def fetch_rows(conn: sqlite3.Connection, grade: str | None, limit: int | None, overwrite: bool) -> list[sqlite3.Row]:
    where = []
    params: list[object] = []
    if grade:
        where.append("dc.grade = ?")
        params.append(grade)
    if not overwrite:
        where.append("t.id IS NULL")
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    limit_sql = "LIMIT ?" if limit else ""
    if limit:
        params.append(limit)
    return conn.execute(
        f"""
        SELECT
            pages.id AS page_id,
            pages.text AS source_text,
            pages.page_label,
            documents.title,
            COALESCE(dc.grade, '未分级') AS grade
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        LEFT JOIN translations t ON t.page_id = pages.id AND t.language = 'zh-CN'
        {where_sql}
        ORDER BY
            CASE COALESCE(dc.grade, '')
                WHEN '核心文献' THEN 1
                WHEN '相关文献' THEN 2
                WHEN '人物关联' THEN 3
                WHEN '背景材料' THEN 4
                ELSE 5
            END,
            documents.date_guess,
            pages.id
        {limit_sql}
        """,
        params,
    ).fetchall()


def upsert_translation(conn: sqlite3.Connection, row: sqlite3.Row, text: str, translator: str, status: str) -> None:
    existing = conn.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (row["page_id"],),
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (existing[0],))
        conn.execute("DELETE FROM translations WHERE id=?", (existing[0],))
    cur = conn.execute(
        """
        INSERT INTO translations(page_id, language, translator, status, text)
        VALUES (?, 'zh-CN', ?, ?, ?)
        """,
        (row["page_id"], translator, status, text),
    )
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, ?, ?, ?, ?)",
        (cur.lastrowid, "zh-CN", row["title"], row["page_label"] or "doc-level", text),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate missing FRUS page segments locally with Argos Translate.")
    parser.add_argument("--grade", help="Only translate one classification grade, for example 核心文献.")
    parser.add_argument("--limit", type=int, help="Translate only the first N matching segments.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing zh-CN translations.")
    parser.add_argument("--max-chunk-chars", type=int, default=1800)
    parser.add_argument("--translator", default="argos-en-zh-local")
    parser.add_argument("--status", default="machine-draft-local-review-needed")
    parser.add_argument("--commit-every", type=int, default=1)
    args = parser.parse_args()

    translate_module = require_argos()
    glossary = load_glossary()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    rows = fetch_rows(conn, args.grade, args.limit, args.overwrite)
    if not rows:
        print("No matching untranslated segments found.")
        return

    translated_count = 0
    for index, row in enumerate(rows, start=1):
        print(f"[{index}/{len(rows)}] page_id={row['page_id']} grade={row['grade']} title={row['title'][:80]}")
        translated = translate_text(translate_module, row["source_text"], glossary, args.max_chunk_chars)
        if not translated:
            print(f"  skipped page_id={row['page_id']} empty translation")
            continue
        upsert_translation(conn, row, translated, args.translator, args.status)
        translated_count += 1
        if translated_count % args.commit_every == 0:
            conn.commit()
    conn.commit()
    conn.close()
    print(f"Translated {translated_count} segments.")


if __name__ == "__main__":
    main()
