#!/usr/bin/env python3
"""NewspaperSG 93 篇 OCR 正文精翻（DeepSeek v4-flash 版）

输入：
- data/newspapersg/manifest.csv（93 行）
- data/newspapersg/documents/<issue_id>-<article_id>.txt（93 个 OCR）
- data/newspapersg/relevance_review.csv（已有 title 级精读，含 grade/score）

输出：
- data/newspapersg/zh_translations.csv（93 行：doc_key,title,date,newspaper,title_zh,zh_text,zh_chars,translator,status）
  — 用户本地 build_research_index 后跑 ingest_newspapersg_translations_from_csv.py 灌入 sqlite

为什么独立 CSV 而不直接写 sqlite：
1) 当前 sparse-checkout 仓库 sqlite 是 0 字节 stub，跑不通基于 sqlite 的脚本
2) CSV 是 plain text，可直接 commit 进 git，用户 pull 后即得
3) 用户本地 sqlite 可用配套 ingest 脚本一键注入

DeepSeek API key 通过环境变量 DEEPSEEK_API_KEY 注入。
"""
from __future__ import annotations
import argparse, csv, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request, urllib.error

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "newspapersg"
DOC_DIR = DATA_DIR / "documents"
MANIFEST = DATA_DIR / "manifest.csv"
REVIEW_CSV = DATA_DIR / "relevance_review.csv"
OUT_CSV = DATA_DIR / "zh_translations.csv"
GLOSSARY_PATH = ROOT / "data" / "translation_glossary.csv"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"
STATUS = "machine-reviewed-newspapersg-deepseek-2026-06-02"
TRANSLATOR = "deepseek-v4-flash-newspapersg"

SYSTEM = """你是中国民主同盟史、民国政治史与英属南洋报刊史研究助理。任务：把 NewspaperSG 报刊 OCR 文本精译为可入库的中文研究译文。

严格遵守：
1. 忠实翻译／校订，不增加档案外事实。英文原报译为现代中文（保留专有名词原文括注一次）；中文繁体／旧字报道整理为现代简体中文（保留旧词如「本坡」「南洋」「澈查」原貌，必要处补注）。
2. 人名、机构、地名、日期、数量、引号内政治口号一字不改。明显 OCR 错字（如 "S"hai" = "Shanghai"）可按上下文校正。
3. 术语统一：
   - Democratic League / Chinese Democratic League / China Democratic League / CDL → "中国民主同盟"（简称"民盟"）
   - Federation of Chinese Democratic Parties → "中国民主政团同盟"
   - Kuomintang / KMT → "国民党"
   - Communist / Chinese Communist Party / CCP → "中国共产党"（简称"中共"）
   - Coalition Government → "联合政府"
   - Quit China Week → "撤美军周"（保留英文原名一次）
   - Chiang Kai-shek → "蒋介石"
   - Carsun Chang / Chang Chun-mai → "张君劢"
4. **段落结构**：按英文/中文原报的段落分段。报头日期行单独一段。社论/评论标注「评论」字样。
5. **OCR 噪声处理**：忽略页眉/页脚/「Continued on page X」/广告碎片；不要把噪声译进正文。
6. 输出 JSON：{"title_zh": "...", "zh_text": "完整中文正文（含段落分隔的纯文本，无 markdown 标记）", "translator_note": "翻译过程中的难点/取舍/可疑处，100 字内"}。
"""

def glossary_text() -> str:
    if not GLOSSARY_PATH.exists():
        return ""
    rows = []
    try:
        with GLOSSARY_PATH.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                term = (row.get("term") or "").strip()
                trans = (row.get("translation") or "").strip()
                if term and trans:
                    rows.append(f"{term} = {trans}")
    except Exception:
        return ""
    return "\n".join(rows[:120])


def article_id_from_url(url: str) -> str:
    m = re.search(r"/article/(.+)$", url)
    return m.group(1) if m else ""


def load_relevance() -> dict:
    """读 relevance_review.csv 拿 grade/score（用于 doc_key 映射）"""
    out = {}
    if not REVIEW_CSV.exists(): return out
    with REVIEW_CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            dk = row.get("doc_key", "").strip()
            if dk.startswith("newspapersg:"):
                dk = dk[len("newspapersg:"):]
            out[dk] = {
                "grade": row.get("grade", ""),
                "score": row.get("score", ""),
                "reason": row.get("reason", ""),
            }
    return out


def call_deepseek(api_key: str, title: str, date: str, newspaper: str, url: str, ocr_text: str, glossary: str) -> dict:
    user = f"""术语表（参考）：
{glossary}

报刊：{newspaper}
日期：{date}
题名：{title}
原始链接：{url}

OCR 原文：
{ocr_text}

请输出 JSON。"""
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                API_URL,
                data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                payload = json.loads(r.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            return json.loads(content)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")[:300]
            if attempt == 2:
                return {"_error": f"HTTP {e.code}: {err_body}"}
            time.sleep(3 * (2 ** attempt))
        except Exception as e:
            if attempt == 2:
                return {"_error": str(e)[:300]}
            time.sleep(2 * (2 ** attempt))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-existing", action="store_true", help="若 OUT_CSV 已含该 doc_key 跳过")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY 未设置")

    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
    review = load_relevance()
    gloss = glossary_text()

    # 已翻译跳过
    existing = {}
    if args.skip_existing and OUT_CSV.exists():
        for r in csv.DictReader(OUT_CSV.open(encoding="utf-8-sig")):
            existing[r["doc_key"]] = r

    tasks = []
    for r in rows:
        art_id = article_id_from_url(r["url"])
        fname = f"{r['issue_id']}-{art_id}.txt"
        doc_key = f"{r['issue_id']}-{art_id}"
        path = DOC_DIR / fname
        if not path.exists():
            print(f"  ! 缺 OCR 文件 {fname}", file=sys.stderr)
            continue
        if args.skip_existing and doc_key in existing:
            continue
        ocr = path.read_text(encoding="utf-8", errors="replace")
        meta = review.get(doc_key, {})
        tasks.append({
            "doc_key": doc_key,
            "issue_id": r["issue_id"],
            "date": r["date"],
            "newspaper": r["newspaper"],
            "title": r["title"],
            "url": r["url"],
            "ocr": ocr,
            "grade": meta.get("grade", ""),
            "score": meta.get("score", ""),
        })

    if args.limit:
        tasks = tasks[: args.limit]

    print(f"待翻译: {len(tasks)} 篇", file=sys.stderr)
    results = list(existing.values())

    def work(t):
        res = call_deepseek(api_key, t["title"], t["date"], t["newspaper"], t["url"], t["ocr"], gloss)
        if "_error" in res:
            print(f"  ✗ {t['doc_key']}: {res['_error'][:120]}", file=sys.stderr)
            return None
        out = {
            "doc_key": t["doc_key"],
            "issue_id": t["issue_id"],
            "date": t["date"],
            "newspaper": t["newspaper"],
            "title": t["title"],
            "title_zh": res.get("title_zh", ""),
            "zh_text": res.get("zh_text", "").strip(),
            "zh_chars": len(res.get("zh_text", "")),
            "translator_note": res.get("translator_note", "")[:300],
            "grade": t["grade"],
            "score": t["score"],
            "url": t["url"],
            "translator": TRANSLATOR,
            "status": STATUS,
        }
        return out

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, t): t for t in tasks}
        for fut in as_completed(futs):
            t = futs[fut]
            r = fut.result()
            done += 1
            if r:
                results.append(r)
                print(f"  ✓ [{done}/{len(tasks)}] {t['date']} | {t['newspaper'][:10]:<10} | {r['zh_chars']:>5}字 | {t['title'][:50]}", file=sys.stderr)
            if done % 10 == 0:
                # 中途落盘（防中断丢失）
                _save(results)

    _save(results)
    ok = sum(1 for r in results if r.get("zh_text"))
    err = len(tasks) - (ok - len(existing))
    total_chars = sum(r.get("zh_chars", 0) for r in results)
    print(f"\n=== 完成 === 总篇数 {len(results)} / 含正文翻译 {ok} / 失败 {err} / 总中文字数 {total_chars}", file=sys.stderr)


def _save(results):
    fields = ["doc_key", "issue_id", "date", "newspaper", "title", "title_zh",
              "zh_text", "zh_chars", "translator_note", "grade", "score",
              "url", "translator", "status"]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(results, key=lambda x: (x.get("date", ""), x.get("doc_key", ""))):
            w.writerow({k: r.get(k, "") for k in fields})


if __name__ == "__main__":
    main()
