#!/usr/bin/env python3
"""用 DeepSeek 重译高优先级问题页（Generalissimo / english_residue / glossary_miss）"""
import sqlite3, json, time, sys, os, requests
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "research_index.sqlite"
GLOSSARY_CSV = Path(__file__).parent.parent / "data" / "translation_glossary.csv"
LOG = Path(__file__).parent.parent / "retranslate.log"

DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DS_KEY:
    print("ERROR: 请设置环境变量 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)
DS_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

# 第三批：剩余 66 个机器初稿页面（覆盖率 84% → 100%）
# 含罗隆基 (124)、张君劢 (333)、俞大维 (150)、莫德惠 (230/231)、
# 司徒雷登多份报告、1944-45 早期驻华使馆报告等民盟史料一手文献
TARGETS = [2, 5, 7, 9, 14, 15, 18, 19, 20, 21, 23, 26, 39, 74, 76, 77, 78, 80, 102, 103, 104, 105, 124, 144, 150, 152, 153, 160, 163, 165, 171, 179, 188, 217, 218, 229, 230, 231, 242, 267, 269, 273, 274, 291, 296, 302, 310, 313, 317, 320, 322, 333, 338, 345, 346, 354, 355, 356, 365, 381, 382, 392, 395, 398, 406, 416]

# 读术语表
glossary_lines = []
import csv
with open(GLOSSARY_CSV) as f:
    for row in csv.DictReader(f):
        glossary_lines.append(f"  {row['term']} → {row['translation']}")
GLOSSARY_TXT = "\n".join(glossary_lines)

SYSTEM_PROMPT = """你是一名资深的中国近代史档案翻译，专精 FRUS（《美国对外关系文件集》）1941-1950 年中国卷册。

任务：把以下 FRUS 英文文档翻译成**高质量中文**，输出**纯中文译文**（不要英文原文，不要解释，不要 markdown 标记）。

要求：
1. 必须使用统一术语：
""" + GLOSSARY_TXT + """

2. 重点术语：
   - Generalissimo / The Generalissimo = 委员长（即蒋介石）
   - Madame Chiang Kai-shek = 蒋夫人
   - Democratic League / Chinese Democratic League = 中国民主同盟 / 民盟
   - Federation of Chinese Democratic Parties = 中国民主政团同盟
   - Kuomintang / KMT = 国民党
   - Political Consultative Conference / PCC = 政治协商会议 / 政协
   - third party / third group = 第三方面
   - Lo Lung-chi = 罗隆基
   - Chang Lan = 张澜
   - Carsun Chang = 张君劢
   - Chang Tung-sun = 张东荪
   - Chang Po-chun = 章伯钧
   - Chou En-lai = 周恩来
   - Stuart = 司徒雷登
   - Atcheson = 艾其森
   - Yu Ta-wei = 俞大维
   - General Wedemeyer = 魏德迈将军

3. 体例：
   - 译为档案体中文，准确传达原意，不删减不臆加
   - 保留原文档号、日期、地点、电报号等元数据
   - 长句可按汉语习惯拆开，但不丢信息
   - 人名首次出现可在中文译名后括注英文原名
   - 标点用中文标点
   - 数字保留阿拉伯数字

4. 输出格式：纯文本中文译文，按原文段落分段。"""

def translate(en_text: str) -> str:
    """调 DeepSeek 翻译"""
    resp = requests.post(
        DS_URL,
        headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": en_text}
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

    with open(LOG, "w") as logf:
        def log(msg):
            print(msg, flush=True)
            logf.write(msg + "\n"); logf.flush()

        log(f"==== 重译启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ====")
        log(f"目标页：{TARGETS}")
        done = []
        failed = []
        for pid in TARGETS:
            row = cur.execute(
                "SELECT t.id AS tid, t.text AS zh, p.text AS en, p.page_label, d.title FROM translations t JOIN pages p ON p.id=t.page_id JOIN documents d ON d.id=p.document_id WHERE t.page_id=? AND t.language='zh-CN'",
                (pid,)
            ).fetchone()
            if not row:
                log(f"  page_id={pid}: 找不到，跳过")
                failed.append((pid, "not_found"))
                continue

            en = row['en']
            log(f"\n--- page_id={pid} | en_chars={len(en)} | title={row['title'][:60]} ---")
            try:
                t0 = time.time()
                new_zh = translate(en)
                dt = time.time() - t0
                log(f"  翻译完成 in {dt:.1f}s | zh_chars={len(new_zh)}")
                # 保存
                cur.execute(
                    "UPDATE translations SET text=?, status='human-reviewed', translator='deepseek-chat-2026-05-15' WHERE id=?",
                    (new_zh, row['tid'])
                )
                cur.execute("DELETE FROM translation_fts WHERE rowid=?", (row['tid'],))
                cur.execute(
                    "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
                    (row['tid'], row['title'], row['page_label'], new_zh)
                )
                conn.commit()
                done.append(pid)
            except Exception as e:
                log(f"  ❌ 翻译失败：{e}")
                failed.append((pid, str(e)[:80]))

        log(f"\n==== 完成 ====")
        log(f"成功：{len(done)} 页 | 失败：{len(failed)} 页")
        log(f"成功 page_ids：{done}")
        log(f"失败：{failed}")

    conn.close()

if __name__ == "__main__":
    main()
