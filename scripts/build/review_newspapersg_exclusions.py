#!/usr/bin/env python3
"""NewspaperSG 93 篇误收复核——识别 4 类"非中国民盟"应剔除/降级文档。

复核标准：
- 中国民主同盟 (China Democratic League) → 保留
- China Democratic League 的新马分部 → 保留
- 台湾民主自治同盟 (Taiwan Democratic Self-Government League) → 剔除
- 马来亚民主同盟 (Malayan Democratic Union/League) → 剔除
- 朝鲜民主党联盟 (Korean Democratic League) → 剔除
- 印英民主同盟 (Indo-British Democratic League) → 剔除
- 其他与中国民盟无关的 Democratic League → 剔除

输出：
- data/newspapersg/exclusions.csv（误收清单：doc_key, exclude_reason, original_grade）
- data/newspapersg/relevance_review_v2.csv（更新后的研究等级）
"""
from __future__ import annotations
import csv, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "newspapersg"
MANIFEST = DATA / "manifest.csv"
DOC_DIR = DATA / "documents"
TRANS_CSV = DATA / "zh_translations.csv"
REVIEW_CSV = DATA / "relevance_review.csv"
EXCL_CSV = DATA / "exclusions.csv"
OUT_CSV = DATA / "relevance_review_v2.csv"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"

SYSTEM = """你是中国民盟史研究专家。任务：判断一篇 NewspaperSG 报刊报道是否**真正涉及中国民主同盟**，还是误收的同名／同英文名组织。

判断口径（严格）：
- 中国民主同盟 (China Democratic League, CDL, 民盟): ✅ 保留
- China Democratic League 的新加坡分部 / 马来亚分部 / 雪兰莪分部 等海外分支: ✅ 保留
- 民盟核心人物（张君劢 Carsun Chang / 罗隆基 Lo Lung-chi / 章伯钧 Chang Po-chun / 沈钧儒 Shen Chun-ju / 梁漱溟 Liang Shu-ming / 李公朴 / 闻一多 / 胡愈之 / 张澜 Chang Lan）报道: ✅ 保留
- 涉中国民盟的事件（重庆政协 PCC / 反内战 / 民盟非法化 / 撤美军周 Quit China Week 等）: ✅ 保留
- 台湾民主自治同盟 (Taiwan Democratic Self-Government League): ❌ 剔除
- 马来亚民主同盟 (Malayan Democratic Union / Malayan Democratic League): ❌ 剔除
- 朝鲜民主党联盟 (Korean Democratic League): ❌ 剔除
- 印英民主同盟 (Indo-British Democratic League): ❌ 剔除
- 其他与中国民盟无关的 Democratic League: ❌ 剔除
- 文本只笼统提及 "Democratic League" 但上下文明确指中国情境（民盟/民主党派/国共政协）: ✅ 保留
- 文本只是用 "Democratic League" 做政治概念笼统类比（未指具体组织）: 判为 "ambiguous" 标 ❓

输出 JSON。"""

USER_TMPL = """报刊：{newspaper}
日期：{date}
原题：{title}
原 grade：{grade}

OCR 原文（前 4000 字）：
{ocr_excerpt}

中文译文（前 4000 字）：
{zh_excerpt}

请输出 JSON：
{{
  "is_china_democratic_league": true/false,
  "decision": "keep" | "exclude" | "downgrade",
  "specific_organization": "实际指的具体组织（如'中国民主同盟'/'马来亚民主同盟'/'台湾民主自治同盟'/'笼统提及'）",
  "exclude_category": "" | "Taiwan-DSGL" | "Malayan-DL" | "Korean-DL" | "Indo-British-DL" | "Other-non-China-DL" | "Ambiguous",
  "reason": "判断理由 50-100 字"
}}"""

def call(api_key, body, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(API_URL,
                data=json.dumps(body).encode(),
                headers={"Authorization":f"Bearer {api_key}", "Content-Type":"application/json"})
            r = urllib.request.urlopen(req, timeout=90).read()
            return json.loads(json.loads(r)["choices"][0]["message"]["content"])
        except Exception as e:
            if i == retries-1: return {"_error": str(e)[:200]}
            time.sleep(2 * (2**i))

def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key: raise SystemExit("DEEPSEEK_API_KEY 未设置")

    manifest = list(csv.DictReader(MANIFEST.open(encoding='utf-8-sig')))
    trans = {r['doc_key']: r for r in csv.DictReader(TRANS_CSV.open(encoding='utf-8-sig'))}
    reviews = {}
    for r in csv.DictReader(REVIEW_CSV.open(encoding='utf-8-sig')):
        dk = r['doc_key'].replace('newspapersg:', '')
        reviews[dk] = r

    tasks = []
    for m in manifest:
        import re
        art_id = re.search(r'/article/(.+)$', m['url']).group(1)
        doc_key = f"{m['issue_id']}-{art_id}"
        t = trans.get(doc_key, {})
        rv = reviews.get(doc_key, {})
        ocr_path = DOC_DIR / f"{doc_key}.txt"
        ocr = ocr_path.read_text(encoding='utf-8', errors='replace') if ocr_path.exists() else ''
        tasks.append({
            'doc_key': doc_key, 'date': m['date'], 'newspaper': m['newspaper'],
            'title': m['title'], 'grade': rv.get('grade', ''),
            'ocr': ocr[:4000], 'zh': (t.get('zh_text') or '')[:4000],
            'original_review': rv,
        })

    print(f"复核 {len(tasks)} 篇", file=sys.stderr)
    results = []
    def work(t):
        body = {"model": MODEL,
                "messages":[{"role":"system","content":SYSTEM},
                            {"role":"user","content":USER_TMPL.format(
                                newspaper=t['newspaper'], date=t['date'], title=t['title'],
                                grade=t['grade'], ocr_excerpt=t['ocr'], zh_excerpt=t['zh'])}],
                "temperature":0.1, "max_tokens":600,
                "response_format":{"type":"json_object"},
                "thinking":{"type":"disabled"}}
        res = call(api_key, body)
        return t, res

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(work, t): t for t in tasks}
        for fut in as_completed(futs):
            t, res = fut.result()
            if '_error' in res:
                print(f"  ✗ {t['doc_key']}: {res['_error'][:80]}", file=sys.stderr)
                continue
            r = {
                'doc_key': t['doc_key'], 'date': t['date'],
                'newspaper': t['newspaper'], 'title': t['title'],
                'original_grade': t['grade'],
                'is_china_cdl': res.get('is_china_democratic_league', None),
                'decision': res.get('decision', '?'),
                'specific_org': res.get('specific_organization', ''),
                'exclude_category': res.get('exclude_category', ''),
                'reason': res.get('reason', '')[:300],
            }
            results.append(r)
            mark = '✓' if r['decision'] == 'keep' else ('✗' if r['decision'] == 'exclude' else '↓')
            if mark != '✓':
                print(f"  {mark} {r['doc_key']:55s} | {r['decision']:8s} | {r['specific_org'][:30]:30s} | {r['reason'][:60]}", file=sys.stderr)

    # 写 exclusions.csv
    excludes = [r for r in results if r['decision'] == 'exclude']
    downgrades = [r for r in results if r['decision'] == 'downgrade']
    keeps = [r for r in results if r['decision'] == 'keep']

    print(f"\n=== 复核结果 ===", file=sys.stderr)
    print(f"  保留: {len(keeps)}", file=sys.stderr)
    print(f"  降级: {len(downgrades)}", file=sys.stderr)
    print(f"  剔除: {len(excludes)}", file=sys.stderr)
    from collections import Counter
    cats = Counter(r['exclude_category'] for r in excludes)
    for k,v in cats.items(): print(f"    - {k}: {v}", file=sys.stderr)

    fields = ['doc_key','date','newspaper','title','original_grade','is_china_cdl',
              'decision','specific_org','exclude_category','reason']
    with EXCL_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted([x for x in results if x['decision'] != 'keep'],
                        key=lambda x:(x['decision'], x['date'])):
            w.writerow(r)

    # 写 relevance_review_v2.csv（v2 = 原表 + decision/exclude_category 列，剔除者标新 grade='前台不展示'）
    review_map = {r['doc_key']: r for r in results}
    out = []
    for orig in reviews.values():
        dk = orig['doc_key'].replace('newspapersg:', '')
        rev = review_map.get(dk, {})
        new_row = dict(orig)
        if rev.get('decision') == 'exclude':
            new_row['grade'] = '前台不展示'
            new_row['needs_review'] = '1'
            new_row['reason'] = (new_row.get('reason','') + f' [v2 剔除: {rev["specific_org"]}, {rev["reason"][:100]}]').strip()
        elif rev.get('decision') == 'downgrade':
            new_row['grade'] = '背景材料'
            new_row['needs_review'] = '1'
            new_row['reason'] = (new_row.get('reason','') + f' [v2 降级: {rev["reason"][:100]}]').strip()
        out.append(new_row)
    with OUT_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        for r in sorted(out, key=lambda x:x['date']): w.writerow(r)

    print(f"\n输出：", file=sys.stderr)
    print(f"  {EXCL_CSV}  (误收清单)", file=sys.stderr)
    print(f"  {OUT_CSV}  (v2 研究等级)", file=sys.stderr)

if __name__ == '__main__':
    main()
