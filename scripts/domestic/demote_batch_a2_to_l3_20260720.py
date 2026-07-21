#!/usr/bin/env python3
"""批次 A2: 11 条 ISBN 待查的 L2 候选降级为 L3。

cheer 2026-07-20 批准选项 A：
- A1: 6 条 ISBN 已验证的 L2 升 accepted (独立脚本处理 accept_batch_a1_l2_books)
- A2: 11 条 ISBN 待查的 L2 → L3 (本脚本, 保持 needs_human_review),
       待 ISBN 补查后再升 L2

降级理由:
- L2 标准要求 ISBN 验证 + 出版社权威 + 编者权威
- ISBN 待查 → 暂不符合 L2 标准
- 保持 needs_human_review，待 ISBN 补查（孔夫子/豆瓣/京东/NLC 馆藏）后再升 L2

不影响 XHB 新华日报影印本（属于批次 0 不在本批范围）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import (
    dedupe_by_cid,
    demote_level,
    read_jsonl,
    validate_after_write,
    write_jsonl_atomic,
)


DEMOTE_IDS = {
    "domestic:HB:hubei-minmengshi-2014-xiangbiwu",
    "domestic:GZ:guizhou-minmengshi-2013",
    "domestic:SN:shaanxi-minmengshi-chenxitao",
    "domestic:GD:guangdong-minmengshi-2012-lijingxian",
    "domestic:JS:jiangsu-minmengshi-gao-2004",
    "domestic:JS:zhongguo-minmengtongmeng-jiangsu-jianshi-2012",
    "domestic:HE:zhongguo-minmengtongmeng-shijiazhuang-shi-zhi-2013",
    "domestic:YN:yunan-minmengshi-2021-chenguang",
    "domestic:SC:sichuan-minmengshi-sichuan-renmin",
    "domestic:AH:anhui-minzhudangpai-shi-meng-zhangjie-2009",
    "domestic:BJ:beijing-minmeng-zuzhi-chengli-70-zhounian-2016",
}

REVIEW_NOTE = (
    "L3 needs_human_review (cheer 2026-07-20 批准选项 A 批次 A2 降级)："
    "ISBN 待查，暂不符合 L2 标准；"
    "保持 needs_human_review，待 ISBN 补查（孔夫子/豆瓣/京东/NLC 馆藏）后再升 L2。"
    "其他字段（出版社 + 编者 + 出版年）已 WebSearch 多源核读。"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    rows, demoted, skipped, missing = demote_level(
        rows,
        DEMOTE_IDS,
        from_level="L2",
        to_level="L3",
        review_note=REVIEW_NOTE,
    )

    backup_path = None
    if args.apply:
        backup_path = write_jsonl_atomic(args.jsonl, rows)
        if not validate_after_write(args.jsonl):
            return 3

    summary = {
        "demoted_l2_to_l3": demoted,
        "skipped": skipped,
        "missing_not_found": missing,
        "applied": args.apply,
        "backup": str(backup_path) if backup_path else None,
        "total_records": len(rows),
        "demote_set_size": len(DEMOTE_IDS),
    }
    # 数字校验
    if (len(demoted) + len(skipped) + len(missing)) != len(DEMOTE_IDS):
        print(
            f"ERROR: count mismatch (demoted+skipped+missing={len(demoted)+len(skipped)+len(missing)} "
            f"!= demote_set_size={len(DEMOTE_IDS)})",
            file=sys.stderr,
        )
        return 4
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
