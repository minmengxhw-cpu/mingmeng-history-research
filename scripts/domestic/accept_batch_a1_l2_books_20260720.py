#!/usr/bin/env python3
"""Accept 批次 A1: 7 条 ISBN 已验证的 L2 省级民盟组织史。

cheer 2026-07-20 批准选项 A：
- A1: 7 条 ISBN 完全验证的 L2 升 accepted
- A2: 11 条 ISBN 待查的降 L3 待补 ISBN 后再升 L2

7 条 ISBN 已验证：
1. domestic:QY:zhongguo-minmengtongmengshi-2012-qunyan (9787802563728)
2. domestic:QY:chongqing-minmengshi-2014-qunyan (9787802566224)
3. domestic:QY:zhongguo-minmengtongmeng-50nian-chongqing-2014 (9787802566217)
4. domestic:CQ:chongqing-minmeng-xu-chaojian-2002 (9787536657700)
5. domestic:FJ:zhongguo-minmengtongmeng-fujian-jianshi-2018 (978-7-5120-2896-2)
6. domestic:HN:hunan-minmengrenwu-2020 (9787519306090)
7. (原本建议 JS 江苏简史 2012 中央党史 + BJ 北京 70周年 2016，但实际两者 ISBN 待查)

→ 实际为 6 条 ISBN 完全验证（1-6），加 QY 50年画册 9787802566217 = 6 条

升级依据（与 FRUS L3→L2 一致）：
- 正式出版物（ISBN 已验证）
- 出版社权威（中央/省级人民出版社 + 群言出版社 + 线装书局）
- 编者权威（民盟中央/省委/党史协作小组）
- WebSearch 2026-07-20 多源核读
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

# 6 条 ISBN 已验证的 L2 候选（精确匹配 candidate_id）
ACCEPT_IDS = [
    "domestic:QY:zhongguo-minmengtongmengshi-2012-qunyan",          # ISBN 9787802563728
    "domestic:QY:chongqing-minmengshi-2014-qunyan",                  # ISBN 9787802566224
    "domestic:QY:zhongguo-minmengtongmeng-50nian-chongqing-2014",    # ISBN 9787802566217
    "domestic:CQ:chongqing-minmeng-xu-chaojian-2002",                # ISBN 9787536657700
    "domestic:FJ:zhongguo-minmengtongmeng-fujian-jianshi-2018",      # ISBN 978-7-5120-2896-2
    "domestic:HN:hunan-minmengrenwu-2020",                           # ISBN 9787519306090
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
        # 升级 L2 needs_human_review → L2 accepted
        r["review_status"] = "accepted"
        r["review_note"] = (
            "L2 accepted (cheer 2026-07-20 批准选项 A 批次 A1)："
            "ISBN 已验证 + 正式出版物 + 出版社权威（中央/省级人民出版社 + 群言出版社 + 线装书局）；"
            "WebSearch 2026-07-20 多源核读（孔夫子旧书网 + 各省人民出版社 + 各省民盟官网）；"
            "升级依据与 FRUS L3→L2 流程一致。"
        )
        # 添加 accepted_at 时间戳（不破坏 schema）
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