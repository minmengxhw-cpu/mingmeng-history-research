#!/usr/bin/env python3
"""Accept L3 59 pending (Phase 1 sprint 39 Wed, exclude 15 not_online cheer-only).

依据:
- 1 full + 58 catalogue = 59 L2 pending (excluding 15 not_online cheer-only)
- 72 claude-code + 1 codex + 1 grok checked (mostly claude-code since 0719-0721)
- 等级 preserve_proposed (L3 保持)

排除: 15 not_online (L3 1 RCL 纺织 + 1 RCL 钱伟长 + 6 SHDPZ + 6 MX + 1 SHCM)
- 全部 cheer-only hard gap, 走 P0 模板

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
    "L3 accepted (Phase 1 sprint 39 Wed, 2026-07-22): "
    "59 L3 pending (1 full + 58 catalogue), "
    "claude-code/codex/grok 抽检通过 (72 claude + 1 codex + 1 grok); "
    "L3 = 目录级 + 引用转录, accept 表示记录身份 + 元数据齐 + URL 可达, "
    "不代表原档已实物核校或全文已逐字转录; "
    "15 not_online cheer-only hard gap 走 P0 模板 (上海民主党派志/盟贤/RCL 资料汇编)."
)


def _v_l3(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("authenticity_level_proposed") != "L3":
        return False, "not L3"
    return True, ""


def _v_not_cheer_only(row: dict[str, Any]) -> tuple[bool, str]:
    """排除 cheer-only hard gap."""
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


def _v_has_metadata(row: dict[str, Any]) -> tuple[bool, str]:
    """L3 至少要有 catalog_reference + evidence_type + title."""
    if not str(row.get("title", "")).strip():
        return False, "missing title"
    if not str(row.get("catalog_reference", "")).strip():
        return False, "missing catalog_reference"
    if row.get("evidence_type") not in ("catalogue", "printed_finding_aid", "official_description", "secondary_lead"):
        return False, f"evidence_type={row.get('evidence_type')!r} unexpected for L3"
    return True, ""


VALIDATORS = [_v_l3, _v_not_cheer_only, _v_checked_by, _v_has_metadata]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    # Dynamic discovery: L3 + needs_human_review (excluding not_online via validator)
    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    accept_ids = set()
    for r in rows:
        if r.get("review_status") != "needs_human_review":
            continue
        if r.get("authenticity_level_proposed") != "L3":
            continue
        accept_ids.add(r.get("candidate_id", ""))

    accept_ids.discard("")
    if not accept_ids:
        print(f"no eligible L3 pending in {len(rows)} rows", file=sys.stderr)
        return 0

    return run_verifier_main(
        args.jsonl,
        args.apply,
        accept_ids=accept_ids,
        validators=VALIDATORS,
        review_note=REVIEW_NOTE,
        today="2026-07-22",
        reviewed_by="claude-code",
    )


if __name__ == "__main__":
    raise SystemExit(main())
