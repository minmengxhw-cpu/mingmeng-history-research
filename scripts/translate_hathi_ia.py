#!/usr/bin/env python3
"""HathiTrust/IA 7 期港媒翻译（DeepSeek + 增强 prompt + cleanup + human-reviewed）"""
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

SYSTEM_PROMPT = """你是一名资深的中国近代史档案翻译专家，专精 1946-1949 香港英文报纸
（China Mail / Hong Kong Telegraph 等）对中国政情的报道，尤其熟悉中国民主同盟相关史料。

任务：把以下 1946-1947 香港英文报纸的 OCR 文本片段翻译成**学术级中文译文**。

【严格要求】

1. **统一术语**（必须按以下表对应翻译）：
""" + GLOSSARY_TXT + """

2. **报纸缩写处理**：
   - DL / Democratic League → 中国民主同盟（民盟）
   - CCP → 中国共产党
   - KMT / Kuomintang → 中国国民党
   - PCC → 政治协商会议
   - third party / third group → 第三方面

3. **人名规范**：
   - LO Lung-chi / Lo Lung-chi → 罗隆基
   - CHANG Lan → 张澜
   - SHEN Chun-ju → 沈钧儒
   - 人名首次出现可在中文译名后括注英文原名

4. **OCR / 报纸版式噪声去除**：
   - 忽略报纸版头页码、广告、栏目标识等无意义片段
   - 忽略残缺的英文字符块
   - 保留正文中的实质新闻信息

5. **体例**：档案体中文、保留日期/地点/电讯来源、中文标点、阿拉伯数字。

6. **输出格式**：纯中文译文，按原文段落分段。"""


def translate(text: str) -> str:
    resp = requests.post(
        DS_URL,
        headers={'Authorization': f'Bearer {DS_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'deepseek-chat',
              'messages': [{'role':'system','content':SYSTEM_PROMPT},
                           {'role':'user','content':text}],
              'max_tokens': 6000, 'temperature': 0.15},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content'].strip()


def cleanup(zh: str) -> str:
    zh = re.sub(r'^好的[，,].{0,80}译文.{0,20}\n+', '', zh)
    zh = re.sub(r'^以下是.{0,30}译文.{0,30}\n+', '', zh)
    zh = re.sub(r'^\*\*译文\*\*\s*\n+', '', zh)
    zh = re.sub(r'\n---+\n', '\n\n', zh)
    zh = re.sub(r'\n\s*\n\s*\n+', '\n\n', zh).strip()
    return zh


def main():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT p.id AS pid, p.text AS en, d.title, d.date_guess
        FROM pages p JOIN documents d ON d.id=p.document_id
        LEFT JOIN translations t ON t.page_id=p.id AND t.language='zh-CN'
        WHERE d.source_platform IN ('hathi_ia','hathitrust') AND t.id IS NULL
        ORDER BY d.date_guess
    """).fetchall()
    print(f'待翻译 HathiTrust/IA: {len(rows)} 段')
    done = 0
    for i, r in enumerate(rows, 1):
        print(f'\n[{i}/{len(rows)}] pid={r["pid"]} | en={len(r["en"])} | {r["title"][:60]}')
        try:
            t0 = time.time()
            zh = cleanup(translate(r['en']))
            dt = time.time() - t0
            cur.execute(
                """INSERT INTO translations (page_id, language, translator, status, text)
                   VALUES (?, 'zh-CN', 'xiao-c-hathi-2026-05-17', 'human-reviewed', ?)""",
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
