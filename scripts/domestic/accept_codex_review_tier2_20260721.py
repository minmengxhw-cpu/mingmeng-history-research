#!/usr/bin/env python3
"""Accept T2.1 9 条 codex-style 复审低风险候选 (cheer 2026-07-21 拍板)。

依据 work/domestic/codex_review_tier2_20260721.md T2.1 档:

T2.1.a L3 5 强 primary source (webfetch 200 验证):
  - WS 1941 解放日报社论 (wikisource 200)
  - WS 1946 闻一多 (baidu baike 200, 刚修 URL)
  - WM 张澜墓 (wikimedia 200)
  - WM 西南联大旧址 (wikimedia 200)
  - BJDCMM 1945 临时全国代表大会宣言剪影 (200)

T2.1.b L4 3 张澜 1943 (URL 共享 zl1872.cn 专题页 producId=1397):
  - ZLWEB 1943-09-18 小册子
  - ZLWEB 1943-09-17 蒋介石当面交锋
  - JFB 1944-02-22 解放日报长文

T2.1.c (L3 NLC 1946 目录缺页 1 条不包含, 保留 T2.2 走 cheer 决策)

accept 表示：URL 可达 / 身份可核 / 引用合规。
不表示原档已实物核校 / 全文已逐字转录 / 复制权利已清。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"
ACCEPT_IDS = {
    # T2.1.a L3 5 强 primary source
    "domestic:WS:democratic-movement-editorial-1941",
    "domestic:WS:wen-yiduo-last-testament-1946",
    "domestic:WM:zhang-lan-tomb",
    "domestic:WM:xinan-lianda-jiuzhi-1946-meng",
    "domestic:BJDCMM:1945-congress-declaration-platform-clipping",
    # T2.1.b L4 3 张澜 1943
    "domestic:ZLWEB:1943-09-18-zhang-lan-china-needs-real-democracy",
    "domestic:ZLWEB:1943-09-17-jiang-zhang-chongqing-exchange",
    "domestic:JFB:1944-02-22-jiefang-ribao-zhang-lan-booklet-review",
}

REVIEW_NOTE = (
    "T2.1 accepted (codex-style 复审 2026-07-21)："
    "L3 5 强 primary source (WS 1941 解放日报社论 wikisource 200 / 闻一多 baike 200 已修 URL / "
    "WM 张澜墓 wikimedia 200 / WM 西南联大旧址 wikimedia 200 / BJDCMM 1945 宣言剪影 bjdcmm.org.cn 200)；"
    "L4 3 张澜 1943 (URL 共享 zl1872.cn/zxxnewsview.aspx?producid=1397 专题页)；"
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
