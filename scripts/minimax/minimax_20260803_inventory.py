#!/usr/bin/env python3
"""
国内资料生产线：盘点（Phase 1）
=================================

读取 data/domestic/candidates.jsonl + source_registry.json，按本轮周期
1941—1943 / 1944—1945 / 1946—1950 三个重点期盘点：

- 已确认的研究价值（accepted + L1/L2/L3）
- 需要人工复核（needs_human_review / LX）
- 已有电子文本 vs 仅有扫描件 vs 完全没有（URL 不通、access=offline）
- 时期 × 证据等级 × 介质 × 访问模式

输出：
  work/minimax-20260803/01_inventory/inventory_full.jsonl
  work/minimax-20260803/01_inventory/inventory_summary.json
  work/minimax-20260803/01_inventory/provenance_full.jsonl
  work/minimax-20260803/01_inventory/period_breakdown.csv
  work/minimax-20260803/01_inventory/repository_breakdown.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

# 字段白名单：只保留稳定字段，避免暴露私有 review_note
KEEP_FIELDS = [
    "candidate_id", "title", "creator", "recipient", "document_date",
    "document_date_precision", "document_type", "repository_code",
    "repository_name", "collection_name", "archive_fonds", "archive_series",
    "archive_file", "archive_item", "catalog_reference",
    "catalog_reference_status", "source_url", "source_url_role",
    "access_mode", "access_note", "medium", "online_availability",
    "rights_status", "reuse_rights", "rights_basis", "copy_allowed",
    "authenticity_level_proposed", "relevance_grade_proposed",
    "event_tags", "person_tags", "place_tags", "evidence_note",
    "evidence_type", "evidence_locator", "uncertainty_note",
    "checked_at", "checked_by", "review_status", "reviewed_at",
    "reviewed_by", "check_outcome", "authenticity_level_accepted",
    "relevance_grade_accepted",
]

# 时期映射（按联盟历史档案的"重点期"分类）
PERIOD_MAP = {
    "1941-1943": ["1941", "1942", "1943"],
    "1944-1945": ["1944", "1945"],
    "1946-1950": ["1946", "1947", "1948", "1949", "1950"],
}

# 时期别名（与 event_tags 模糊匹配）
EVENT_TAG_PATTERNS = {
    "1941-1943": [r"1941", r"1942", r"1943"],
    "1944-1945": [r"1944", r"1945"],
    "1946-1950": [r"1946", r"1947", r"1948", r"1949", r"1950"],
}


def period_of(candidate: dict) -> str | None:
    """根据 event_tags / document_date 推断候选所属重点期。

    优先根据 document_date 推导；若 candidates 同时跨多期，按其最早的
    在重点期内的日期归并。
    """
    doc_date = candidate.get("document_date") or ""
    for prio_period, years in PERIOD_MAP.items():
        for y in years:
            if doc_date.startswith(y):
                return prio_period

    # 退路：用 event_tags 中的任意年份匹配
    event_tags = candidate.get("event_tags") or []
    for tag in event_tags:
        for prio_period, patterns in EVENT_TAG_PATTERNS.items():
            for p in patterns:
                if re.search(p, str(tag)):
                    return prio_period
    return None


def media_class(medium: str, online_availability: str, access_mode: str) -> str:
    """把 (medium, online_availability, access_mode) 合并为一个语义标签。"""
    if access_mode == "offline":
        return "no_digital_only_offline"
    if online_availability == "full_item_online":
        return "fully_digital"
    if online_availability == "surrogate_online":
        return "surrogate_digital"
    if online_availability == "catalogue_only_online":
        return "catalogue_only"
    if online_availability == "not_online":
        return "no_digital_only_offline"
    if medium == "physical":
        return "physical_only"
    return "unknown"


def value(row: dict, key: str):
    return row.get(key)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates", type=Path, default=Path("data/domestic/candidates.jsonl")
    )
    parser.add_argument(
        "--sources", type=Path, default=Path("data/domestic/source_registry.json")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("work/minimax-20260803/01_inventory")
    )
    args = parser.parse_args()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    candidates = [
        json.loads(line)
        for line in args.candidates.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sources = json.loads(args.sources.read_text(encoding="utf-8"))

    # 来源索引
    source_by_id = {s["source_id"]: s for s in sources}

    # 接受/排除分流
    accepted = [c for c in candidates if c.get("review_status") == "accepted"]
    pending = [c for c in candidates if c.get("review_status") == "needs_human_review"]
    rejected = [c for c in candidates if c.get("review_status") in {"rejected", "duplicate"}]

    # 跨期筛选：本轮 1941—1950 重点期
    in_scope = []
    for c in candidates:
        p = period_of(c)
        if p:
            c2 = dict(c)
            c2["_period"] = p
            in_scope.append(c2)

    # 字段归一化输出
    inventory_rows = []
    for c in in_scope:
        row = {k: c.get(k) for k in KEEP_FIELDS}
        row["_period"] = c["_period"]
        row["_media_class"] = media_class(
            c.get("medium") or "",
            c.get("online_availability") or "",
            c.get("access_mode") or "",
        )
        # 文档日期推断（如果不在 1941-1950 内，标 out_of_scope 但保留）
        row["_in_priority_window"] = period_of(c) is not None
        # 来源家族分类（用于入口映射）
        repo = c.get("repository_code") or ""
        if repo in {"MMSH", "MM1941", "MMHIST", "MMZY", "MMYunnan", "GXMM", "FJMM",
                    "HLJMM", "SCU", "CDMM", "BJMM", "ZJMM", "BJDCMM", "HNMM", "SHCM"}:
            row["_source_family"] = "民盟自身与盟史"
        elif repo in {"SAAC", "DRNH", "NLC", "SHAC", "MGCH", "DAJS", "JS", "CQ",
                      "YN", "GD", "SC", "AH", "BJ", "SH", "ZJ", "FJ", "HB", "HN",
                      "HE", "SN", "MG", "MJ", "NJSH", "WP", "BJTZB", "HBMJ"}:
            row["_source_family"] = "国内党政机关与档案馆"
        elif repo in {"PP", "CPPCC", "ZSY", "CSSN", "CPC", "SCIO", "XINHUA", "CAIXIN",
                      "RMzxw", "RMzxb", "RMrb", "RMTZ", "NGD", "TM", "93", "93JS",
                      "GMD", "JS", "MG"}:
            row["_source_family"] = "政协/统一战线/官方媒体"
        elif repo in {"NLC", "WM", "MH", "HKU", "SHDPZ", "MX", "XHB", "FRUS",
                      "MMC", "ACAD", "WS", "ZL1872", "ZLWEB", "JFB", "VOC", "SHPRESS"}:
            row["_source_family"] = "公共数字化/学术/海外"
        else:
            row["_source_family"] = "其他"
        inventory_rows.append(row)

    # ====== 写出 1：inventory_full.jsonl ======
    inv_path = out / "inventory_full.jsonl"
    with inv_path.open("w", encoding="utf-8") as f:
        for r in inventory_rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    # ====== 写出 2：provenance_full.jsonl（包含来源级别溯源） ======
    prov_path = out / "provenance_full.jsonl"
    with prov_path.open("w", encoding="utf-8") as f:
        for c in inventory_rows:
            url = c.get("source_url") or ""
            host = urlparse(url).netloc if url else ""
            prov = {
                "candidate_id": c["candidate_id"],
                "repository_code": c.get("repository_code"),
                "repository_name": c.get("repository_name"),
                "source_url": url,
                "source_url_role": c.get("source_url_role"),
                "url_host": host,
                "catalog_reference": c.get("catalog_reference"),
                "catalog_reference_status": c.get("catalog_reference_status"),
                "archive_fonds": c.get("archive_fonds"),
                "archive_series": c.get("archive_series"),
                "archive_file": c.get("archive_file"),
                "archive_item": c.get("archive_item"),
                "access_mode": c.get("access_mode"),
                "online_availability": c.get("online_availability"),
                "rights_status": c.get("rights_status"),
                "reuse_rights": c.get("reuse_rights"),
                "copy_allowed": c.get("copy_allowed"),
                "needs_ocr": (
                    c.get("medium") in {"physical", "hybrid"}
                    and c.get("online_availability") not in {"full_item_online"}
                ),
                "needs_human_review": c.get("review_status") == "needs_human_review",
                "investigation_priority": c["_period"],
                "evidence_level_accepted": c.get("authenticity_level_accepted"),
                "evidence_level_proposed": c.get("authenticity_level_proposed"),
                "source_family": c.get("_source_family"),
            }
            f.write(json.dumps(prov, ensure_ascii=False, separators=(",", ":")) + "\n")

    # ====== 写出 3：period_breakdown.csv ======
    period_x_level = defaultdict(Counter)
    period_x_media = defaultdict(Counter)
    period_x_review = defaultdict(Counter)
    period_x_repo = defaultdict(Counter)
    for r in inventory_rows:
        p = r["_period"]
        lev = r.get("authenticity_level_accepted") or r.get("authenticity_level_proposed") or "?"
        period_x_level[p][lev] += 1
        period_x_media[p][r["_media_class"]] += 1
        period_x_review[p][r.get("review_status") or "?"] += 1
        period_x_repo[p][r.get("repository_code") or "?"] += 1

    p_csv = out / "period_breakdown.csv"
    with p_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "p1941_1943", "p1944_1945", "p1946_1950", "total"])
        all_keys = sorted(set().union(*[set(c.keys()) for c in period_x_level.values()]))
        w.writerow(["by_authenticity_level"] + [""] * 3)
        for k in all_keys:
            row = [
                period_x_level["1941-1943"].get(k, 0),
                period_x_level["1944-1945"].get(k, 0),
                period_x_level["1946-1950"].get(k, 0),
                sum(period_x_level[p].get(k, 0) for p in PERIOD_MAP),
            ]
            w.writerow([f"  {k}"] + row)
        w.writerow([])
        w.writerow(["by_media_class"] + [""] * 3)
        all_keys = sorted(set().union(*[set(c.keys()) for c in period_x_media.values()]))
        for k in all_keys:
            row = [
                period_x_media["1941-1943"].get(k, 0),
                period_x_media["1944-1945"].get(k, 0),
                period_x_media["1946-1950"].get(k, 0),
                sum(period_x_media[p].get(k, 0) for p in PERIOD_MAP),
            ]
            w.writerow([f"  {k}"] + row)
        w.writerow([])
        w.writerow(["by_review_status"] + [""] * 3)
        for k in ["accepted", "needs_human_review", "rejected", "duplicate"]:
            row = [
                period_x_review["1941-1943"].get(k, 0),
                period_x_review["1944-1945"].get(k, 0),
                period_x_review["1946-1950"].get(k, 0),
                sum(period_x_review[p].get(k, 0) for p in PERIOD_MAP),
            ]
            w.writerow([f"  {k}"] + row)

    # ====== 写出 4：repository_breakdown.csv ======
    repo_data = defaultdict(lambda: {"total": 0, "accepted": 0, "pending": 0, "L1": 0, "L2": 0, "L3": 0, "L4": 0, "LX": 0})
    for r in inventory_rows:
        repo = r.get("repository_code") or "?"
        repo_data[repo]["total"] += 1
        if r.get("review_status") == "accepted":
            repo_data[repo]["accepted"] += 1
        elif r.get("review_status") == "needs_human_review":
            repo_data[repo]["pending"] += 1
        lev = r.get("authenticity_level_accepted") or r.get("authenticity_level_proposed") or ""
        if lev in repo_data[repo]:
            repo_data[repo][lev] += 1

    r_csv = out / "repository_breakdown.csv"
    with r_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repository_code", "total", "accepted", "pending", "L1", "L2", "L3", "L4", "LX"])
        for repo in sorted(repo_data.keys(), key=lambda x: -repo_data[x]["total"]):
            d = repo_data[repo]
            w.writerow([repo, d["total"], d["accepted"], d["pending"], d["L1"], d["L2"], d["L3"], d["L4"], d["LX"]])

    # ====== 写出 5：inventory_summary.json ======
    summary = {
        "batch_id": "minimax-20260803-phase1-inventory",
        "produced_at": "2026-08-03",
        "scope": "1941-1950 三个重点期（1941-1943 / 1944-1945 / 1946-1950）",
        "input_totals": {
            "candidates_total": len(candidates),
            "candidates_accepted": len(accepted),
            "candidates_pending_human_review": len(pending),
            "candidates_rejected_or_duplicate": len(rejected),
            "sources": len(sources),
        },
        "in_scope_totals": {
            "1941-1943": sum(1 for r in inventory_rows if r["_period"] == "1941-1943"),
            "1944-1945": sum(1 for r in inventory_rows if r["_period"] == "1944-1945"),
            "1946-1950": sum(1 for r in inventory_rows if r["_period"] == "1946-1950"),
            "total": len(inventory_rows),
        },
        "by_authenticity_level": dict(
            Counter(
                (r.get("authenticity_level_accepted") or r.get("authenticity_level_proposed") or "?")
                for r in inventory_rows
            )
        ),
        "by_media_class": dict(
            Counter(r["_media_class"] for r in inventory_rows)
        ),
        "by_source_family": dict(
            Counter(r["_source_family"] for r in inventory_rows)
        ),
        "needs_ocr_candidates": sum(
            1 for r in inventory_rows
            if r.get("medium") in {"physical", "hybrid"}
            and r.get("online_availability") not in {"full_item_online"}
        ),
        "needs_human_review_candidates": sum(
            1 for r in inventory_rows if r.get("review_status") == "needs_human_review"
        ),
        "outputs": {
            "inventory_full_jsonl": str(inv_path),
            "provenance_full_jsonl": str(prov_path),
            "period_breakdown_csv": str(p_csv),
            "repository_breakdown_csv": str(r_csv),
        },
    }
    (out / "inventory_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
