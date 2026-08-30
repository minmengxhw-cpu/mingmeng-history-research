#!/usr/bin/env python3
"""
国内资料生产线：needs_review 27 条 拆分为人工任务
================================================

读 staging.sqlite 的 needs_review 桶，按机构 × 时期 × 缺口类型拆分：

缺口类型：
- catalog_missing：无 catalog_reference
- archive_id_missing：无 archive_fonds / series / file
- online_only_catalogue：online_availability=catalogue_only_online
- access_login：access_mode=login / reading_room
- access_offline：access_mode=offline
- period_unclear：document_date 为空或精度不够

每条任务输出：
- task_id
- candidate_id
- 缺口类型
- 建议动作
- 优先级
- 估计处理时间
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


TASK_TEMPLATES = {
    "catalog_missing": {
        "action": "在源网站或数据库查档号 / ISBN / 馆藏标识 / URL 中提取",
        "priority": "p1",
        "estimated_minutes": 5,
    },
    "archive_id_missing": {
        "action": "补全全宗 / 系列 / 案卷 / 件号；如无档号，建立临时引用并标注",
        "priority": "p1",
        "estimated_minutes": 8,
    },
    "online_only_catalogue": {
        "action": "查看图书馆/档案馆 OPAC 是否能调阅原文；若可下载，登记 URL",
        "priority": "p2",
        "estimated_minutes": 10,
    },
    "access_login": {
        "action": "注册账号 / 馆内访问 / cheer-only 接力；记录 access 状态",
        "priority": "p2",
        "estimated_minutes": 15,
    },
    "access_offline": {
        "action": "调档申请 / 现场核验 / 采购扫描；写入 acquisition_required",
        "priority": "p3",
        "estimated_minutes": 30,
    },
    "period_unclear": {
        "action": "核对 document_date 精度；如不可考，置 LX 或 L4",
        "priority": "p2",
        "estimated_minutes": 5,
    },
    "level_review": {
        "action": "升级或降级当前等级；提供理由",
        "priority": "p1",
        "estimated_minutes": 5,
    },
    "uncertainties_clarify": {
        "action": "解决 uncertainty_note 警告：查证不确定项并写明依据",
        "priority": "p2",
        "estimated_minutes": 8,
    },
}


def classify_gap(c: dict) -> list[str]:
    gaps = []
    if not c.get("archive_fonds") and not c.get("archive_series") and not c.get("archive_file"):
        gaps.append("archive_id_missing")
    if not c.get("catalog_reference") or c.get("catalog_reference") == "web:":
        gaps.append("catalog_missing")
    if c.get("online_availability") == "catalogue_only_online":
        gaps.append("online_only_catalogue")
    if c.get("access_mode") in {"login", "reading_room"}:
        gaps.append("access_login")
    if c.get("access_mode") == "offline":
        gaps.append("access_offline")
    if not c.get("document_date"):
        gaps.append("period_unclear")
    if c.get("uncertainty_note") and ("未核" in (c.get("uncertainty_note") or "") or "未确" in (c.get("uncertainty_note") or "")):
        gaps.append("uncertainties_clarify")
    if c.get("authenticity_level_accepted") in {"LX", None, ""}:
        gaps.append("level_review")
    if not gaps:
        gaps.append("uncertainties_clarify")  # fallback
    return gaps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("work/minimax-20260803/04_staging/staging.sqlite"))
    parser.add_argument("--out", type=Path, default=Path("work/minimax-20260803/05_checkpoint/needs_review_tasks.csv"))
    parser.add_argument("--out-md", type=Path, default=Path("work/minimax-20260803/05_checkpoint/needs_review_tasks.md"))
    args = parser.parse_args()

    with sqlite3.connect(args.db) as conn:
        cur = conn.execute(
            """SELECT candidate_id, title, creator, document_date, period, repository_code,
                      repository_name, catalog_reference, archive_fonds, archive_series, archive_file,
                      online_availability, access_mode, authenticity_level_accepted,
                      uncertainty_note, review_note, source_url
               FROM staging_domestic_candidates WHERE staging_bucket='needs_review'"""
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    tasks = []
    task_id = 0
    for c in rows:
        gaps = classify_gap(c)
        for gap in gaps:
            task_id += 1
            tmpl = TASK_TEMPLATES.get(gap, TASK_TEMPLATES["uncertainties_clarify"])
            tasks.append({
                "task_id": f"NR-{task_id:04d}",
                "candidate_id": c["candidate_id"],
                "title": c["title"],
                "period": c["period"],
                "repository_code": c["repository_code"],
                "repository_name": c["repository_name"],
                "current_level": c["authenticity_level_accepted"],
                "gap_type": gap,
                "action": tmpl["action"],
                "priority": tmpl["priority"],
                "estimated_minutes": tmpl["estimated_minutes"],
                "source_url": c.get("source_url"),
            })

    # 写 CSV
    if tasks:
        with args.out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(tasks[0].keys()))
            w.writeheader()
            for t in tasks:
                w.writerow(t)
    # 写 MD
    by_priority = defaultdict(list)
    for t in tasks:
        by_priority[t["priority"]].append(t)

    md = [
        "# needs_review 27 条 拆分人工任务",
        "",
        f"- 总任务数: {len(tasks)}",
        f"- 涉及候选数: {len(rows)}",
        f"- 估计总时间: {sum(t['estimated_minutes'] for t in tasks)} 分钟 ({sum(t['estimated_minutes'] for t in tasks) / 60:.1f} 小时)",
        "",
        "## 按优先级",
        "",
    ]
    for p in ["p1", "p2", "p3"]:
        ps = by_priority.get(p, [])
        md.append(f"### {p} ({len(ps)} 任务, {sum(t['estimated_minutes'] for t in ps)} 分钟)")
        for t in ps:
            md.append(f"- `{t['task_id']}` | `{t['candidate_id']}` | {t['gap_type']} | {t['action']}")
        md.append("")

    md.append("## 按缺口类型")
    md.append("")
    by_gap = defaultdict(int)
    for t in tasks:
        by_gap[t["gap_type"]] += 1
    for k, v in sorted(by_gap.items(), key=lambda x: -x[1]):
        md.append(f"- {k}: {v}")

    args.out_md.write_text("\n".join(md), encoding="utf-8")

    print(f"tasks: {len(tasks)}")
    print(f"candidates: {len(rows)}")
    print(f"total minutes: {sum(t['estimated_minutes'] for t in tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
