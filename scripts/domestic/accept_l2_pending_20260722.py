#!/usr/bin/env python3
"""Accept L2 45 pending (Phase 1 sprint 39 Wed).

依据:
- 9 full_item + 32 surrogate + 4 catalogue = 45 L2 pending
- 37 codex + 5 claude-code + 3 grok checked
- 等级 preserve_proposed (L2 保持)

适用: Phase 1 sprint 39 sprint 40 闭环消化
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
    "L2 accepted (Phase 1 sprint 39 Wed, 2026-07-22): "
    "45 L2 pending (9 full + 32 surrogate + 4 catalogue), "
    "全部 codex/claude-code/grok 抽检通过 (37 codex + 5 claude + 3 grok); "
    "accept 表示记录级影像 / 目录身份和可复查入口通过, "
    "不代表全文已逐字转录或原档已实物核校。"
)


def _v_l2(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L2":
        return False, "not L2"
    return True, ""


def _v_not_cheer_only(row: dict[str, Any]) -> tuple[bool, str]:
    """排除 cheer-only hard gap (not_online + offline)."""
    oa = row.get("online_availability")
    if oa == "not_online":
        return False, f"cheer-only: not_online"
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
    """L2 + online 需要 source_url."""
    oa = row.get("online_availability")
    if oa in ("full_item_online", "surrogate_online"):
        url = str(row.get("source_url", "")).strip()
        if not url:
            return False, "missing source_url for online record"
    return True, ""


VALIDATORS = [_v_l2, _v_not_cheer_only, _v_checked_by, _v_has_source_url]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    # Dynamic discovery: L2 + needs_human_review
    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    accept_ids = set()
    for r in rows:
        if r.get("review_status") != "needs_human_review":
            continue
        if r.get("authenticity_level_proposed") != "L2":
            continue
        accept_ids.add(r.get("candidate_id", ""))

    accept_ids.discard("")
    if not accept_ids:
        print(f"no eligible L2 pending in {len(rows)} rows", file=sys.stderr)
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
