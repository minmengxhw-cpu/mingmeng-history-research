#!/usr/bin/env python3
"""Phase 1 P4-B accept: 1 L3 SHCM 1945 纲领目录 accept.

依据:
- 1 L3 pending: domestic:SHCM:revolutionary-relics-1945-minmeng-platform
- evidence_type = catalogue (官方目录)
- catalog_reference_status = verified
- source_url = https://whlyj.sh.gov.cn/...pdf (上海市文化和旅游局官方 PDF, 公开可访问)
- evidence_locator 引用 PDF 第159页条目1046 (中共一大会址纪念馆三级文物)

等级: preserve_proposed (L3 保持)
review_status: needs_human_review → accepted
reviewer: minimax
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_verifier_main


SHCM_ID = "domestic:SHCM:revolutionary-relics-1945-minmeng-platform"

REVIEW_NOTE = (
    "L3 accepted (Phase 1 P4-B 阶段 1 闭环, 2026-07-22): "
    "1945年10月中国民主同盟发布的《中国民主同盟纲领》官方目录条目. "
    "evidence_type=catalogue; catalog_reference_status=verified; "
    "source_url=上海市文化和旅游局《上海市第二批革命文物名录》官方 PDF (whlyj.sh.gov.cn), "
    "evidence_locator=PDF 第159页条目1046 (中共一大会址纪念馆三级文物, 数量1). "
    "accept 表示记录级官方目录身份和馆藏登记通过, "
    "不代表原件影像/页界/全文/复制权利已取得. "
    "升级 L2 需 cheer 提供原件影像或馆藏复制授权; "
    "升级 L1 需原件照片或 NLC 一类官方影像入口."
)


def _v_shcm(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("candidate_id") != SHCM_ID:
        return False, "not SHCM 1945 纲领记录"
    return True, ""


def _v_catalogue(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("evidence_type") != "catalogue":
        return False, f"evidence_type={row.get('evidence_type')!r} not catalogue"
    return True, ""


def _v_verified(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("catalog_reference_status") != "verified":
        return False, f"catalog_reference_status={row.get('catalog_reference_status')!r} not verified"
    return True, ""


def _v_l3(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L3":
        return False, "not L3"
    return True, ""


VALIDATORS = [_v_shcm, _v_l3, _v_catalogue, _v_verified]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    from _accept_lib import dedupe_by_cid, read_jsonl
    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    accept_ids = {SHCM_ID}
    print(f"SHCM 1945 纲领目录候选: {len(accept_ids)}")
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
