#!/usr/bin/env python3
"""把 CIA 非核心 41 篇按敏感分级入库

分级：
- P 政治运动主题（1 篇）: 不入库
- S 标题敏感（1 篇）: 入库 + 翻译，grade='前台不展示'，前台过滤
- R + W + L 相关 / 弱相关 / 较新参考（39 篇）: 入库 + 翻译，grade='相关文献'
"""
import sqlite3, json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "research_index.sqlite"
CIA_DIR = ROOT / "data" / "cia_meng"
MANIFEST = CIA_DIR / "manifest.json"
CORE_IDENTS_FILE = Path("/tmp/cia_core_idents.json")

# 敏感分级关键词
POLITICAL_CAMPAIGN_KW = [
    'THREE-ANTI', 'THREE ANTI',
    'FIVE-ANTI', 'FIVE ANTI',
    'ANTI-RIGHTIST', 'ANTI RIGHTIST',
    'CULTURAL REVOLUTION',
]
SOFT_SENSITIVE_KW = ['ARRESTS, EXECUTIONS', 'ARRESTS AND EXECUTIONS']


# 复用 ingest_cia_meng.py 的 clean_ocr_text / clean_title
sys.path.insert(0, str(ROOT / 'scripts'))
from ingest_cia_meng import clean_ocr_text, clean_title


def grade_for(title: str):
    t = title.upper()
    for kw in POLITICAL_CAMPAIGN_KW:
        if kw in t:
            return None    # 不入库
    for kw in SOFT_SENSITIVE_KW:
        if kw in t:
            return ('前台不展示', 30, '建国后历史事件标题敏感，入库供内部检索，前台不展开原文/译文')
    return ('相关文献', 60, 'CIA 民盟关键词命中但主题相关性次于核心档案')


def main():
    core_idents = set(json.load(open(CORE_IDENTS_FILE)))
    manifest = json.load(open(MANIFEST))
    non_core = [m for m in manifest if m['identifier'] not in core_idents]
    print(f"非核心档案: {len(non_core)} 篇")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # source（与核心共享）
    src = cur.execute(
        "SELECT id FROM sources WHERE source_type='cia' AND source_id='ciareadingroom' LIMIT 1"
    ).fetchone()
    if not src:
        print("ERR: 找不到 CIA source，请先跑 ingest_cia_meng.py")
        sys.exit(1)
    source_id = src['id']

    stats = {'inserted': 0, 'skipped_existing': 0, 'skipped_political': 0, 'hidden': 0}
    for d in non_core:
        ident = d['identifier']
        doc_key = f"cia-meng:{ident}"
        if cur.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone():
            stats['skipped_existing'] += 1
            continue

        title = clean_title(d.get('title', ''))
        date_guess = d.get('date', '')[:10]
        detail_url = d.get('detail_url') or f"https://archive.org/details/{ident}"
        grade_info = grade_for(title)
        if grade_info is None:
            print(f"  ⊗ [{date_guess}] {title[:60]} → 不入库（建国后政治运动主题）")
            stats['skipped_political'] += 1
            continue
        grade, score, reason = grade_info
        if grade == '前台不展示':
            stats['hidden'] += 1

        doc_dir = CIA_DIR / 'documents' / ident
        txt_files = list(doc_dir.glob('*_djvu.txt'))
        if not txt_files:
            print(f"  ⚠ 找不到 OCR: {ident}")
            continue
        raw = txt_files[0].read_text(encoding='utf-8', errors='replace')
        cleaned = clean_ocr_text(raw)

        cur.execute(
            """INSERT INTO documents (source_id, doc_key, volume_id, volume_title, doc_id,
                                       doc_number, title, date_guess, url, local_html, local_txt,
                                       hit_type, matched_terms, source_platform)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                doc_key,
                "CIA-CREST",
                "CIA Records Reading Room",
                ident,
                "",
                title,
                date_guess,
                detail_url,
                "",
                str(txt_files[0].relative_to(ROOT)),
                "related" if grade == '相关文献' else 'hidden',
                d.get('matched_term', ''),
                "cia",
            ),
        )
        document_id = cur.lastrowid

        cur.execute(
            """INSERT INTO pages (document_id, page_label, page_url, text)
               VALUES (?, ?, ?, ?)""",
            (document_id, "1", detail_url, cleaned),
        )
        page_id = cur.lastrowid

        # FTS: hidden 的也入 FTS（内部检索能查到），前台展示由 grade 控制
        try:
            cur.execute(
                """INSERT INTO page_fts (volume_id, doc_id, title, page_label, matched_terms, text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("CIA-CREST", ident, title, "1", d.get('matched_term', ''), cleaned),
            )
        except sqlite3.OperationalError as e:
            print(f"  FTS skip: {e}")

        cur.execute(
            """INSERT OR REPLACE INTO document_classifications
               (document_id, grade, score, reason, needs_review)
               VALUES (?, ?, ?, ?, ?)""",
            (document_id, grade, score, reason, 0),
        )

        stats['inserted'] += 1
        marker = '🔒' if grade == '前台不展示' else '✓'
        print(f"  {marker} [{date_guess}] {title[:55]}  page={page_id} grade={grade}")

    conn.commit()
    print()
    print("=== 入库完成 ===")
    print(f"  新入库:           {stats['inserted']}")
    print(f"  跳过(已存在):     {stats['skipped_existing']}")
    print(f"  不入库(政治运动): {stats['skipped_political']}")
    print(f"  入库但前台隐藏:   {stats['hidden']}")

    cur.execute("SELECT COUNT(*) FROM documents WHERE source_platform='cia'")
    print(f"  CIA documents 总数: {cur.fetchone()[0]}")
    cur.execute("""
      SELECT COALESCE(dc.grade, '未分级') AS grade, COUNT(*) AS n
      FROM documents d
      LEFT JOIN document_classifications dc ON dc.document_id=d.id
      WHERE d.source_platform='cia'
      GROUP BY grade
    """)
    for r in cur.fetchall():
        print(f"    {r['grade']}: {r['n']}")
    conn.close()


if __name__ == '__main__':
    main()
