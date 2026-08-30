#!/usr/bin/env python3
"""DeepSeek 翻译 CIA 核心 21 篇（source_platform='cia'）

复用 retranslate_with_deepseek.py 的 SYSTEM_PROMPT + 术语表（已扩到 361 条）。
针对 CIA 档案的 OCR 噪声 + 缩写词（CCP / KMT / DL / PCC）做适配。
"""
import sqlite3, json, time, sys, os, csv, requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "research_index.sqlite"
GLOSSARY_CSV = ROOT / "data" / "translation_glossary.csv"
LOG = ROOT / "translate_cia.log"

DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DS_KEY:
    print("ERROR: 请设置环境变量 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)
DS_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

# 读术语表
glossary_lines = []
with open(GLOSSARY_CSV, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        glossary_lines.append(f"  {row['term']} → {row['translation']}")
GLOSSARY_TXT = "\n".join(glossary_lines)

SYSTEM_PROMPT = """你是一名资深的中国近代史档案翻译，专精 1940s-1950s 美方一手档案
（FRUS / CIA / Wilson Center 等），尤其熟悉中国民主同盟相关史料。

任务：把以下英文档案翻译成**高质量中文**，输出**纯中文译文**
（不要英文原文、不要解释、不要 markdown 标记）。

要求：
1. 必须使用统一术语：
""" + GLOSSARY_TXT + """

2. CIA 档案特有缩写处理：
   - DL = 中国民主同盟（民盟）
   - CCP = 中国共产党
   - KMT = 国民党
   - PCC = 政治协商会议（政协）
   - CPPCC = 中国人民政治协商会议（新政协）
   - PPC = 国民参政会
   - non-Communist = 非中共
   - third force / third party = 第三方面

3. CIA 档案常见 OCR 噪声处理：
   - 忽略 "Approved For Release..."、"CONFIDENTIAL"、"25X1A" 等水印
   - 忽略 "STATE NAVY ARMY AIR FBI" 等表单分发清单
   - 忽略残缺的页眉页脚字符
   - 但保留正文中的所有实质信息

4. 体例：
   - 译为档案体中文，准确传达原意，不删减不臆加
   - 保留原文档号、日期、地点、电报号等元数据
   - 人名首次出现可在中文译名后括注英文原名
   - 标点用中文标点
   - 数字保留阿拉伯数字
   - 表格类内容（如人员名单）保留分行结构

5. 输出格式：纯文本中文译文。"""


def translate(en_text: str) -> str:
    resp = requests.post(
        DS_URL,
        headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": en_text},
            ],
            "max_tokens": 8000,
            "temperature": 0.2,
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 找 CIA 核心档案中未翻译的 pages
    rows = cur.execute(
        """
        SELECT p.id AS page_id, p.text AS en_text, d.title, d.date_guess, d.doc_id
        FROM pages p
        JOIN documents d ON d.id = p.document_id
        LEFT JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
        WHERE d.source_platform='cia' AND t.id IS NULL
        ORDER BY d.date_guess, p.id
        """
    ).fetchall()
    print(f"待翻译 CIA 片段: {len(rows)}")

    with open(LOG, 'w') as logf:
        def log(msg):
            print(msg, flush=True)
            logf.write(msg + "\n")
            logf.flush()

        log(f"==== CIA 翻译启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ====")
        done, fail = 0, 0
        for r in rows:
            pid = r['page_id']
            en = r['en_text']
            log(f"\n--- page_id={pid} | en_chars={len(en)} | [{r['date_guess']}] {r['title'][:50]}")
            try:
                t0 = time.time()
                zh = translate(en)
                dt = time.time() - t0
                log(f"  翻译 OK in {dt:.1f}s | zh_chars={len(zh)}")

                # 插入 translations + FTS
                cur.execute(
                    """INSERT INTO translations (page_id, language, translator, status, text)
                       VALUES (?, 'zh-CN', 'deepseek-chat-2026-05-16-cia', 'machine-draft', ?)""",
                    (pid, zh),
                )
                tid = cur.lastrowid
                try:
                    cur.execute(
                        """INSERT INTO translation_fts (rowid, language, title, page_label, text)
                           VALUES (?, 'zh-CN', ?, ?, ?)""",
                        (tid, r['title'], "1", zh),
                    )
                except sqlite3.OperationalError as e:
                    log(f"  FTS skip: {e}")
                conn.commit()
                done += 1
            except Exception as e:
                log(f"  ERR: {e}")
                fail += 1
                time.sleep(2)

        log(f"\n==== 完成 ====")
        log(f"  成功: {done}")
        log(f"  失败: {fail}")
    conn.close()


if __name__ == '__main__':
    main()
