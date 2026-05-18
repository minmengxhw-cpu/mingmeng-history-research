#!/usr/bin/env python3
"""Hoover Institution · Carsun Chang Papers 入库

数据性质：研究者赴斯坦福胡佛档案馆现场调档，对原件实物拍照、英文文本逐字校对后入库。
区别于公网批量抓取，这是真正的「现场调档 + 实物一手」资料。

首批入库：
  - CC-1947-07-26-wedemeyer  张君劢致魏德迈（6 页）
  - CC-1947-11-01-marshall   张君劢致马歇尔（2 页）

两封信均属民盟史**核心文献**（1947 民盟「非法」事件前后第三方面对美政策一手陈述）。
"""
import sqlite3, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / 'data' / 'research_index.sqlite'
HV_DIR = ROOT / 'data' / 'hoover'
MANIFEST = HV_DIR / 'manifest.json'


def main():
    if not MANIFEST.exists():
        print(f'ERR: {MANIFEST} 不存在'); sys.exit(1)
    manifest = json.load(open(MANIFEST))
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # source
    src = cur.execute("SELECT id FROM sources WHERE source_type='hoover' LIMIT 1").fetchone()
    if not src:
        cur.execute("""INSERT INTO sources (source_type, source_id, title, origin_url, local_path)
                       VALUES (?, ?, ?, ?, ?)""",
                    ('hoover', 'carsun-chang-papers',
                     'Hoover Institution · Carsun Chang Papers (现场调档)',
                     'https://oac.cdlib.org/findaid/ark:/13030/kt8h4nf468/',
                     str(HV_DIR)))
        source_id = cur.lastrowid
    else:
        source_id = src['id']

    inserted = 0
    for d in manifest:
        ident = d['identifier']
        doc_key = f'hoover:{ident}'
        if cur.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone():
            print(f'  跳过已入库: {ident}')
            continue

        # 读全文（已校对的英文文本）
        txt_path = HV_DIR / 'documents' / ident / 'text.txt'
        full = txt_path.read_text(encoding='utf-8')

        # 文档分级：两封信都是核心文献
        n_hits = d.get('democratic_league_hits', 0)
        grade, score = '核心文献', 95
        reason = f'{d["author"]} 致 {d["recipient"]} 私人信件（{d["date"]}） · Hoover 现场调档实物 · 民盟史 1947「非法」事件前后第三方面对美政策一手陈述 · Democratic League 直接出现 {n_hits} 次'

        title = d['title']

        cur.execute(
            """INSERT INTO documents (source_id, doc_key, volume_id, volume_title,
                                       doc_id, doc_number, title, date_guess, url,
                                       local_html, local_txt, hit_type, matched_terms, source_platform)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source_id, doc_key,
             'hoover-carsun-chang-papers',
             'Hoover Institution · Carsun Chang Papers (1946-1962)',
             ident, '', title,
             d['date'], d.get('detail_url', ''),
             '', str(txt_path.relative_to(ROOT)),
             'core',
             'Democratic League; Carsun Chang; Marshall; Wedemeyer; coalition government; Kuomintang; civil war; Manchuria',
             'hoover'),
        )
        document_id = cur.lastrowid

        cur.execute("""INSERT INTO pages (document_id, page_label, page_url, text)
                        VALUES (?, ?, ?, ?)""",
                    (document_id, '1', d.get('detail_url', ''), full))
        page_id = cur.lastrowid

        try:
            cur.execute("""INSERT INTO page_fts (volume_id, doc_id, title, page_label, matched_terms, text)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                        ('hoover-carsun-chang-papers', ident, title,
                         '1', 'Democratic League; Carsun Chang; Marshall; Wedemeyer; coalition government', full))
        except sqlite3.OperationalError as e:
            print(f'  FTS skip: {e}')

        cur.execute("""INSERT OR REPLACE INTO document_classifications
                        (document_id, grade, score, reason, needs_review)
                        VALUES (?, ?, ?, ?, ?)""",
                    (document_id, grade, score, reason, 0))

        inserted += 1
        print(f'  ✓ [{d["date"]}] {ident} | {len(full)} chars | grade={grade}/{score}')

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM documents WHERE source_platform='hoover'")
    print(f'\n入库 {inserted} 篇，Hoover 总数: {cur.fetchone()[0]}')
    conn.close()


if __name__ == '__main__':
    main()
