#!/usr/bin/env python3
"""为 CIA 史学论文 v2 准备：逐篇精读 CIA 102 篇里剔除 26 后的 76 篇 OCR，
用 DeepSeek v4-flash 提炼民盟相关核心事实，输出 JSON 索引。

用法：
  export DEEPSEEK_API_KEY=sk-xxxx
  python3 scripts/build/summarize_cia_for_paper.py [--limit N] [--parallel 8]

输出：
  data/cia_paper_summaries.json
"""
import csv
import json
import os
import re
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent.parent
CIA_DIR = ROOT / "data" / "cia_meng"
MANIFEST = CIA_DIR / "manifest.json"
DOC_DIR = CIA_DIR / "documents"
APP_PY = ROOT / "app.py"
OUT_JSON = ROOT / "data" / "cia_paper_summaries.json"

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"

# 26 篇已剔除的 identifier（来自 exclude_cia_off_topic.py）
EXCLUDED = {
    # A 朝鲜
    "cia-rdp82-00457r001400250001-2", "cia-rdp82-00457r007300270002-4",
    "cia-rdp80s01540r003200080003-1", "cia-rdp80t00246a072100330001-4",
    # B 日本
    "cia-rdp78-01617a003300010001-3",
    # C 东南亚
    "cia-rdp78-01617a003500050003-5", "cia-rdp78-01617a003700140001-5",
    "cia-rdp79-01082a000100030008-9", "cia-rdp79-01383a000200020002-1",
    "cia-rdp80-00810a001500240005-4", "cia-rdp82-00457r002900580005-6",
    "cia-rdp82-00457r007100570010-4", "cia-rdp82-00457r010100310001-8",
    "cia-rdp82-00457r010400160005-8", "cia-rdp82-00457r009400360001-2",
    # D 1956+
    "cia-rdp79t00975a000800420001-9", "03193795", "03192683",
    "cia-rdp78-00915r000700150013-4", "03003301", "02066870", "03174706",
    "cia-rdp79t00975a029600010002-1", "cia-rdp08-00534r000100180001-3",
    # E 台湾
    "cia-rdp82-00457r003500280004-3", "cia-rdp82-00457r009900020008-7",
}

SYSTEM = """你是中国民盟史 + 美方情报史的专业研究助理。任务是阅读 CIA / CIG（美国中央情报局/中央情报组）解密档案的 OCR 英文原文，提炼与中国民主同盟（China Democratic League / Chinese Democratic League / Federation of Chinese Democratic Parties，简称民盟）相关的核心事实。

严格遵守：
1. CIA 档案的 OCR 质量较差，含大量 CIA 元数据噪声（CIA-RDP 编号 / 25X1A / S-E-C-R-E-T / Approved For Release 等）—— 忽略这些噪声，只看实质内容
2. 民盟在 CIA 档案中的命名变体多：China Democratic League、Chinese Democratic League、Democratic League、League 等；威氏拼音人名：CHIANG Kai-shek 蒋介石 / MAO Tse-tung 毛泽东 / CHANG Lan 张澜 / LO Lung-chi 罗隆基 / CHANG Po-chun 章伯钧 / SHEN Chun-ju 沈钧儒 / HUANG Yen-pei 黄炎培 / YEH Tu-yi 叶笃义 等
3. 仅陈述档案中实际记载的事实，不补充档案外的背景知识
4. 如果档案是民盟海外分支（华南民盟、香港分部、雪兰莪分部）的活动，明确标注"海外分支"
5. 用中文输出 JSON 格式"""

USER_TEMPLATE = """档案元数据：
- identifier：{identifier}
- 标题：{title}
- 日期：{date}
- matched_term：{matched_term}

===== OCR 全文（节选前 5500 字符）=====
{text}
===== OCR 全文 结束 =====

请输出 JSON：
{{
  "core_fact": "用 2-5 句中文，提炼档案中与中国民盟相关的最核心事实（含具体人物、地点、时间、行动）。例如：'1949-05-23 报告记载三位民盟执委 YEH Tu-yi（叶笃义）等于 1949-05-20 化装撤离上海至香港，报告同时记述 LO Lung-chi 罗隆基与 CHANG Lan 张澜的处境'。如果是误命中或仅旁证提及，明确说明。",
  "people_mentioned": ["民盟相关人物中文名列表（如有）"],
  "geography": "档案涉及的地理范围（如：华南、香港、上海、北平、马来亚雪兰莪、东南亚等）",
  "event_type": "事件分类（如：民盟领导人活动 / 组织情报 / 海外分支 / 政策研判 / 非法化前后 / 新政协参与 / 新政权下角色）",
  "importance": "重要度 1-5（1=误命中/旁证；3=一般情报；5=民盟史关键档案）",
  "key_quote": "档案中含民盟人物言论或核心定性的英文原句（不超过 250 字符；无则空字符串）"
}}

只输出 JSON。"""


def call_deepseek(prompt_user, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": prompt_user},
                    ],
                    "max_tokens": 900,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "thinking": {"type": "disabled"},
                },
                timeout=90,
            )
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"].strip())
        except (requests.RequestException, json.JSONDecodeError) as e:
            if attempt == retries - 1:
                return {"_error": str(e)[:200]}
            time.sleep(2 ** attempt)


def find_ocr_path(ident):
    """OCR 文件路径有两种命名：大写 / 小写带 readingroom 前缀"""
    candidates = [
        DOC_DIR / ident / f"{ident}_djvu.txt",
        DOC_DIR / f"cia-readingroom-document-{ident.lower()}" / f"cia-readingroom-document-{ident.lower()}_djvu.txt",
        DOC_DIR / ident.upper() / f"{ident.upper()}_djvu.txt",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def normalize_id(ident):
    """统一 identifier：去 cia-readingroom-document- 前缀，转小写"""
    s = ident.lower().removeprefix("cia-readingroom-document-")
    return s


def load_all_ids():
    """收集 102 个 identifier（manifest 62 + app.py 标题字典补充 40）"""
    ids = {}

    # 1. manifest.json 62 篇
    if MANIFEST.exists():
        for d in json.load(MANIFEST.open()):
            raw_ident = d.get("identifier", "")
            ident = normalize_id(raw_ident)
            ids[ident] = {
                "identifier": ident,
                "title": d.get("title", ""),
                "date": d.get("date", ""),
                "matched_term": d.get("matched_term", ""),
                "description": d.get("description", "")[:1000],
                "url": d.get("detail_url", ""),
            }

    # 2. 从 app.py 标题翻译字典补充
    content = APP_PY.read_text()
    for m in re.finditer(r'"CIA Reading Room ([\w\-]+):\s*(.+?)":\s*"(.+?)"', content):
        raw, en, zh = m.groups()
        ident = normalize_id(raw)
        if ident not in ids:
            ids[ident] = {
                "identifier": ident,
                "title": f"CIA Reading Room {raw}: {en}",
                "date": "",
                "matched_term": "",
                "description": "",
                "title_zh": zh,
                "url": "",
            }
        else:
            ids[ident]["title_zh"] = zh

    return ids


def process_one(meta):
    ident = meta["identifier"]
    ocr_path = find_ocr_path(ident)
    if ocr_path:
        text = ocr_path.read_text(encoding="utf-8", errors="replace")[:5500]
    else:
        # 用 manifest description 作 fallback
        text = meta.get("description", "")[:1500]
        if not text:
            return {"_error": "no OCR or description", "identifier": ident}

    prompt = USER_TEMPLATE.format(
        identifier=ident,
        title=meta.get("title", "")[:200],
        date=meta.get("date", ""),
        matched_term=meta.get("matched_term", "")[:80],
        text=text,
    )
    result = call_deepseek(prompt)
    result["identifier"] = ident
    result["title"] = meta.get("title", "")
    result["title_zh"] = meta.get("title_zh", "")
    result["date"] = meta.get("date", "")
    result["url"] = meta.get("url", "")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--parallel", type=int, default=8)
    args = parser.parse_args()

    all_ids = load_all_ids()
    print(f"总 identifier 数: {len(all_ids)}", file=sys.stderr)

    # 剔除 26 篇
    todo_meta = [m for ident, m in all_ids.items() if ident not in EXCLUDED]
    print(f"剔除 {len(all_ids)-len(todo_meta)} 篇后待处理: {len(todo_meta)}", file=sys.stderr)

    if args.limit:
        todo_meta = todo_meta[: args.limit]

    # 增量缓存
    existing = {}
    if OUT_JSON.exists():
        try:
            existing = {r["identifier"]: r for r in json.load(OUT_JSON.open())}
            print(f"已有 {len(existing)} 篇缓存", file=sys.stderr)
        except Exception:
            existing = {}
    todo = [m for m in todo_meta if m["identifier"] not in existing]
    print(f"实际待跑: {len(todo)} 篇\n", file=sys.stderr)

    results = list(existing.values())
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futs = {ex.submit(process_one, m): m for m in todo}
        for fut in as_completed(futs):
            done += 1
            try:
                res = fut.result()
            except Exception as e:
                m = futs[fut]
                res = {"_error": str(e), "identifier": m["identifier"]}
            results.append(res)
            if done % 15 == 0 or done == len(todo):
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (len(todo) - done) / max(rate, 0.1)
                print(f"  [{done}/{len(todo)}] {rate:.2f} 篇/秒，ETA {eta:.0f} 秒", file=sys.stderr)
                results.sort(key=lambda x: (x.get("date") or "", x.get("identifier") or ""))
                OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    results.sort(key=lambda x: (x.get("date") or "", x.get("identifier") or ""))
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    err = sum(1 for r in results if "_error" in r)
    print(f"\n=== 完成 === 总 {len(results)} 篇 / 错误 {err}", file=sys.stderr)
    print(f"输出：{OUT_JSON}", file=sys.stderr)


if __name__ == "__main__":
    main()
