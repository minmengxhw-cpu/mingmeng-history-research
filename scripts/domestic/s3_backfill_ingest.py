#!/usr/bin/env python3
"""S3 补采：把 work/domestic 下已存在的 OCR 文本入库 documents/pages（DRY-RUN 默认）。

数据来源：domestic_candidates 中 check_outcome='pass'、可下载（wikimedia PDF / NLC 编号）的候选。
OCR 定位策略（按优先级）：
  1. evidence_locator 直接引用的 .ocr.md 路径（含「及」「至」「、」「；」分隔与页范围）
  2. 按 locator 里的 NLC 编号 → 扫描 work/domestic 下 4 类 OCR 来源目录：
       a. month_20260728/pages/<NLC>/ocr/page-000N.ocr.md   （逐页，按 PDF 页号）
       b. minimax_machine_month_20260729/w3/rerun_ocr/<NLC>/page-000N.ocr.md
       c. minimax_domestic_evidence_v2_month_20260729/03_rerun_ocr/<NLC>/page-000N.ocr.md
       d. ocr_collection_phase4/<NLC>_*.ocr.md               （整期单文件）
  3. locator 里的「PDF第X—Y页 / 本地PDF第X页」页码 → 从候选目录挑对应页；无页码→整期全部页。
入库模式复用 apply_page_batch.py（documents + pages + page_fts + provenance + bigram FTS）。
--commit 才真正写库，默认 DRY-RUN。
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"

NLC_RE = re.compile(r"(NLC[0-9a-zA-Z_\-]+)")
OCR_DIR_CANDIDATES = [
    ROOT / "work" / "domestic" / "month_20260728" / "pages",
    ROOT / "work" / "domestic" / "minimax_machine_month_20260729" / "w3" / "rerun_ocr",
    ROOT / "work" / "domestic" / "minimax_domestic_evidence_v2_month_20260729" / "03_rerun_ocr",
    ROOT / "work" / "domestic" / "minimax_domestic_evidence_v2_month_20260729" / "04_variant_ocr",
    ROOT / "work" / "domestic" / "minmeng_wenxian_1946",
    ROOT / "work" / "domestic" / "MULTI_AGENT_SUPERLONG_TASK_20260801" / "16_MINIMAX_W2_TEXT_OCR_PILOT_20260801" / "P0_PILOT" / "ocr_md",
]
COLLECTION_DIR = ROOT / "work" / "domestic" / "ocr_collection_phase4"


def body_text(md_text: str) -> str:
    """从 OCR md 提取正文文本：去掉 markdown 头部与「# OCR 识别结果」等。"""
    lines = []
    for ln in md_text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith(("#", ">", "*", "-", "|", "```")):
            continue
        if re.match(r"^(来源文件|OCR 引擎|运行方式|生成时间|OCR 识别结果)", s):
            continue
        lines.append(s)
    return "\n".join(lines)


def build_nlc_index() -> dict[str, list[Path]]:
    """扫描全部 OCR 来源目录，建 NLC编号 -> [ocr 文件] 索引。"""
    idx: dict[str, list[Path]] = {}

    def add(base: Path, name: str, p: Path):
        key = name.split("_")[0]
        if not re.match(r"^NLC\d+-\d+", key):
            return
        idx.setdefault(key, []).append(p)

    # 逐页目录（含子目录 ocr/ 或直接放文件）
    for base in OCR_DIR_CANDIDATES:
        if not base.exists():
            continue
        for sub in base.iterdir():
            if not sub.is_dir():
                continue
            ocr_dir = sub / "ocr" if (sub / "ocr").exists() else sub
            for f in sorted(ocr_dir.glob("*.ocr.md")):
                # 只保留逐页 page-NNN.ocr.md，排除 tile 分块 / merged 合并 / 其他碎片
                if "-tile-" in f.name or ".merged." in f.name:
                    continue
                if not re.search(r"page-\d+\.ocr\.md$", f.name):
                    continue
                add(base, sub.name, f)
    return idx


def parse_pdf_pages(locator: str):
    """从 locator 提取正文 PDF 页码范围（如「PDF第2—3页」「本地PDF第1页」）。

    只匹配独立出现的「(本地)?PDF第X页」，排除「目录PDF第X页」「书内第X页」等。
    返回 1-based 页号列表；无正文页码时返回 None。
    """
    pages: set[int] = set()
    found = False
    for m in re.finditer(r"(?<!目录)(?:本地)?PDF\s*第\s*(\d+)\s*(?:[—–至到]\s*(\d+))?\s*页", locator or ""):
        found = True
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        for i in range(a, b + 1):
            pages.add(i)
    return sorted(pages) if found else None


def resolve_ocr_files(locator: str, nlc_idx: dict[str, list[Path]], source_url: str = "") -> list[str]:
    """解析候选的 OCR 文件相对路径列表。"""
    out: dict[str, Path] = {}

    def add(p: Path):
        if p.exists():
            out[str(p.relative_to(ROOT))] = p

    # 1) locator 直接引用 .ocr.md
    for raw in re.findall(r"([^\s;，,、；及至]+\.ocr\.md)", locator or ""):
        p = Path(raw.strip().strip("；;，,、及"))
        if not p.is_absolute():
            p = ROOT / p
        add(p)

    # 2) NLC 编号 → 来源目录（locator 优先，其次 source_url）
    nlcs = []
    url_decoded = unquote(source_url or "")
    for n in set(NLC_RE.findall(locator or "") + NLC_RE.findall(url_decoded)):
        n = n.split("_")[0]
        if re.match(r"^NLC\d+-\d+", n):
            nlcs.append(n)

    # 来源优先级：month_20260728 > w3/rerun_ocr > v2/03_rerun_ocr > 其他
    def src_rank(p: Path) -> int:
        s = str(p)
        if "month_20260728/pages" in s:
            return 0
        if "w3/rerun_ocr" in s:
            return 1
        if "03_rerun_ocr" in s:
            return 2
        return 3

    for nlc in nlcs:
        if nlc not in nlc_idx:
            continue
        files = sorted(nlc_idx[nlc], key=src_rank)
        pdf_pages = parse_pdf_pages(locator)
        if pdf_pages is not None:
            # 按 PDF 页号选页，同一页码只保留优先级最高的来源
            by_page: dict[int, Path] = {}
            for f in files:
                m = re.search(r"page-0*(\d+)\.ocr\.md$", f.name)
                if m and int(m.group(1)) in pdf_pages:
                    pg = int(m.group(1))
                    if pg not in by_page:
                        by_page[pg] = f
            if by_page:
                for pg in sorted(by_page):
                    add(by_page[pg])
                continue
        # 无页码或页码未匹配 → 全部加入（整期），去重后保留最高优先级
        seen: dict[str, Path] = {}
        for f in files:
            m = re.search(r"page-0*(\d+)\.ocr\.md$", f.name)
            key = m.group(1) if m else f.name
            if key not in seen:
                seen[key] = f
        for f in seen.values():
            add(f)
    return list(out.keys())


def _nlc_keys(text: str) -> set[str]:
    """从文本提取去重的 NLC 编号（截断中文/后缀部分）。"""
    out = set()
    for m in NLC_RE.finditer(text or ""):
        n = m.group(1).split("_")[0]
        if re.match(r"^NLC\d+-\d+", n):
            out.add(n)
    return out


def match_candidates(cur) -> tuple[list[dict], list[dict]]:
    """返回 (已入库候选, 可采候选)。已入库判定：locator 的 NLC 在 documents.title 中。"""
    doc_map = {}
    for r in cur.execute("SELECT id, title FROM documents WHERE source_platform='domestic'"):
        for n in _nlc_keys(r["title"] or ""):
            doc_map.setdefault(n, r["id"])

    nlc_idx = build_nlc_index()

    cands = cur.execute(
        "SELECT candidate_id, title, evidence_locator, source_url, online_availability, repository_name, document_date, document_type, creator, event_tags, person_tags, relevance_grade_accepted, authenticity_level_accepted, evidence_note "
        "FROM domestic_candidates WHERE check_outcome='pass'"
    ).fetchall()

    already, items = [], []
    for r in cands:
        loc = r["evidence_locator"] or ""
        nlc_hit = bool(_nlc_keys(loc) & set(doc_map))
        if nlc_hit:
            already.append(r["candidate_id"])
            continue
        if r["online_availability"] != "full_item_online":
            continue
        if "wikimedia" not in (r["source_url"] or ""):
            continue
        if ".pdf" not in (r["source_url"] or "") and not re.search(r"NLC\d+", r["source_url"] or ""):
            continue  # 图片类
        if "硬缺口" in (r["document_type"] or "") or "硬缺口" in (r["evidence_note"] or ""):
            continue  # 正文硬缺口候选不入库
        ocr_paths = resolve_ocr_files(loc, nlc_idx, r["source_url"] or "")
        missing = [p for p in re.findall(r"([^\s;，,、；及至]+\.ocr\.md)", loc) if not (ROOT / p).exists()]
        items.append({
            "candidate_id": r["candidate_id"],
            "title": r["title"],
            "date": r["document_date"],
            "repo": r["repository_name"],
            "source_url": r["source_url"],
            "doc_type": r["document_type"],
            "ocr_paths": ocr_paths,
            "missing_ocr": missing[:3],
            "locator": loc[:120],
        })
    return already, items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="真正写库")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    already, items = match_candidates(cur)
    with_ocr = [it for it in items if it["ocr_paths"]]
    no_ocr = [it for it in items if not it["ocr_paths"]]

    print(f"已入库候选(NLC 已在 documents): {len(already)}")
    print(f"可采候选总数: {len(items)}")
    print(f"  有现成 OCR 文件: {len(with_ocr)}")
    print(f"  无 OCR 文件(需重采): {len(no_ocr)}")
    print()

    if args.commit:
        from lib_ingest import ingest_items
        ingested = ingest_items(conn, with_ocr)
        print(f"已入库: {ingested}")
    else:
        print("=== DRY-RUN：有 OCR 的候选（全部）===")
        for it in with_ocr:
            print(f"  {it['candidate_id']}")
            print(f"    {str(it['title'])[:50]}")
            for op in it["ocr_paths"][:3]:
                print(f"      → {op}")
        print()
        print("无 OCR 候选:")
        for it in no_ocr:
            print(f"  {it['candidate_id']} | {str(it['title'])[:40]}")

    out = ROOT / "work" / "domestic" / "S3_BACKFILL_MANIFEST.json"
    out.write_text(json.dumps({
        "already_in_documents": len(already), "total": len(items),
        "with_ocr": len(with_ocr), "no_ocr": len(no_ocr),
        "items": items,
    }, ensure_ascii=False, indent=2))
    print(f"\n清单写入 {out.relative_to(ROOT)}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
