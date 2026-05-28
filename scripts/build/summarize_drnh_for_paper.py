#!/usr/bin/env python3
"""为 DRNH 史学论文 v2 准备：基于 drnh_review_layers.csv 的 282 篇档案
（重点校订 136 + 常规校订 13 + 背景保留 133），用 DeepSeek v4-flash 逐篇精读
（DRNH 无 OCR，使用题名 + 内容描述 + 关键词组 + 相关人员等元数据）。

输出与 CIA/FRUS 一致的 JSON 索引，作为撰写"打压方内部档案中的民盟"史学叙事
论文的精读底稿。

用法：
  export DEEPSEEK_API_KEY=sk-xxxx
  python3 scripts/build/summarize_drnh_for_paper.py [--limit N] [--parallel 8]

输出：
  data/drnh_paper_summaries.json
"""
import csv
import json
import os
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent.parent
REVIEW_CSV = ROOT / "data" / "drnh_review_layers.csv"
HITS_CSV = ROOT / "data" / "drnh_probe" / "drnh_hits.csv"
OUT_JSON = ROOT / "data" / "drnh_paper_summaries.json"

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"

SYSTEM = """你是中国民盟史 + 民国档案史的专业研究助理。任务是阅读台北国史馆（DRNH, ahonline.drnh.gov.tw）档案的繁体中文元数据（題名、內容描述、關鍵詞組、相關人員），提炼与中国民主同盟（民盟、民主政团同盟、民主同盟）相关的核心事实。

严格遵守：
1. DRNH 档案是国民政府最高决策层 + 军统/保密局 + 各战区呈蒋的内部档案，视角是"打压方内部观察"。注意区分档案产出主体：（A）戴笠/军统呈件（1946 之前）；（B）保密局呈件（1946 之后）；（C）蒋介石本人批阅 / 接见 / 电令；（D）各战区呈报（薛岳/邱清泉/郑介民/张镇等）；（E）政要档案（张嘉璈/宋子文/陈布雷等）；（F）其他党政公文中含民盟信息
2. 民盟核心人物：张澜、罗隆基、章伯钧、张君劢、左舜生、黄炎培、沈钧儒、张申府、李公朴、潘光旦、史良、彭学沛等
3. 仅陈述档案题名/内容描述中实际记载的事实，不补充档案外的背景知识
4. 重点关注国民政府对民盟的态度、监视、查办、批阅、政策决定等行为
5. 简化输出：用中文输出 JSON 格式"""

USER_TEMPLATE = """档案元数据：
- doc_key：{doc_key}
- 題名：{title}
- 本件日期：{date}
- 全宗：{collection}
- 內容描述：{description}
- 關鍵詞組：{keywords}
- 相關人員：{persons}
- 相關地點：{places}
- 校订分层：{tier}

请输出 JSON：
{{
  "producer": "档案产出主体（A戴笠/军统呈件 / B保密局呈件 / C蒋介石批阅 / D各战区呈报 / E政要档案 / F其他党政公文）",
  "producer_detail": "具体呈报人或机构（如：戴笠、毛人凤、保密局、薛岳、邱清泉、郑介民、张镇、陈布雷等）",
  "core_fact": "用 2-4 句中文，提炼档案中与民盟相关的最核心事实，包含：哪个机构 / 对民盟做什么 / 涉及哪些民盟人物 / 时间 / 事件。例如：'1945-05-24 戴笠呈蒋介石，报告民盟分子左舜生、张君劢拟从事调解国共纠纷的活动情况。属军统对民盟领导层与国共调解关系的监视情报'",
  "people_mentioned": ["档案涉及的民盟相关人物中文名列表（如有）"],
  "event_type": "事件分类（如：军统/保密局情报呈报 / 民盟领导人活动监视 / 蒋介石批阅决策 / 战区地方动态 / 民盟非法化前后 / 国大相关 / 海外分支 / 与美方接触 / 与中共关系 / 民盟内部分化）",
  "geography": "档案涉及的地理范围（如：南京、重庆、上海、昆明、华南、香港、华北等）",
  "ningmeng_relevance": "民盟相关度（核心 / 相关 / 背景 / 误命中）",
  "key_phrase": "档案题名或内容描述中含民盟相关信息的关键短句（不超过 100 字符；可用繁体中文原文）"
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
                    "max_tokens": 700,
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


def load_review_layers():
    """加载分层校订表，与 hits.csv 合并出完整元数据"""
    # 1. 加载 hits.csv，key=_identifier
    hits = {}
    with open(HITS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hits[row["_identifier"]] = row

    # 2. 加载 review_layers.csv，按 doc_key 关联
    items = []
    with open(REVIEW_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            doc_key = row["doc_key"]
            ident = doc_key.removeprefix("drnh:")
            h = hits.get(ident, {})
            items.append({
                "doc_key": doc_key,
                "tier": row["tier"],
                "title": row["title"] or h.get("題名", ""),
                "date": row["date_guess"] or h.get("本件日期", ""),
                "collection": h.get("全宗名稱", ""),
                "description": h.get("內容描述", "")[:600],
                "keywords": h.get("關鍵詞組", "")[:200],
                "persons": h.get("相關人員", "")[:200],
                "places": h.get("相關地點", "")[:200],
                "url": row["url"],
            })
    return items


def process_one(item):
    prompt = USER_TEMPLATE.format(
        doc_key=item["doc_key"],
        title=item["title"][:200],
        date=item["date"],
        collection=item["collection"][:60],
        description=item["description"][:600],
        keywords=item["keywords"][:200],
        persons=item["persons"][:200],
        places=item["places"][:200],
        tier=item["tier"],
    )
    result = call_deepseek(prompt)
    result["doc_key"] = item["doc_key"]
    result["title"] = item["title"]
    result["date"] = item["date"]
    result["tier"] = item["tier"]
    result["url"] = item["url"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--parallel", type=int, default=8)
    parser.add_argument("--tier", default="", help="仅处理某层级")
    args = parser.parse_args()

    items = load_review_layers()
    print(f"DRNH review_layers 总数: {len(items)}", file=sys.stderr)
    if args.tier:
        items = [i for i in items if i["tier"] == args.tier]
        print(f"按 tier={args.tier} 过滤后: {len(items)}", file=sys.stderr)
    if args.limit:
        items = items[: args.limit]

    # 增量缓存
    existing = {}
    if OUT_JSON.exists():
        try:
            existing = {r["doc_key"]: r for r in json.load(OUT_JSON.open())}
            print(f"已有 {len(existing)} 篇缓存", file=sys.stderr)
        except Exception:
            existing = {}
    todo = [i for i in items if i["doc_key"] not in existing]
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
                res = {"_error": str(e), "doc_key": m["doc_key"]}
            results.append(res)
            if done % 20 == 0 or done == len(todo):
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (len(todo) - done) / max(rate, 0.1)
                print(f"  [{done}/{len(todo)}] {rate:.2f} 篇/秒，ETA {eta:.0f} 秒", file=sys.stderr)
                results.sort(key=lambda x: (x.get("date") or "", x.get("doc_key") or ""))
                OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    results.sort(key=lambda x: (x.get("date") or "", x.get("doc_key") or ""))
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    err = sum(1 for r in results if "_error" in r)
    print(f"\n=== 完成 === 总 {len(results)} 篇 / 错误 {err}", file=sys.stderr)
    print(f"输出：{OUT_JSON}", file=sys.stderr)


if __name__ == "__main__":
    main()
