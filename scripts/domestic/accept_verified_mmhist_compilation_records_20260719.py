#!/usr/bin/env python3
"""Accept three explicitly page-bounded MMHIST compilation records.

The records remain L2 compilation evidence.  Acceptance closes the identity,
title, date and page-boundary review only; it does not claim that the 1983
surrogate is the 1941/1945 original or that a diplomatic transcription is
complete.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_verifier_main


ACCEPT_IDS = {
    "domestic:MMHIST:formation-declaration-1941",
    "domestic:MMHIST:platform-1945",
    "domestic:MMHIST:congress-declaration-1945",
}

REVIEW_NOTE = (
    "通过记录级正式汇编扫描审核：题名、日期、正文页界、下一文边界和本地页图定位已核对；"
    "保留L2，accepted只表示该汇编记录可作为稳定研究入口，不表示1941/1945原件 provenance、"
    "同期原刊互校、全文逐字转录、异文整理或复制权利已经完成。"
)


def _v_repo_mmhist(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("repository_code") != "MMHIST":
        return False, "not MMHIST"
    return True, ""


def _v_level_l2(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L2":
        return False, "unexpected evidence level"
    return True, ""


def _v_title_date(row: dict[str, Any]) -> tuple[bool, str]:
    if not row.get("document_date") or not row.get("title"):
        return False, "missing title/date"
    return True, ""


def _v_mmhist_local_locator(row: dict[str, Any]) -> tuple[bool, str]:
    if "work/domestic/mmhist_" in str(row.get("evidence_locator", "")):
        return True, ""
    return False, "missing MMHIST local page locator"


VALIDATORS = [_v_repo_mmhist, _v_level_l2, _v_title_date, _v_mmhist_local_locator]


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
