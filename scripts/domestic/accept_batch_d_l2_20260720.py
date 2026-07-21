#!/usr/bin/env python3
"""Accept 批次 D-A: 24 条 L2 升 accepted（8 党派官网 + 1 saac 聚合 + 15 saac 具体档案）。

L3（特园 + 二史馆）保持 needs_human_review。

依据：
- 8 党派中央官网 = 各党派中央委员会发布 + 多源印证（WebSearch 2026-07-20）
- saac.gov.cn = 中央档案馆 / 国家档案局官方公布（含 200+ 珍贵档案部分首次公开）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

# 24 条 L2 候选（精确匹配 candidate_id）
ACCEPT_IDS = [
    # 8 党派中央官网
    "domestic:MG:minge-gov-cn-history-1948-hongkong",
    "domestic:CJD:cndca-gov-cn-history-1945-chongqing",
    "domestic:MJ:minj-gov-cn-history-1945-shanghai",
    "domestic:NGD:ngd-org-cn-history-1930-shanghai",
    "domestic:ZG:zg-org-cn-history-1925-america",
    "domestic:93:93-gov-cn-history-1945-chongqing",
    "domestic:TM:taimeng-org-cn-history-1947-hongkong",
    # 1 saac.gov.cn 聚合
    "domestic:SAAC:album-51koukou-kaoguodadian",
    # 15 saac.gov.cn 具体档案
    "domestic:SAAC:51koukou-p01-dde04",
    "domestic:SAAC:51koukou-p01-dde07",
    "domestic:SAAC:51koukou-p01-dde13",
    "domestic:SAAC:51koukou-p01-dde14",
    "domestic:SAAC:51koukou-p01-dde20",
    "domestic:SAAC:51koukou-p01-dde21",
    "domestic:SAAC:51koukou-p04-dde04",
    "domestic:SAAC:51koukou-p04-dde05",
    "domestic:SAAC:51koukou-p04-dde07",
    "domestic:SAAC:51koukou-p04-dde12",
    "domestic:SAAC:51koukou-p05-dde02",
    "domestic:SAAC:51koukou-p05-dde11",
    "domestic:SAAC:51koukou-p05-dde10",
    "domestic:SAAC:51koukou-p05-dde16",
    "domestic:SAAC:51koukou-p05-dde15",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]

    accepted, missing, skipped = [], [], []
    accept_set = set(ACCEPT_IDS)

    for r in rows:
        cid = r["candidate_id"]
        if cid not in accept_set:
            continue
        if r.get("review_status") == "accepted":
            skipped.append(cid)
            continue
        r["review_status"] = "accepted"
        r["review_note"] = (
            "L2 accepted (批次 D-A)："
            "8 党派官网 = 各党派中央委员会官方发布 + WebSearch 多源印证；"
            "saac.gov.cn = 中央档案馆 / 国家档案局官方公布；"
            "升级依据与 FRUS L3→L2 流程一致（多源核读 + 官方一手）。"
        )
        r["accepted_at"] = TODAY
        accepted.append(cid)

    for cid in ACCEPT_IDS:
        if cid not in accepted and cid not in skipped:
            missing.append(cid)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {
            "accepted": accepted,
            "skipped_already_accepted": skipped,
            "missing_not_found": missing,
            "applied": args.apply,
            "total_records": len(rows),
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())