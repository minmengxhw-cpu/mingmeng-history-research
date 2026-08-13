#!/usr/bin/env python3
"""Batch 13: re-OCR recommendations, stratified human sample, missing-provenance plan.

Read-only analysis. Does not run OCR. Does not write formal SQLite
(provenance stubs applied by batch13_migrate).
"""
from __future__ import annotations

import csv
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from _guard import guard

guard()
BASE = Path(__file__).resolve().parents[2]
AN = BASE / "work/deepseek-20260803/02_analysis"
OUT = AN
DB = Path(os.environ.get(
    "DEEPSEEK_FORMAL_DB",
    "/Users/cheer/Documents/mm agent/mingmeng-history-research/data/research_index.sqlite",
))


def recommend(code: str, engine: str, img_size: str, title: str) -> tuple[str, str, str, str]:
    """engine_suggestion, params, preprocess, note"""
    size = int(img_size) if str(img_size).isdigit() else None
    if code == "D0_EMPTY_HANDWRITING":
        return (
            "paddleocr-PP-OCRv4 / 可选专门手写模型试验",
            "det_db_box_thresh=0.3; use_angle_cls=true; drop_score=0.3; lang=ch",
            "灰度+轻度锐化；勿过度二值化（签到簿易丢笔迹）",
            "优先人工著录姓名关键字段；全页 OCR 仅作辅助",
        )
    if code in {"D0_EMPTY_NEEDS_REOCR", "D0_EMPTY_LIKELY_BLANK"}:
        return (
            "paddleocr-PP-OCRv4-server (重跑)",
            "det_db_box_thresh=0.4; use_angle_cls=true; drop_score=0.4",
            "若 size<50KB 先人工目检是否空白；空白则跳过 OCR",
            "空白页保留结构，不入正文检索",
        )
    if code == "D1_BINARY_GARBAGE":
        return (
            "N/A（先清伪文本）",
            "clear pages.text binary; attach image-only provenance",
            "下载原图后 OCR，禁止把 PNG 字节写入 text",
            "page_id=20623 为图片 URL 误当正文",
        )
    if code == "D6_OCR_GARBLED":
        eng = engine or "paddleocr"
        return (
            f"{eng} 重跑 + 版面方向校正",
            "use_angle_cls=true; det_limit_side_len=2048; drop_score=0.5",
            "deskew；竖排古籍/报纸试 use_space_char；双栏先切栏",
            "乱码页核验前 citation_ready 必须为 0",
        )
    return (
        "paddleocr 默认重跑",
        "use_angle_cls=true; drop_score=0.5",
        "标准预处理",
        "",
    )


def main() -> None:
    if not DB.exists() or DB.stat().st_size == 0:
        raise SystemExit(f"formal DB missing/empty: {DB}")

    reocr = list(csv.DictReader(open(AN / "short_pages_reocr_queue.csv", encoding="utf-8-sig")))
    refresh = list(csv.DictReader(open(AN / "short_pages_batch12_refresh.csv", encoding="utf-8-sig")))
    disp = {int(r["page_id"]): r for r in csv.DictReader(open(AN / "short_pages_dispositions.csv", encoding="utf-8-sig"))}

    # 1) re-OCR recommendation table
    rec_rows = []
    for r in reocr:
        eng_s, params, prep, note = recommend(
            r["disposition_code"], r.get("ocr_engine", ""), r.get("image_size_bytes", ""), r.get("title", "")
        )
        rec_rows.append({
            **{k: r[k] for k in [
                "page_id", "document_id", "doc_key", "title", "page_label", "text_length",
                "disposition_code", "reocr_priority", "image_path_resolved", "image_exists",
                "image_size_bytes", "ocr_engine",
            ]},
            "engine_suggestion": eng_s,
            "param_suggestion": params,
            "preprocess_suggestion": prep,
            "operator_note": note,
            "do_not_run_in_audit_branch": "yes",
            "citation_before_human_verify": "forbidden",
        })
    rec_fields = list(rec_rows[0].keys())
    with (OUT / "batch13_reocr_recommendations.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rec_fields)
        w.writeheader()
        w.writerows(rec_rows)

    # 2) stratified human sample checklist (target ~20)
    # buckets: empty(all6), handwriting already in empty, binary(1), library, issue, cover, ad, garbled, short_body
    by_code: dict[str, list] = defaultdict(list)
    for r in refresh:
        by_code[r["disposition_code"]].append(r)

    sample_plan = [
        ("D0_EMPTY_LIKELY_BLANK", 1),
        ("D0_EMPTY_NEEDS_REOCR", 1),
        ("D0_EMPTY_HANDWRITING", 2),
        ("D1_BINARY_GARBAGE", 1),
        ("D2_LIBRARY_STAMP", 2),
        ("D3_ISSUE_HEADER", 2),
        ("D4_COVER_TITLE", 2),
        ("D5_AD_OR_CARTOON", 2),
        ("D6_OCR_GARBLED", 4),
        ("D7_SHORT_BODY_CANDIDATE", 5),
    ]
    samples = []
    for code, n in sample_plan:
        pool = sorted(by_code.get(code, []), key=lambda x: int(x["page_id"]))
        # prefer citation conflict or high reocr priority if available
        pool = sorted(
            pool,
            key=lambda x: (
                0 if x.get("citation_ready_conflict") == "yes" else 1,
                -int(x.get("reocr_priority") or 0),
                int(x["page_id"]),
            ),
        )
        for r in pool[:n]:
            samples.append({
                "sample_id": f"S13-{len(samples)+1:02d}",
                "page_id": r["page_id"],
                "document_id": r["document_id"],
                "doc_key": r["doc_key"],
                "title": r["title"],
                "page_label": r["page_label"],
                "text_length": r["text_length"],
                "disposition_code": r["disposition_code"],
                "batch7_bucket": r["batch7_bucket"],
                "image_path_resolved": r["image_path_resolved"],
                "page_url": r["page_url"],
                "text_excerpt": r["text_excerpt"],
                "check_items": "影像是否存在|OCR是否完整|是否正文|是否可引用|建议动作",
                "human_result": "",
                "human_reviewer": "",
                "human_reviewed_at": "",
                "human_notes": "",
            })

    with (OUT / "batch13_human_sample_checklist.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(samples[0].keys()))
        w.writeheader()
        w.writerows(samples)

    # 3) missing provenance plan for 11 short pages + broader count
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    no_prov_short = [r for r in refresh if r["citation_ready"] == ""]
    broader = con.execute(
        """
        SELECT count(*) FROM pages p
        JOIN documents d ON d.id=p.document_id
        LEFT JOIN page_provenance pp ON pp.page_id=p.id
        WHERE d.source_platform='domestic' AND pp.page_id IS NULL
        """
    ).fetchone()[0]

    stub_rows = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for r in no_prov_short:
        pid = int(r["page_id"])
        page = con.execute(
            "SELECT id, document_id, page_label, page_url, length(trim(coalesce(text,''))) n, text FROM pages WHERE id=?",
            (pid,),
        ).fetchone()
        doc = con.execute(
            "SELECT id, doc_key, title, hit_type, url, source_platform FROM documents WHERE id=?",
            (page["document_id"],),
        ).fetchone()
        # page number guess from label
        label = page["page_label"] or ""
        m = re.search(r"(\d+)", label)
        pdf_page = int(m.group(1)) if m else None
        is_binary = (page["text"] or "").startswith("�PNG") or (page["text"] or "").startswith("\x89PNG")
        stub_rows.append({
            "page_id": pid,
            "document_id": page["document_id"],
            "doc_key": doc["doc_key"],
            "title": doc["title"],
            "page_label": label,
            "text_length": page["n"],
            "disposition_code": disp[pid]["disposition_code"],
            "source_id": "domestic-pilot-missing-prov",
            "source_file": page["page_url"] or doc["url"] or "",
            "page_image_path": page["page_url"] or "",
            "pdf_page_no": pdf_page if pdf_page is not None else "",
            "physical_page_no": pdf_page if pdf_page is not None else "",
            "ocr_engine": "unknown-pre-provenance",
            "ocr_mode": "legacy_import_without_provenance",
            "text_chars": page["n"],
            "citation_ready": 0,
            "needs_human_review": 1,
            "review_status": "review_only",
            "machine_review_note": (
                f"DeepSeek Batch13 provenance stub for short page lacking page_provenance; "
                f"disposition={disp[pid]['disposition_code']}; citation_ready forced 0"
                + ("; BINARY_GARBAGE_TEXT_CLEAR_RECOMMENDED" if is_binary else "")
            ),
            "batch_id": "deepseek-batch13-20260807",
            "period": "1941-1950",
            "clear_binary_text": "yes" if is_binary else "no",
            "created_at": now,
            "updated_at": now,
            "action": "INSERT_STUB",
        })
    con.close()

    stub_fields = list(stub_rows[0].keys())
    with (OUT / "batch13_missing_provenance_stubs.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=stub_fields)
        w.writeheader()
        w.writerows(stub_rows)

    # Report
    code_c = Counter(r["disposition_code"] for r in reocr)
    prio_c = Counter(r["reocr_priority"] for r in reocr)
    lines = [
        "# Batch 13 · 重 OCR 建议 / 人工抽检 / 无 provenance 补档计划",
        "",
        f"- 正式库只读路径：`{DB}`",
        f"- 生成时间：{now}",
        f"- 重 OCR 队列：**{len(reocr)}**（priority≥2，来自 Batch12）",
        f"- 人工抽检样本：**{len(samples)}**",
        f"- 短页无 provenance 拟补桩：**{len(stub_rows)}**",
        f"- 国内页无 provenance 全量（观察）：**{broader}**（本批仅处理短页 11 条）",
        f"- **本批不执行 OCR**（审计分支约束）",
        "",
        "## 重 OCR 队列构成",
        "",
        "| disposition | 数量 |",
        "|---|---:|",
    ]
    for k, v in sorted(code_c.items(), key=lambda x: -x[1]):
        lines.append(f"| {k} | {v} |")
    lines += ["", "| priority | 数量 |", "|---:|---:|"]
    for k, v in sorted(prio_c.items(), key=lambda x: -int(x[0])):
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## 引擎与参数总则",
        "",
        "1. 默认引擎：现网已用 PaddleOCR；重跑建议 PP-OCRv4 + `use_angle_cls=true`。",
        "2. 手写签到（4 页）：降低 det 阈值、保留灰度，优先人工著录人名。",
        "3. 空文本大图（1 页）：标准重跑；空文本小图（1 页）：先目检是否空白。",
        "4. 乱码 64 页：提高 `det_limit_side_len`、deskew；报纸双栏先切栏。",
        "5. 二进制伪文本：先清 `pages.text`，再按图 OCR。",
        "6. 任何重 OCR 结果须重新过 citation 门禁；默认 `citation_ready=0`。",
        "",
        "## 人工抽检样本分层",
        "",
        "| sample_id | page_id | code | title |",
        "|---|---:|---|---|",
    ]
    for s in samples:
        title = (s["title"] or "")[:40].replace("|", "/")
        lines.append(f"| {s['sample_id']} | {s['page_id']} | {s['disposition_code']} | {title} |")

    lines += [
        "",
        "## 无 provenance 短页 11 条",
        "",
        "| page_id | code | clear_binary | doc_key |",
        "|---:|---|---|---|",
    ]
    for r in stub_rows:
        lines.append(
            f"| {r['page_id']} | {r['disposition_code']} | {r['clear_binary_text']} | `{r['doc_key']}` |"
        )

    lines += [
        "",
        "## 产出",
        "",
        "- `batch13_reocr_recommendations.csv`",
        "- `batch13_human_sample_checklist.csv`",
        "- `batch13_missing_provenance_stubs.csv`",
        "- `batch13_short_pages_ops_report.md`（本文件）",
        "",
        "## 迁移（batch13_migrate）",
        "",
        "- 为 11 条短页插入 `page_provenance` 桩（citation_ready=0, needs_human_review=1）",
        "- 对 page_id=20623 清空 PNG 伪文本（若仍存在）",
        "- 不跑 OCR、不晋升 citation",
        "",
    ]
    (OUT / "batch13_short_pages_ops_report.md").write_text("\n".join(lines), encoding="utf-8")
    print({
        "reocr": len(reocr),
        "samples": len(samples),
        "stubs": len(stub_rows),
        "domestic_no_prov_all": broader,
        "reocr_by_code": dict(code_c),
    })


if __name__ == "__main__":
    main()
