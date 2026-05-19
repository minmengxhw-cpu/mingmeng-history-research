#!/usr/bin/env python3
"""HathiTrust/IA 港媒翻译敏感词扫描

针对 1950 年（建国初期）港媒报道可能涉及三反/五反、政治运动、含混表述，
扫描译文，命中敏感词的标记 grade='前台不展示'（内部仍可检索）。
"""
import sqlite3, re
from pathlib import Path

DB = Path(__file__).parent.parent / 'data' / 'research_index.sqlite'

# 严格禁词（出现即下架前台）
HARD_BAN = [
    '反右', '党天下', '文革', '批斗', '含冤', '抑郁去世',
    '出卖情报', '海瑞罢官', '姚文元', '被迫害致死',
    '章罗联盟', '大右派', '三反', '五反',
]
# 软警示（出现需人工复核，先标记审核）
SOFT_FLAG = [
    '镇压反革命', '土地改革', '思想改造', '运动', '清算',
    '叛徒', '反革命', '阶级斗争',
]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 拿 1950 年所有港媒 + 翻译
    rows = cur.execute("""
        SELECT d.id AS did, d.doc_id, d.date_guess, d.title,
               t.text AS zh, dc.grade
        FROM documents d
        JOIN pages p ON p.document_id=d.id
        LEFT JOIN translations t ON t.page_id=p.id AND t.language='zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id=d.id
        WHERE d.source_platform='hathitrust'
          AND d.date_guess >= '1949-10'
        ORDER BY d.date_guess
    """).fetchall()
    print(f'扫描范围: 1949-10 起 {len(rows)} 篇（建国后）')

    # 策略：1949-10 起的港媒，按用户铁律「建国后不展示前台」一律下架
    # 同时扫硬禁/软警示词作为内部审计记录
    hard_hits, soft_hits = [], []
    for r in rows:
        zh = r['zh'] or ''
        h = [w for w in HARD_BAN if w in zh]
        s = [w for w in SOFT_FLAG if w in zh]
        if h:
            hard_hits.append((r, h))
        elif s:
            soft_hits.append((r, s))

    # 统一把 1949-10 起的 hathitrust 下架前台
    print(f'\n建国后默认下架前台: {len(rows)} 篇（含敏感词命中）')
    for r in rows:
        zh = r['zh'] or ''
        h = [w for w in HARD_BAN if w in zh]
        reason_suffix = (' | 敏感词: ' + ', '.join(h)) if h else ' | 建国后默认下架'
        cur.execute("""UPDATE document_classifications
                       SET grade='前台不展示',
                           reason=COALESCE(reason,'') || ?
                       WHERE document_id=?""",
                    (reason_suffix, r['did']))

    print(f'\n硬禁词命中: {len(hard_hits)} 篇')
    for r, words in hard_hits:
        print(f'  [{r["date_guess"]}] {r["doc_id"]} | 命中: {", ".join(words)}')

    print(f'\n软警示词命中: {len(soft_hits)} 篇')
    for r, words in soft_hits:
        print(f'  [{r["date_guess"]}] {r["doc_id"]} | 命中: {", ".join(words)}')

    conn.commit()
    # 复核统计
    cur.execute("""SELECT dc.grade, COUNT(*) FROM documents d
                   LEFT JOIN document_classifications dc ON dc.document_id=d.id
                   WHERE d.source_platform='hathitrust' GROUP BY dc.grade""")
    print('\nHathiTrust grade 分布:')
    for r in cur.fetchall():
        print(f'  {r[0]}: {r[1]}')
    conn.close()


if __name__ == '__main__':
    main()
