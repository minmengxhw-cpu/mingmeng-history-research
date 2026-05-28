#!/usr/bin/env python3
"""为 Wilson 史学论文 v2 准备：基于 Wilson Center 24 篇苏方/东欧档案英文译稿，
用 DeepSeek v4-flash 逐篇精读。

输出与 CIA/FRUS/DRNH/HathiTrust 一致的 JSON 索引。

用法：
  export DEEPSEEK_API_KEY=sk-xxxx
  python3 scripts/build/summarize_wilson_for_paper.py [--limit N] [--parallel 6]

输出：
  data/wilson_paper_summaries.json
"""
import json
import os
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data" / "wilson_center"
MANIFEST = DATA_DIR / "manifest.json"
TEXT_DIR = DATA_DIR / "text"
OUT_JSON = ROOT / "data" / "wilson_paper_summaries.json"

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr)
    sys.exit(1)

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"

SYSTEM = """你是中国民盟史 + 冷战国际史的专业研究助理。任务是阅读 Wilson Center Digital Archive 所存 1945-1958 年苏联及东欧解密档案的英文译稿（原档案多为俄文，经 CWIHP 翻译为英文），提炼与中国民主同盟（Democratic League / Chinese democratic parties / democratic groups 等表述）以及"民主党派"在苏方视角下的描述事实。

严格遵守：
1. 苏方档案中对民盟的称呼变体多：Democratic League, Chinese Democratic League, democratic parties and groups, democratic forces, non-Party people 等。请识别这些变体
2. 苏方档案的主要语境：（A）1945-10 苏联驻华大使 Petrov 与周恩来/毛泽东会谈；（B）1948-12 至 1949-12 Mao-Stalin 通信；（C）1949-01 至 02 Mikoyan 访华西柏坡 4 次会谈；（D）Kovalev 报告（苏方派驻中共代表）；（E）1949-07 刘少奇秘密访苏；（F）1949-07-07 新政协预备委员会民主党派构成
3. 仅陈述档案中实际记载的事实，不补充档案外的背景知识
4. 注意区分：档案是"民盟直接提及"还是"民主党派/民主势力"的间接覆盖
5. 用中文输出 JSON 格式"""

USER_TEMPLATE = """档案元数据：
- doc_key：{doc_key}
- 标题：{title}
- 日期：{date}
- 文献类型：{kind}
- 平台评级：{grade}

===== 档案英文译稿（节选前 6500 字符）=====
{text}
===== 档案 结束 =====

请输出 JSON：
{{
  "core_fact": "用 3-5 句中文，提炼档案中与中国民盟（或'民主党派'广义）相关的核心事实，含具体讲话人、对话对象、时间、地点、话题。例如：'1949-02-04 Mikoyan 与毛泽东会谈中，毛向 Mikoyan 解释新政协参与方包括共产党、各民主党派（含民主同盟）、人民团体三方面，并说明民主党派与共产党的合作基础'",
  "people_mentioned": ["档案涉及的民盟相关人物中文名列表（如有），及苏方人物如 Stalin, Mikoyan, Kovalev, Petrov 等",],
  "geography": "档案涉及的地理范围（如：莫斯科、西柏坡、北平、南京、香港等）",
  "event_type": "事件分类（如：苏联驻华大使会谈 / Mao-Stalin 通信 / Mikoyan 访华 / Kovalev 报告 / 刘少奇访苏 / 新政协参与 / 政治理论文献）",
  "ningmeng_direct": "民盟直接提及程度（直接命名民盟 / 民主党派广义覆盖 / 间接提及 / 仅含背景）",
  "key_quote": "档案中含民盟或民主党派的英文关键句（不超过 250 字符；无则空字符串）"
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
                timeout=120,
            )
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"].strip())
        except (requests.RequestException, json.JSONDecodeError) as e:
            if attempt == retries - 1:
                return {"_error": str(e)[:200]}
            time.sleep(2 ** attempt)


def process_one(meta):
    doc_key = meta["doc_key"]
    # 找文本文件——支持多种 ID 形式
    ident = doc_key.removeprefix("wilson:")
    candidates = [
        TEXT_DIR / f"{ident}.txt",
        TEXT_DIR / f"{ident.replace(':','-')}.txt",
    ]
    text = ""
    for c in candidates:
        if c.exists():
            text = c.read_text(encoding="utf-8", errors="replace")
            break
    if not text:
        return {"_error": "no text file", "doc_key": doc_key}

    # 跳过开头的页眉模板（如 Digital Archive / digitalarchive.wilsoncenter.org）
    lines = text.split("\n")
    start_idx = 0
    for i, line in enumerate(lines[:30]):
        if "Citation" in line or "Citation:" in line or i > 15:
            start_idx = i
            break
    body = "\n".join(lines[start_idx:])[:6500]

    prompt = USER_TEMPLATE.format(
        doc_key=doc_key,
        title=meta.get("title", "")[:200],
        date=meta.get("date", ""),
        kind=meta.get("kind", ""),
        grade=meta.get("grade", ""),
        text=body,
    )
    result = call_deepseek(prompt)
    result["doc_key"] = doc_key
    result["title"] = meta.get("title", "")
    result["date"] = meta.get("date", "")
    result["grade"] = meta.get("grade", "")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--parallel", type=int, default=6)
    args = parser.parse_args()

    items = json.load(MANIFEST.open())
    items.sort(key=lambda x: x.get("date", ""))
    print(f"Wilson 总篇数: {len(items)}", file=sys.stderr)
    if args.limit:
        items = items[: args.limit]

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
            if done % 5 == 0 or done == len(todo):
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (len(todo) - done) / max(rate, 0.1)
                print(f"  [{done}/{len(todo)}] {rate:.2f} 篇/秒，ETA {eta:.0f} 秒", file=sys.stderr)

    results.sort(key=lambda x: (x.get("date") or "", x.get("doc_key") or ""))
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    err = sum(1 for r in results if "_error" in r)
    print(f"\n=== 完成 === 总 {len(results)} 篇 / 错误 {err}", file=sys.stderr)
    print(f"输出：{OUT_JSON}", file=sys.stderr)


if __name__ == "__main__":
    main()
