#!/usr/bin/env python3
"""CIA 译文 LLM 精修 v2（第六步：剔除完成后的翻译精修）

背景：
- 2026-05-16 曾用 deepseek-chat 做过一轮 CIA 译文复审（61 篇 → machine-reviewed），
  但 deepseek-chat 已弃用，且当时复审覆盖了后来被剔除的 26 篇离题档案。
- 2026-05-28 完成 CIA 范围二次清理（剔除 26 篇，前台保留 76 篇）。
- 本脚本对**仅保留的 76 篇** CIA 译文做新一轮 LLM 精修，用 deepseek-v4-flash +
  术语表 + 威氏拼音对照，重点解决"残留英文人名片段过多"（名单类档案）
  与 OCR 噪声水印问题。

两种运行模式：
  1. DB 模式（默认，需 data/research_index.sqlite）：逐页取 EN 源文 + 现有中文初稿，
     LLM 精修后写回 translations 表，状态升级 machine-reviewed-v2-cia-<date>，更新 FTS。
     幂等：已是 v2 状态的页跳过。
  2. OCR 演示模式（--demo-from-ocr）：不连 DB，直接对 data/cia_meng/documents/<id>/
     的整篇 OCR 做精修，输出到 workspace/cia_refine_samples/，用于预览精修质量。

用法：
  export DEEPSEEK_API_KEY=sk-xxxx
  # 生产精修（在有 DB 的环境跑）
  python3 scripts/build/refine_cia_translations_llm.py [--limit N] [--parallel 4]
  # 仅预览最严重的名单类档案精修效果（无需 DB）
  python3 scripts/build/refine_cia_translations_llm.py --demo-from-ocr \
      --ids CIA-RDP82-00457R005200480001-5,...

输出：
  DB 模式：写回 translations 表 + data/cia_translation_refine_v2_report.json
  演示模式：workspace/cia_refine_samples/<id>.md（EN/旧译/新译三栏对照）
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"
CIA_DIR = ROOT / "data" / "cia_meng"
MANIFEST = CIA_DIR / "manifest.json"
DOC_DIR = CIA_DIR / "documents"
GLOSSARY_CSV = ROOT / "data" / "translation_glossary.csv"
APP_PY = ROOT / "app.py"
REPORT_JSON = ROOT / "data" / "cia_translation_refine_v2_report.json"
SAMPLE_DIR = ROOT / "workspace" / "cia_refine_samples"

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"
STATUS_V2 = "machine-reviewed-v2-cia-2026-05-28"

# 26 篇已剔除 identifier（与 exclude_cia_off_topic.py 同步；本脚本只精修保留的 76 篇）
EXCLUDED = {
    "cia-rdp82-00457r001400250001-2", "cia-rdp82-00457r007300270002-4",
    "cia-rdp80s01540r003200080003-1", "cia-rdp80t00246a072100330001-4",
    "cia-rdp78-01617a003300010001-3",
    "cia-rdp78-01617a003500050003-5", "cia-rdp78-01617a003700140001-5",
    "cia-rdp79-01082a000100030008-9", "cia-rdp79-01383a000200020002-1",
    "cia-rdp80-00810a001500240005-4", "cia-rdp82-00457r002900580005-6",
    "cia-rdp82-00457r007100570010-4", "cia-rdp82-00457r010100310001-8",
    "cia-rdp82-00457r010400160005-8", "cia-rdp82-00457r009400360001-2",
    "cia-rdp79t00975a000800420001-9", "03193795", "03192683",
    "cia-rdp78-00915r000700150013-4", "03003301", "02066870", "03174706",
    "cia-rdp79t00975a029600010002-1", "cia-rdp08-00534r000100180001-3",
    "cia-rdp82-00457r003500280004-3", "cia-rdp82-00457r009900020008-7",
}


def normalize_id(ident: str) -> str:
    return ident.lower().removeprefix("cia-readingroom-document-")


def load_glossary(max_terms: int = 120) -> str:
    """读术语表，拼成精修 prompt 用的对照清单（取民盟史最相关项）。"""
    if not GLOSSARY_CSV.exists():
        return ""
    lines = []
    with open(GLOSSARY_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            term = (row.get("term") or "").strip()
            trans = (row.get("translation") or "").strip()
            if term and trans:
                lines.append(f"{term} = {trans}")
    return "\n".join(lines[:max_terms])


SYSTEM = """你是中国民盟史 + 民国政治史档案翻译的精修专家。任务是对 CIA / CIG 解密档案的现有中文机器翻译初稿做精修，使其成为干净、通顺、术语统一的学术参考译文。

精修规则（严格遵守）：
1. 彻底删除一切 OCR 噪声与 CIA 元数据水印：CIA-RDP 编号、25X1A/25X1X、Approved For Release、CONFIDENTIAL、S-E-C-R-E-T（含被 OCR 切碎的变体）、NO. OF PAGES、DATE DISTR、CD NO.、SUPPLEMENT TO REPORT、THIS IS UNEVALUATED INFORMATION、Next Review Date 等——这些不是档案内容，一律不出现在译文里
2. 残留的英文人名按威氏拼音规则译成标准中文。民盟核心人物对照：CHANG Lan 张澜 / LO Lung-chi 罗隆基 / CHANG Po-chun(CHANG Po-chu) 章伯钧 / SHEN Chun-ju 沈钧儒 / HUANG Yen-pei 黄炎培 / CHANG Chun-mai(Carsun Chang) 张君劢 / TSO Shun-sheng 左舜生 / LIANG Shu-ming 梁漱溟 / CHANG Tung-sun 张东荪 / SHIH Liang 史良 / CHANG Shen-fu 张申府 / CHIANG Kai-shek 蒋介石 / MAO Tse-tung 毛泽东 / CHOU En-lai 周恩来 / LI Chi-shen 李济琛。其他威氏拼音人名按标准音译，无把握时译音后加"（音译）"
3. 机构 / 术语按术语表统一（见用户消息提供的对照表）。Democratic League / Chinese Democratic League / China Democratic League 一律译"中国民主同盟"
4. 名单类档案（委员名单 / 职务名单）：把每个英文人名都译成中文，保留名单的条目结构（如 a. b. c. / 1. 2. 3.），不要遗漏任何人名
5. 只精修，不增删档案事实；不补充档案外背景；不加译者注（人名不确定时用"（音译）"即可）
6. 输出纯中文译文正文，不要任何解释、标题前缀、markdown 代码块包裹"""

USER_TEMPLATE = """【术语对照表（节选，精修时统一采用）】
{glossary}

【档案英文 OCR 源文】
{source}

【现有中文翻译初稿（可能含 OCR 噪声 + 残留英文人名，需精修）】
{draft}

请输出精修后的干净中文译文（删尽 OCR 噪声、英文人名全部译为中文、术语统一、行文通顺）："""


def call_deepseek(source: str, draft: str, glossary: str, retries: int = 3) -> dict:
    prompt = USER_TEMPLATE.format(glossary=glossary, source=source[:6000], draft=draft[:6000])
    for attempt in range(retries):
        try:
            r = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 3000,
                    "temperature": 0.2,
                    "thinking": {"type": "disabled"},
                },
                timeout=150,
            )
            r.raise_for_status()
            return {"text": r.json()["choices"][0]["message"]["content"].strip()}
        except (requests.RequestException, KeyError, ValueError) as e:
            if attempt == retries - 1:
                return {"_error": str(e)[:200]}
            time.sleep(2 ** attempt)


# ============ 残留质量检测（与 build_translation_quality_report 同口径）============
NOISE_MARKERS = ["CIA-RDP", "25X1", "Approved For Release", "CONFIDENTIAL", "DATE DISTR"]
EN_FRAGMENT_RE = re.compile(r"[A-Za-z][A-Za-z'\-]{2,}(?:\s+[A-Za-z][A-Za-z'\-]{2,})*")


def count_issues(text: str) -> dict:
    noise = sum(text.count(m) for m in NOISE_MARKERS)
    en_frags = [m.group(0) for m in EN_FRAGMENT_RE.finditer(text) if len(m.group(0)) > 3]
    return {"noise": noise, "en_fragments": len(en_frags)}


# ============ 模式 1：DB 生产精修 ============
def get_cia_pages(conn: sqlite3.Connection):
    """取保留 76 篇的所有页：page_id, EN 源文, 现有中文, 状态, identifier。"""
    rows = conn.execute(
        """
        SELECT p.id AS page_id, p.text AS source_text,
               t.id AS trans_id, t.text AS zh_text, t.status AS zh_status,
               d.identifier AS identifier
        FROM pages p
        JOIN documents d ON d.id = p.document_id
        JOIN sources s ON s.id = d.source_id
        LEFT JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
        WHERE s.source_type='cia'
        ORDER BY d.identifier, p.page_number
        """
    ).fetchall()
    out = []
    for r in rows:
        ident = normalize_id(r["identifier"] or "")
        if ident in EXCLUDED:
            continue
        if not r["zh_text"]:
            continue
        out.append(dict(r))
    return out


def update_fts(conn, trans_id, page_id, text):
    try:
        conn.execute("DELETE FROM translations_fts WHERE rowid=?", (trans_id,))
        conn.execute("INSERT INTO translations_fts(rowid, page_id, text) VALUES(?,?,?)",
                     (trans_id, page_id, text))
    except sqlite3.OperationalError:
        pass  # 无 FTS 表则跳过


def run_db_mode(limit: int, parallel: int):
    if not DB_PATH.exists():
        print(f"ERROR: 找不到数据库 {DB_PATH}。请在有 research_index.sqlite 的环境运行，"
              f"或用 --demo-from-ocr 预览。", file=sys.stderr)
        sys.exit(1)
    glossary = load_glossary()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pages = get_cia_pages(conn)
    # 幂等：跳过已精修到 v2 的页
    todo = [p for p in pages if p["zh_status"] != STATUS_V2]
    if limit:
        todo = todo[:limit]
    print(f"保留 76 篇 CIA 共 {len(pages)} 个有译文页，待精修 {len(todo)} 页", file=sys.stderr)

    report = []
    t0 = time.time()
    done = 0

    def work(p):
        res = call_deepseek(p["source_text"] or "", p["zh_text"] or "", glossary)
        return p, res

    with ThreadPoolExecutor(max_workers=parallel) as ex:
        futs = {ex.submit(work, p): p for p in todo}
        for fut in as_completed(futs):
            done += 1
            p, res = fut.result()
            if "_error" in res:
                report.append({"identifier": p["identifier"], "page_id": p["page_id"], "error": res["_error"]})
                continue
            new_text = res["text"]
            before = count_issues(p["zh_text"] or "")
            after = count_issues(new_text)
            conn.execute("UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
                         (new_text, STATUS_V2, "deepseek-v4-flash-2026-05-28-cia-refine", p["trans_id"]))
            update_fts(conn, p["trans_id"], p["page_id"], new_text)
            conn.commit()
            report.append({
                "identifier": p["identifier"], "page_id": p["page_id"],
                "noise_before": before["noise"], "noise_after": after["noise"],
                "en_frag_before": before["en_fragments"], "en_frag_after": after["en_fragments"],
            })
            if done % 10 == 0 or done == len(todo):
                rate = done / (time.time() - t0)
                print(f"  [{done}/{len(todo)}] {rate:.2f} 页/秒", file=sys.stderr)
    conn.close()
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    ok = [r for r in report if "error" not in r]
    improved = [r for r in ok if r["en_frag_after"] < r["en_frag_before"] or r["noise_after"] < r["noise_before"]]
    print(f"\n=== 完成 === 精修 {len(ok)} 页 / 错误 {len(report)-len(ok)} / 有改善 {len(improved)}", file=sys.stderr)
    print(f"报告：{REPORT_JSON}", file=sys.stderr)


# ============ 模式 2：OCR 演示精修（无需 DB）============
def run_demo_from_ocr(ids: list[str]):
    glossary = load_glossary()
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {normalize_id(d["identifier"]): d for d in json.load(MANIFEST.open())}
    for raw in ids:
        # 找 OCR 文件（大写目录 / 小写 readingroom 前缀）
        cands = [
            DOC_DIR / raw / f"{raw}_djvu.txt",
            DOC_DIR / raw.upper() / f"{raw.upper()}_djvu.txt",
            DOC_DIR / f"cia-readingroom-document-{raw.lower()}" / f"cia-readingroom-document-{raw.lower()}_djvu.txt",
        ]
        ocr_path = next((p for p in cands if p.exists()), None)
        if not ocr_path:
            print(f"  ✗ 找不到 OCR：{raw}", file=sys.stderr)
            continue
        source = ocr_path.read_text(encoding="utf-8", errors="replace")
        meta = manifest.get(normalize_id(raw), {})
        title = meta.get("title", raw)
        date = meta.get("date", "")
        # 演示模式：把 OCR 当作"初稿"输入，让模型直接产出干净译文
        res = call_deepseek(source, "（无中文初稿，请基于英文 OCR 源文直接给出精修译文）", glossary)
        if "_error" in res:
            print(f"  ✗ {raw}: {res['_error']}", file=sys.stderr)
            continue
        before = count_issues(source)
        after = count_issues(res["text"])
        out = SAMPLE_DIR / f"{raw}.md"
        out.write_text(
            f"# CIA 译文精修演示 · {title}\n\n> {date} · identifier `{raw}`\n\n"
            f"残留检测：OCR 噪声标记 {before['noise']} → 精修后 {after['noise']}；"
            f"英文片段 {before['en_fragments']} → {after['en_fragments']}\n\n"
            f"---\n\n## 精修后中文译文\n\n{res['text']}\n\n"
            f"---\n\n## 英文 OCR 源文（节选）\n\n```\n{source[:2500]}\n```\n",
            encoding="utf-8",
        )
        print(f"  ✓ {raw} → {out}（英文片段 {before['en_fragments']}→{after['en_fragments']}）", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--demo-from-ocr", action="store_true")
    parser.add_argument("--ids", default="", help="演示模式：逗号分隔的 identifier")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: 请设置 DEEPSEEK_API_KEY", file=sys.stderr)
        sys.exit(1)

    if args.demo_from_ocr:
        ids = [x.strip() for x in args.ids.split(",") if x.strip()]
        if not ids:
            print("ERROR: 演示模式需 --ids", file=sys.stderr)
            sys.exit(1)
        run_demo_from_ocr(ids)
    else:
        run_db_mode(args.limit, args.parallel)


if __name__ == "__main__":
    main()
