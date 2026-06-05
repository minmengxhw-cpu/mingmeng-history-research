#!/usr/bin/env python3
"""下载 cia_extended_v2 候选 OCR，并精读判定民盟相关度。"""
import csv, json, os, re, sys, time, urllib.request, urllib.parse, ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CAND_CSV = ROOT / "data/cia_extended_v2_candidates.csv"
OUT_CSV = ROOT / "data/cia_extended_v2_llm_review.csv"
CACHE = ROOT / "data" / "cia_extended_v2_ocr_cache"
CACHE.mkdir(exist_ok=True)

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

API = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"

SYSTEM = """你是中国民盟史研究助理。任务：读 CIA 解密档案 OCR 全文，判断是否涉及中国民主同盟 (CDL / 民盟)。

判断口径：
- 'China Democratic League', 'Chinese Democratic League', 'CDL' 直接提及 → 涉及
- 民盟核心人物：罗隆基 (Lo Lung-chi), 章伯钧 (Chang Po-chun), 沈钧儒 (Shen Chun-ju), 张君劢 (Carsun Chang), 张澜 (Chang Lan), 梁漱溟 (Liang Shu-ming), 黄炎培 (Huang Yen-pei), 史良 (Shih Liang), 胡愈之 (Hu Yu-chih), 李公朴, 闻一多, 章伯钧, 杜斌丞, 张东荪 → 涉及
- 'Federation of Chinese Democratic Parties' / 中国民主政团同盟 → 涉及（民盟前身）
- 仅泛提'third party' 'minor parties' 'Coalition Government' 但具体涉及中国共产党+国民党的两党博弈、不涉民盟 → 不涉
- 涉及 Malayan/Taiwan/Korean/Burmese DL → 排除
- 涉及 WFDW (World Federation of Democratic Women) → 排除

输出 JSON。"""

USER = """档案: {ident}
标题: {title}
日期: {date}
关键词命中: {kws}

OCR 全文 (前 5000 字)：
{text}

请输出 JSON: {{
  "is_meng": true/false,
  "decision": "core" | "related" | "background" | "exclude",
  "meng_mentions": "民盟出现具体形式, 若无则'无'",
  "people": ["命中的民盟人物威氏拼音或中文"],
  "summary_zh": "档案内容中文摘要 50-100 字"
}}"""

DIRECT_TERMS = [
    "china democratic league",
    "chinese democratic league",
    "federation of chinese democratic parties",
]
PEOPLE_TERMS = [
    "lo lung-chi", "chang po-chun", "shen chun-ju", "carsun chang", "chang lan",
    "liang shu-ming", "huang yen-pei", "shih liang", "hu yu-chih", "li kung-pu",
    "wen i-to", "tu pin-cheng", "chang tung-sun", "tao hsing-chih", "ma yin-chu",
    "kao ch'ung-min",
]
CONTEXT_TERMS = [
    "third force", "third party", "minor parties", "coalition government",
    "political consultative", "democratic parties",
]
EXCLUDE_TERMS = [
    "malayan democratic", "taiwan democratic", "korean democratic",
    "burmese democratic", "world federation of democratic women", "wfdw",
]


def snippets(text, terms, width=180):
    lower = text.lower()
    out = []
    for term in terms:
        start = lower.find(term)
        if start < 0:
            continue
        left = max(0, start - width)
        right = min(len(text), start + len(term) + width)
        out.append(re.sub(r"\s+", " ", text[left:right]).strip())
    return out[:4]


def local_review(r, text):
    lower = text.lower()
    direct = [t for t in DIRECT_TERMS if t in lower]
    people = [t for t in PEOPLE_TERMS if t in lower]
    context = [t for t in CONTEXT_TERMS if t in lower]
    exclude = [t for t in EXCLUDE_TERMS if t in lower]
    title = r["title"]

    if direct:
        decision = "core"
        is_meng = True
        mention = "; ".join(direct)
        summary = "OCR 直接出现中国民主同盟或其前身名称，列为 CIA v2 关键期核心候选，待后续翻译入库。"
    elif people:
        decision = "related"
        is_meng = True
        mention = "民盟人物: " + "; ".join(people)
        summary = "OCR 出现民盟核心人物姓名，虽未必直接提及民盟组织名，但与民盟史研究密切相关。"
    elif exclude:
        decision = "exclude"
        is_meng = False
        mention = "排除项: " + "; ".join(exclude)
        summary = "OCR 命中民主同盟类词汇但指向其他政党或国际组织，不纳入中国民主同盟核心范围。"
    elif context:
        decision = "background"
        is_meng = False
        mention = "无"
        summary = "OCR 仅出现第三势力、联合政府、少数党派等背景概念，未发现民盟名称或核心人物。"
    else:
        decision = "exclude"
        is_meng = False
        mention = "无"
        summary = "未发现民盟名称、民盟前身或核心人物，暂不入库。"

    evidence_terms = direct + people + context + exclude
    return {
        "is_meng": is_meng,
        "decision": decision,
        "meng_mentions": mention,
        "people": people,
        "summary_zh": summary,
        "review_method": "local_rules",
        "evidence_snippet": " || ".join(snippets(text, evidence_terms or [title[:40].lower()]))[:500],
    }

def dl_ocr(ident):
    cache_file = CACHE / f"{ident}.txt"
    if cache_file.exists() and cache_file.stat().st_size > 100:
        return cache_file.read_text(encoding='utf-8', errors='replace')
    # 多种命名尝试
    url_patterns = [
        f"https://archive.org/download/{ident}/{ident.replace('cia-readingroom-document-','')}_djvu.txt",
        f"https://archive.org/download/{ident}/{ident}_djvu.txt",
    ]
    for url in url_patterns:
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            text = urllib.request.urlopen(req, timeout=20, context=ctx).read().decode('utf-8','replace')
            if len(text) > 100:
                cache_file.write_text(text, encoding='utf-8')
                return text
        except Exception: continue
    return None

def llm(api_key, ident, title, date, kws, text):
    body = {"model": MODEL,
            "messages":[{"role":"system","content":SYSTEM},
                        {"role":"user","content":USER.format(
                            ident=ident, title=title[:150], date=date,
                            kws=kws, text=text[:5000])}],
            "temperature":0.1, "max_tokens":600,
            "response_format":{"type":"json_object"},
            "thinking":{"type":"disabled"}}
    for i in range(2):
        try:
            req = urllib.request.Request(API,
                data=json.dumps(body).encode(),
                headers={"Authorization":f"Bearer {api_key}",
                         "Content-Type":"application/json"})
            r = urllib.request.urlopen(req, timeout=90).read()
            return json.loads(json.loads(r)["choices"][0]["message"]["content"])
        except Exception as e:
            if i==1: return {"_error":str(e)[:150]}
            time.sleep(3)

def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    use_llm = bool(api_key)

    rows = list(csv.DictReader(CAND_CSV.open(encoding='utf-8-sig')))
    # 取 1946-1949 关键期 22 篇
    rows = [r for r in rows if 1946 <= int(r['year']) <= 1949]
    print(f"待处理 {len(rows)} 篇（1946-1949 民盟关键期）", flush=True)

    # 下 OCR
    print("下载 OCR...", flush=True)
    ocrs = {}
    def dl(r):
        text = dl_ocr(r['identifier'])
        return r['identifier'], text
    with ThreadPoolExecutor(max_workers=6) as ex:
        for fut in as_completed({ex.submit(dl, r): r for r in rows}):
            ident, text = fut.result()
            ocrs[ident] = text
            print(f"  {'✓' if text else '✗'} {ident[:55]} ({'%dKB'%(len(text)//1024) if text else '无 OCR'})", flush=True)

    ok = sum(1 for v in ocrs.values() if v)
    print(f"\nOCR 下载: {ok}/{len(rows)}", flush=True)

    # LLM 精读
    print("\n精读复核...", flush=True)
    if not use_llm:
        print("DEEPSEEK_API_KEY 未设置，改用本地规则复核并保留证据窗口。", flush=True)
    results = []
    def work(r):
        text = ocrs.get(r['identifier'])
        if not text or len(text) < 200:
            return r, {"_error":"OCR 缺/太短", "decision":"skip"}
        if use_llm:
            res = llm(api_key, r['identifier'], r['title'], r['date'], r['matched_keywords'], text)
            if "_error" not in res:
                res["review_method"] = "llm"
        else:
            res = local_review(r, text)
        return r, res

    with ThreadPoolExecutor(max_workers=5) as ex:
        for fut in as_completed({ex.submit(work, r): r for r in rows}):
            r, res = fut.result()
            if "_error" in res:
                print(f"  ✗ {r['identifier'][:50]}: {res['_error'][:80]}", flush=True); continue
            entry = {
                "identifier": r['identifier'],
                "title": r['title'][:200],
                "date": r['date'],
                "matched_keywords": r['matched_keywords'],
                "is_meng": res.get('is_meng'),
                "decision": res.get('decision','?'),
                "meng_mentions": res.get('meng_mentions','')[:200],
                "people": '; '.join(res.get('people',[])),
                "summary_zh": res.get('summary_zh','')[:300],
                "review_method": res.get("review_method", ""),
                "evidence_snippet": res.get("evidence_snippet", "")[:500],
                "ia_detail_url": r['ia_detail_url'],
            }
            results.append(entry)
            mark = '⭐' if entry['is_meng'] else '·'
            print(f"  {mark} {r['identifier'][:50]:50s} | {entry['decision']:10s} | {entry['meng_mentions'][:60]}", flush=True)

    # 落盘
    fields = ["identifier","title","date","matched_keywords","is_meng",
              "decision","meng_mentions","people","summary_zh","review_method",
              "evidence_snippet","ia_detail_url"]
    with OUT_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(results, key=lambda x:(not x['is_meng'], x['date'])):
            w.writerow(r)

    from collections import Counter
    cnt = Counter(r['decision'] for r in results)
    n_meng = sum(1 for r in results if r['is_meng'])
    print(f"\n=== 完成 ===", flush=True)
    print(f"精读: {len(results)} / 涉民盟: {n_meng}", flush=True)
    print(f"决定分布: {dict(cnt)}", flush=True)
    print(f"输出: {OUT_CSV}", flush=True)

if __name__ == '__main__':
    main()
