#!/usr/bin/env python3
"""
国内资料生产线：Evidence Gap 报告（阶段 2 入口）
==========================================

基于：
- event_coverage.json（9 个关键事件）
- staging.sqlite（664 candidates + 545 import_ready + 27 needs_review + 92 exclude）
- source_manifest.jsonl（每份资料的证据等级）

输出：
  - evidence_gap_<event_id>.md：每个事件的 L1/L2 引用差距、来源家族覆盖度
  - evidence_gap_summary.csv：每个事件在 4 维（民盟/机关/政协/报刊）上的覆盖
  - evidence_gap_actionable.json：可下批的人工 / OCR 任务清单

评估维度：
- L1_citation_ready 数量（高价值证据）
- L2_page_cite 数量（可引用但需复核）
- L4_secondary 数量（线索）
- 来源家族覆盖（民盟自身 / 党政机关 / 政协 / 公共报刊）
- 时期覆盖（早期 / 中期 / 后期）
- 关键缺口（cheer-only 链路）
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


# 9 个关键事件的中文名映射
EVENT_NAMES = {
    "domestic-1941-formation": "1941 中国民主政团同盟成立",
    "domestic-1944-reorganization": "1944 改组并更名为中国民主同盟",
    "domestic-1945-first-congress": "1945 民盟第一次全国代表大会",
    "domestic-1946-pcc": "1946 政治协商会议（旧政协）",
    "domestic-1946-refuse-national-assembly": "1946 民盟拒绝参加国民大会",
    "domestic-1946-li-wen": "1946 李公朴、闻一多遇害及各方反应",
    "domestic-1947-illegal-dissolution": "1947 民盟被宣布非法与组织解散",
    "domestic-1948-third-plenum-may-day": "1948 一届三中全会及响应\"五一口号\"",
    "domestic-1949-new-pcc": "1949 新政协筹备、民主人士北上与第一届全体会议",
}

# 来源家族匹配规则
SOURCE_FAMILY_PATTERNS = {
    "民盟自身": ("MMSH", "MM1941", "MMHIST", "MMZY", "MMYunnan", "GXMM", "FJMM",
              "HLJMM", "SCU", "CDMM", "BJMM", "ZJMM", "BJDCMM", "HNMM", "SHCM",
              "YADS", "LNU", "QY"),
    "国内党政机关": ("SAAC", "DRNH", "NLC", "SHAC", "MGCH", "DAJS", "JS", "CQ",
                  "YN", "GD", "SC", "AH", "BJ", "SH", "ZJ", "FJ", "HB", "HN",
                  "HE", "SN", "MG", "MJ", "NJSH", "WP", "BJTZB", "HBMJ", "ZJMG"),
    "政协/统一战线": ("PP", "CPPCC", "ZSY", "CSSN", "CPC", "SCIO", "XINHUA", "CAIXIN",
                  "TM", "93", "RMrb", "RMzxb", "RMzxw", "RMTZ", "NGD", "GMD", "RCL", "KMY"),
    "公共数字化/学术": ("WM", "MH", "HKU", "SHDPZ", "MX", "XHB", "FRUS",
                    "MMC", "ACAD", "WS", "ZL1872", "ZLWEB", "JFB", "VOC", "SHPRESS"),
}


def event_ids_from_tags(event_id: str) -> list[str]:
    return [event_id]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("work/minimax-20260803/04_staging/staging.sqlite"))
    parser.add_argument("--events", type=Path, default=Path("data/domestic/event_coverage.json"))
    parser.add_argument("--out", type=Path, default=Path("work/minimax-20260803/05_checkpoint"))
    parser.add_argument("--actionable", type=Path, default=Path("work/minimax-20260803/05_checkpoint/evidence_gap_actionable.json"))
    args = parser.parse_args()

    events = json.loads(args.events.read_text(encoding="utf-8"))
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    # 加载 staging
    with sqlite3.connect(args.db) as conn:
        cur = conn.execute("""SELECT * FROM staging_domestic_candidates""")
        cols = [d[0] for d in cur.description]
        candidates = [dict(zip(cols, row)) for row in cur.fetchall()]
        c_by_id = {c["candidate_id"]: c for c in candidates}

    # 4 大来源家族映射
    family_by_repo = {}
    for family, repos in SOURCE_FAMILY_PATTERNS.items():
        for r in repos:
            family_by_repo[r] = family

    summary_rows = []
    actionable = []

    for event in events:
        eid = event["event_id"]
        ename = EVENT_NAMES.get(eid, event["event_name"])
        # 1. 该事件已有的 candidate_ids
        cand_ids = set(event.get("domestic_candidate_ids", []))
        # 2. 这些候选在 staging 中的状态
        event_candidates = [c for c in candidates if c["candidate_id"] in cand_ids]
        # 3. 统计
        by_level = Counter(c["authenticity_level_accepted"] for c in event_candidates)
        by_family = Counter(family_by_repo.get(c["repository_code"], "其他") for c in event_candidates)
        by_bucket = Counter(c["staging_bucket"] for c in event_candidates)
        cite_ready = sum(1 for c in event_candidates if c["citation_ready"] == 1)

        # 4. 缺口分析
        gaps = []
        # gap 1: 没有任何 L1
        if by_level.get("L1", 0) == 0:
            gaps.append("L1 缺失")
        # gap 2: 没有任何 L2
        if by_level.get("L2", 0) == 0:
            gaps.append("L2 缺失")
        # gap 3: 4 个来源家族中有 0 个
        required_families = ["民盟自身", "国内党政机关", "政协/统一战线", "公共数字化/学术"]
        missing_families = [f for f in required_families if by_family.get(f, 0) == 0]
        if missing_families:
            gaps.append(f"来源家族缺失: {', '.join(missing_families)}")
        # gap 4: needs_review 占比过高
        if by_bucket.get("needs_review", 0) >= 3:
            gaps.append(f"needs_review 过多（{by_bucket['needs_review']} 条）")
        # gap 5: 时期跨度
        periods = Counter(c["period"] for c in event_candidates)
        if len(periods) == 1:
            gaps.append(f"仅 1 个时期：{list(periods.keys())[0]}")
        # gap 6: 都是 LX
        if by_level.get("LX", 0) > 0 and by_level.get("L1", 0) + by_level.get("L2", 0) == 0:
            gaps.append(f"均为 LX 待裁别（{by_level['LX']} 条）")

        # 5. 写入 markdown
        md_path = out / f"evidence_gap_{eid}.md"
        lines = [
            f"# Evidence Gap: {ename}",
            "",
            f"- event_id: `{eid}`",
            f"- 候选总数: {len(event_candidates)}",
            f"- 时期分布: {dict(periods)}",
            f"- 来源家族分布: {dict(by_family)}",
            f"- 证据等级分布: {dict(by_level)}",
            f"- 入库分布: {dict(by_bucket)}",
            f"- citation_ready 数: {cite_ready}",
            "",
            "## 缺口",
            "",
        ]
        if gaps:
            for g in gaps:
                lines.append(f"- ⚠️ {g}")
        else:
            lines.append("- ✅ 4 维均覆盖")
        lines.append("")
        lines.append("## 全部候选明细")
        lines.append("")
        lines.append("| candidate_id | 等级 | 来源家族 | 时期 | 库桶 | citation_ready |")
        lines.append("|---|---|---|---|---|---|")
        for c in sorted(event_candidates, key=lambda x: (x["authenticity_level_accepted"] or "Z", x["document_date"] or "")):
            fam = family_by_repo.get(c["repository_code"], "其他")
            lines.append(f"| {c['candidate_id']} | {c['authenticity_level_accepted']} | {fam} | {c['period']} | {c['staging_bucket']} | {'yes' if c['citation_ready'] == 1 else 'no'} |")
        md_path.write_text("\n".join(lines), encoding="utf-8")

        # 6. 摘要
        summary_rows.append({
            "event_id": eid,
            "event_name": ename,
            "total_candidates": len(event_candidates),
            "L1": by_level.get("L1", 0),
            "L2": by_level.get("L2", 0),
            "L3": by_level.get("L3", 0),
            "L4": by_level.get("L4", 0),
            "LX": by_level.get("LX", 0),
            "import_ready": by_bucket.get("import_ready", 0),
            "needs_review": by_bucket.get("needs_review", 0),
            "exclude": by_bucket.get("exclude", 0),
            "citation_ready": cite_ready,
            "meng_self": by_family.get("民盟自身", 0),
            "gov_archives": by_family.get("国内党政机关", 0),
            "tongzhan": by_family.get("政协/统一战线", 0),
            "public_digital": by_family.get("公共数字化/学术", 0),
            "gaps": "; ".join(gaps) if gaps else "OK",
        })

        # 7. actionable：每个缺口产生可下批任务
        for g in gaps:
            if "L1 缺失" in g:
                # 推荐：一分钟内可 OCR 的 L2 + 公共数字化
                actionable.append({
                    "event_id": eid,
                    "type": "ocr_target_l1",
                    "priority": "p0",
                    "reason": "L1 缺失，建议对 L2 page_cite 优先做 OCR 升级",
                    "candidate_ids": [c["candidate_id"] for c in event_candidates if c["authenticity_level_accepted"] == "L2"][:5],
                })
            elif "来源家族缺失" in g:
                fam = missing_families[0]
                actionable.append({
                    "event_id": eid,
                    "type": "acquire_new_source",
                    "priority": "p1",
                    "reason": f"该事件缺失 {fam} 来源家族，建议补查二史馆/民盟中央/政协史料",
                    "candidate_ids": [],
                })
            elif "needs_review 过多" in g:
                actionable.append({
                    "event_id": eid,
                    "type": "human_review_needed",
                    "priority": "p1",
                    "reason": f"该事件 needs_review 过多 ({by_bucket['needs_review']} 条)，需人工复核",
                    "candidate_ids": [c["candidate_id"] for c in event_candidates if c["staging_bucket"] == "needs_review"],
                })

    # 写 summary.csv
    import csv
    sum_path = out / "evidence_gap_summary.csv"
    with sum_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        for r in summary_rows:
            w.writerow(r)

    # 写 actionable
    args.actionable.write_text(
        json.dumps({
            "produced_at": "2026-08-03",
            "totals": Counter(a["type"] for a in actionable),
            "items": actionable,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"events: {len(events)}")
    print(f"actionable: {len(actionable)}")
    print(f"  by type: {dict(Counter(a['type'] for a in actionable))}")
    print(f"summary: {sum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
