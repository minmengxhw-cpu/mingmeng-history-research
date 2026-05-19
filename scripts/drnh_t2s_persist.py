#!/usr/bin/env python3
"""把数据库里所有 drnh 平台的中文从繁体永久转为简体

用户要求：「台北国史馆这部分，繁体字都变成简体字 + 都是中文字就不需要翻译」
做法：
- documents.title (drnh) 繁 → 简
- pages.text (drnh) 繁 → 简
- translations.text 保持简体（与 page.text 重复，但保留兼容性）
- 重建 FTS5 索引（trigram tokenizer 已经在用）
"""
import sqlite3
import zhconv
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "research_index.sqlite"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. 把 documents.title 转简体（仅 drnh）
print("=== documents.title 繁→简 ===")
rows = cur.execute(
    "SELECT id, title FROM documents WHERE source_platform='drnh'"
).fetchall()
n_t = 0
for doc_id, title in rows:
    simp = zhconv.convert(title or "", "zh-cn")
    if simp != title:
        cur.execute("UPDATE documents SET title=? WHERE id=?", (simp, doc_id))
        n_t += 1
print(f"  更新 {n_t} 条")

# 2. 把 pages.text 转简体（仅 drnh 的 pages）
print("\n=== pages.text 繁→简（drnh）===")
rows = cur.execute("""
    SELECT p.id, p.text FROM pages p
    JOIN documents d ON d.id = p.document_id
    WHERE d.source_platform='drnh'
""").fetchall()
n_p = 0
for page_id, text in rows:
    simp = zhconv.convert(text or "", "zh-cn")
    if simp != text:
        cur.execute("UPDATE pages SET text=? WHERE id=?", (simp, page_id))
        n_p += 1
print(f"  更新 {n_p} 条")

# 3. translations.text 已经是简体，再保险跑一遍
print("\n=== translations.text 繁→简（drnh，保险）===")
rows = cur.execute("""
    SELECT t.id, t.text FROM translations t
    JOIN pages p ON p.id = t.page_id
    JOIN documents d ON d.id = p.document_id
    WHERE d.source_platform='drnh' AND t.language='zh-CN'
""").fetchall()
n_tr = 0
for t_id, text in rows:
    simp = zhconv.convert(text or "", "zh-cn")
    if simp != text:
        cur.execute("UPDATE translations SET text=? WHERE id=?", (simp, t_id))
        n_tr += 1
print(f"  更新 {n_tr} 条")

conn.commit()

# 4. 重建 page_fts + translation_fts（trigram tokenizer，drnh 部分内容改了）
print("\n=== 重建 FTS5 索引 ===")
cur.execute("DROP TABLE IF EXISTS page_fts")
cur.execute("DROP TABLE IF EXISTS translation_fts")
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
cur.execute("""
    INSERT INTO page_fts(rowid, volume_id, doc_id, title, page_label, matched_terms, text)
    SELECT p.id,
           COALESCE(d.volume_id, ''), COALESCE(d.doc_id, ''),
           COALESCE(d.title, ''), COALESCE(p.page_label, ''),
           COALESCE(d.matched_terms, ''), COALESCE(p.text, '')
    FROM pages p JOIN documents d ON d.id = p.document_id
""")
n_p_fts = cur.rowcount
cur.execute("""
    INSERT INTO translation_fts(rowid, language, title, page_label, text)
    SELECT t.id, COALESCE(t.language, ''), COALESCE(d.title, ''),
           COALESCE(p.page_label, ''), COALESCE(t.text, '')
    FROM translations t
    JOIN pages p ON p.id = t.page_id
    JOIN documents d ON d.id = p.document_id
""")
n_t_fts = cur.rowcount
conn.commit()
print(f"  page_fts: {n_p_fts}")
print(f"  translation_fts: {n_t_fts}")

# 验证
print("\n=== 验证：drnh 现在搜简体能命中 ===")
for q in ["民主同盟", "戴笠", "张澜", "蒋中正", "国民政府"]:
    n = cur.execute("""
        SELECT COUNT(*) FROM page_fts
        JOIN pages p ON p.id=page_fts.rowid
        JOIN documents d ON d.id=p.document_id
        WHERE page_fts MATCH ? AND d.source_platform='drnh'
    """, (q,)).fetchone()[0]
    print(f"  {q:<10}: {n}")

print("\n=== 抽样看 3 条 drnh title 是否已是简体 ===")
for r in cur.execute(
    "SELECT title FROM documents WHERE source_platform='drnh' LIMIT 3"
):
    print(f"  {r[0][:100]}")

conn.close()
print("\n✅ drnh 全文繁→简完成")
