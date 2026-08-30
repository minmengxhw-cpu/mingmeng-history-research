#!/usr/bin/env python3
"""Accept T2.1 8 条 codex-style 复审低风险候选 (cheer 2026-07-21 拍板)。

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

注意: T2.1.c (L3 NLC 1946 目录缺页 1 条) 不包含, 保留 T2.2 走 cheer 决策。

等级: preserve_proposed (L3 / L4 各自保持原等级)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_standard_main


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
        level_mode="preserve_proposed",
    )


if __name__ == "__main__":
    raise SystemExit(main())
