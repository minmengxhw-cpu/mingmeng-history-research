#!/usr/bin/env python3
"""Accept T1 36 条 codex-style 复审低风险候选 (cheer 2026-07-21 拍板)。

依据 work/domestic/codex_review_20260721.md T1 档:
- T1.a L4 29 地方民盟 lead-文章 (full_item_online + 官方平台 + citation_only)
- T1.b LX 4 wikisource 1941/1946 公开转录 (webfetch 2026-07-21 全部 200)
- T1.c L3 3 强 primary source (HNMM 1948 五一 / YADS 1945 延安 / LNU 1941 索引)

等级: preserve_proposed (accept 不改等级, 保持原 L4/LX/L3)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_standard_main


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
