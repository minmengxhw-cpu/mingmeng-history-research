#!/usr/bin/env python3
"""Hoover · Carsun Chang Papers 翻译精修

按民盟史学术规范修订术语 + 加关键历史脚注。
"""
import sqlite3, re
from pathlib import Path

DB = Path(__file__).parent.parent / 'data' / 'research_index.sqlite'

# 关键术语硬修订（按民盟史学术惯例）
TERM_FIXES = [
    # State Council 1947-04 国民政府改组后的最高机构正式译名
    ('国务会议', '国民政府委员会'),
    # 信件 1 / 2 中提到"new constitution"标准化为《中华民国宪法》
    ('去年底通过之宪法', '去年底通过的《中华民国宪法》'),
    ('去年底通过的宪法', '去年底通过的《中华民国宪法》'),
    # 中苏条约 — 完整名称
    ('委员长依据中苏条约之立场', '委员长依据《中苏友好同盟条约》之立场'),
    # 民社党参政 12 点协议
    ('十二点文件', '《十二项协议》（民社党参政 12 条）'),
]

# 信末加入历史脚注
NOTE_MARSHALL = """

---
**译者注**

1. **民盟被宣布"非法"事件**：1947 年 10 月 27 日，国民政府内政部发布公告，宣布中国民主同盟为"非法团体"，勒令解散其总部及各地组织。这是 1946 年政协会议后国共谈判破裂、内战全面化背景下，国民政府对民主党派最严厉的镇压举措。张君劢此信写于事件发生后第 5 天。
2. **王世杰**（1891-1981）：时任国民政府外交部长，刚结束访美返沪，故张君劢以此切入开篇。
3. **魏德迈使华团**：1947 年 7 月，美国总统杜鲁门派魏德迈中将赴华做"实情调查"。张君劢曾于 7 月 26 日致函魏德迈陈述第三方面立场（详见本档案 CC-1947-07-26-wedemeyer）；本信续接其后。
4. **信件地点**：上海霞飞路 646 号（1947 年时实际中文路名为林森中路，1949 年后改名淮海中路）。

**原件信息**：Carsun Chang Papers, Hoover Institution Archives, Stanford University. 现场调档实物拍照入库。
"""

NOTE_WEDEMEYER = """

---
**译者注**

1. **政治协商会议**（1946-01-10 ~ 01-31，重庆）：由国共两党及民盟、青年党、民社党、社会贤达共 5 方代表 38 人召开。通过《政协五项决议》（政府组织案、和平建国纲领、军事问题案、国民大会案、宪法草案案）。但 1946 年 3 月国民党六届二中全会否定政协决议，会议成果实际破裂。
2. **1946 年 6 月 30 日协议**：指美国调停下国共在东北停战及整军方案的最后一份阶段性协议，因蒋介石坚持中共撤出苏北、承德、安东而终致破裂。
3. **《中苏友好同盟条约》**（1945-08-14）：国民政府与苏联签订，苏联承诺将东北主权归还中国政府，作为交换中国默认外蒙独立、苏联在旅顺、大连、中长铁路的特殊权益。本信讨论"满洲问题"即基于此条约框架。
4. **1937 年五五宪草**：实为 1936 年 5 月 5 日国民政府公布的《中华民国宪法草案》，规范不民主。1946 年 12 月 25 日制宪国大通过的《中华民国宪法》在此基础上大幅修订。
5. **国民政府委员会**（State Council）：1947 年 4 月 23 日国民政府改组后设立的最高决策机构，含国民党 17 席、青年党 4 席、民社党 4 席、社会贤达 4 席，民盟拒绝参加。
6. **民盟提出满洲联合政府方案**（1946-03/04）：本信中"中国民主同盟介入调处"一段，是民盟史上重要外交主张的一手记录。
7. **俞飞鹏**（1884-1966）：浙江奉化人，蒋介石同乡，时任粮食部长。**王邵镛**：时任监察院副院长。张君劢以此二人为例批评国民党"以旧人塞新位"。
8. **三区治理方案**：张君劢向蒋介石提出的内战时期国土分区治理设想，是民国第三方面少有的系统化战略建言。
9. **第三条道路**（中国成为苏美缓冲，不亲苏不亲美）：本信末段是张君劢"中国第三条道路"思想最完整的英文一手陈述，与其后续在美时期的著作（如 *The Third Force in China*, 1952）形成思想连贯链。

**原件信息**：Carsun Chang Papers, Hoover Institution Archives, Stanford University. 现场调档实物拍照入库。
"""


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT t.id AS tid, t.text AS zh, d.doc_id, d.date_guess
        FROM translations t
        JOIN pages p ON p.id=t.page_id
        JOIN documents d ON d.id=p.document_id
        WHERE d.source_platform='hoover' AND t.language='zh-CN'
        ORDER BY d.date_guess
    """).fetchall()

    for r in rows:
        zh = r['zh']
        orig_len = len(zh)
        # 术语精修
        for bad, good in TERM_FIXES:
            zh = zh.replace(bad, good)
        # 脚注
        if r['doc_id'] == 'CC-1947-11-01-marshall':
            zh = zh.rstrip() + NOTE_MARSHALL
        elif r['doc_id'] == 'CC-1947-07-26-wedemeyer':
            zh = zh.rstrip() + NOTE_WEDEMEYER

        cur.execute("""UPDATE translations SET text=?, translator=?
                       WHERE id=?""",
                    (zh, '小班-hoover-refined-2026-05-18', r['tid']))
        # FTS 同步
        try:
            cur.execute("DELETE FROM translation_fts WHERE rowid=?", (r['tid'],))
            cur.execute("""INSERT INTO translation_fts (rowid, language, title, page_label, text)
                           VALUES (?, 'zh-CN', ?, '1', ?)""",
                        (r['tid'], r['doc_id'], zh))
        except sqlite3.OperationalError:
            pass

        print(f'  ✓ [{r["date_guess"]}] {r["doc_id"]} | {orig_len} → {len(zh)} chars')

    conn.commit()
    conn.close()
    print('\n精修完成')


if __name__ == '__main__':
    main()
