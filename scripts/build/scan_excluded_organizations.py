#!/usr/bin/env python3
"""扫描 CIA + HathiTrust + NewspaperSG 全部 documents，
按 data/excluded_organizations.csv 黑名单识别疑似误收文档。

策略：两阶段
1) 关键词扫描：硬关键词命中（Taiwan/Malayan/Korean/Indo-British/Burmese/Vietnamese
   + Democratic League 共现）→ 候选清单
2) LLM 二次精读（DeepSeek）：对候选篇做"是否真涉中国民主同盟"判断

输出：
- data/excluded_org_scan_candidates.csv（关键词命中候选）
- data/excluded_org_final.csv（LLM 精读后定的误收清单，含 platform/doc_key/category/reason）
"""
from __future__ import annotations
import csv, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent.parent
EXCL_DEF = ROOT / "data" / "excluded_organizations.csv"
OUT_CAND = ROOT / "data" / "excluded_org_scan_candidates.csv"
OUT_FINAL = ROOT / "data" / "excluded_org_final.csv"

# 关键词扫描规则：每条 (category, 正则模式, 描述)
# 规则要求：异国 Democratic League 关键词 + 上下文必须共现
SCAN_PATTERNS = [
    # Taiwan Democratic Self-Government League（注意：与"Taiwanese democracy"等泛指区分）
    ("Taiwan-DSGL",
     r"\b(Taiwan Democratic Self-Government League|Taiwan Min Chu Tzu Chih Tung Meng|台湾民主自治同盟|臺灣民主自治同盟|台盟)\b",
     "台盟"),
    # Malayan Democratic Union / Malayan Democratic League（独立组织，非中国民盟分部）
    ("Malayan-DL",
     r"\b(Malayan Democratic (Union|League)|MDU|马来亚民主(联盟|同盟))\b",
     "Malayan DU"),
    # Korean Democratic League
    ("Korean-DL",
     r"\b(Korean Democratic League|KDL|朝鲜民主(党联盟|联盟))\b",
     "韩民盟"),
    # Indo-British Democratic League
    ("Indo-British-DL",
     r"\b(Indo-British Democratic League|IBDL|印英民主同盟)\b",
     "印英民盟"),
    # Burmese Democratic League
    ("Burmese-DL",
     r"\b(Burmese Democratic League|缅甸民主同盟)\b",
     "缅甸民盟"),
    # Vietnamese Democratic League
    ("Vietnam-DL",
     r"\b(Vietnamese Democratic League|Democratic Party of Vietnam|越南民主同盟)\b",
     "越南民盟"),
]

# 排除上下文：如果同时出现这些中国民盟核心信号，**不算误收**
CHINA_CDL_SIGNALS = re.compile(
    r"\b(China Democratic League|Chinese Democratic League|"
    r"Lo Lung[- ]?chi|罗隆基|"
    r"Chang Po[- ]?chun|章伯钧|"
    r"Shen Chun[- ]?ju|沈钧儒|"
    r"Carsun Chang|张君劢|"
    r"Liang Shu[- ]?ming|梁漱溟|"
    r"Huang Yen[- ]?pei|黄炎培|"
    r"Chang Lan|张澜|"
    r"中国民主同盟|中國民主同盟|中国民盟|"
    r"China Democratic League Singapore Branch|"
    r"民盟[东中华西北南]?(总?[分支]部|分会|办事处|总部))",
    re.I,
)

API = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"

LLM_SYSTEM = """你是中国民盟史研究专家。任务：判断一篇文档中提到的'XX Democratic League' 是否是中国民主同盟（CDL）。

判断口径：
- 'China Democratic League / Chinese Democratic League / CDL' 或上下文涉中国国共调停/民盟核心人物/民盟分部: → 中国民盟
- 'Taiwan Democratic Self-Government League / 台盟': → 误收（非中国民盟，是另一个民主党派但本平台不收）
- 'Malayan Democratic Union / Malayan DL': → 误收（除非明确是 'China Democratic League 在马来亚分部'）
- 'Korean / Burmese / Vietnamese / Indo-British DL': → 误收
- 同一文档可能含两种 DL；只要主要叙事涉中国民盟，保留；只是顺带提及它国 DL 而正文主体是中国民盟，保留
- 一份文档可能是综合分析多国 DL 的清单文，需谨慎降级或剔除"""

LLM_USER_TMPL = """平台：{platform}
文档 ID：{doc_id}
标题：{title}
日期：{date}

OCR 文本（前 5000 字符）：
{text}

请输出 JSON：
{{
  "is_china_cdl": true/false/null（null = 文档同时含中国民盟和它国 DL，但主体是它国）,
  "decision": "keep" | "exclude" | "downgrade",
  "specific_organization": "实际指的组织（如'中国民盟'/'马来亚民盟'/'综合分析含中国民盟和它国DL'）",
  "exclude_category": "" | "Taiwan-DSGL" | "Malayan-DL" | "Korean-DL" | "Indo-British-DL" | "Burmese-DL" | "Vietnam-DL" | "Other-non-China-DL",
  "reason": "判断理由 50-100 字"
}}"""

def call_llm(api_key, body, retries=2):
    for i in range(retries):
        try:
            req = urllib.request.Request(API,
                data=json.dumps(body).encode(),
                headers={"Authorization":f"Bearer {api_key}",
                         "Content-Type":"application/json"})
            r = urllib.request.urlopen(req, timeout=90).read()
            return json.loads(json.loads(r)["choices"][0]["message"]["content"])
        except Exception as e:
            if i == retries-1: return {"_error": str(e)[:200]}
            time.sleep(2 ** i * 2)

def load_cia():
    mf = json.load(open(ROOT/"data"/"cia_meng"/"manifest.json"))
    out = []
    for m in mf:
        ident = m["identifier"]
        # CIA 实际路径：documents/<ident>/<ident>_djvu.txt（含 cia-readingroom-document- 前缀）
        doc_dir = ROOT/"data"/"cia_meng"/"documents"/ident
        if not doc_dir.exists(): continue
        txts = list(doc_dir.glob("*_djvu.txt"))
        if not txts: continue
        out.append({
            "platform": "cia",
            "doc_id": ident,
            "doc_key": f"cia:{ident.replace('cia-readingroom-document-','')}",
            "title": m["title"][:200],
            "date": m["date"],
            "url": m.get("detail_url",""),
            "ocr_path": txts[0],
        })
    return out

def load_hathitrust():
    mf = json.load(open(ROOT/"data"/"hathitrust_ia"/"manifest.json"))
    out = []
    for m in mf:
        ident = m["identifier"]
        # HT 实际路径：documents/<ident>/<ident>_djvu.txt 或 documents/<ident>/<ident>.txt
        doc_dir = ROOT/"data"/"hathitrust_ia"/"documents"/ident
        if not doc_dir.exists(): continue
        txts = list(doc_dir.glob("*_djvu.txt")) + list(doc_dir.glob("*.txt"))
        txts = [t for t in txts if t.stat().st_size > 100]
        if not txts: continue
        out.append({
            "platform": "hathitrust",
            "doc_id": ident,
            "doc_key": f"hathitrust:{ident}",
            "title": m.get("title","")[:200],
            "date": m.get("date",""),
            "url": m.get("detail_url",""),
            "ocr_path": txts[0],
        })
    return out

def scan_doc(doc):
    text = doc["ocr_path"].read_text(encoding="utf-8", errors="replace")
    text_for_match = text[:30000]  # 限制扫描长度
    hits = []
    for cat, pat, desc in SCAN_PATTERNS:
        for m in re.finditer(pat, text_for_match, re.I):
            hits.append((cat, desc, m.group(), m.start()))
    # 扩展：基础 'Democratic League' 命中且中国民盟信号低（≤1）→ 也视为候选
    dl_basic = re.findall(r"\bDemocratic League\b", text_for_match, re.I)
    china_signal_count = len(CHINA_CDL_SIGNALS.findall(text_for_match))
    if not hits and dl_basic and china_signal_count <= 1:
        hits.append(("Other-non-China-DL", "笼统DL+低中国信号", dl_basic[0], 0))
    if not hits: return None
    suspect_count = len(hits)
    by_cat = {}
    for cat, desc, term, pos in hits:
        by_cat.setdefault(cat, []).append((desc, term, pos))
    return {
        "doc": doc,
        "text": text,
        "hits": hits,
        "by_cat": by_cat,
        "china_signal_count": china_signal_count,
        "suspect_count": suspect_count,
    }

def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key: raise SystemExit("DEEPSEEK_API_KEY 未设置")

    docs = load_cia() + load_hathitrust()
    print(f"扫描 {len(docs)} 篇 (CIA + HathiTrust)", file=sys.stderr)

    candidates = []
    for d in docs:
        r = scan_doc(d)
        if r: candidates.append(r)
    print(f"关键词命中候选: {len(candidates)} 篇", file=sys.stderr)

    # 写候选 CSV（先供人工查阅）
    with OUT_CAND.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["platform","doc_id","title","date","china_signal_count",
                    "suspect_count","categories","sample_hit"])
        for c in candidates:
            cats = "; ".join(sorted(c["by_cat"].keys()))
            sample = c["hits"][0][2] if c["hits"] else ""
            w.writerow([c["doc"]["platform"], c["doc"]["doc_id"], c["doc"]["title"],
                       c["doc"]["date"], c["china_signal_count"], c["suspect_count"],
                       cats, sample])

    # LLM 精读（仅对 china_signal < 2 或 suspect_count >= 3 的篇）
    needs_llm = [c for c in candidates
                 if c["china_signal_count"] < 2 or c["suspect_count"] >= 3]
    print(f"需 LLM 精读: {len(needs_llm)} 篇", file=sys.stderr)

    results = []
    def work(c):
        doc = c["doc"]
        # 改进：抽 DL 命中点上下文（前 200 + 后 400 字符），保证 LLM 看到真正的
        # Democratic League 出现位置而非只看页眉/页脚的前 5000 字符
        text = c["text"]
        # 1) 题名 + 日期 + 文档前 1500（含元数据）
        head = text[:1500]
        # 2) DL 命中段落（每段 600 字符上下文）
        dl_iter = list(re.finditer(r"\bDemocratic League\b", text, re.I))
        snippets = []
        for m in dl_iter[:5]:
            s = max(0, m.start() - 200); e = min(len(text), m.end() + 400)
            snippets.append(f"[DL 命中 @ pos {m.start()}]\n{text[s:e]}")
        # 3) 拼接送 LLM（避免前 5000 字符截断噪声）
        combined = head + "\n\n----DL 命中上下文----\n\n" + "\n\n".join(snippets)
        body = {"model": MODEL,
                "messages":[{"role":"system","content":LLM_SYSTEM},
                            {"role":"user","content":LLM_USER_TMPL.format(
                                platform=doc["platform"], doc_id=doc["doc_id"],
                                title=doc["title"], date=doc["date"],
                                text=combined[:8000])}],
                "temperature":0.1, "max_tokens":500,
                "response_format":{"type":"json_object"},
                "thinking":{"type":"disabled"}}
        res = call_llm(api_key, body)
        return c, res

    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(work, c): c for c in needs_llm}
        for fut in as_completed(futs):
            c, res = fut.result()
            if "_error" in res:
                print(f"  ✗ {c['doc']['doc_id']}: {res['_error'][:80]}", file=sys.stderr)
                continue
            r = {
                "platform": c["doc"]["platform"],
                "doc_id": c["doc"]["doc_id"],
                "doc_key": c["doc"]["doc_key"],
                "title": c["doc"]["title"][:200],
                "date": c["doc"]["date"],
                "is_china_cdl": res.get("is_china_cdl"),
                "decision": res.get("decision", "?"),
                "specific_organization": res.get("specific_organization",""),
                "exclude_category": res.get("exclude_category",""),
                "reason": res.get("reason","")[:300],
                "categories_found": "; ".join(sorted(c["by_cat"].keys())),
                "china_signal_count": c["china_signal_count"],
                "suspect_count": c["suspect_count"],
                "url": c["doc"]["url"],
            }
            results.append(r)
            mark = "✓" if r["decision"]=="keep" else ("✗" if r["decision"]=="exclude" else "↓")
            if mark != "✓":
                print(f"  {mark} {c['doc']['platform']}: {c['doc']['doc_id'][:50]} | {r['decision']} | {r['specific_organization'][:30]} | {r['reason'][:80]}", file=sys.stderr)

    # 全 keep 的篇也保留候选列表（标 keep），便于追溯
    keep_doc_keys = {r["doc_id"] for r in results}
    for c in candidates:
        if c["doc"]["doc_id"] not in keep_doc_keys and c not in needs_llm:
            results.append({
                "platform": c["doc"]["platform"],
                "doc_id": c["doc"]["doc_id"],
                "doc_key": c["doc"]["doc_key"],
                "title": c["doc"]["title"][:200],
                "date": c["doc"]["date"],
                "is_china_cdl": True,
                "decision": "keep",
                "specific_organization": "中国民盟（候选含信号，未送 LLM）",
                "exclude_category": "",
                "reason": "关键词命中但中国民盟信号足够多（china_signal_count≥2 且 suspect_count<3），按规则保留",
                "categories_found": "; ".join(sorted(c["by_cat"].keys())),
                "china_signal_count": c["china_signal_count"],
                "suspect_count": c["suspect_count"],
                "url": c["doc"]["url"],
            })

    fields = ["platform","doc_id","doc_key","title","date",
              "is_china_cdl","decision","specific_organization",
              "exclude_category","reason","categories_found",
              "china_signal_count","suspect_count","url"]
    with OUT_FINAL.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(results, key=lambda x:(x["platform"], x["decision"], x["date"])):
            w.writerow(r)

    from collections import Counter
    decisions = Counter(r["decision"] for r in results)
    print(f"\n=== 结果 ===", file=sys.stderr)
    for k,v in decisions.items(): print(f"  {k}: {v}", file=sys.stderr)
    print(f"\n输出:", file=sys.stderr)
    print(f"  {OUT_CAND}", file=sys.stderr)
    print(f"  {OUT_FINAL}", file=sys.stderr)


if __name__ == "__main__":
    main()
