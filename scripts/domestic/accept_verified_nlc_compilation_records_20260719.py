#!/usr/bin/env python3
"""Accept two explicitly page-bounded 1946 NLC compilation records.

This is record-level acceptance of the 1946 official compilation surrogate,
not acceptance of the 1941 original newspaper or an independent original.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_verifier_main


ACCEPT_IDS = {
    "domestic:NLC:minmeng-wenxian-1946-formation-declaration",
    "domestic:NLC:minmeng-wenxian-1946-ten-program",
}

REVIEW_NOTE = (
    "通过记录级1946年民盟总部官方汇编扫描审核：题名、日期、连续正文页界、目录定位、"
    "本地页图和SHA256已核对；保留L2。accepted仅表示该汇编记录是稳定可复查入口，"
    "不表示1941年《光明報》原刊、独立原始印本、底本关系、全文逐字转录或复制权利已经闭环。"
)

EXPECTED_LOCATOR_PATH = "work/domestic/minmeng_wenxian_1946/formation_9_13_images/"


def _v_repo_nlc(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("repository_code") != "NLC":
        return False, "not NLC"
    return True, ""


def _v_level_l2(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L2":
        return False, "unexpected evidence level"
    return True, ""


def _v_title_date(row: dict[str, Any]) -> tuple[bool, str]:
    if not row.get("document_date") or not row.get("title"):
        return False, "missing title/date"
    return True, ""


def _v_local_page_locator(row: dict[str, Any]) -> tuple[bool, str]:
    if EXPECTED_LOCATOR_PATH in str(row.get("evidence_locator", "")):
        return True, ""
    return False, "missing local page-image locator"


VALIDATORS = [_v_repo_nlc, _v_level_l2, _v_title_date, _v_local_page_locator]


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
    )


if __name__ == "__main__":
    raise SystemExit(main())
