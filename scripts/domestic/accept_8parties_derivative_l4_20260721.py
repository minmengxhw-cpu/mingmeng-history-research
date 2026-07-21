#!/usr/bin/env python3
"""Accept 5 条 L4 衍生内容（8 民主党派中央官网衍生）— cheer 2026-07-21 拍板。

依据：
- 4 条来自 mmzy.org.cn（民盟中央官网）lead-人物/lead-事件专题页 + 1945 一大专题
- 2 条来自 93.gov.cn（九三学社中央官网）lead-大事记 / lead-五一口号

等级：hardcode L4 (per cheer 决定 — 不论 proposed, 全部接受为 L4)。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 共享 lib (同目录)
sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_standard_main


ACCEPT_IDS = {
    # 民盟中央官网衍生（mmzy.org.cn）
    "domestic:MMZY:1945-first-congress-page",
    "domestic:MMZY:lead-周恩来与第一届人民政协会议的召开",
    "domestic:MMZY:lead-楚图南-民盟文章",
    # 九三学社中央官网衍生（93.gov.cn）
    "domestic:93JS:lead-九三学社1947年大事记",
    "domestic:93JS:lead-历史的必然-郑重的选择-中共中央发布-五一口号-的历史由",
}

REVIEW_NOTE = (
    "L4 accepted (cheer 2026-07-21 拍板)："
    "5 条均为 8 民主党派中央官网（mmzy.org.cn / 93.gov.cn）衍生内容（lead-人物文章 / lead-事件专题 / 大事记 / 党史专题页）；"
    "L4 等级保持不变（衍生品 = secondary，非原始档案影印件），"
    "accept 表示：URL 可访问 + 身份可核 + 引用合规（reuse_rights=citation_only），"
    "不代表原档已实物核校。"
)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    return run_standard_main(
        args.jsonl,
        args.apply,
        accept_ids=ACCEPT_IDS,
        review_note=REVIEW_NOTE,
        today="2026-07-21",
        level_mode="hardcode",
        hardcoded_level="L4",
    )


if __name__ == "__main__":
    raise SystemExit(main())
