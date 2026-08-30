#!/usr/bin/env python3
"""Accept 批次 D-A: 24 条 L2 升 accepted（8 党派官网 + 1 saac 聚合 + 15 saac 具体档案）。

L3（特园 + 二史馆）保持 needs_human_review。

依据：
- 8 党派中央官网 = 各党派中央委员会发布 + 多源印证（WebSearch 2026-07-20）
- saac.gov.cn = 中央档案馆 / 国家档案局官方公布（含 200+ 珍贵档案部分首次公开）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_standard_main


ACCEPT_IDS = {
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
}

REVIEW_NOTE = (
    "L2 accepted (批次 D-A)："
    "8 党派官网 = 各党派中央委员会官方发布 + WebSearch 多源印证；"
    "saac.gov.cn = 中央档案馆 / 国家档案局官方公布；"
    "升级依据与 FRUS L3→L2 流程一致（多源核读 + 官方一手）。"
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
