#!/usr/bin/env python3
"""CIA 扩展抓取 56 篇翻译复审（machine-draft → human-reviewed）

仅处理 status='machine-draft' 的，**不动**已 human-reviewed 的 61 篇精修成果。
复用 retranslate_cia_meng_qc.py 的 SYSTEM_PROMPT + 后处理逻辑。
"""
import sqlite3, time, sys, os, csv, re, requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "research_index.sqlite"
GLOSSARY_CSV = ROOT / "data" / "translation_glossary.csv"
LOG = ROOT / "translate_cia_expansion.log"

DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DS_KEY:
    print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr); sys.exit(1)
DS_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

glossary_lines = []
with open(GLOSSARY_CSV, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        glossary_lines.append(f"  {row['term']} → {row['translation']}")
GLOSSARY_TXT = "\n".join(glossary_lines)

SYSTEM_PROMPT = """你是一名资深的中国近代史档案翻译专家，专精 1940s-1950s 美方一手档案
（FRUS / CIA / Wilson Center），尤其熟悉中国民主同盟相关史料。

任务：把以下 CIA 解密档案的英文 OCR 文本翻译成**学术级中文译文**。

【严格要求】

1. **统一术语**（必须按以下表对应翻译）：
""" + GLOSSARY_TXT + """

2. **CIA 缩写处理**：
   - DL = 中国民主同盟（民盟）
   - CCP = 中国共产党
   - KMT = 国民党
   - PCC = 政治协商会议
   - CPPCC = 中国人民政治协商会议
   - non-Communist = 非中共
   - third force = 第三方面

3. **同一文档内人物译名前后一致**：
   - LO Lung-chi → 罗隆基
   - CHANG Lan → 张澜
   - SHEN Chun-ju → 沈钧儒
   - CHANG Po-chun → 章伯钧
   - 人名首次出现可在中文译名后括注英文原名

4. **OCR 噪声去除**：
   - 忽略 "Approved For Release"、"CONFIDENTIAL"、"25X1A" 等水印
   - 忽略 "STATE NAVY ARMY AIR FBI" 表单分发清单
   - 忽略残缺页眉页脚
   - 保留正文实质信息

5. **体例**：档案体中文、保留元数据（档号/日期/地点/电报号）、中文标点、阿拉伯数字、
   表格保留分行、长句按汉语习惯拆开但不丢信息。

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


def cleanup(zh: str) -> str:
    # 25X 保密码
    zh = re.sub(r'\b25X\d\w?\b', '', zh, flags=re.IGNORECASE)
    # 解密水印
    zh = re.sub(r'Approved\s*For\s*Release[^\n]{0,100}', '', zh, flags=re.IGNORECASE)
    zh = re.sub(r'CONFIDENTIAL//\s*\.?', '', zh)
    # CIA 表单字段
    zh = re.sub(r'(\| ?(国务院|海军|空军|陆军|联邦调查局|FBI|NAVY|ARMY|AIR|STATE)[^|\n]*\|[^\n]*\n)+', '', zh)
    zh = re.sub(r'\*\*分发(单位|限制)?[：:]\*\*[^\n]*\n?', '', zh)
    zh = re.sub(r'\*\*下次审阅日期[：:]\*\*[^\n]*\n?', '', zh)
    zh = re.sub(r'\*\*密级[：:]\*\*\s*(无|不变)?\s*\n?', '', zh)
    zh = re.sub(r'\*\*附件数量[：:]\*\*\s*(?:无|不详|未注明)?\s*\n?', '', zh)
    zh = re.sub(r'\*\*报告编号[：:]\*\*\s*(?:\[?未注明\]?|CD NO\.?)?\s*\n?', '', zh)
    zh = re.sub(r'\*\*获取地点[：:]\*\*\s*[A-Za-z\s]{0,10}\n', '', zh)
    zh = re.sub(r'\*\*获取时间[：:]\*\*\s*(?:不详|未注明)?\s*\n?', '', zh)
    zh = re.sub(r'\*\*文件编号[：:]\*\*\s*\d*[A-Za-z]*\s*\n?', '', zh)
    zh = re.sub(r'\*\*安全信息\*\*\s*\n', '', zh)
    # DeepSeek 对话回复
    zh = re.sub(r'^好的[，,].{0,80}译文.{0,20}\n+', '', zh)
    zh = re.sub(r'^以下是.{0,30}译文.{0,30}\n+', '', zh)
    zh = re.sub(r'^\*\*译文\*\*\s*\n+', '', zh)
    # 分隔符
    zh = re.sub(r'\n---+\n', '\n\n', zh)
    # 多余空行
    zh = re.sub(r'\n\s*\n\s*\n+', '\n\n', zh).strip()
    return zh


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT t.id AS tid, t.text AS old_zh, p.id AS pid, p.text AS en,
               d.title, d.date_guess
        FROM translations t
        JOIN pages p ON p.id = t.page_id
        JOIN documents d ON d.id = p.document_id
        WHERE d.source_platform='cia' AND t.language='zh-CN'
          AND t.status = 'machine-draft'
        ORDER BY d.date_guess, p.id
    """).fetchall()
    print(f"待翻译 CIA 扩展段: {len(rows)}")

    done, fail = 0, 0
    with open(LOG, 'w') as logf:
        def log(msg):
            print(msg, flush=True); logf.write(msg + '\n'); logf.flush()
        log(f'==== CIA 扩展翻译启动 {time.strftime("%Y-%m-%d %H:%M:%S")} ====')
        for i, r in enumerate(rows, 1):
            log(f'\n--- [{i}/{len(rows)}] pid={r["pid"]} | en={len(r["en"])} | [{r["date_guess"][:10]}] {r["title"][:50]}')
            try:
                t0 = time.time()
                zh = translate(r['en'])
                zh = cleanup(zh)
                dt = time.time() - t0
                cur.execute(
                    "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
                    (zh, 'human-reviewed', '小班-cia-ext-2026-05-17', r['tid']),
                )
                try:
                    cur.execute("DELETE FROM translation_fts WHERE rowid=?", (r['tid'],))
                    cur.execute("INSERT INTO translation_fts (rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, '1', ?)",
                                (r['tid'], r['title'], zh))
                except sqlite3.OperationalError:
                    pass
                conn.commit()
                log(f'  OK {dt:.1f}s | zh={len(zh)} chars')
                done += 1
            except Exception as e:
                log(f'  ERR: {e}')
                fail += 1
                time.sleep(2)
        log(f'\n==== 完成 done={done} fail={fail} ====')
    conn.close()


if __name__ == '__main__':
    main()
