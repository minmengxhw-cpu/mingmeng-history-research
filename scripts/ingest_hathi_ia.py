#!/usr/bin/env python3
"""HathiTrust / archive.org 一手公开档案入库（第一批：港媒 1946-1947 民盟报道）

策略：单期港媒整版 OCR 100-200KB（大量无关内容），仅抽取含「Democratic League」
及相邻段落入库为 1 page；保留 archive.org 原档详情 / PDF / 完整 OCR 链接供溯源。
"""
import sqlite3, json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / 'data' / 'research_index.sqlite'
HIA_DIR = ROOT / 'data' / 'hathitrust_ia'
MANIFEST = HIA_DIR / 'manifest.json'


def extract_meng_paragraphs(full_ocr: str) -> str:
    """抽取含 Democratic League / 民盟相关上下文段落"""
    paragraphs = re.split(r'\n\s*\n+', full_ocr)
    KW = re.compile(
        r'Democratic\s+League|Communist|Kuomintang|KMT|'
        r'Lo\s+Lung-?chi|Chang\s+Lan|Shen\s+Chun-?ju|'
        r'Carsun\s+Chang|third\s+party|coalition\s+government|'
        r'Political\s+Consultative',
        re.I,
    )
    hits = [p for p in paragraphs if KW.search(p) and len(p.strip()) > 30]
    if not hits:
        # 兜底：找 "Democratic League" 前后 2000 字
        m = re.search(r'Democratic\s+League', full_ocr, re.I)
        if m:
            start = max(0, m.start() - 1000)
            end = min(len(full_ocr), m.end() + 1500)
            return full_ocr[start:end]
        return full_ocr[:3000]
    # 合并相关段落
    return '\n\n'.join(hits[:15])  # 限制最多 15 段


def main():
    if not MANIFEST.exists():
        print(f'ERR: {MANIFEST} 不存在'); sys.exit(1)
    manifest = json.load(open(MANIFEST))
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # source
    src = cur.execute("SELECT id FROM sources WHERE source_type='hathi_ia' LIMIT 1").fetchone()
    if not src:
        cur.execute("""INSERT INTO sources (source_type, source_id, title, origin_url, local_path)
                       VALUES (?, ?, ?, ?, ?)""",
                    ('hathi_ia', 'archive.org', 'HathiTrust / Internet Archive 公开档案',
                     'https://archive.org', str(HIA_DIR)))
        source_id = cur.lastrowid
    else:
        source_id = src['id']

    inserted = 0
    for d in manifest:
        ident = d['identifier']
        doc_key = f'hathi-ia:{ident}'
        if cur.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone():
            print(f'  跳过已入库: {ident}')
            continue

        # 读全文 OCR + 抽民盟段落
        ocr_path = HIA_DIR / 'documents' / ident / f'{ident}_djvu.txt'
        full = ocr_path.read_text(encoding='utf-8', errors='replace')
        extracted = extract_meng_paragraphs(full)

        # 文档分级（含民盟命中数判断）
        n_hits = d.get('democratic_league_hits', 0)
        if n_hits >= 2:
            grade, score = '核心文献', 85
        elif n_hits >= 1:
            grade, score = '相关文献', 70
        else:
            grade, score = '相关文献', 55

        # 标题：date + 简短描述
        title = f"{d.get('title','')} · {d.get('description','')[len(d.get('title','')):][:60]}"

        cur.execute(
            """INSERT INTO documents (source_id, doc_key, volume_id, volume_title,
                                       doc_id, doc_number, title, date_guess, url,
                                       local_html, local_txt, hit_type, matched_terms, source_platform)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source_id, doc_key, 'HK-Press-1946-1947', 'Hong Kong Press archive.org mirror',
             ident, '', d.get('description', '')[:200],
             d.get('date', '')[:10], d.get('detail_url', ''),
             '', str(ocr_path.relative_to(ROOT)),
             'core' if n_hits >= 2 else 'related',
             'Democratic League; KMT; Communist',
             'hathi_ia'),
        )
        document_id = cur.lastrowid

        cur.execute("""INSERT INTO pages (document_id, page_label, page_url, text)
                        VALUES (?, ?, ?, ?)""",
                    (document_id, '1', d.get('detail_url', ''), extracted))
        page_id = cur.lastrowid

        try:
            cur.execute("""INSERT INTO page_fts (volume_id, doc_id, title, page_label, matched_terms, text)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                        ('HK-Press-1946-1947', ident, d.get('description', '')[:120],
                         '1', 'Democratic League; KMT; Communist', extracted))
        except sqlite3.OperationalError as e:
            print(f'  FTS skip: {e}')

        cur.execute("""INSERT OR REPLACE INTO document_classifications
                        (document_id, grade, score, reason, needs_review)
                        VALUES (?, ?, ?, ?, ?)""",
                    (document_id, grade, score,
                     f'1946-47 香港 China Mail 民盟相关报道（{n_hits} 处 Democratic League 命中）', 0))

        inserted += 1
        print(f'  ✓ [{d.get("date","")[:10]}] {ident} | extracted {len(extracted)} chars | grade={grade}')

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM documents WHERE source_platform='hathi_ia'")
    print(f'\n入库 {inserted} 篇，HathiTrust/IA 总数: {cur.fetchone()[0]}')
    conn.close()


if __name__ == '__main__':
    main()
