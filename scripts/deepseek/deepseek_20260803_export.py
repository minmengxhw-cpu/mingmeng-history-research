#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 国内证据审计 · 数据层导出（只读）
=============================================
职责：
  1. 从生产 SQLite（mode=ro）导出审计快照：
     - domestic documents（含 classification / provenance / pages 统计）
     - domestic_candidates 全部（accepted + needs_human_review）
     - document_classifications 孤儿（15 条）
     - research_events（国内相关 + 全量供关联分析）
     - domestic_sources / sources 注册表
  2. 从 MiniMax staging 导出：
     - staging.sqlite 的 staging_domestic_candidates / staging_domestic_sources / staging_dedup_clusters
     - 04_staging/*.csv（import_ready / needs_review / exclude）原样复制
     - 02_manifests/source_manifest.jsonl 原样复制
  3. data/domestic 既有结构化产物原样复制：
     - evidence_units.jsonl / evidence_unit_relations.jsonl / candidates.jsonl / source_registry.json
  4. 生成 inventory_reconciliation.json：对账报告（基线文档口径 vs 库口径）。

约束：
  - 只读打开生产库（URI mode=ro），任何路径都不写正式 SQLite。
  - 不修改任何原始数据文件，只复制快照。
"""
import csv
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]          # 基线仓库根
WORK = BASE / "work" / "deepseek-20260803"
INPUTS = WORK / "01_inputs"
INPUTS.mkdir(parents=True, exist_ok=True)

PROD_DB = Path(os.environ.get(
    "DEEPSEEK_PROD_DB",
    "/Users/cheer/Documents/mm agent/mingmeng-history-research/data/research_index.sqlite",
))
STAGING_DB = BASE / "work" / "minimax-20260803" / "04_staging" / "staging.sqlite"
STAGING_CSV_DIR = BASE / "work" / "minimax-20260803" / "04_staging"
MANIFESTS_DIR = BASE / "work" / "minimax-20260803" / "02_manifests"
DOMESTIC_DATA = BASE / "data" / "domestic"


def q(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()


def dump_rows(path, rows, headers):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  [ok] {path.relative_to(BASE)} ({len(rows)} rows)")


def main():
    if not PROD_DB.exists():
        sys.exit(f"production DB not found: {PROD_DB} (set DEEPSEEK_PROD_DB)")
    if not STAGING_DB.exists():
        sys.exit(f"staging DB not found: {STAGING_DB}")

    conn = sqlite3.connect(f"file:{PROD_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    sconn = sqlite3.connect(f"file:{STAGING_DB}?mode=ro", uri=True)
    sconn.row_factory = sqlite3.Row

    summary = {"produced_at": "2026-08-03", "source_db": str(PROD_DB),
               "counts": {}, "staging": {}}

    # ---- 1. domestic documents ----
    rows = q(conn, """
        SELECT d.id, d.doc_key, d.title, d.date_guess, d.url, d.hit_type,
               d.ingested_candidate_id, d.volume_title, d.volume_id, d.doc_id, d.doc_number,
               dc.grade AS class_grade, dc.score AS class_score, dc.needs_review AS class_needs_review,
               dc.reason AS class_reason,
               s.source_type AS source_type, s.source_id AS source_registry_id, s.title AS source_title,
               s.origin_url AS source_origin_url, s.local_path AS source_local_path,
               s2.sub AS sub_count,
               (SELECT COUNT(*) FROM page_provenance pp WHERE pp.document_id = d.id) AS prov_count
        FROM documents d
        JOIN sources s ON s.id = d.source_id
        LEFT JOIN document_classifications dc ON dc.document_id = d.id
        LEFT JOIN (SELECT document_id, COUNT(*) AS sub FROM pages GROUP BY document_id) s2 ON s2.document_id = d.id
        WHERE d.source_platform = 'domestic'
        ORDER BY d.id
    """)
    dump_rows(INPUTS / "domestic_documents.csv", [tuple(r) for r in rows],
              list(rows[0].keys()) if rows else [])
    summary["counts"]["domestic_documents"] = len(rows)

    # ---- 2. domestic_candidates 全部 ----
    rows = q(conn, "SELECT * FROM domestic_candidates ORDER BY id")
    dump_rows(INPUTS / "domestic_candidates.csv", [tuple(r) for r in rows],
              list(rows[0].keys()) if rows else [])
    summary["counts"]["candidates_total"] = len(rows)
    summary["counts"]["candidates_by_status"] = dict(
        q(conn, "SELECT review_status, COUNT(*) FROM domestic_candidates GROUP BY review_status"))

    # ---- 3. classification orphans ----
    rows = q(conn, """
        SELECT dc.document_id, dc.grade, dc.score, dc.needs_review, dc.reason
        FROM document_classifications dc
        WHERE NOT EXISTS (SELECT 1 FROM documents d WHERE d.id = dc.document_id)
        ORDER BY dc.document_id
    """)
    dump_rows(INPUTS / "classification_orphans.csv", [tuple(r) for r in rows],
              ["document_id", "grade", "score", "needs_review", "reason"])
    summary["counts"]["classification_orphans"] = len(rows)

    # ---- 4. research_events（全量 + 国内页）----
    rows = q(conn, "SELECT * FROM research_events ORDER BY id")
    dump_rows(INPUTS / "research_events_all.csv", [tuple(r) for r in rows],
              list(rows[0].keys()) if rows else [])
    summary["counts"]["events_total"] = len(rows)
    rows = q(conn, """
        SELECT re.* FROM research_events re
        JOIN pages p ON p.id = re.page_id
        JOIN documents d ON d.id = p.document_id
        WHERE d.source_platform = 'domestic'
        ORDER BY re.id
    """)
    dump_rows(INPUTS / "research_events_domestic.csv", [tuple(r) for r in rows],
              list(rows[0].keys()) if rows else [])
    summary["counts"]["events_domestic"] = len(rows)

    # ---- 5. sources 注册表 ----
    try:
        rows = q(conn, "SELECT * FROM domestic_sources ORDER BY id")
        dump_rows(INPUTS / "domestic_sources.csv", [tuple(r) for r in rows],
                  list(rows[0].keys()) if rows else [])
        summary["counts"]["domestic_sources"] = len(rows)
    except sqlite3.OperationalError as e:
        print("  [skip] domestic_sources:", e)
    rows = q(conn, "SELECT * FROM sources ORDER BY id")
    dump_rows(INPUTS / "sources_all.csv", [tuple(r) for r in rows],
              list(rows[0].keys()) if rows else [])
    summary["counts"]["sources_total"] = len(rows)

    conn.close()

    # ---- 6. staging DB ----
    tables = ["staging_domestic_candidates", "staging_domestic_sources",
              "staging_dedup_clusters"]
    for t in tables:
        try:
            rows = q(sconn, f"SELECT * FROM {t} ORDER BY id")
            dump_rows(INPUTS / f"{t}.csv", [tuple(r) for r in rows],
                      list(rows[0].keys()) if rows else [])
            summary["staging"][t] = len(rows)
        except sqlite3.OperationalError as e:
            print(f"  [skip] {t}: {e}")
    sconn.close()

    # ---- 7. staging CSV / manifests 原样复制 ----
    for f in ["import_ready.csv", "needs_review.csv", "exclude.csv"]:
        src = STAGING_CSV_DIR / f
        if src.exists():
            shutil.copy2(src, INPUTS / f"staging_{f}")
            print(f"  [copy] staging_{f}")
    for f in ["source_manifest.jsonl", "source_manifest_summary.md", "duplicate_report.csv",
              "duplicate_clusters.json"]:
        src = MANIFESTS_DIR / f
        if src.exists():
            shutil.copy2(src, INPUTS / f"manifest_{f}")
            print(f"  [copy] manifest_{f}")

    # ---- 8. data/domestic 既有产物原样复制 ----
    for f in ["evidence_units.jsonl", "evidence_unit_relations.jsonl",
              "candidates.jsonl", "source_registry.json"]:
        src = DOMESTIC_DATA / f
        if src.exists():
            shutil.copy2(src, INPUTS / f"snapshot_{f}")
            print(f"  [copy] snapshot_{f}")

    # ---- 9. 对账摘要 ----
    with open(INPUTS / "inventory_reconciliation.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\ninventory_reconciliation.json written")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
