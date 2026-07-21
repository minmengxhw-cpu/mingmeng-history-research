#!/usr/bin/env python3
"""批次 A2: 11 条 ISBN 待查的 L2 候选降级为 L3。

cheer 2026-07-20 批准选项 A：
- A1: 6 条 ISBN 已验证的 L2 升 accepted（独立脚本处理）
- A2: 11 条 ISBN 待查的 L2 → L3（保持 needs_human_review），待 ISBN 补查后再升 L2

11 条 ISBN 待查降 L3：
1. domestic:HB:hubei-minmengshi-2014-xiangbiwu
2. domestic:GZ:guizhou-minmengshi-2013
3. domestic:SN:shaanxi-minmengshi-chenxitao
4. domestic:GD:guangdong-minmengshi-2012-lijingxian
5. domestic:JS:jiangsu-minmengshi-gao-2004
6. domestic:JS:zhongguo-minmengtongmeng-jiangsu-jianshi-2012
7. domestic:HE:zhongguo-minmengtongmeng-shijiazhuang-shi-zhi-2013
8. domestic:YN:yunan-minmengshi-2021-chenguang
9. domestic:SC:sichuan-minmengshi-sichuan-renmin
10. domestic:AH:anhui-minzhudangpai-shi-meng-zhangjie-2009
11. domestic:BJ:beijing-minmeng-zuzhi-chengli-70-zhounian-2016

降级理由：
- L2 标准要求 ISBN 验证 + 出版社权威 + 编者权威
- ISBN 待查 → 暂不符合 L2 标准
- 保持 needs_human_review，待 ISBN 补查后再升 L2

不影响 XHB 新华日报影印本（属于批次 0 不在本批范围）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

DEMOTE_IDS = [
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
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]

    demoted, missing, skipped = [], [], []
    demote_set = set(DEMOTE_IDS)

    for r in rows:
        cid = r["candidate_id"]
        if cid not in demote_set:
            continue
        if r.get("authenticity_level_proposed") == "L3":
            skipped.append(cid)
            continue
        # 降级 L2 → L3
        r["authenticity_level_proposed"] = "L3"
        r["review_note"] = (
            "L3 needs_human_review（cheer 2026-07-20 批准选项 A 批次 A2 降级）："
            "ISBN 待查，暂不符合 L2 标准；"
            "保持 needs_human_review，待 ISBN 补查（孔夫子/豆瓣/京东/NLC 馆藏）后再升 L2。"
            "其他字段（出版社 + 编者 + 出版年）已 WebSearch 多源核读。"
        )
        demoted.append(cid)

    for cid in DEMOTE_IDS:
        if cid not in demoted and cid not in skipped:
            missing.append(cid)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {
            "demoted_l2_to_l3": demoted,
            "skipped_already_l3": skipped,
            "missing_not_found": missing,
            "applied": args.apply,
            "total_records": len(rows),
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())