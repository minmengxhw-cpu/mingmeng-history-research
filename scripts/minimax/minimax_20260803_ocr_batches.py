#!/usr/bin/env python3
"""
国内资料生产线：OCR 批次调度（阶段 2 入口）
==========================================

将 216 条 OCR 计划按以下维度分组：
- 优先级（p1 / p2 / p3）
- 时期（1941-1943 / 1944-1945 / 1946-1950）
- 来源家族（民盟 / 党政 / 政协 / 公共）
- 估计页数（决定批次大小）

输出每批的 batch_id, file_ids, total_pages, est_runtime, decision_note。
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


# 估计每页 OCR 时间（秒），按 evidence grade
SECONDS_PER_PAGE_BY_GRADE = {
    "L1": 8,    # 高质量扫描，需精核
    "L2": 6,    # 中等
    "L3": 4,    # 报刊，密度高
}


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("work/minimax-20260803/04_staging/staging.sqlite"))
    parser.add_argument("--out", type=Path, default=Path("work/minimax-20260803/05_checkpoint"))
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    # 加载 OCR 计划
    with sqlite3.connect(args.db) as conn:
        cur = conn.execute("""SELECT file_id, source_url, source_kind, repository_code,
                                    primary_candidate_id, period, authenticity_level,
                                    evidence_grade, page_count, ocr_priority, ocr_priority_reason,
                                    cluster_ids, candidate_ids
                            FROM staging_ocr_plan""")
        cols = [d[0] for d in cur.description]
        plans = [dict(zip(cols, row)) for row in cur.fetchall()]

    # 解析 candidate_ids JSON
    for p in plans:
        p["candidate_ids"] = json.loads(p["candidate_ids"]) if p["candidate_ids"] else []
        p["cluster_ids"] = json.loads(p["cluster_ids"]) if p["cluster_ids"] else []
        p["source_family"] = next(
            (fam for fam, repos in SOURCE_FAMILY_PATTERNS.items() if p["repository_code"] in repos),
            "其他",
        )

    # ============== 批次切分 ==============
    # 每个 batch: 同一优先级 + 同一时期 + 估计总时间 ≤ 30 分钟
    TARGET_SECONDS = 1800  # 30 分钟

    # 1. 按 (priority, period) 分组
    groups = defaultdict(list)
    for p in plans:
        groups[(p["ocr_priority"], p["period"])].append(p)

    # 2. 每组内部按估计时间贪心切分子批
    batches = []
    for (priority, period), group in groups.items():
        # 按页数降序
        group.sort(key=lambda x: -x["page_count"])
        current = []
        current_seconds = 0
        for p in group:
            per_page = SECONDS_PER_PAGE_BY_GRADE.get(p["authenticity_level"], 6)
            est = p["page_count"] * per_page
            if current and current_seconds + est > TARGET_SECONDS:
                # 提交当前
                batch_id = f"OCR-BATCH-{priority}-{period}-{len(batches) + 1:02d}"
                batches.append({
                    "batch_id": batch_id,
                    "ocr_priority": priority,
                    "period": period,
                    "file_ids": [c["file_id"] for c in current],
                    "total_files": len(current),
                    "total_pages": sum(c["page_count"] for c in current),
                    "estimated_seconds": current_seconds,
                    "estimated_minutes": round(current_seconds / 60, 1),
                    "evidence_grade_distribution": dict_from_list(current, "evidence_grade"),
                    "source_family_distribution": dict_from_list(current, "source_family"),
                    "candidate_ids": list_of_lists_flatten([c["candidate_ids"] for c in current]),
                    "decision_note": ""
                })
                current = []
                current_seconds = 0
            current.append(p)
            current_seconds += est
        if current:
            batch_id = f"OCR-BATCH-{priority}-{period}-{len(batches) + 1:02d}"
            batches.append({
                "batch_id": batch_id,
                "ocr_priority": priority,
                "period": period,
                "file_ids": [c["file_id"] for c in current],
                "total_files": len(current),
                "total_pages": sum(c["page_count"] for c in current),
                "estimated_seconds": current_seconds,
                "estimated_minutes": round(current_seconds / 60, 1),
                "evidence_grade_distribution": dict_from_list(current, "evidence_grade"),
                "source_family_distribution": dict_from_list(current, "source_family"),
                "candidate_ids": list_of_lists_flatten([c["candidate_ids"] for c in current]),
                "decision_note": ""
            })

    # 3. 决策注释
    for b in batches:
        notes = []
        if b["ocr_priority"] == "p1":
            notes.append("1946-1950 L1 关键件，优先排程")
        elif b["ocr_priority"] == "p2":
            notes.append("L2 汇编，可补页级定位")
        elif b["ocr_priority"] == "p3":
            notes.append("L3 剪报 / 待处理 LX")
        if "民盟自身" in b["source_family_distribution"]:
            notes.append("含民盟自身原件")
        if b["total_pages"] > 100:
            notes.append("大批量，建议分夜处理")
        b["decision_note"] = "; ".join(notes)

    # ============== 写出 ==============
    batches_path = out / "ocr_batches.json"
    batches_path.write_text(
        json.dumps({
            "produced_at": "2026-08-03",
            "totals": {
                "batches": len(batches),
                "files": len(plans),
                "estimated_total_minutes": round(sum(b["estimated_seconds"] for b in batches) / 60, 1),
            },
            "by_priority": {
                p: [b for b in batches if b["ocr_priority"] == p]
                for p in ["p1", "p2", "p3"]
            },
            "batches": batches,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 摘要 markdown
    md = [
        "# OCR 批次调度",
        "",
        f"- 计划文件：{len(plans)}",
        f"- 切分批次：{len(batches)}",
        f"- 估计总时间：{round(sum(b['estimated_seconds'] for b in batches) / 60, 1)} 分钟",
        "",
        "## 按优先级",
        "",
    ]
    for p in ["p1", "p2", "p3"]:
        ps = [b for b in batches if b["ocr_priority"] == p]
        files = sum(b["total_files"] for b in ps)
        pages = sum(b["total_pages"] for b in ps)
        minutes = round(sum(b["estimated_seconds"] for b in ps) / 60, 1)
        md.append(f"### {p} ({len(ps)} batches, {files} files, {pages} pages, {minutes} min)")
        for b in ps:
            md.append(f"- `{b['batch_id']}` | {b['period']} | {b['total_files']} files / {b['total_pages']} pages / {b['estimated_minutes']} min")
            md.append(f"  - {b['decision_note']}")
        md.append("")

    # 给出建议
    md.append("## 阶段 2 建议")
    md.append("")
    md.append("1. **第一晚**: p1 + 1946-1950（高价值关键件，估计 1-2 晚可完成）")
    md.append("2. **第二晚**: p2 + 1944-1945（汇编类，可补页级定位）")
    md.append("3. **第三晚**: p3 + 1941-1943（最早事件，需要 cheer-only 接力）")
    md.append("")
    md.append("每批跑完后：")
    md.append("- 重新跑 `python3 scripts/minimax/minimax_20260803_ocr_manifest.py --done <batch_id>`")
    md.append("- 升级 passing 候选的 citation_ready（人工复核后）")
    md.append("- 跑 `python3 scripts/minimax/minimax_20260803_three_lists.py` 重新生成清单")

    # 写入 markdown
    (out / "ocr_batches.md").write_text("\n".join(md), encoding="utf-8")

    print(f"batches: {len(batches)}")
    print(f"total files: {len(plans)}")
    print(f"total minutes: {round(sum(b['estimated_seconds'] for b in batches) / 60, 1)}")
    return 0


def dict_from_list(items: list, key: str) -> dict:
    from collections import Counter
    return dict(Counter(x[key] for x in items))


def list_of_lists_flatten(lists: list) -> list:
    out = []
    seen = set()
    for l in lists:
        for x in l:
            if x not in seen:
                out.append(x)
                seen.add(x)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
