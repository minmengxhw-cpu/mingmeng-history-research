#!/usr/bin/env python3
"""Batch 12: refresh short-page queue and deep-disposition Q0 + Q3/Q4 priority pages.

Read-only against formal SQLite. Produces disposition CSVs and a re-OCR queue.
Does not OCR and does not write the formal DB (demotion is Batch12 migrate).
"""
from __future__ import annotations

import csv
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from _guard import guard

guard()
BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "work/deepseek-20260803/02_analysis"
OUT.mkdir(parents=True, exist_ok=True)
DB = Path(os.environ.get(
    "DEEPSEEK_FORMAL_DB",
    "/Users/cheer/Documents/mm agent/mingmeng-history-research/data/research_index.sqlite",
))
# Formal DB lives outside this worktree; resolve relative image paths against that root.
DB_ROOT = DB.resolve().parents[1]  # .../mingmeng-history-research

LIBRARY_STAMP = re.compile(r"(上海图书馆藏书|上海圖書館藏書|A541\s*212|藏书号|索书号)", re.I)
ISSUE_HEADER = re.compile(r"^(年|第|卷|期|\d|\s|·|\.)+$")
BINARY_GARBAGE = re.compile(r"^[\x00-\x08\x0b\x0c\x0e-\x1f]|^\x89PNG|^%PDF|^\xFF\xD8\xFF|JFIF|IHDR")
OCR_ARTIFACT = re.compile(r"month-task-ocr-complete|<!--\s*month-task")
GARBLE_MARKERS = re.compile(r"[?？「」\[\]{}|\\~`^]{2,}|[A-Za-z]{1}\s+[A-Za-z]{1}\s+[A-Za-z]{1}")
COVER_MARKERS = re.compile(r"(封面|封底|版权|版權|出版|編印|编印|藏書|藏书|言論集|文献|文獻)")
AD_MARKERS = re.compile(r"(方成|木刻|漫画|漫畫|稿投迎歡|各大藥房|廣告|广告)")
HANDWRITING_HINT = re.compile(r"(签到|簽到|签名|簽名|名单|名單|手写|手寫)")


def local_path_from_url(page_url: str | None, source_file: str | None, image_path: str | None) -> Path | None:
    for raw in (image_path, source_file, page_url):
        if not raw:
            continue
        s = raw.strip()
        if s.startswith("file://"):
            p = Path(unquote(urlparse(s).path))
            return p
        p = Path(s)
        if p.is_absolute():
            return p
        # relative to formal project root
        cand = (DB_ROOT / s).resolve()
        return cand
    return None


def classify_batch7(page_label: str, hit_type: str, text: str, n: int) -> str:
    blob = f"{page_label} {hit_type} {text[:500]}".lower()
    if not text.strip():
        return "Q0_EMPTY"
    if "catalogue" in blob or any(x in blob for x in ("目录", "书目", "档号", "全宗", "获取说明", "检索词")):
        return "Q1_CATALOG"
    if page_label.lower() in {"cover", "front", "封面", "封底", "目录页"}:
        return "Q2_STRUCTURAL"
    if ("ocr" in blob or "paddle" in blob or "识别" in blob) and n < 60:
        return "Q3_OCR_SUSPECT"
    if n < 30:
        return "Q4_FRAGMENT"
    return "Q5_SHORT_REVIEW"


def deep_disposition(
    *,
    text: str,
    n: int,
    title: str,
    page_label: str,
    hit_type: str,
    img_exists: bool | None,
    img_size: int | None,
    citation_ready: int | None,
    ocr_lines: int | None,
) -> tuple[str, str, str, str, int]:
    """Return (code, label, action, citation_eligible, reocr_priority 0-3)."""
    blob = f"{title} {page_label} {text}"
    if n == 0:
        if img_exists is False:
            return (
                "D0_EMPTY_MISSING_IMAGE",
                "空文本且影像缺失",
                "修复源文件路径或重新导入影像；citation 禁止",
                "no",
                3,
            )
        if img_size is not None and img_size < 50000:
            return (
                "D0_EMPTY_LIKELY_BLANK",
                "空文本且影像偏小（疑似空白/低信息页）",
                "保留结构页；低优先级重 OCR；citation 禁止",
                "no",
                1,
            )
        if HANDWRITING_HINT.search(blob):
            return (
                "D0_EMPTY_HANDWRITING",
                "空文本且题名/语境提示签到手写",
                "高优先级手写/版式 OCR 或人工著录要点；citation 禁止",
                "no",
                3,
            )
        return (
            "D0_EMPTY_NEEDS_REOCR",
            "空文本但有影像（OCR 失败）",
            "高优先级重 OCR；核验前 citation 禁止",
            "no",
            3,
        )

    if BINARY_GARBAGE.search(text) or text.startswith("�PNG") or "PNG" in text[:8]:
        return (
            "D1_BINARY_GARBAGE",
            "正文槽位写入二进制/图片头",
            "清空伪文本并改挂影像 provenance；citation 禁止",
            "no",
            0,
        )

    if LIBRARY_STAMP.search(text) and n < 80:
        return (
            "D2_LIBRARY_STAMP",
            "馆藏章/索书号页",
            "保留结构用途；不作为正文证据；citation 禁止",
            "no",
            0,
        )

    stripped = re.sub(r"\s+", "", text)
    if ISSUE_HEADER.match(stripped) or re.fullmatch(r"[年第卷期\d·.\s]{1,20}", text):
        return (
            "D3_ISSUE_HEADER",
            "卷期封面标题行",
            "保留刊期定位；不作为正文引用",
            "no",
            0,
        )

    if COVER_MARKERS.search(text) and n < 80 and not re.search(r"[。！？；]{1}", text):
        return (
            "D4_COVER_TITLE",
            "封面/版权/题名页短文本",
            "结构保留；citation 禁止（可用作题名辅助）",
            "no",
            0,
        )

    if AD_MARKERS.search(text) and n < 120:
        return (
            "D5_AD_OR_CARTOON",
            "广告/漫画/木刻页短文本",
            "非政论正文；citation 默认禁止",
            "no",
            0,
        )

    if OCR_ARTIFACT.search(text) or (n < 60 and GARBLE_MARKERS.search(text)):
        return (
            "D6_OCR_GARBLED",
            "OCR 乱码/截断/伪完成标记",
            "重 OCR 或人工对照影像；citation 禁止",
            "no",
            2,
        )

    if n < 30:
        return (
            "D6_OCR_GARBLED",
            "极短碎片（无法独立引用）",
            "对照影像判断截断/图注；citation 禁止",
            "no",
            2,
        )

    # Q5 zone: 30-119 chars of seemingly body-like text
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    if cjk >= max(20, int(n * 0.45)) and not GARBLE_MARKERS.search(text):
        return (
            "D7_SHORT_BODY_CANDIDATE",
            "短正文候选（需人工抽检影像）",
            "人工对照影像确认完整性后，方可个案解除 citation 禁令",
            "no",
            1,
        )

    return (
        "D6_OCR_GARBLED",
        "短文本质量不足（乱码或信息密度低）",
        "重 OCR 或人工复核；citation 禁止",
        "no",
        2,
    )


def main() -> None:
    if not DB.exists() or DB.stat().st_size == 0:
        raise SystemExit(f"formal DB missing/empty: {DB}")

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT p.id AS page_id, p.document_id, d.doc_key, d.title, d.hit_type,
               d.url AS document_url, p.page_label, p.page_url,
               length(trim(coalesce(p.text,''))) AS text_length,
               replace(replace(substr(trim(coalesce(p.text,'')),1,240), char(10),' '), char(13),' ') AS text_excerpt,
               pp.citation_ready, pp.needs_human_review, pp.review_status,
               pp.ocr_engine, pp.ocr_model, pp.ocr_lines, pp.ocr_mean_confidence,
               pp.source_file, pp.source_file_size, pp.page_image_path,
               pp.batch_id, pp.machine_review_note
        FROM pages p
        JOIN documents d ON d.id = p.document_id
        LEFT JOIN page_provenance pp ON pp.page_id = p.id
        WHERE d.source_platform = 'domestic'
          AND length(trim(coalesce(p.text,''))) < 120
        ORDER BY
          CASE WHEN length(trim(coalesce(p.text,''))) = 0 THEN 0
               WHEN length(trim(coalesce(p.text,''))) < 30 THEN 1
               WHEN coalesce(pp.citation_ready,0) = 1 THEN 2
               ELSE 3 END,
          p.document_id, p.id
        """
    ).fetchall()
    con.close()

    out_rows: list[dict] = []
    for r in rows:
        text = r["text_excerpt"] or ""
        n = int(r["text_length"] or 0)
        b7 = classify_batch7(r["page_label"] or "", r["hit_type"] or "", text, n)
        img = local_path_from_url(r["page_url"], r["source_file"], r["page_image_path"])
        img_exists = img.exists() if img else None
        img_size = img.stat().st_size if img and img.exists() else (
            int(r["source_file_size"]) if r["source_file_size"] is not None else None
        )
        code, label, action, cite, prio = deep_disposition(
            text=text,
            n=n,
            title=r["title"] or "",
            page_label=r["page_label"] or "",
            hit_type=r["hit_type"] or "",
            img_exists=img_exists,
            img_size=img_size,
            citation_ready=r["citation_ready"],
            ocr_lines=r["ocr_lines"],
        )
        cr = r["citation_ready"]
        conflict = int(cr == 1)  # any short page with citation_ready=1 is a conflict under Batch7 gate
        out_rows.append(
            {
                "page_id": r["page_id"],
                "document_id": r["document_id"],
                "doc_key": r["doc_key"],
                "title": r["title"],
                "hit_type": r["hit_type"],
                "page_label": r["page_label"],
                "page_url": r["page_url"],
                "text_length": n,
                "text_excerpt": text,
                "batch7_bucket": b7,
                "disposition_code": code,
                "disposition_label": label,
                "recommended_action": action,
                "citation_eligible": cite,
                "reocr_priority": prio,
                "citation_ready": "" if cr is None else cr,
                "needs_human_review": "" if r["needs_human_review"] is None else r["needs_human_review"],
                "review_status": r["review_status"] or "",
                "ocr_engine": r["ocr_engine"] or "",
                "ocr_lines": "" if r["ocr_lines"] is None else r["ocr_lines"],
                "image_path_resolved": str(img) if img else "",
                "image_exists": "" if img_exists is None else ("yes" if img_exists else "no"),
                "image_size_bytes": "" if img_size is None else img_size,
                "citation_ready_conflict": "yes" if conflict else "no",
                "demote_citation_ready": "yes" if conflict else "no",
                "priority_queue": (
                    "P0_EMPTY" if b7 == "Q0_EMPTY"
                    else "P1_OCR_OR_FRAGMENT" if b7 in {"Q3_OCR_SUSPECT", "Q4_FRAGMENT"}
                    else "P2_SHORT_BODY"
                ),
                "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )

    fields = list(out_rows[0].keys()) if out_rows else []
    refresh_path = OUT / "short_pages_batch12_refresh.csv"
    with refresh_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    # Priority queue: Q0 + Q3 + Q4 (and all citation conflicts)
    priority = [
        r for r in out_rows
        if r["priority_queue"] in {"P0_EMPTY", "P1_OCR_OR_FRAGMENT"} or r["citation_ready_conflict"] == "yes"
    ]
    with (OUT / "short_pages_priority_queue.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(priority)

    reocr = [r for r in out_rows if int(r["reocr_priority"]) >= 2]
    reocr_fields = [
        "page_id", "document_id", "doc_key", "title", "page_label", "text_length",
        "disposition_code", "reocr_priority", "image_path_resolved", "image_exists",
        "image_size_bytes", "ocr_engine", "recommended_action",
    ]
    with (OUT / "short_pages_reocr_queue.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=reocr_fields)
        w.writeheader()
        w.writerows({k: r[k] for k in reocr_fields} for r in sorted(reocr, key=lambda x: (-int(x["reocr_priority"]), x["page_id"])))

    demote = [r for r in out_rows if r["demote_citation_ready"] == "yes"]
    demote_fields = [
        "page_id", "document_id", "doc_key", "title", "page_label", "text_length",
        "disposition_code", "citation_ready", "review_status", "text_excerpt", "recommended_action",
    ]
    with (OUT / "short_pages_citation_demote.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=demote_fields)
        w.writeheader()
        w.writerows({k: r[k] for k in demote_fields} for r in demote)

    # Compact disposition table (all 220)
    disp_fields = [
        "page_id", "document_id", "doc_key", "batch7_bucket", "disposition_code",
        "disposition_label", "priority_queue", "reocr_priority", "citation_eligible",
        "citation_ready_conflict", "demote_citation_ready", "text_length", "recommended_action",
    ]
    with (OUT / "short_pages_dispositions.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=disp_fields)
        w.writeheader()
        w.writerows({k: r[k] for k in disp_fields} for r in out_rows)

    # Report
    b7c = Counter(r["batch7_bucket"] for r in out_rows)
    dc = Counter(r["disposition_code"] for r in out_rows)
    pq = Counter(r["priority_queue"] for r in out_rows)
    empty = [r for r in out_rows if r["batch7_bucket"] == "Q0_EMPTY"]
    conflicts = len(demote)
    no_prov = sum(1 for r in out_rows if r["citation_ready"] == "")

    lines = [
        "# Batch 12 · 短页面队列复核与深层处置",
        "",
        f"- 正式库只读路径：`{DB}`",
        f"- 刷新时间：{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- 短页面总数：**{len(out_rows)}**（与 Batch7 对齐）",
        f"- 优先队列（Q0+Q3+Q4 或 citation 冲突）：**{len(priority)}**",
        f"- 重 OCR 队列（priority≥2）：**{len(reocr)}**",
        f"- citation_ready=1 冲突待降级：**{conflicts}**",
        f"- 无 page_provenance：**{no_prov}**",
        "",
        "## Batch7 分层（刷新后）",
        "",
        "| 分层 | 数量 |",
        "|---|---:|",
    ]
    for k, v in sorted(b7c.items()):
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## 深层处置码",
        "",
        "| 处置码 | 数量 |",
        "|---|---:|",
    ]
    for k, v in sorted(dc.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## 优先队列",
        "",
        "| 队列 | 数量 |",
        "|---|---:|",
    ]
    for k, v in sorted(pq.items()):
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## P0 空文本 6 条明细",
        "",
        "| page_id | doc_key | page | 影像 | size | 处置 |",
        "|---:|---|---|---|---:|---|",
    ]
    for r in empty:
        lines.append(
            f"| {r['page_id']} | `{r['doc_key']}` | {r['page_label']} | {r['image_exists'] or 'n/a'} | "
            f"{r['image_size_bytes'] or ''} | {r['disposition_code']} |"
        )

    lines += [
        "",
        "## 处置规则（本批）",
        "",
        "1. **不晋升**：任何 text<120 页面不得新设 `citation_ready=1`。",
        "2. **应降级**：已是 `citation_ready=1` 的短页面一律降为 0，并标记 `needs_human_review=1`（见 migrate）。",
        "3. **空文本**：影像在则入重 OCR 队列；影像 <50KB 标为疑似空白；签到类标手写优先。",
        "4. **二进制伪文本**（如 PNG 头写入 text）：清理伪文本槽，不按正文引用。",
        "5. **馆藏章/卷期头/封面/广告**：结构保留，citation 禁止。",
        "6. **D7 短正文候选**：仅允许人工抽检后个案解除，本批仍 `citation_eligible=no`。",
        "7. 本分析脚本只读；正式库写入由 `deepseek_20260803_batch12_migrate.py` 执行。",
        "",
        "## 产出文件",
        "",
        "- `short_pages_batch12_refresh.csv` — 全量刷新",
        "- `short_pages_dispositions.csv` — 处置摘要",
        "- `short_pages_priority_queue.csv` — P0/P1 + citation 冲突",
        "- `short_pages_reocr_queue.csv` — 重 OCR 优先队列",
        "- `short_pages_citation_demote.csv` — 待降级 citation_ready 清单",
        "",
    ]
    (OUT / "batch12_short_pages_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(
        {
            "short_pages": len(out_rows),
            "batch7": dict(sorted(b7c.items())),
            "dispositions": dict(sorted(dc.items())),
            "priority": len(priority),
            "reocr": len(reocr),
            "demote": conflicts,
            "no_provenance": no_prov,
        }
    )


if __name__ == "__main__":
    main()
