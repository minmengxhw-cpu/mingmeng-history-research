#!/usr/bin/env python3
"""为 HathiTrust 史学论文 v2 准备：基于 54 期港媒 OCR 整期文本，
用 DeepSeek v4-flash 逐期抽取与民盟相关的段落并做精读。

每期港媒 OCR 长度 100-300KB，含大量与民盟无关的国际新闻 / 商业广告。
本脚本策略：
  1. 将 OCR 全文分段（按页/按双换行）
  2. 关键词预筛（Democratic League / League / Lo Lung-chi / Chang Lan /
     Chang Po-chun / Shen Chun-ju / Huang Yen-pei / Carsun Chang /
     coalition government / Political Consultative / third party 等）
  3. 提取含关键词的段落（前后 100 字符上下文）
  4. 把所有相关段落拼接成"民盟相关精选"提交给 DeepSeek 精读

输出与 CIA/FRUS/DRNH 一致的 JSON 索引。

用法：
  export DEEPSEEK_API_KEY=sk-xxxx
  python3 scripts/build/summarize_hathitrust_for_paper.py [--limit N] [--parallel 6]

输出：
  data/hathitrust_paper_summaries.json
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
DATA_DIR = ROOT / "data" / "hathitrust_ia"
MANIFEST = DATA_DIR / "manifest.json"
DOC_DIR = DATA_DIR / "documents"
OUT_JSON = ROOT / "data" / "hathitrust_paper_summaries.json"

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"

# 关键词预筛（大小写不敏感）
KEYWORDS = [
    "Democratic League", "Democratic Leagu",  # OCR 可能截断
    "democratic league",
    "China Democratic", "Chinese Democratic",
    "Lo Lung-chi", "Lo Lung Chi", "LO LUNG",
    "Chang Lan", "CHANG LAN",
    "Chang Po-chun", "Chang Po Chun", "CHANG PO",
    "Shen Chun-ju", "Shen Chun Ju", "SHEN CHUN",
    "Huang Yen-pei", "Huang Yen Pei", "HUANG YEN",
    "Carsun Chang", "CARSUN",
    "Tso Shun-sheng", "TSO SHUN",
    "Chang Chun-mai", "CHANG CHUN-MAI",
    "Liang Shu-ming", "LIANG SHU",
    "Federation of Chinese Democratic",
    "coalition government", "Coalition Government",
    "Political Consultative",
    "third party", "Third Party",
    "Li Tsi-shen", "Li Chi-shen", "LI CHI-SHEN",
    "Soong Ching Ling", "SOONG CHING",
    "Kuo Mo-jo", "KUO MO",
]

SYSTEM = """你是中国民盟史 + 香港英文报刊史的专业研究助理。任务是阅读 1946-1950 年香港英文报刊《华字日报》（China Mail, CM）与《士蔑报》（Hong Kong Telegraph, HKT）的整期 OCR 中已抽取出的与中国民主同盟相关的段落，提炼港媒"第三方公开舆论"对民盟的报道事实。

严格遵守：
1. 港媒报道民盟的命名变体：Democratic League, Chinese Democratic League, China Democratic League, Federation of Chinese Democratic Parties。1947-10 民盟被国府"非法化"后港媒大量用 "outlawed Democratic League"、"banned Democratic League" 等表述
2. 民盟核心人物威氏拼音：Lo Lung-chi 罗隆基, Chang Lan 张澜, Chang Po-chun 章伯钧, Chang Chun-mai/Carsun Chang 张君劢, Shen Chun-ju 沈钧儒, Huang Yen-pei 黄炎培, Tso Shun-sheng 左舜生, Liang Shu-ming 梁漱溟, Li Chi-shen 李济琛
3. OCR 质量较差，常含连写错误 / 字符替换 / 分页噪声 —— 忽略噪声，看实质内容
4. 仅陈述档案中实际记载的事实，不补充档案外的背景知识
5. 港媒报道角度多元：消息发自南京/上海/香港/华盛顿等地，注意区分新闻来源（路透社 Reuters / 美联社 AP / 本报 CM staff / 中央社 / 新华社等）
6. 用中文输出 JSON 格式"""

USER_TEMPLATE = """档案元数据：
- identifier：{identifier}
- 报刊：{paper}（{paper_abbr}）
- 日期：{date}

===== 从该期 OCR 中预筛抽取的与民盟相关段落（前后 100 字符上下文，多段以 === 分隔） =====
{text}
===== 抽取段落 结束 =====

请输出 JSON：
{{
  "core_fact": "用 2-5 句中文，提炼该期港媒中与中国民盟相关的最核心报道事实，含报道日期、地点、人物、事件、信息来源（如该期报道引用 Reuters/AP/中央社 等）。例如：'1947-11-05 China Mail 综合 Reuters 与 AP 电报道：国民政府 10-28 宣布民盟非法后，民盟主席张澜在沪发表抗议声明；港埠多个民间团体声援民盟'。如该期无民盟相关实质内容则明确说明",
  "people_mentioned": ["港媒报道中提及的民盟相关人物中文名列表（如有）"],
  "geography": "报道涉及的地理范围（如：南京、上海、香港、华盛顿、华南、西南等）",
  "event_type": "事件分类（如：政协会议报道 / 国共调解 / 民盟内部动态 / 民盟非法化 / 民盟领导人活动 / 民盟与美方接触 / 新政协参与 / 民盟与中共关系 / 海外分支 / 公开声明）",
  "news_source": "信息来源（如：Reuters / AP / CM staff / Central News Agency / 自家电讯 / 评论文章等）",
  "importance": "重要度 1-5（1=误命中/旁证；3=一般报道；5=民盟史关键事件直接报道）",
  "key_quote": "港媒原文中含民盟相关的英文关键句（不超过 250 字符；无则空字符串）"
}}

只输出 JSON。"""


def extract_relevant_passages(text, window=100, max_total=8000):
    """从 OCR 全文中抽取含关键词的段落，每段加 window 字符前后上下文"""
    passages = []
    text_lower = text.lower()
    found_positions = set()

    for kw in KEYWORDS:
        kw_lower = kw.lower()
        start = 0
        while True:
            pos = text_lower.find(kw_lower, start)
            if pos < 0:
                break
            # 避免重叠：如果该位置 ±50 已被记录则跳过
            if any(abs(pos - p) < 80 for p in found_positions):
                start = pos + len(kw)
                continue
            found_positions.add(pos)
            s = max(0, pos - window)
            e = min(len(text), pos + len(kw) + window * 2)
            passages.append(text[s:e].strip())
            start = pos + len(kw)

    if not passages:
        return ""

    # 拼接，控制总长度
    out = "\n\n=== \n\n".join(passages)
    if len(out) > max_total:
        out = out[:max_total] + "\n\n[...truncated...]"
    return out


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
                timeout=120,
            )
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"].strip())
        except (requests.RequestException, json.JSONDecodeError) as e:
            if attempt == retries - 1:
                return {"_error": str(e)[:200]}
            time.sleep(2 ** attempt)


def process_one(meta):
    ident = meta["identifier"]
    # 找 OCR 文件
    p = DOC_DIR / ident / f"{ident}_djvu.txt"
    if not p.exists():
        return {"_error": "no OCR", "identifier": ident}
    text = p.read_text(encoding="utf-8", errors="replace")
    passages = extract_relevant_passages(text, window=120, max_total=7500)
    if not passages:
        return {
            "_error": "no relevant passages",
            "identifier": ident,
            "title": meta.get("title", ""),
            "date": meta.get("date", ""),
        }

    paper = "China Mail" if ident.startswith("NPCM") else ("Hong Kong Telegraph" if ident.startswith("NPTG") else "?")
    paper_abbr = "CM" if ident.startswith("NPCM") else ("HKT" if ident.startswith("NPTG") else "?")

    prompt = USER_TEMPLATE.format(
        identifier=ident,
        paper=paper,
        paper_abbr=paper_abbr,
        date=meta.get("date", ""),
        text=passages,
    )
    result = call_deepseek(prompt)
    result["identifier"] = ident
    result["title"] = meta.get("title", "")
    result["date"] = meta.get("date", "")
    result["paper"] = paper
    result["passage_count"] = passages.count("=== ") + 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--parallel", type=int, default=6)
    args = parser.parse_args()

    items = json.load(MANIFEST.open())
    items.sort(key=lambda x: x.get("date", ""))
    print(f"HathiTrust 总期数: {len(items)}", file=sys.stderr)
    if args.limit:
        items = items[: args.limit]

    # 增量缓存
    existing = {}
    if OUT_JSON.exists():
        try:
            existing = {r["identifier"]: r for r in json.load(OUT_JSON.open())}
            print(f"已有 {len(existing)} 篇缓存", file=sys.stderr)
        except Exception:
            existing = {}
    todo = [i for i in items if i["identifier"] not in existing]
    print(f"实际待跑: {len(todo)} 期\n", file=sys.stderr)

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
            if done % 10 == 0 or done == len(todo):
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (len(todo) - done) / max(rate, 0.1)
                print(f"  [{done}/{len(todo)}] {rate:.2f} 期/秒，ETA {eta:.0f} 秒", file=sys.stderr)
                results.sort(key=lambda x: (x.get("date") or "", x.get("identifier") or ""))
                OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    results.sort(key=lambda x: (x.get("date") or "", x.get("identifier") or ""))
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    err = sum(1 for r in results if "_error" in r)
    print(f"\n=== 完成 === 总 {len(results)} 期 / 错误或空 {err}", file=sys.stderr)
    print(f"输出：{OUT_JSON}", file=sys.stderr)


if __name__ == "__main__":
    main()
