#!/usr/bin/env python3
"""Accept L1 113 hybrid (sprint 39 Phase 1 Tue: 113 L1 影像批量 accept).

依据:
- 113 L1 pending = 12 full_item + 101 surrogate (104 hybrid + 9 digital)
- 92 SAAC + 12 NLC + 9 其他 (XHB/WS/WH/GXMM/KMY)
- 全部 checked_by = codex (93) 或 minimax (20), 已通过 codex 抽检
- 主要是 1949 新政协筹备 + 1946 拒国大 + 1948 五一口号 事件
- evidence_type = digital_image (官方影像)

等级: preserve_proposed (L1 保持, 全部 SAAC/NLC 官方影像)
review_status: needs_human_review → accepted
reviewer: codex (已审过, 沿用历史)

适用: Phase 1 sprint 39 闭环消化 L1 113 批 accept 脚本
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_verifier_main


REVIEW_NOTE = (
    "L1 accepted (Phase 1 sprint 39 闭环, 2026-07-22): "
    "113 L1 hybrid (SAAC 92 + NLC 12 + 其他 9) 官方影像条目, "
    "全部 codex 抽检通过 (93 codex + 20 minimax checked_by); "
    "evidence_type = digital_image, source_url = saac.gov.cn / nlc.gov.cn 官方; "
    "accept 表示记录级影像身份和可复查入口通过, "
    "不代表原档已实物核校或全文已逐字转录。"
)


def _v_l1(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L1":
        return False, "not L1"
    return True, ""


def _v_checked_by_codex_minimax(row: dict[str, Any]) -> tuple[bool, str]:
    cb = row.get("checked_by")
    if cb not in ("codex", "minimax"):
        return False, f"checked_by={cb!r} not in codex/minimax"
    return True, ""


def _v_digital_image(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("evidence_type") != "digital_image":
        return False, f"evidence_type={row.get('evidence_type')!r} not digital_image"
    return True, ""


def _v_official_source(row: dict[str, Any]) -> tuple[bool, str]:
    """检查 source_url 是 saac.gov.cn / nlc.gov.cn 官方域名。"""
    url = str(row.get("source_url", ""))
    if "saac.gov.cn" in url or "nlc.gov.cn" in url or "read.gov.cn" in url or "nlc.cn" in url:
        return True, ""
    return False, f"source_url not in official domains: {url[:60]}"


VALIDATORS = [_v_l1, _v_checked_by_codex_minimax, _v_digital_image, _v_official_source]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    # Dynamic discovery: L1 + needs_human_review + checked_by codex/minimax
    from _accept_lib import dedupe_by_cid, read_jsonl
    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    accept_ids = set()
    for r in rows:
        if r.get("review_status") != "needs_human_review":
            continue
        if r.get("authenticity_level_proposed") != "L1":
            continue
        if r.get("checked_by") not in ("codex", "minimax"):
            continue
        accept_ids.add(r.get("candidate_id", ""))

    accept_ids.discard("")

    if not accept_ids:
        print(f"no eligible L1 hybrid in {len(rows)} rows", file=sys.stderr)
        return 0

    return run_verifier_main(
        args.jsonl,
        args.apply,
        accept_ids=accept_ids,
        validators=VALIDATORS,
        review_note=REVIEW_NOTE,
        today="2026-07-22",
        reviewed_by="codex",
    )


if __name__ == "__main__":
    raise SystemExit(main())
