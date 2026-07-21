#!/usr/bin/env python3
"""Accept 5 条 L4 衍生内容（8 民主党派中央官网衍生）— cheer 2026-07-21 拍板。

依据：
- 4 条来自 mmzy.org.cn（民盟中央官网）lead-人物/lead-事件专题页 + 1945 一大专题
- 2 条来自 93.gov.cn（九三学社中央官网）lead-大事记 / lead-五一口号
- reuse_rights = citation_only（适合 L4）
- relevance_grade_proposed = related（与民盟历史间接相关，作为旁证）

L4 保持不变（不升 L2）。这 5 条仅作 8 党派中央官网 100% 覆盖之外的
衍生旁证，accept 表示：身份 / URL / 内容可访问，引用 OK；不代表
原始档案影印件已经过实物核校。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"
ACCEPT_IDS = [
    # 民盟中央官网衍生（mmzy.org.cn）
    "domestic:MMZY:1945-first-congress-page",
    "domestic:MMZY:lead-周恩来与第一届人民政协会议的召开",
    "domestic:MMZY:lead-楚图南-民盟文章",
    # 九三学社中央官网衍生（93.gov.cn）
    "domestic:93JS:lead-九三学社1947年大事记",
    "domestic:93JS:lead-历史的必然-郑重的选择-中共中央发布-五一口号-的历史由",
]

REVIEW_NOTE = (
    "L4 accepted (cheer 2026-07-21 拍板)："
    "5 条均为 8 民主党派中央官网（mmzy.org.cn / 93.gov.cn）衍生内容（lead-人物文章 / lead-事件专题 / 大事记 / 党史专题页）；"
    "L4 等级保持不变（衍生品 = secondary，非原始档案影印件），"
    "accept 表示：URL 可访问 + 身份可核 + 引用合规（reuse_rights=citation_only），"
    "不代表原档已实物核校。"
)


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
        r["reviewed_by"] = "human"
        r["reviewed_at"] = TODAY
        r["check_outcome"] = "pass"
        r["authenticity_level_accepted"] = "L4"
        r["relevance_grade_accepted"] = r.get("relevance_grade_proposed", "related")
        r["review_note"] = REVIEW_NOTE
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
