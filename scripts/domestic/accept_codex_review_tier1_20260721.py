#!/usr/bin/env python3
"""Accept T1 36 条 codex-style 复审低风险候选 (cheer 2026-07-21 拍板)。

依据 work/domestic/codex_review_20260721.md T1 档：
- T1.a L4 29 地方民盟 lead-文章 (full_item_online + 官方平台 + citation_only)
- T1.b LX 4 wikisource 1941/1946 公开转录 (webfetch 2026-07-21 全部 200)
- T1.c L3 3 强 primary source (HNMM 1948 五一 / YADS 1945 延安 / LNU 1941 索引)

保留各条 proposed 等级不变，accept 表示：URL 可达 / 身份可核 / 引用合规。
不表示原档已实物核校 / 全文已逐字转录 / 复制权利已清。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"
ACCEPT_IDS = {
    # T1.a L4 29 (地方民盟 lead-文章 + ZL1872 + CPPCC)
    "domestic:MMSH:web-history",
    "domestic:MMSH:web-leaders",
    "domestic:MMSH:web-bases",
    "domestic:MMSH:web-office-history",
    "domestic:MMSH:web-political-cooperation",
    "domestic:MMSH:web-newspapers",
    "domestic:MMSH:web-zhanglan",
    "domestic:MMSH:web-intro",
    "domestic:MMSH:web-liukaiqu",
    "domestic:FJMM:lead-福建民盟盟史导言",
    "domestic:HNMM:lead-民盟精神解析",
    "domestic:GXMM:lead--大公报-和-观察-对民盟被迫解散的不同反应",
    "domestic:BJTZB:lead-人民民主统一战线的巩固和扩大",
    "domestic:HBMJ:lead-民建简史第三章-迎接新中国的诞生",
    "domestic:ZJMG:lead-中国国民党革命委员会60年-一-",
    "domestic:MMSH:lead-新中国成立前民盟对政治协商制度的贡献",
    "domestic:FJMM:lead-少年记忆-初识民盟",
    "domestic:BJDCMM:reorganization-1944",
    "domestic:HLJMM:first-congress-files-1945",
    "domestic:GXMM:dagongbao-dissolution-report-1947-11-06",
    "domestic:GXMM:xinminbao-professors-statement-1947-11-04",
    "domestic:GXMM:observer-professors-statement-1947-11-08",
    "domestic:ZL1872:chang-lan-pcc-opening-transcript-1946",
    "domestic:MMSH:guangmingbao-formation-editorial-1941",
    "domestic:ZL1872:chang-lan-dissolution-statement-1947",
    "domestic:GXMM:dagongbao-tianjin-dissolution-1947-11-06",
    "domestic:ZJMM:yann-an-meeting-minmeng-1945-07-01",
    "domestic:GXMM:forced-dissolution-1947-11-05",
    "domestic:CPPCC:liang-shuming-guangmingbao-founding-2020",
    # T1.b LX 4 (wikisource 1941/1946 公开转录)
    "domestic:WS:democratic-league-declaration-1941",
    "domestic:WS:peace-building-program-1946",
    "domestic:WS:pcc-national-assembly-resolution-1946",
    "domestic:WS:pcc-government-reorganization-1946",
    # T1.c L3 3 (强 primary source)
    "domestic:HNMM:response-may-day-1948",
    "domestic:YADS:yanan-record-1945-07-04",
    "domestic:LNU:guangmingbao-index-1941",
}

REVIEW_NOTE = (
    "T1 accepted (codex-style 复审 2026-07-21)："
    "L4 29 地方民盟 lead-文章 + ZL1872 + CPPCC = 官方平台 + citation_only + full_item_online；"
    "LX 4 wikisource 1941/1946 公开转录 = webfetch 2026-07-21 全部 200；"
    "L3 3 强 primary source (HNMM 1948 五一 / YADS 1945 延安会谈记录 / LNU 1941 光明报索引)；"
    "accept 表示：URL 可达 / 身份可核 / 引用合规；"
    "不代表原档已实物核校 / 全文已逐字转录 / 复制权利已清。"
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
        # 保留 proposed 等级不变
        proposed = r.get("authenticity_level_proposed")
        if proposed:
            r["authenticity_level_accepted"] = proposed
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
