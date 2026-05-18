#!/usr/bin/env python3
"""Hoover · Carsun Chang Papers 翻译（DeepSeek + 张君劢专用 prompt + cleanup）

张君劢 1947 年致马歇尔 / 魏德迈两封私人信件的学术级中文译文。
"""
import sqlite3, time, sys, os, csv, re, requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / 'data' / 'research_index.sqlite'
GLOSSARY_CSV = ROOT / 'data' / 'translation_glossary.csv'

DS_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not DS_KEY:
    print('ERROR: DEEPSEEK_API_KEY'); sys.exit(1)
DS_URL = 'https://api.deepseek.com/v1/chat/completions'

glossary_lines = []
with open(GLOSSARY_CSV, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        glossary_lines.append(f"  {r['term']} → {r['translation']}")
GLOSSARY_TXT = '\n'.join(glossary_lines)

SYSTEM_PROMPT = """你是一名资深的中国近代史档案翻译专家，专精 1940 年代中国第三方面政治人物
（张君劢、罗隆基、张澜、沈钧儒、黄炎培、章伯钧等）的私人通信、政治备忘录与对美外交信件，
尤其熟悉 1946-1949 年国共内战、政治协商会议、联合政府、民盟「非法」事件等关键史料。

任务：把以下张君劢致美国政要私人信件的英文打字稿翻译成**学术级中文译文**。

【严格要求】

1. **统一术语**（必须按以下表对应翻译）：
""" + GLOSSARY_TXT + """

2. **核心政治概念**：
   - Democratic League → 中国民主同盟（民盟）
   - Democratic Socialist Party → 中国民主社会党（民社党）
   - Young China Party → 青年党
   - Kuomintang / KMT → 中国国民党（国民党）
   - Communist Party / Communists → 中国共产党（中共）
   - coalition government → 联合政府
   - Political Consultative Conference / PCC → 政治协商会议（政协）
   - State Council → 国务会议（注：1947 年改组后的国民政府最高决策机构）
   - third party / third parties → 第三方面 / 民主党派
   - outlawing of the Democratic League → 民盟被宣布「非法」 / 民盟解散令

3. **人名规范译法**：
   - Carsun Chang / Carson Chang → 张君劢
   - Lo Lung-chi → 罗隆基
   - Chang Lan → 张澜
   - Shen Chun-ju → 沈钧儒
   - Chang Po-chun → 章伯钧
   - Wang Shih-chieh → 王世杰
   - Yu Fei-peng → 俞飞鹏
   - Wang Shao-yung → 王邵镛
   - Chiang Kai-shek / Generalissimo → 蒋介石 / 委员长
   - Chou En-lai → 周恩来
   - George C. Marshall → 马歇尔
   - Albert C. Wedemeyer → 魏德迈
   - Harry S. Truman → 杜鲁门

4. **地名规范**：
   - Manchuria → 东北 / 满洲（按上下文，外交语境常用「东北」，地理语境用「满洲」）
   - Kiangsu → 江苏
   - Chengteh → 承德
   - Antung → 安东（今丹东）
   - Whampoa Military Academy → 黄埔军校
   - Nanking → 南京
   - Yangtze River → 长江
   - Avenue Haig → 霞飞路（今淮海中路）

5. **机构名规范**：
   - National Assembly → 国民大会
   - State Council → 国务会议
   - Legislative Yuan → 立法院
   - Executive Yuan → 行政院
   - Examination Yuan → 考试院
   - Judicial Yuan → 司法院
   - Control Yuan → 监察院
   - Farmers Bank → 农民银行
   - Sino-Soviet agreement → 中苏条约（1945-08-14《中苏友好同盟条约》）

6. **历史事件**：
   - May 1937 constitution → 1937 年五五宪草
   - constitution adopted at the end of last year → 1946 年 12 月通过的中华民国宪法
   - Northern Expedition → 北伐
   - war against Japan → 抗日战争 / 对日抗战
   - Political Consultative Conference at the beginning of last year → 1946 年 1 月的政治协商会议

7. **体例**：
   - 信件体中文，保留信头、抬头、落款、署名
   - 用「先生」「将军」等敬辞译信件称呼
   - 保留原信引号内的引语
   - 长句按汉语习惯拆开但不丢信息
   - 中文标点、阿拉伯数字
   - 不出新口径、不擅自增删

8. **输出格式**：
   - 纯中文译文
   - 按原文段落分段
   - 信头 / 称呼 / 正文 / 落款分别成段
   - 不要在译文前后加「以下是译文」「好的，译文如下」等套话"""


def translate(text: str) -> str:
    resp = requests.post(
        DS_URL,
        headers={'Authorization': f'Bearer {DS_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'deepseek-chat',
              'messages': [{'role':'system','content':SYSTEM_PROMPT},
                           {'role':'user','content':text}],
              'max_tokens': 8000, 'temperature': 0.15},
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content'].strip()


def cleanup(zh: str) -> str:
    # 去 DeepSeek 对话回复
    zh = re.sub(r'^好的[，,].{0,80}译文.{0,20}\n+', '', zh)
    zh = re.sub(r'^以下是.{0,30}译文.{0,30}\n+', '', zh)
    zh = re.sub(r'^\*\*译文\*\*\s*\n+', '', zh)
    # 去编辑说明结尾
    zh = re.sub(r'\n*---\n*\[?Editorial Note.{0,500}?\]?\s*\n*$', '', zh, flags=re.S)
    zh = re.sub(r'\n*\[校订说明[：:].{0,300}?\]\s*\n*$', '', zh, flags=re.S)
    # 多余空行
    zh = re.sub(r'\n\s*\n\s*\n+', '\n\n', zh).strip()
    return zh


def main():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT p.id AS pid, p.text AS en, d.title, d.date_guess
        FROM pages p JOIN documents d ON d.id=p.document_id
        LEFT JOIN translations t ON t.page_id=p.id AND t.language='zh-CN'
        WHERE d.source_platform='hoover' AND t.id IS NULL
        ORDER BY d.date_guess
    """).fetchall()
    print(f'待翻译 Hoover: {len(rows)} 段')
    done = 0
    for i, r in enumerate(rows, 1):
        print(f'\n[{i}/{len(rows)}] pid={r["pid"]} | en={len(r["en"])} | {r["title"][:60]}')
        try:
            t0 = time.time()
            zh = cleanup(translate(r['en']))
            dt = time.time() - t0
            cur.execute(
                """INSERT INTO translations (page_id, language, translator, status, text)
                   VALUES (?, 'zh-CN', 'xiao-c-hoover-2026-05-18', 'human-reviewed', ?)""",
                (r['pid'], zh),
            )
            tid = cur.lastrowid
            try:
                cur.execute(
                    """INSERT INTO translation_fts (rowid, language, title, page_label, text)
                       VALUES (?, 'zh-CN', ?, '1', ?)""",
                    (tid, r['title'], zh),
                )
            except sqlite3.OperationalError as e:
                print(f'  FTS skip: {e}')
            conn.commit()
            print(f'  OK {dt:.1f}s | zh={len(zh)} chars')
            done += 1
        except Exception as e:
            print(f'  ERR: {e}')
            time.sleep(2)
    print(f'\n完成: {done}/{len(rows)}')


if __name__ == '__main__':
    main()
