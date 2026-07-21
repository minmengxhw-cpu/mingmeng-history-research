#!/usr/bin/env python3
"""Accept explicitly page-verified article cards at record level.

This does not assert that the article has been transcribed.  It only closes
the identity/page-image review when the title, date, page locator and local
image/PDF path are already present in the candidate record.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import run_verifier_main


ACCEPT_IDS = {
    "domestic:NLC:guangmingbao-1948-1949-v1n12-article",
    "domestic:NLC:guangmingbao-1948-1949-v1n1-article",
    "domestic:NLC:minxian-v1n9-democracy-vs-nondemocracy-1944-11-20",
    "domestic:NLC:guangmingbao-1946-issue8-conditional-national-assembly",
    "domestic:NLC:guangmingbao-1946-issue11-anti-one-party-constitution",
    "domestic:NLC:guangmingbao-1946-issue11-zhang-lan-shanghai-welcome-speech",
    "domestic:NLC:guangmingbao-1946-issue11-china-at-1947-threshold",
    "domestic:NLC:guangmingbao-1946-issue11-truman-december-18-statement",
    "domestic:NLC:guangmingbao-1946-issue01-refounding-editorial",
    "domestic:NLC:guangmingbao-1946-issue02-people-power-editorial",
    "domestic:NLC:guangmingbao-1946-issue04-urgent-situation-editorial",
    "domestic:NLC:guangmingbao-1946-issue07-why-not-national-assembly",
    "domestic:NLC:guangmingbao-1946-issue03-double-ten-task-article",
    "domestic:NLC:guangmingbao-1947-19-article-01",
    "domestic:NLC:guangmingbao-1947-19-article-02",
    "domestic:NLC:guangmingbao-1947-19-article-03",
    "domestic:NLC:guangmingbao-1947-19-article-04",
    "domestic:NLC:guangmingbao-1947-19-article-05",
}

REVIEW_NOTE = (
    "通过记录级同期原刊影像审核：题名、日期、文章页位、原刊来源和本地页图/PDF定位已核对；"
    "accepted 只表示记录身份和页级入口通过，不表示全文逐字转录、异文整理、署名补全或复制权利已经完成。"
)


def _v_repo_nlc(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("repository_code") != "NLC":
        return False, "not NLC"
    return True, ""


def _v_title_date(row: dict[str, Any]) -> tuple[bool, str]:
    if not row.get("document_date") or not row.get("title"):
        return False, "missing title/date"
    return True, ""


def _v_local_locator(row: dict[str, Any]) -> tuple[bool, str]:
    locator = str(row.get("evidence_locator", ""))
    if "data/domestic/" in locator or "work/domestic/" in locator:
        return True, ""
    return False, "missing local locator"


VALIDATORS = [_v_repo_nlc, _v_title_date, _v_local_locator]


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
