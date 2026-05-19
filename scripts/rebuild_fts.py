#!/usr/bin/env python3
"""重建 page_fts + translation_fts 全文索引

ingest_drnh.py 漏了同步 FTS5 索引，导致 drnh 的 364 条原文 + 简体翻译都搜不到。
本脚本：DELETE FROM ... + INSERT FROM source tables，全量重建。
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "research_index.sqlite"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 看初始状态
print("=== 重建前 ===")
print(f"  pages 表: {cur.execute('SELECT COUNT(*) FROM pages').fetchone()[0]}")
print(f"  translations 表: {cur.execute('SELECT COUNT(*) FROM translations').fetchone()[0]}")
print(f"  page_fts: {cur.execute('SELECT COUNT(*) FROM page_fts').fetchone()[0]}")
print(f"  translation_fts: {cur.execute('SELECT COUNT(*) FROM translation_fts').fetchone()[0]}")

# 重建 page_fts
print("\n重建 page_fts...")
cur.execute("DELETE FROM page_fts")
cur.execute("""
    INSERT INTO page_fts(rowid, volume_id, doc_id, title, page_label, matched_terms, text)
    SELECT p.id,
           COALESCE(d.volume_id, ''),
           COALESCE(d.doc_id, ''),
           COALESCE(d.title, ''),
           COALESCE(p.page_label, ''),
           COALESCE(d.matched_terms, ''),
           COALESCE(p.text, '')
    FROM pages p
    JOIN documents d ON d.id = p.document_id
""")
print(f"  完成: {cur.rowcount}")

# 重建 translation_fts
print("\n重建 translation_fts...")
cur.execute("DELETE FROM translation_fts")
cur.execute("""
    INSERT INTO translation_fts(rowid, language, title, page_label, text)
    SELECT t.id,
           COALESCE(t.language, ''),
           COALESCE(d.title, ''),
           COALESCE(p.page_label, ''),
           COALESCE(t.text, '')
    FROM translations t
    JOIN pages p ON p.id = t.page_id
    JOIN documents d ON d.id = p.document_id
""")
print(f"  完成: {cur.rowcount}")

conn.commit()

# 验证：drnh 搜「民主同盟」「张澜」「魏德邁」
print("\n=== 验证 ===")
for q in ["民主同盟", "张澜", "張瀾", "魏德邁", "魏德迈", "戴笠"]:
    try:
        n_fts = cur.execute("""
            SELECT COUNT(*) FROM page_fts
            JOIN pages p ON p.id=page_fts.rowid
            JOIN documents d ON d.id=p.document_id
            WHERE page_fts MATCH ? AND d.source_platform='drnh'
        """, (q,)).fetchone()[0]
    except sqlite3.OperationalError as e:
        n_fts = f"ERR({e})"
    try:
        n_zh = cur.execute("""
            SELECT COUNT(*) FROM translation_fts
            JOIN translations t ON t.id=translation_fts.rowid
            JOIN pages p ON p.id=t.page_id
            JOIN documents d ON d.id=p.document_id
            WHERE translation_fts MATCH ? AND d.source_platform='drnh'
        """, (q,)).fetchone()[0]
    except sqlite3.OperationalError as e:
        n_zh = f"ERR({e})"
    print(f"  {q}  → page_fts: {n_fts:>6}  translation_fts: {n_zh:>6}")

conn.close()
print("\n✅ FTS 索引重建完成")
