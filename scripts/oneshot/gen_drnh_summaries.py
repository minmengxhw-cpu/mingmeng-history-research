#!/usr/bin/env python3
"""为台北国史馆（DRNH）有访客水印图的档案，据「案由」生成机器初拟摘要（小段落）。

说明：
- 仅处理 data/drnh_images/ 下确有 p*.jpg 的 DRNH 档案。
- 摘要严格依据案由本身整理，不补案由中没有的史实——前端卡片会明确标注
  「据国史馆档案案由整理 · 机器初拟，待人工校订」。
- 结果写入 documents.drnh_summary。
- 可重复运行：已有 drnh_summary 的档案自动跳过（断点续跑）。
"""
import sqlite3
import glob
import json
import re
import time
import urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
LOG = Path(__file__).with_suffix(".log")

LLM_URL = "http://100.95.78.72:11435/v1/chat/completions"
MODEL = "Qwen3.5-122B-A10B-UD-Q4_K_XL"

PROMPT = """你是一名民国史档案整理员。下面是一条「台北国史馆档案」的案由（档案题名/内容提要），请把它整理成一段通顺、易读的白话说明。

严格要求：
1. 只能依据案由本身的信息。可做：文言断句、解释生僻词语、把案由中已明确出现的人物、机构、事件讲清楚。
2. 背景补充仅限确定无疑的常识，凡不确定一律不补。
3. 严禁编造案由中没有的内容：不得添加未提及的人物身份、确切日期、事件经过、历史评价或意义定性。
4. 不要写「史料价值」「历史意义」之类需要主观判断的话。
5. 篇幅约 120-180 字，一段，不分点。直接输出说明正文，不要任何前言、标题或结语。

案由：{anyou}"""


def log(msg: str) -> None:
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def call_llm(anyou: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(anyou=anyou)}],
        "temperature": 0.3,
        "max_tokens": 2000,
    }).encode("utf-8")
    req = urllib.request.Request(
        LLM_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=240) as r:
        d = json.load(r)
    text = (d["choices"][0]["message"].get("content") or "").strip()
    # 去掉可能残留的思维链标记
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    return text


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)")]
    if "drnh_summary" not in cols:
        conn.execute("ALTER TABLE documents ADD COLUMN drnh_summary TEXT")
        conn.commit()
        log("已新增列 documents.drnh_summary")

    docs = conn.execute(
        """
        SELECT d.id, d.doc_key, d.title, p.text AS anyou, d.drnh_summary
        FROM documents d JOIN pages p ON p.document_id = d.id
        WHERE COALESCE(d.source_platform, 'frus') = 'drnh'
        """
    ).fetchall()

    targets = []
    for d in docs:
        safe = d["doc_key"].replace(":", "__").replace("/", "_")
        if glob.glob(str(ROOT / "data" / "drnh_images" / safe / "p*.jpg")):
            targets.append(d)
    todo = [d for d in targets if not (d["drnh_summary"] or "").strip()]
    log(f"有水印图档案 {len(targets)} 份；待生成 {len(todo)} 份")

    ok = fail = 0
    for i, d in enumerate(todo, 1):
        anyou = (d["anyou"] or d["title"] or "").strip()
        if not anyou:
            fail += 1
            log(f"  [{i}] {d['doc_key']} 跳过：无案由文本")
            continue
        summary = ""
        for attempt in range(3):
            try:
                summary = call_llm(anyou)
                if summary and len(summary) >= 30:
                    break
            except Exception as e:  # noqa: BLE001
                log(f"  [{i}] {d['doc_key']} 第{attempt+1}次失败：{e}")
                time.sleep(6)
        if summary and len(summary) >= 30:
            conn.execute(
                "UPDATE documents SET drnh_summary = ? WHERE id = ?",
                (summary, d["id"]),
            )
            conn.commit()
            ok += 1
        else:
            fail += 1
            log(f"  [{i}] {d['doc_key']} 最终失败")
        if i % 10 == 0:
            log(f"进度 {i}/{len(todo)}　成功 {ok}　失败 {fail}")

    log(f"完成：成功 {ok}，失败 {fail}，共目标 {len(todo)}")


if __name__ == "__main__":
    main()
