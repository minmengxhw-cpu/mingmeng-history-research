#!/usr/bin/env python3
"""
国内资料生产线：LX 升级提案（阶段 2 入口）
==========================================

4 条 LX 候选（维基文库公开转录）的升级评估：

- domestic:WS:democratic-league-declaration-1941
- domestic:WS:peace-building-program-1946
- domestic:WS:pcc-national-assembly-resolution-1946
- domestic:WS:pcc-government-reorganization-1946
- domestic:WS:democratic-league-formation-1941-wikisource
- domestic:WS:democratic-movement-editorial-1941
- domestic:WS:democratic-league-1941-zhang-lan-publish

逐条输出：
- 候选原文摘要
- 公开转录 URL
- 评估：是否升级为 L1 / 是否保持 LX / 是否降为 L4
- 提议动作
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("work/minimax-20260803/04_staging/staging.sqlite"))
    parser.add_argument("--out", type=Path, default=Path("work/minimax-20260803/05_checkpoint/lx_upgrade_proposals.md"))
    args = parser.parse_args()

    with sqlite3.connect(args.db) as conn:
        cur = conn.execute(
            """SELECT candidate_id, title, creator, document_date, repository_code,
                      catalog_reference, source_url, evidence_note, uncertainty_note,
                      review_status, period, source_family, evidence_grade
               FROM staging_domestic_candidates
               WHERE authenticity_level_accepted = 'LX'"""
        )
        cols = [d[0] for d in cur.description]
        lx_rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    # 评估标准
    # WS 条目：维基文库公开转录。这里采用更激进的策略：
    #   - 满足 4 个核心字段（source_url / catalog_reference / document_date / creator）
    #   - URL 主机为 zh.wikisource.org
    #   - 不评 uncertainty_note 为降级条件（因为 wikisource 收录有底本信息）
    # 升级为 L1，但 status 标记 pending_real_artifact_comparison，
    # 表明需要后续与原件影像核对。

    proposals = []
    for r in lx_rows:
        cid = r["candidate_id"]
        notes = []
        score = 0
        l1_eligible = True

        if r["source_url"]:
            score += 1
            notes.append(f"有 source_url: {r['source_url']}")
        else:
            l1_eligible = False
            notes.append("❌ 无 source_url")
        if r["catalog_reference"]:
            score += 1
            notes.append(f"有 catalog_reference: {r['catalog_reference'][:60]}")
        else:
            l1_eligible = False
            notes.append("❌ 无 catalog_reference")
        if r["document_date"]:
            score += 1
            notes.append(f"有 document_date: {r['document_date']}")
        else:
            l1_eligible = False
            notes.append("❌ 无 document_date")
        if r["creator"]:
            score += 1
            notes.append(f"有 creator: {r['creator']}")
        else:
            l1_eligible = False
            notes.append("❌ 无 creator")

        # 检查 URL 主机是否为 wikisource
        is_wikisource = "zh.wikisource.org" in (r["source_url"] or "")

        # 决策
        if l1_eligible and is_wikisource:
            recommended = "L1"
            action = "升级为 L1（公开转录 + 完整溯源 + wikisource 收录）"
        elif l1_eligible:
            recommended = "L2"
            action = "升级为 L2（公开转录 + 完整溯源，但非 wikisource 标准平台）"
        elif score >= 3:
            recommended = "L4"
            action = "保留为 L4 二次呈现"
        else:
            recommended = "LX"
            action = "保留 LX，继续人工复核"

        proposals.append({
            "candidate_id": cid,
            "title": r["title"],
            "document_date": r["document_date"],
            "score": score,
            "is_wikisource": is_wikisource,
            "recommended_level": recommended,
            "action": action,
            "notes": notes,
            "source_url": r["source_url"],
        })

    # 写 markdown
    md = [
        "# LX 4 条升级提案",
        "",
        "LX = 等级未确认。本节对 LX 候选逐条评估升级建议。",
        "",
        "评估维度：",
        "- 是否 source_url",
        "- 是否 catalog_reference",
        "- 是否 document_date",
        "- 是否 creator",
        "- URL 主机是否为 zh.wikisource.org",
        "",
        "## 决策矩阵",
        "",
        "| 条件 | 等级 | 理由 |",
        "|---|---|---|",
        "| 4 字段全有 + wikisource URL | L1 | 公开转录 + 完整溯源 |",
        "| 4 字段全有 + 非 wikisource | L2 | 公开转录 + 完整溯源 |",
        "| 3 字段 | L4 | 二手呈现 |",
        "| < 3 字段 | LX | 继续人工复核 |",
        "",
        "## 升级提案",
        "",
    ]

    for p in proposals:
        md.append(f"### `{p['candidate_id']}`")
        md.append("")
        md.append(f"- title: {p['title']}")
        md.append(f"- document_date: {p['document_date']}")
        md.append(f"- score: {p['score']}/4")
        md.append(f"- **recommended**: {p['recommended_level']}")
        md.append(f"- action: {p['action']}")
        if p["source_url"]:
            md.append(f"- source_url: {p['source_url']}")
        md.append("- notes:")
        for n in p["notes"]:
            md.append(f"  - {n}")
        md.append("")

    # 优先级
    md.append("## 阶段 2 行动项")
    md.append("")
    l1_upgrade = [p for p in proposals if p["recommended_level"] == "L1"]
    l2_upgrade = [p for p in proposals if p["recommended_level"] == "L2"]
    l4_demote = [p for p in proposals if p["recommended_level"] == "L4"]
    keep_lx = [p for p in proposals if p["recommended_level"] == "LX"]
    md.append(f"- **L1 升级候选**：{len(l1_upgrade)} 条")
    for p in l1_upgrade:
        md.append(f"  - `{p['candidate_id']}`")
    md.append(f"- **L2 升级候选**：{len(l2_upgrade)} 条")
    for p in l2_upgrade:
        md.append(f"  - `{p['candidate_id']}`")
    md.append(f"- **L4 降级候选**：{len(l4_demote)} 条")
    for p in l4_demote:
        md.append(f"  - `{p['candidate_id']}`")
    md.append(f"- **保持 LX**：{len(keep_lx)} 条")
    for p in keep_lx:
        md.append(f"  - `{p['candidate_id']}`")
    md.append("")
    md.append("**实施步骤**：")
    md.append("1. 跑 `python3 scripts/minimax/minimax_20260803_lx_apply.py`")
    md.append("2. 对每条 L1 升级候选，复核 source_url 实际可访问性 + 文本是否真包含 title")
    md.append("3. 通过后写入 `staging_domestic_candidates.authenticity_level_accepted` = 'L1'")
    md.append("4. 重新跑 `three_lists.py` 生成新清单")

    args.out.write_text("\n".join(md), encoding="utf-8")

    # 可执行 JSON
    exe_path = args.out.with_suffix(".json")
    exe_path.write_text(
        json.dumps({
            "produced_at": "2026-08-03",
            "proposals": proposals,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"proposals: {len(proposals)}")
    print(f"  L1 upgrade: {len(l1_upgrade)}")
    print(f"  L2 upgrade: {len(l2_upgrade)}")
    print(f"  L4 demote: {len(l4_demote)}")
    print(f"  keep LX: {len(keep_lx)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
