#!/usr/bin/env python3
"""
国内资料生产线：三类清单（Phase 5）
==================================

读取 staging.sqlite，输出：
  - import_ready.csv — 可入库清单
  - needs_review.csv — 需复核清单
  - exclude.csv — 应排除清单（重复 / 拒收）

每个 CSV 包含字段：
  candidate_id, period, repository_code, repository_name, title, document_date,
  authenticity_level, evidence_grade, source_url, source_family, source_kind,
  citation_ready, review_status, catalog_reference, sha256, page_count,
  cluster_id, cluster_role, notes

输出至 work/minimax-20260803/04_staging/
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


def fetch_bucket(conn: sqlite3.Connection, bucket: str) -> list[dict]:
    cur = conn.execute(
        """SELECT
            candidate_id, period, repository_code, repository_name, title,
            document_date, authenticity_level_accepted, evidence_grade,
            source_url, source_family, source_kind, citation_ready,
            review_status, catalog_reference, sha256, page_count,
            cluster_id, cluster_role, cluster_size, source_kind,
            needs_ocr, evidence_note, uncertainty_note
        FROM staging_domestic_candidates
        WHERE staging_bucket = ?""",
        (bucket,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("(empty)\n", encoding="utf-8")
        return
    fieldnames = [
        "candidate_id", "period", "repository_code", "repository_name", "title",
        "document_date", "authenticity_level_accepted", "evidence_grade",
        "source_url", "source_family", "source_kind", "citation_ready",
        "review_status", "catalog_reference", "sha256", "page_count",
        "cluster_id", "cluster_role", "needs_ocr", "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = dict(r)
            row["notes"] = row.get("evidence_note") or row.get("uncertainty_note") or ""
            if row.get("citation_ready") is not None:
                row["citation_ready"] = "yes" if row["citation_ready"] else "no"
            if row.get("needs_ocr") is not None:
                row["needs_ocr"] = "yes" if row["needs_ocr"] else "no"
            for k in ("title", "repository_name", "catalog_reference", "evidence_note", "uncertainty_note"):
                row.pop(k, None)
            w.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("work/minimax-20260803/04_staging/staging.sqlite"))
    parser.add_argument("--out", type=Path, default=Path("work/minimax-20260803/04_staging"))
    args = parser.parse_args()

    out = args.out
    with sqlite3.connect(args.db) as conn:
        import_ready = fetch_bucket(conn, "import_ready")
        needs_review = fetch_bucket(conn, "needs_review")
        exclude = fetch_bucket(conn, "exclude")

    write_csv(out / "import_ready.csv", import_ready)
    write_csv(out / "needs_review.csv", needs_review)
    write_csv(out / "exclude.csv", exclude)

    # 三组分别分时期输出
    def by_period(rows):
        result = {}
        for r in rows:
            result.setdefault(r.get("period", "?"), []).append(r)
        return result

    # 简短 markdown 摘要
    rd = by_period(import_ready)
    nr = by_period(needs_review)
    ex = by_period(exclude)

    md = [
        "# 三类清单 ∙ 阶段汇总",
        "",
        "本轮 1941—1950 三个重点期。",
        "",
        "## 1. 可入库（import_ready）",
        "",
        f"共计 **{len(import_ready)}** 条",
        "",
        "| 时期 | 数量 |",
        "|---|---:|",
    ]
    for period in ["1941-1943", "1944-1945", "1946-1950"]:
        md.append(f"| {period} | {len(rd.get(period, []))} |")
    md.append(f"| **合计** | **{len(import_ready)}** |")

    md.append("")
    md.append("### 入库等级分布")
    md.append("")
    by_level = {}
    for r in import_ready:
        lvl = r.get("authenticity_level_accepted") or "?"
        by_level[lvl] = by_level.get(lvl, 0) + 1
    for k, v in sorted(by_level.items()):
        md.append(f"- {k}: {v}")

    md.append("")
    md.append("### 可被引用（citation_ready=yes）")
    md.append("")
    cit = sum(1 for r in import_ready if r.get("citation_ready") == 1)
    md.append(f"- 共 **{cit}** 条可直接进 citation 级（其余仅可作为线索 / 检索）")

    md.append("")
    md.append("## 2. 需复核（needs_review）")
    md.append("")
    md.append(f"共计 **{len(needs_review)}** 条，主要因 review_status=needs_human_review 或 LX 等级")
    md.append("")
    md.append("| 时期 | 数量 |")
    md.append("|---|---:|")
    for period in ["1941-1943", "1944-1945", "1946-1950"]:
        md.append(f"| {period} | {len(nr.get(period, []))} |")
    md.append(f"| **合计** | **{len(needs_review)}** |")

    md.append("")
    md.append("## 3. 应排除（exclude）")
    md.append("")
    md.append(f"共计 **{len(exclude)}** 条，主要是 cluster 中的 duplicates")
    md.append("")
    md.append("| 时期 | 数量 |")
    md.append("|---|---:|")
    for period in ["1941-1943", "1944-1945", "1946-1950"]:
        md.append(f"| {period} | {len(ex.get(period, []))} |")
    md.append(f"| **合计** | **{len(exclude)}** |")

    md.append("")
    md.append("## 复审约束")
    md.append("")
    md.append("- 可入库：仅 `accepted` 且等级 L1—L4；OCR 草稿一律 `citation_ready=no`")
    md.append("- 需复核：LX / review_status=needs_human_review；需补档号、影像、页码或人工复核")
    md.append("- 应排除：来源重复 / 拒收；保留 cluster_id 与 canonical_id 用于后续追溯")
    (out / "three_lists_summary.md").write_text("\n".join(md), encoding="utf-8")

    print(f"import_ready: {len(import_ready)}")
    print(f"needs_review: {len(needs_review)}")
    print(f"exclude: {len(exclude)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
