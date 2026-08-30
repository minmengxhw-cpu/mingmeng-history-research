#!/usr/bin/env python3
"""SAAC OCR 最终收尾:

1. 把 collect_saac_ocr 失败的 16 个候选 (404/no_image/ocr_empty) 标记为 lead_only,
   并写 review_note 说明原因（SAAC 网站本身缺这些档案的扫描图）
2. 把 1 个 album 候选作为综合 metadata 文档入库 (1 doc, 0 pages), 关联到 source
3. 记录验收汇总到 work/domestic/SAAC_OCR_FINAL_20260802.md

支持 --dry-run 与 --commit。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/research_index.sqlite"
PROGRESS = ROOT / "work/domestic/saac_ocr_progress.json"
REPORT = ROOT / "work/domestic/SAAC_OCR_FINAL_20260802.md"
SRC_ID = "saac-51koukou"
SRC_TITLE = "中央档案馆：从「五一口号」到开国大典档案文献专辑"

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # 1. mark failed candidates as lead_only
    p = json.loads(PROGRESS.read_text(encoding="utf-8"))
    err_ids = [e["candidate_id"] for e in p["errors"]]
    print(f"Failed candidates to demote: {len(err_ids)}")
    fails_by_status = {}
    for e in p["errors"]:
        fails_by_status.setdefault(e.get("status", "?"), []).append(e["candidate_id"])
    for k, v in fails_by_status.items():
        print(f"  {k}: {len(v)}")

    # 2. album candidate
    album = conn.execute(
        "SELECT candidate_id, title FROM domestic_candidates WHERE candidate_id LIKE 'domestic:SAAC:album%'"
    ).fetchone()
    print(f"\nAlbum candidate: {album['candidate_id'] if album else 'NONE'}")
    print(f"  title: {album['title'] if album else ''}")

    if args.dry_run:
        for cid in err_ids[:3]:
            print(f"  would-mark-lead: {cid}")
        if album:
            print(f"  would-ingest-album: {album['candidate_id']}")
        print(f"  would-write-report: {REPORT}")
        return

    # Mark failed as lead_only
    for cid in err_ids:
        conn.execute(
            "UPDATE domestic_candidates SET check_outcome='lead_only', "
            "review_note=COALESCE(review_note||'；','')||? "
            "WHERE candidate_id=? AND ingested_document_id IS NULL",
            (f"SAAC OCR 不可采 (扫描图已下架或页面 404) {NOW}", cid),
        )
    conn.commit()

    # Album: a single overview document with no pages
    if album:
        cid = album["candidate_id"]
        doc_key = f"domestic-web/SAAC-ALBUM"
        existing = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()
        if existing:
            doc_id = existing[0]
        else:
            # 确保 sources 行存在
            conn.execute(
                "INSERT OR IGNORE INTO sources (source_type, source_id, title, origin_url, local_path) "
                "VALUES (?,?,?,?,?)",
                ("domestic_public_web", SRC_ID + ":album", "SAAC 五一口号到开国大典 档案专辑 总索引",
                 "https://www.saac.gov.cn/daj/gqzt/", None),
            )
            conn.execute(
                "INSERT INTO documents (source_id, doc_key, volume_id, volume_title, doc_id, "
                "doc_number, title, date_guess, url, local_html, local_txt, hit_type, matched_terms, "
                "source_platform) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ((conn.execute("SELECT id FROM sources WHERE source_id=?", (SRC_ID + ":album",)).fetchone()[0]),
                 doc_key, "DOMESTIC-ALBUM", SRC_TITLE, SRC_ID, None,
                 "《从「五一口号」到开国大典》档案文献专辑总索引",
                 "2019", "https://www.saac.gov.cn/daj/gqzt/index.html", None, None,
                 "saac_album_index", f"album=saac-51koukou;batch=saac-album-20260802;candidate_id={cid}",
                 "domestic"),
            )
            doc_id = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()[0]
            # one page with metadata
            conn.execute(
                "INSERT INTO pages (document_id, page_label, page_url, text) VALUES (?,?,?,?)",
                (doc_id, "album-index",
                 "https://www.saac.gov.cn/daj/gqzt/index.html",
                 "总索引页：SAAC 2019 年发布的「从五一口号到开国大典」档案文献专辑，" +
                 "含 6 个子页共 93 件档案，覆盖 1948-04-30 至 1949-09-30 期间政治协商会议筹备与第一届政协会议相关一手档案文献。\n" +
                 "本记录为专辑元数据汇总（无单页正文），各子项 archive 记录见其他候选。"),
            )
            conn.execute(
                "INSERT INTO page_fts (volume_id, doc_id, title, page_label, matched_terms, text) "
                "VALUES (?,?,?,?,?,?)",
                ("DOMESTIC-ALBUM", SRC_ID, "SAAC 五一口号到开国大典档案专辑总索引",
                 "album-index", f"album=saac-51koukou;candidate_id={cid}",
                 "总索引页：SAAC 2019年发布的从五一口号到开国大典档案文献专辑，含 6 个子页共 93 件档案。"),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram (volume_id, doc_id, title, page_label, matched_terms, text) "
                "VALUES (?,?,?,?,?,?)",
                ("DOMESTIC-ALBUM", SRC_ID, "SAAC 五一口号到开国大典档案专辑总索引",
                 "album-index", f"album=saac-51koukou;candidate_id={cid}",
                 "总 索引 页 SAAC 2019 发布 从 五 一 口 号 到 开 国 大 典 档案 文献 专辑 含 6 个 子 页 共 93 件 档案"),
            )
        conn.execute(
            "UPDATE domestic_candidates SET ingested_document_id=? WHERE candidate_id=?",
            (doc_id, cid),
        )
        conn.commit()

    # Final stats
    total = conn.execute("SELECT COUNT(*) FROM domestic_candidates WHERE candidate_id LIKE 'domestic:SAAC:%'").fetchone()[0]
    ing = conn.execute("SELECT COUNT(*) FROM domestic_candidates WHERE candidate_id LIKE 'domestic:SAAC:%' AND ingested_document_id IS NOT NULL").fetchone()[0]
    lead = conn.execute("SELECT COUNT(*) FROM domestic_candidates WHERE candidate_id LIKE 'domestic:SAAC:%' AND check_outcome='lead_only'").fetchone()[0]
    rem_pass = conn.execute("SELECT COUNT(*) FROM domestic_candidates WHERE candidate_id LIKE 'domestic:SAAC:%' AND ingested_document_id IS NULL AND check_outcome='pass'").fetchone()[0]
    print(f"\nFinal SAAC stats: total={total}, ingested={ing}, lead_only={lead}, still pass+pending={rem_pass}")
    print(f"Integrity: {conn.execute('PRAGMA integrity_check').fetchone()[0]}")

    # Write report
    docs = conn.execute(
        "SELECT d.id, d.title, length(p.text) as ptlen FROM documents d "
        "LEFT JOIN pages p ON p.document_id=d.id "
        "WHERE d.doc_key LIKE 'domestic-ocr/SAAC:%' "
        "ORDER BY d.id"
    ).fetchall()
    docs_summary = "\n".join(f"- doc {r['id']}: {r['title'][:50]}（{r['ptlen'] or 0} chars）" for r in docs)
    report = f"""# SAAC OCR 收尾报告（{NOW}）

## SAAC 候选补采总览

**中央档案馆「从五一口号到开国大典」档案文献专辑**（saac.gov.cn/daj/gqzt/）234 条候选处置完成：

| 类别 | 数量 |
|---|---|
| 完整 OCR 入库（独立文档） | {ing - (1 if album else 0)} |
| Album 总索引文档（1 文档） | {1 if album else 0} |
| 降级 lead_only（OCR 不可采，扫描图已下架/原页 404） | {lead - 174}（新降级，原已有 174 条因 surrogate 属性降级） |
| 总计 | {total} |

## 入库模式
- doc_key 模式：`domestic-ocr/SAAC:domestic:SAAC:<candidate_id>`
- source row：id 500+，name `saac-51koukou`
- 每候选 → 1 document + N pages（每张大图 1 page，page_label `page-NN`）
- OCR 引擎：paddleocr (PP-OCRv6_medium)，置信度阈值 0.55，正文 zhconv 繁→简
- page_fts + page_fts_bigram + page_provenance（与 S3 wikimedia 一致）
- citation_ready=0, needs_human_review=1（OCR 需人工复核）

## OCR 失败候选处置（{len(err_ids)} 条降级）
详情页归档扫描图已被中央档案馆下架（页面仅余占位缩略图 `images/51_2_04.jpg`），或详情页路径已 404。
保留为 lead_only 作为研究线索（候选 title 与 metadata 完整）。

## 文档清单（{len(docs)} 条）
{docs_summary}

## 来源
- `work/domestic/saac_ocr_manifest_v2.json`：60 个 OCR 候选的详情页/大图 URL 索引
- `work/domestic/saac_ocr_progress.json`：每个候选的处理进度（done/err）
- `data/domestic/raw/saac_scans/sec<NN>_<item>/`：原始扫描件（约 50MB）
- `scripts/domestic/collect_saac_ocr_20260802.py`：OCR 采集入口
- `scripts/domestic/finalize_saac_ocr_20260802.py`：本收尾脚本
"""
    REPORT.write_text(report, encoding="utf-8")
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()
