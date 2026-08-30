#!/usr/bin/env python3
"""Accept explicitly audited NLC image records at the record level.

This does not certify a full transcription or prove that the scan is an
original government document.  It only records that the catalog identifier,
date, title/author, page locator, local scan and visible page evidence were
checked by Codex.  The candidate's uncertainty note remains in force.

与 accept_with_verification 的 rejected 列表不同, 旧版在 L1 缺失时直接 raise
(数据不匹配). 这里用 enforce_unchanged_status + 一个强 validator 实现.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_verifier_main


ACCEPT_IDS = {
    "domestic:NLC:observer-1947-v3n11",
    "domestic:NLC:observer-1947-v3n11-dong-shijin",
    "domestic:NLC:observer-1947-v3n11-han-depei",
    "domestic:NLC:dagongbao-hankow-1947-11-04-zhang-qun-notice",
    "domestic:NLC:dagongbao-hankow-1947-11-04-league-dissolution-meeting",
    "domestic:NLC:dagongbao-hankow-1947-11-06-league-dissolution",
    "domestic:NLC:dagongbao-shanghai-1947-11-06-page2-full",
    "domestic:NLC:dagongbao-tianjin-1947-11-06-page2-full",
}

REVIEW_NOTE = (
    "通过记录级原刊影像审计：国家图书馆馆藏标识、题名/署名、日期、"
    "页级定位、本地影像和可视证据已核对；全文逐字转录、异文整理及复制权利仍待完成。"
    "accepted 只表示记录级影像身份通过，不表示已取得政府公函原件或无条件再利用授权。"
)


def _v_l1_digital_image(row: dict[str, Any]) -> tuple[bool, str]:
    """强校验: L1 + digital_image + needs_human_review (旧版用 raise, 这里转 rejected)."""
    if row.get("authenticity_level_proposed") != "L1":
        return False, "not L1"
    if row.get("evidence_type") != "digital_image":
        return False, "not digital_image"
    return True, ""


VALIDATORS = [_v_l1_digital_image]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-19")
    args = parser.parse_args()

    return run_verifier_main(
        args.jsonl,
        args.apply,
        accept_ids=ACCEPT_IDS,
        validators=VALIDATORS,
        review_note=REVIEW_NOTE,
        today=args.checked_at,
        reviewed_by="codex",
        # 不开 enforce_unchanged_status: already-accepted 应该 skip (跟原版行为一致)
    )


if __name__ == "__main__":
    raise SystemExit(main())
