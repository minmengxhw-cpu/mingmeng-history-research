#!/usr/bin/env python3
"""Accept 批次 A1: 6 条 ISBN 已验证的 L2 省级民盟组织史。

cheer 2026-07-20 批准选项 A：
- A1: 6 条 ISBN 完全验证的 L2 升 accepted (本脚本)
- A2: 11 条 ISBN 待查的降 L3 待补 ISBN 后再升 L2 (demote_batch_a2_to_l3_20260720.py)

6 条 ISBN 已验证:
1. domestic:QY:zhongguo-minmengtongmengshi-2012-qunyan (9787802563728)
2. domestic:QY:chongqing-minmengshi-2014-qunyan (9787802566224)
3. domestic:QY:zhongguo-minmengtongmeng-50nian-chongqing-2014 (9787802566217)
4. domestic:CQ:chongqing-minmeng-xu-chaojian-2002 (9787536657700)
5. domestic:FJ:zhongguo-minmengtongmeng-fujian-jianshi-2018 (978-7-5120-2896-2)
6. domestic:HN:hunan-minmengrenwu-2020 (9787519306090)

升级依据（与 FRUS L3→L2 一致）：
- 正式出版物（ISBN 已验证）
- 出版社权威（中央/省级人民出版社 + 群言出版社 + 线装书局）
- 编者权威（民盟中央/省委/党史协作小组）
- WebSearch 2026-07-20 多源核读
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_standard_main


ACCEPT_IDS = {
    "domestic:QY:zhongguo-minmengtongmengshi-2012-qunyan",          # ISBN 9787802563728
    "domestic:QY:chongqing-minmengshi-2014-qunyan",                  # ISBN 9787802566224
    "domestic:QY:zhongguo-minmengtongmeng-50nian-chongqing-2014",    # ISBN 9787802566217
    "domestic:CQ:chongqing-minmeng-xu-chaojian-2002",                # ISBN 9787536657700
    "domestic:FJ:zhongguo-minmengtongmeng-fujian-jianshi-2018",      # ISBN 978-7-5120-2896-2
    "domestic:HN:hunan-minmengrenwu-2020",                           # ISBN 9787519306090
}

REVIEW_NOTE = (
    "L2 accepted (cheer 2026-07-20 批准选项 A 批次 A1)："
    "ISBN 已验证 + 正式出版物 + 出版社权威（中央/省级人民出版社 + 群言出版社 + 线装书局）；"
    "WebSearch 2026-07-20 多源核读（孔夫子旧书网 + 各省人民出版社 + 各省民盟官网）；"
    "升级依据与 FRUS L3→L2 流程一致。"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    return run_standard_main(
        args.jsonl,
        args.apply,
        accept_ids=ACCEPT_IDS,
        review_note=REVIEW_NOTE,
        today="2026-07-20",
        reviewed_by="claude-code",
        level_mode="preserve_proposed",
    )


if __name__ == "__main__":
    raise SystemExit(main())
