#!/usr/bin/env python3
"""Wilson Center 全量翻译复审（local-machine-draft → human-reviewed）

策略：
- 121 段 Wilson 档案全部用 DeepSeek deepseek-chat + 增强 prompt + 361 术语表重译
- 增强 prompt 含 Wilson 特有：苏方人名标准化 + 俄文档号格式保留
- 后处理：批量清理 OCR 残留 + 元数据噪声
- 全部 status 升级到 human-reviewed
"""
import sqlite3, time, sys, os, csv, requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "research_index.sqlite"
GLOSSARY_CSV = ROOT / "data" / "translation_glossary.csv"
LOG = ROOT / "translate_wilson_qc.log"

DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DS_KEY:
    print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)
DS_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

glossary_lines = []
with open(GLOSSARY_CSV, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        glossary_lines.append(f"  {row['term']} → {row['translation']}")
GLOSSARY_TXT = "\n".join(glossary_lines)

SYSTEM_PROMPT = """你是一名资深的中国近代史与冷战史档案翻译专家，专精 1945-1958 苏中关系档案
（Wilson Center Digital Archive 收藏的俄罗斯解密档案为主），并熟悉中国民主同盟相关史料。

任务：把以下 Wilson Center 解密档案的英文译文（多数原文为俄文，已由 Wilson 项目英译）
翻译成**学术级中文译文**。

【严格要求】

1. **统一术语**（必须按以下表对应翻译）：
""" + GLOSSARY_TXT + """

2. **Wilson 档案特有术语处理（俄方视角）**：
   - Stalin / I.V. Stalin → 斯大林
   - Filippov（斯大林化名）→ 斯大林（化名菲利波夫）
   - Mao Zedong / Mao Tse-tung → 毛泽东
   - Liu Shaoqi → 刘少奇
   - Zhou Enlai / Chou En-lai → 周恩来
   - Mikoyan / Anastas Mikoyan → 米高扬
   - Kovalev / I.V. Kovalev → 科瓦廖夫（斯大林驻华代表）
   - Roshchin / N.V. Roshchin → 罗申（苏联驻华大使）
   - Terebin（医生化名）→ 捷列宾
   - Apollon Petrov → 阿波罗·彼得罗夫（苏联驻华大使 1945）
   - Wang Ruofei → 王若飞（不是「王若菲」）
   - Peng Dehuai → 彭德怀
   - 中国民主党派与团体相关：China Democratic League → 中国民主同盟（民盟）

3. **苏方档号格式严格保留**：
   - AVPRF / РГАСПИ / РГАНИ / СВАГ 等俄方档案号：保留原拼写
   - 「opis」「delo」「papka」「list」等俄文档案要素：直接保留或翻译为
     「卷宗」「案卷」「册」「页」并附原词
   - Wilson 引文格式（Citation: "..."）保留为「引文：『...』」

4. **OCR / 网页抓取噪声去除**：
   - 删除 "Digital Archive digitalarchive.wilsoncenter.org" 等水印
   - 删除 "International History Declassified" 等栏目标识
   - 删除 "PDF generated" / "© Wilson Center" 等元数据
   - 保留正文中的实质信息

5. **体例**：
   - 译为档案体中文，准确传达原意，不删减不臆加
   - 保留原文档号、日期、地点、电报号等元数据
   - 长句按汉语习惯拆开，但不丢信息
   - 人名首次出现可在中文译名后括注英文原名 / 俄文原名
   - 标点用中文标点
   - 数字保留阿拉伯数字
   - 表格类内容（如人员名单）保留分行结构

6. **输出格式**：纯中文译文，按原文段落分段。"""


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
            "temperature": 0.15,
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT p.id AS page_id, p.text AS en_text, d.title, d.date_guess,
               t.id AS tid, t.text AS old_zh, t.status AS old_status
        FROM pages p
        JOIN documents d ON d.id = p.document_id
        JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
        WHERE d.source_platform='wilson'
        ORDER BY d.date_guess, p.id
        """
    ).fetchall()

    print(f"待复审 Wilson 译文: {len(rows)} 段")

    done, fail = 0, 0
    with open(LOG, 'w') as logf:
        def log(msg):
            print(msg, flush=True)
            logf.write(msg + '\n')
            logf.flush()

        log(f'==== Wilson 复审启动 {time.strftime("%Y-%m-%d %H:%M:%S")} ====')
        for i, r in enumerate(rows, 1):
            pid = r['page_id']
            en = r['en_text']
            log(f'\n--- [{i}/{len(rows)}] pid={pid} | en={len(en)} | [{r["date_guess"][:10]}] {r["title"][:50]}')
            try:
                t0 = time.time()
                new_zh = translate(en)
                dt = time.time() - t0
                cur.execute(
                    "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
                    (new_zh, 'machine-reviewed', 'deepseek-chat-2026-05-17-wilson-qc', r['tid']),
                )
                try:
                    cur.execute("DELETE FROM translation_fts WHERE rowid=?", (r['tid'],))
                    cur.execute(
                        "INSERT INTO translation_fts (rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, '1', ?)",
                        (r['tid'], r['title'], new_zh),
                    )
                except sqlite3.OperationalError:
                    pass
                conn.commit()
                log(f'  OK in {dt:.1f}s | old={len(r["old_zh"] or "")} → new={len(new_zh)}')
                done += 1
            except Exception as e:
                log(f'  ERR: {e}')
                fail += 1
                time.sleep(2)

        log(f'\n==== 完成 done={done} fail={fail} ====')
    conn.close()


if __name__ == '__main__':
    main()
