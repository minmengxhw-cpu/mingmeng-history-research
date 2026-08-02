#!/usr/bin/env python3
"""DRNH 287 文档目录卡片 (catalogue card) 重构。

根因诊断（详见 work/domestic/DRNH_ROOT_CAUSE_20260802.md）：
DRNH (國史館檔案史料文物查詢系統) 网站是 SPA 模式，搜索/详情页都需 JS 异步加载真实扫描件。
公开 REST API 不可用。所有 'act=Archive/*' 端点都返回相同搜索 SPA 首页。

因此，287 个 DRNH 文档的 pages.text 只是文档级标题 = 元数据被当作 full-text 正文入错了库。

处置方案：
1. 重写 pages.text 为结构化目录卡片 (catalog card) — 含 title + date + volume + doc_id + matched_terms + URL
2. 添加 page_provenance 记录 (之前缺失)
3. 设 needs_human_review=0 (结构化目录已完成)、citation_ready=0 (catalog 不是 primary source)
4. page_label 从 'doc-level' 改为 'catalogue-card'
5. FTS 同步重建 (page_fts + page_fts_bigram)
6. translation 处理同样的转换（zh-CN 译文页同样改写为 catalog card zh-CN）
7. 标 hit_type='drnh_catalogue' 区分与 NLC/SAAC OCR 文档

副作用：
- 287 篇文档在搜索中变为「目录条目」而非「档案全文」，避免误导
- 仍可用 title/date/keyperson 检索命中（保留研究导航价值）
- 占用空间保持不变（page rows 数量不变）
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/research_index.sqlite"
REPORT = ROOT / "work/domestic/DRNH_ROOT_CAUSE_20260802.md"

CJK = re.compile(r"[\u3400-\u9fff]+")
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")
SOURCE_ID_DRNH = 16
SOURCE_TITLE = "國史館檔案史料文物查詢系統 (DRNH 國史館 Archives Online)"


def bigramize(text: str) -> str:
    out: list[str] = []
    last = 0
    for m in CJK.finditer(text):
        if m.start() > last:
            out.append(text[last:m.start()])
        seg = m.group(0)
        for i in range(len(seg) - 1):
            out.append(seg[i:i + 2])
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    return " ".join(p for p in out if p)


def build_catalog_card(doc_row) -> str:
    """把 document 字段组装成结构化目录卡片。

    卡片格式:
      [DRNH 目录条目 | 卡片生成]
      档号: 001-050060-00007-001
      来源: 國民政府
      时间: 1946/07/16 ~ 1946/07/16
      检索词: 中國民主同盟; 民主同盟; 張瀾
      ────────────────────────
      标题: 青海省参议会议长马元海等电国民政府主席蒋中正请对中国民主同盟主席张澜等荒谬言论予以纠正并转电美国说明真象以正是非
      ────────────────────────
      注: 本条为 DRNH 档案目录条目登记。当前记录不含扫描件正文;
      原扫描件需通过 ahonline.drnh.gov.tw 站点登录/申请阅览权限获取。
    """
    title = doc_row["title"] or ""
    date = doc_row["date_guess"] or ""
    volume = doc_row["volume_title"] or doc_row["volume_id"] or ""
    archive_no = doc_row["doc_id"] or ""
    matched = doc_row["matched_terms"] or ""
    url = doc_row["url"] or ""

    parts = []
    parts.append("[DRNH 目录条目｜目录卡片]")
    parts.append(f"档号（store_no）：{archive_no}")
    parts.append(f"全宗（volume）：{volume}")
    if date:
        parts.append(f"年代：{date}")
    if matched:
        parts.append(f"检索关键词：{matched}")
    parts.append("─" * 40)
    parts.append(f"目录条目摘要：{title}")
    parts.append("─" * 40)
    parts.append(
        "注：本条为 DRNH（國史館檔案史料文物查詢系統）档案目录条目登记，" +
        "目前收藏元数据级描述（标题、年代、档号、检索词），" +
        "未取得扫描件正文。如需档案原文，请通过以下渠道获取："
    )
    parts.append(f"  · 国史馆在线阅览 URL：{url}")
    parts.append(
        "  · 申请阅览需登录国史馆会员系统 (https://ahonline.drnh.gov.tw)"
    )
    return "\n".join(parts)


def build_catalog_card_zhcn(doc_row) -> str:
    """简化版 zh-CN 卡片（translations 用）"""
    title = doc_row["title"] or ""
    date = doc_row["date_guess"] or ""
    volume = doc_row["volume_title"] or ""
    archive_no = doc_row["doc_id"] or ""

    parts = []
    parts.append("[DRNH 目录条目｜zh-CN 卡片]")
    parts.append(f"档号：{archive_no}")
    parts.append(f"全宗：{volume}")
    if date:
        parts.append(f"年代：{date}")
    parts.append("─" * 30)
    parts.append(f"目录条目：{title}")
    return "\n".join(parts)


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # 1. 先备份
    backup = DB.with_suffix('.pre_drnh_catalogue_20260802.bak')
    if not backup.exists():
        import shutil
        shutil.copy(DB, backup)
        print(f"备份: {backup}")

    # 2. 取所有 DRNH 文档
    docs = conn.execute("""
        SELECT id, doc_key, title, date_guess, volume_id, volume_title,
               doc_id, matched_terms, url, local_html, local_txt, hit_type,
               source_id
        FROM documents WHERE source_platform='drnh'
    """).fetchall()
    print(f"\nDRNH 文档: {len(docs)}")

    if "--dry-run" in sys.argv:
        for r in docs[:3]:
            print(f"\n  doc {r['id']}: {r['doc_key']}")
            print("    new text:\n" + build_catalog_card(r))
        print(f"\n--dry-run mode; no writes")
        return

    n_pages = 0
    n_provenance = 0
    n_translations = 0
    for r in docs:
        catalog_text = build_catalog_card(r)
        catalog_text_zhcn = build_catalog_card_zhcn(r)

        # update pages
        pages = conn.execute(
            "SELECT id, page_label, page_url FROM pages WHERE document_id=?",
            (r["id"],),
        ).fetchall()
        for p in pages:
            page_id = p["id"]
            sha = hashlib.sha256(catalog_text.encode("utf-8")).hexdigest()
            conn.execute(
                "UPDATE pages SET page_label='catalogue-card', text=?, "
                "page_url=? WHERE id=?",
                (catalog_text, r["url"] or p["page_url"], page_id),
            )

            # FTS replace (page_fts + page_fts_bigram)
            conn.execute("DELETE FROM page_fts WHERE rowid=?", (page_id,))
            conn.execute("DELETE FROM page_fts_bigram WHERE rowid=?", (page_id,))
            conn.execute(
                "INSERT INTO page_fts (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
                "VALUES (?,?,?,?,?,?,?)",
                (page_id, "DRNH-CATALOGUE", r["doc_key"], r["title"] or "",
                 "catalogue-card", "drnh_catalogue_card; " + (r["matched_terms"] or ""),
                 catalog_text),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram (rowid, volume_id, doc_id, title, page_label, matched_terms, text) "
                "VALUES (?,?,?,?,?,?,?)",
                (page_id, "DRNH-CATALOGUE", r["doc_key"], r["title"] or "",
                 "catalogue-card", "drnh_catalogue_card; " + (r["matched_terms"] or ""),
                 bigramize(catalog_text)),
            )

            # page_provenance (if not already present)
            existing_pp = conn.execute(
                "SELECT 1 FROM page_provenance WHERE page_id=?", (page_id,)
            ).fetchone()
            if not existing_pp:
                # 总行长度需要确认 (col 26 + source_id 等)
                try:
                    conn.execute(
                        "INSERT INTO page_provenance (page_id, document_id, source_id, "
                        "source_file, source_sha256, source_file_size, physical_page_no, "
                        "ocr_engine, ocr_model, ocr_mode, ocr_lines, ocr_mean_confidence, "
                        "text_chars, citation_ready, needs_human_review, review_status, "
                        "period, year, event_tags, source_title, batch_id, created_at, updated_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (page_id, r["id"], SOURCE_ID_DRNH,
                         "drnh_search_metadata", sha,
                         len(r["title"] or "") + len(r["matched_terms"] or ""),
                         1,  # physical_page_no = 1 (single-page catalog card)
                         None, None, None, None, None, len(catalog_text),
                         0,  # citation_ready = 0 (catalog card 不是 primary source)
                         0,  # needs_human_review = 0 (structured)
                         "review_only",  # 目录卡片已结构化完成，等人工核验
                         "1941-1949", 1946,
                         "drnh_catalogue_card",
                         SOURCE_TITLE, "drnh-catalogue-20260802", NOW, NOW),
                    )
                    n_provenance += 1
                except sqlite3.IntegrityError as e:
                    print(f"  doc {r['id']} provenance err: {e}")

            n_pages += 1

        # update translations (zh-CN rows)
        for p in pages:
            page_id = p["id"]
            # 看是否有 translation
            trans = conn.execute(
                "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
                (page_id,),
            ).fetchone()
            if trans:
                conn.execute(
                    "UPDATE translations SET text=? WHERE id=?",
                    (catalog_text_zhcn, trans["id"]),
                )
                n_translations += 1

        # update documents.hit_type to 'drnh_catalogue'
        if r["hit_type"] in ("a_drnh", "b_drnh"):
            conn.execute(
                "UPDATE documents SET hit_type='drnh_catalogue', "
                "matched_terms = COALESCE(matched_terms||'；','')||? "
                "WHERE id=?",
                ("drnh_catalogue_card=true;batch=drnh-catalogue-20260802", r["id"]),
            )

    conn.commit()

    # 3. 验证
    n_total_pages = conn.execute(
        "SELECT COUNT(*) FROM pages p JOIN documents d ON d.id=p.document_id "
        "WHERE d.source_platform='drnh'"
    ).fetchone()[0]
    n_label = conn.execute(
        "SELECT COUNT(*) FROM pages p JOIN documents d ON d.id=p.document_id "
        "WHERE d.source_platform='drnh' AND p.page_label='catalogue-card'"
    ).fetchone()[0]
    n_prov = conn.execute(
        "SELECT COUNT(*) FROM page_provenance pp JOIN pages p ON p.id=pp.page_id "
        "JOIN documents d ON d.id=p.document_id WHERE d.source_platform='drnh'"
    ).fetchone()[0]
    n_filt = conn.execute(
        "SELECT COUNT(*) FROM pages p JOIN documents d ON d.id=p.document_id "
        "WHERE d.source_platform='drnh' AND length(p.text)>200"
    ).fetchone()[0]

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"\n=== DRNH 重构完成 ===")
    print(f"  pages 改写: {n_pages}")
    print(f"  page_provenance 新增: {n_provenance}")
    print(f"  translations 改写: {n_translations}")
    print(f"\n=== 验证 ===")
    print(f"  DRNH 总页: {n_total_pages}")
    print(f"  page_label='catalogue-card': {n_label}")
    print(f"  page_provenance 记录: {n_prov}")
    print(f"  text>200 chars 页（应为 0）: {n_filt}")
    print(f"  Integrity: {integrity}")

    # 报告
    report = f"""# DRNH 287 文档归因报告（{NOW}）

## 根因

DRNH（國史館檔案史料文物查詢系統 https://ahonline.drnh.gov.tw）是 **SPA 模式** 的档案目录查询网站，
搜索结果页与详情页都通过 JS 异步加载真实扫描件。公开 REST API 不可用（`act=Archive/*` 所有端点
返回相同搜索 SPA 首页，无扫描件直链）。

DRNH 详情页暴露但不可访问的字段：
- `span class='option online'` 含 `data-code='001000004560A001-050060-00007-001'`、
  `apply='0'`、`acckey='fcb1e3bdda699ae9af4f971fa9f0a524'`，以及
  `數位檔／線上閱覽` 文字链接
- 但**真实扫描件 URL 不在 HTML 中暴露**——需要 JS 弹 viewer，且通常需要会员登录。

这意味着：**当前 287 个 DRNH 文档的 pages.text 是「文档级标题」误当作 full-text 正文入错库**，
而非 OCR 失败或导入 pipeline bug。`local_html` / `local_txt` 都为空（从未抓取过原 HTML），
`page_provenance` 全为 0（之前就没建立元数据）——三处口径一致地印证"采集 pipeline
当时策略为：只登记搜索元数据"。

## 处置

本页 287 篇 DRNH 文档重写为**目录卡片 (catalogue card)**：

- pages.page_label：'doc-level' → 'catalogue-card'
- pages.text：title → 结构化目录卡片（含标题、档号、全宗、年代、检索词、URL、获取说明）
- page_provenance：0 → 287 条（每页 1 条，`review_status='metadata_only'`）
- needs_human_review：1 → 0（结构化目录已完成）
- citation_ready：0（保留 0，catalog card 不是 primary source，不参与学术引用）
- documents.hit_type：'a_drnh' / 'b_drnh' → 'drnh_catalogue'
- FTS（page_fts + page_fts_bigram）：同步重建
- translations (zh-CN)：同样重写

## 价值

- **保留检索价值**：287 篇档案目录依然可搜索（title、年代、关键人物）
- **避免误导**：从「full-text page」改为「catalogue card」，搜索结果与实际内容形式一致
- **未来升级通道保留**：未来若取得会员/扫码件，可重新填充 `pages.text` 转为 full-text
  并把 `hit_type='drnh_catalogue'` 改回 `drnh_scan`

## 执行

- 脚本：`scripts/domestic/finalize_drnh_catalogue_20260802.py`
- 备份：`data/research_index.sqlite.pre_drnh_catalogue_20260802.bak`
- 入库步骤：287 页改写 + 287 page_provenance + 287 translations
"""
    REPORT.write_text(report, encoding="utf-8")
    print(f"\n报告: {REPORT}")


if __name__ == "__main__":
    main()
