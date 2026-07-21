#!/usr/bin/env python3
"""Accept L4 6 pending (Phase 1 sprint 39 Wed, exclude 1 not_online cheer-only).

依据:
- 6 catalogue (5 codex + 1 claude-code checked)
- 1 not_online cheer-only (SHPRESS 张澜 时代日报) - 排除

L4 = 衍生 / lead 文章 / secondary 来源, accept 表示:
- URL 可达 + 身份可核 + 引用合规 (reuse_rights=citation_only)
- 不代表原档已实物核校或全文已逐字转录

适用: Phase 1 sprint 39/40 闭环消化
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import (
    dedupe_by_cid,
    read_jsonl,
    run_verifier_main,
)


REVIEW_NOTE = (
    "L4 accepted (Phase 1 sprint 39 Wed, 2026-07-22): "
    "6 L4 catalogue pending (1 SHAC + 1 MMYunnan + 3 GXMM 1947-10 大公报 + 1 MH 近代史平台 国讯), "
    "codex/claude-code 抽检通过; "
    "L4 = 衍生 / lead 文章 / secondary 来源 (地方民盟平台 / 转载 / 学术 PDF), "
    "accept 表示 URL 可达 + 身份可核 + 引用合规 (reuse_rights=citation_only); "
    "不代表原档已实物核校或全文已逐字转录; "
    "1 not_online cheer-only (SHPRESS 张澜 时代日报) 排除, 走 P0 模板."
)


def _v_l4(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L4":
        return False, "not L4"
    return True, ""


def _v_not_cheer_only(row: dict[str, Any]) -> tuple[bool, str]:
    oa = row.get("online_availability")
    if oa == "not_online":
        return False, "cheer-only: not_online"
    am = row.get("access_mode")
    if am in ("offline", "reading_room"):
        return False, f"cheer-only: access_mode={am}"
    return True, ""


def _v_checked_by(row: dict[str, Any]) -> tuple[bool, str]:
    cb = row.get("checked_by")
    if cb not in ("codex", "claude-code", "grok", "minimax"):
        return False, f"checked_by={cb!r} not recognized"
    return True, ""


def _v_has_source_url(row: dict[str, Any]) -> tuple[bool, str]:
    url = str(row.get("source_url", "")).strip()
    if not url:
        return False, "missing source_url"
    return True, ""


VALIDATORS = [_v_l4, _v_not_cheer_only, _v_checked_by, _v_has_source_url]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    accept_ids = set()
    for r in rows:
        if r.get("review_status") != "needs_human_review":
            continue
        if r.get("authenticity_level_proposed") != "L4":
            continue
        accept_ids.add(r.get("candidate_id", ""))

    accept_ids.discard("")
    if not accept_ids:
        print(f"no eligible L4 pending in {len(rows)} rows", file=sys.stderr)
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
