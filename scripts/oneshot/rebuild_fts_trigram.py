#!/usr/bin/env python3
"""把 page_fts / translation_fts 改用 trigram tokenizer 重建

原默认 unicode61 tokenizer 不切分中文，导致「戴笠」「魏德邁」等短词搜不到。
trigram tokenizer 按 3 字符滑窗切，中文友好。
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent.parent / "data" / "research_index.sqlite"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=== 重建前 ===")
print(f"  page_fts: {cur.execute('SELECT COUNT(*) FROM page_fts').fetchone()[0]}")
print(f"  translation_fts: {cur.execute('SELECT COUNT(*) FROM translation_fts').fetchone()[0]}")

# 删旧表
print("\n删除旧 FTS 表...")
cur.execute("DROP TABLE IF EXISTS page_fts")
cur.execute("DROP TABLE IF EXISTS translation_fts")

# 用 trigram tokenizer 重建
print("用 trigram tokenizer 重建...")
cur.execute("""
    CREATE VIRTUAL TABLE page_fts USING fts5(
        volume_id, doc_id, title, page_label, matched_terms, text,
        tokenize='trigram'
    )
""")
cur.execute("""
    CREATE VIRTUAL TABLE translation_fts USING fts5(
        language, title, page_label, text,
        tokenize='trigram'
    )
""")

# 重新填充
print("\n填充 page_fts...")
cur.execute("""
    INSERT INTO page_fts(rowid, volume_id, doc_id, title, page_label, matched_terms, text)
    SELECT p.id,
           COALESCE(d.volume_id, ''), COALESCE(d.doc_id, ''),
           COALESCE(d.title, ''), COALESCE(p.page_label, ''),
           COALESCE(d.matched_terms, ''), COALESCE(p.text, '')
    FROM pages p JOIN documents d ON d.id = p.document_id
""")
print(f"  完成: {cur.rowcount}")

print("\n填充 translation_fts...")
cur.execute("""
    INSERT INTO translation_fts(rowid, language, title, page_label, text)
    SELECT t.id, COALESCE(t.language, ''), COALESCE(d.title, ''),
           COALESCE(p.page_label, ''), COALESCE(t.text, '')
    FROM translations t
    JOIN pages p ON p.id = t.page_id
    JOIN documents d ON d.id = p.document_id
""")
print(f"  完成: {cur.rowcount}")

conn.commit()

# 验证：drnh + 各种关键词
print("\n=== 验证（trigram tokenizer 后）===")
test_queries = ["民主同盟", "民盟", "张澜", "張瀾", "魏德邁", "魏德迈", "戴笠", "保密局", "蒋中正", "蔣中正", "作战会报", "作戰會報"]
for q in test_queries:
    n_fts = cur.execute("""
        SELECT COUNT(*) FROM page_fts
        JOIN pages p ON p.id=page_fts.rowid
        JOIN documents d ON d.id=p.document_id
        WHERE page_fts MATCH ? AND d.source_platform='drnh'
    """, (q,)).fetchone()[0]
    n_zh = cur.execute("""
        SELECT COUNT(*) FROM translation_fts
        JOIN translations t ON t.id=translation_fts.rowid
        JOIN pages p ON p.id=t.page_id
        JOIN documents d ON d.id=p.document_id
        WHERE translation_fts MATCH ? AND d.source_platform='drnh'
    """, (q,)).fetchone()[0]
    print(f"  {q:<10}  page_fts(原文): {n_fts:>4}  translation_fts(简体): {n_zh:>4}")

# 其他平台也验证
print("\n=== 各平台「Marshall」（FRUS）+「Carsun Chang」 ===")
for q in ["Marshall", "Carsun Chang", "Democratic League"]:
    for plat in ["frus", "drnh", "cia", "wilson", "hoover", "hathitrust"]:
        n = cur.execute("""
            SELECT COUNT(*) FROM page_fts
            JOIN pages p ON p.id=page_fts.rowid
            JOIN documents d ON d.id=p.document_id
            WHERE page_fts MATCH ? AND d.source_platform=?
        """, (q, plat)).fetchone()[0]
        if n > 0:
            print(f"  {q:<22}  [{plat}]: {n}")

conn.close()
print("\n✅ trigram FTS 重建完成")
