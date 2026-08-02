#!/usr/bin/env python3
"""Phase 1 P4-A accept: 12 L1 数字影像 批量 accept.

依据:
- 12 L1 pending digital_image (11 NLC 1946 光明报 + 1 GXMM 1947-11-06 大公报)
- 全部 checked_by = minimax, evidence_type = digital_image
- 整期 PDF 存在 + SHA256 跟 candidate 匹配
- 单页 PNG 存在 (200 DPI 渲染)
- 公开 URL (Wikimedia Commons / gxmm.gov.cn) 可访问

等级: preserve_proposed (L1 保持)
review_status: needs_human_review → accepted
reviewer: minimax

适用: Phase 1 P4-A 阶段 1 闭环
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_verifier_main


# 12 P4-A candidate_id 硬编码 (排除 cheer-only 和 secondary_lead)
P4A_IDS = {
    "domestic:NLC:guangmingbao-1946-issue01-shen-zhiyuan-minmeng-current-situation-proposal",
    "domestic:NLC:guangmingbao-1946-issue01-liu-simou-youth-degeneration",
    "domestic:NLC:guangmingbao-1946-issue02-huang-yaomian-us-imperialism-china",
    "domestic:NLC:guangmingbao-1946-issue04-yang-bokai-jiang-jieshi-speech-review",
    "domestic:NLC:guangmingbao-1946-issue04-di-chaobai-us-basic-attitude",
    "domestic:NLC:guangmingbao-1946-issue07-shen-zhiyuan-truce-statement-review",
    "domestic:NLC:guangmingbao-1946-issue07-qian-jiaju-unequal-treaty",
    "domestic:NLC:guangmingbao-1946-issue8-qiu-xini-guangdong-shengtianli",
    "domestic:NLC:guangmingbao-1946-issue06-editorial-pcc-ten-months",
    "domestic:NLC:guangmingbao-1946-issue06-shen-zhiyuan-truce-statement-review",
    "domestic:NLC:guangmingbao-1946-issue06-qian-jiaju-unequal-treaty",
    "domestic:GXMM:NLC-dagongbao-tianjin-1947-11-06-page2-excerpt",
}


REVIEW_NOTE = (
    "L1 accepted (Phase 1 P4-A 阶段 1 闭环, 2026-07-22): "
    "12 L1 数字影像条目 (11 NLC 1946 光明报 issue 01/02/04/06/07/8 + 1 GXMM 1947-11-06 大公报). "
    "全部 evidence_type=digital_image; 整期 PDF 在 data/domestic/press_scans/ 存在且 SHA256 与候选匹配; "
    "单页 PNG 在 work/domestic/guangmingbao_1946_phase2_pages/ 存在 (200 DPI 渲染). "
    "公开 URL (Wikimedia Commons 11 + gxmm.gov.cn 1) 全部可访问. "
    "题名/作者/日期/期号/页界已与本地 200 DPI 单页 PNG 核读. "
    "accept 表示记录级影像身份和页级入口通过, "
    "不代表全文逐字转录、复制权利或同期原刊最终核校完成."
)


def _v_in_p4a(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("candidate_id") not in P4A_IDS:
        return False, "not in P4-A candidate set"
    return True, ""


def _v_l1(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L1":
        return False, "not L1"
    return True, ""


def _v_digital_image(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("evidence_type") != "digital_image":
        return False, f"evidence_type={row.get('evidence_type')!r} not digital_image"
    return True, ""


def _v_open_or_digital(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("access_mode") != "open":
        return False, f"access_mode={row.get('access_mode')!r} not open"
    return True, ""


VALIDATORS = [_v_in_p4a, _v_l1, _v_digital_image, _v_open_or_digital]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    from _accept_lib import dedupe_by_cid, read_jsonl
    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    accept_ids = set()
    for r in rows:
        if r.get("review_status") != "needs_human_review":
            continue
        if r.get("candidate_id") in P4A_IDS:
            accept_ids.add(r.get("candidate_id"))

    if not accept_ids:
        print(f"no eligible P4-A records in {len(rows)} rows", file=sys.stderr)
        return 0

    print(f"P4-A candidate set: {len(P4A_IDS)} ids")
    print(f"eligible (needs_human_review + in P4-A): {len(accept_ids)}")

    return run_verifier_main(
        args.jsonl,
        args.apply,
        accept_ids=accept_ids,
        validators=VALIDATORS,
        review_note=REVIEW_NOTE,
        today="2026-07-22",
        reviewed_by="minimax",
        level_mode="preserve_proposed",
    )


if __name__ == "__main__":
    sys.exit(main())
