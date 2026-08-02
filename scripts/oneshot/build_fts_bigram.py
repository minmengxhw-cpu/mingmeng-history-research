#!/usr/bin/env python3
"""为中文 2 字词检索新增 bigram FTS5 索引表

背景（S2）：page_fts/translation_fts 用 trigram tokenizer，需要 3+ 连续字符，
中文人名/核心词大量为 2 字（民盟/张澜/政协/卢汉…），trigram 命中为 0，
只能退化为 LIKE 全表扫描（~40ms 且无 bm25 排序）。

方案：新增 page_fts_bigram / translation_fts_bigram，使用 unicode61 tokenizer，
插入时把 CJK 连续段预切分为「空格分隔的重叠 2 字 bigram」。
unicode61 下每个 bigram 是独立 token，2 字词单 token 命中、多字词用相邻
bigram phrase 命中。英文保持原样（unicode61 按空格分词）。

查询端（app.py rows_for_search）：
- CJK 词 → 切 bigram → phrase "民主 主同 同盟" 匹配 bigram 表
- 英文 3+ 词 → 沿用 trigram 表
- 短英文/1 字中文 → LIKE 兜底
"""
import re
import sqlite3
import sys
from pathlib import Path

CJK_RE = re.compile(r"[\u3400-\u9fff]+")

DB = Path(__file__).resolve().parent.parent.parent / "data" / "research_index.sqlite"
ROOT = DB.parent.parent
NEWSPAPERSG_CLEAN_DIR = ROOT / "data" / "newspapersg" / "documents_clean"


def bigramize(text: str) -> str:
    """把 CJK 连续段切为空格分隔的重叠 2 字 bigram，非 CJK 内容原样保留。"""
    out: list[str] = []
    last = 0
    for m in CJK_RE.finditer(text):
        if m.start() > last:
            out.append(text[last : m.start()])
        seg = m.group(0)
        for i in range(len(seg) - 1):
            out.append(seg[i : i + 2])
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    return " ".join(p for p in out if p)


def build():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    print("=== 重建前 ===")
    try:
        n_pg = cur.execute("SELECT COUNT(*) FROM page_fts_bigram").fetchone()[0]
    except sqlite3.OperationalError:
        n_pg = 0
    try:
        n_tr = cur.execute("SELECT COUNT(*) FROM translation_fts_bigram").fetchone()[0]
    except sqlite3.OperationalError:
        n_tr = 0
    print(f"  page_fts_bigram: {n_pg}")
    print(f"  translation_fts_bigram: {n_tr}")

    print("\n删除旧 bigram FTS 表...")
    cur.execute("DROP TABLE IF EXISTS page_fts_bigram")
    cur.execute("DROP TABLE IF EXISTS translation_fts_bigram")

    print("用 unicode61 tokenizer 重建 bigram 表...")
    cur.execute("""
        CREATE VIRTUAL TABLE page_fts_bigram USING fts5(
            volume_id, doc_id, title, page_label, matched_terms, text,
            tokenize='unicode61'
        )
    """)
    cur.execute("""
        CREATE VIRTUAL TABLE translation_fts_bigram USING fts5(
            language, title, page_label, text,
            tokenize='unicode61'
        )
    """)

    print("\n填充 page_fts_bigram（预切 bigram）...")
    n = 0
    page_rows = cur.execute("""
        SELECT p.id,
               COALESCE(d.volume_id, ''), COALESCE(d.doc_id, ''),
               COALESCE(d.title, ''), COALESCE(p.page_label, ''),
               COALESCE(d.matched_terms, ''), COALESCE(p.text, '')
        FROM pages p JOIN documents d ON d.id = p.document_id
    """).fetchall()
    for row in page_rows:
        cur.execute(
            "INSERT INTO page_fts_bigram(rowid, volume_id, doc_id, title, page_label, matched_terms, text) VALUES (?,?,?,?,?,?,?)",
            (
                row[0],
                bigramize(row[1]),
                bigramize(row[2]),
                bigramize(row[3]),
                bigramize(row[4]),
                bigramize(row[5]),
                bigramize(row[6]),
            ),
        )
        n += 1
    print(f"  完成: {n}")

    if NEWSPAPERSG_CLEAN_DIR.exists():
        print("\n覆盖 NewspaperSG page_fts_bigram 为清洗 OCR...")
        cleaned = 0
        nsg_rows = cur.execute("""
            SELECT p.id, d.doc_key
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            WHERE d.source_platform='newspapersg'
        """).fetchall()
        for page_id, doc_key in nsg_rows:
            clean_path = NEWSPAPERSG_CLEAN_DIR / f"{doc_key.removeprefix('newspapersg:')}.txt"
            if not clean_path.exists():
                continue
            text = clean_path.read_text(encoding="utf-8", errors="replace").strip()
            cur.execute(
                "UPDATE page_fts_bigram SET text=? WHERE rowid=?",
                (bigramize(text), page_id),
            )
            cleaned += 1
        print(f"  完成: {cleaned}")

    print("\n填充 translation_fts_bigram（预切 bigram）...")
    n = 0
    tr_rows = cur.execute("""
        SELECT t.id, COALESCE(t.language, ''), COALESCE(d.title, ''),
               COALESCE(p.page_label, ''), COALESCE(t.text, '')
        FROM translations t
        JOIN pages p ON p.id = t.page_id
        JOIN documents d ON d.id = p.document_id
    """).fetchall()
    for row in tr_rows:
        cur.execute(
            "INSERT INTO translation_fts_bigram(rowid, language, title, page_label, text) VALUES (?,?,?,?,?)",
            (row[0], bigramize(row[1]), bigramize(row[2]), bigramize(row[3]), bigramize(row[4])),
        )
        n += 1
    print(f"  完成: {n}")

    conn.commit()

    print("\n=== 验证（bigram phrase 查询）===")
    test_queries = ["民盟", "张澜", "卢汉", "政协", "民主同盟", "张君劢", "戴笠", "蒋中正"]
    for q in test_queries:
        # 构造 phrase
        phrases = []
        for m in CJK_RE.finditer(q):
            seg = m.group(0)
            bgs = [seg[i : i + 2] for i in range(len(seg) - 1)]
            if bgs:
                phrases.append('"' + " ".join(bgs) + '"')
        if not phrases:
            continue
        fts_q = " AND ".join(phrases)
        n_bg = cur.execute(
            "SELECT COUNT(*) FROM page_fts_bigram WHERE page_fts_bigram MATCH ?", (fts_q,)
        ).fetchone()[0]
        n_zh = cur.execute(
            "SELECT COUNT(*) FROM translation_fts_bigram WHERE translation_fts_bigram MATCH ?",
            (fts_q,),
        ).fetchone()[0]
        print(f"  {q:<10}  page_fts_bigram: {n_bg:>4}  translation_fts_bigram: {n_zh:>4}")

    print("\n=== 英文回归（unicode61 原样分词）===")
    for q in ["Marshall", "Carsun Chang", "Democratic League"]:
        n = cur.execute(
            "SELECT COUNT(*) FROM page_fts_bigram WHERE page_fts_bigram MATCH ?", (q,)
        ).fetchone()[0]
        print(f"  {q:<22}  page_fts_bigram: {n}")

    conn.close()
    print("\n✅ bigram FTS 索引构建完成")


if __name__ == "__main__":
    sys.exit(build())
