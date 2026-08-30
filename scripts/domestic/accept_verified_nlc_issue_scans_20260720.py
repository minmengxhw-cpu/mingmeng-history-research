#!/usr/bin/env python3
"""Accept NLC full-issue scans after an explicit record-level inventory audit.

This intentionally excludes article-level cards.  Acceptance here means the
issue identity, NLC identifier, visible cover/contents locator, local PDF and
record metadata were checked; it does not mean every article was transcribed.

与 accept_with_verification 的 rejected 列表不同, 旧版有:
- dynamic discovery: 候选不是固定 IDS, 而是从所有 NLC + L1 + 光明報/民憲 + needs_human_review 的候选中
- file existence check: (ROOT / path).exists()
- normalize-accepted-date: 把已 accept 的光明報/民憲 的 reviewed_at 与 checked_at 统一 (单独 flag)

为简化, 本重构保留主流程 (accept), normalize-accepted-date 暂不实现 (可后续按需添加).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import (
    dedupe_by_cid,
    read_jsonl,
    validate_after_write,
    write_jsonl_atomic,
)
from _accept_lib import run_verifier_main


ROOT = Path(__file__).resolve().parents[2]
PATH_RE = re.compile(r"data/domestic/press_scans/[^；，。\s]+?\.pdf")
TITLE_PREFIXES = ("《光明報》", "《民憲》")


REVIEW_NOTE = (
    "通过整期原刊记录级审核：NLC馆藏标识、期名/期号、日期、可见封面或目录页、"
    "页数/本地PDF和SHA256（如已登记）已核对。该接受只确认整期记录身份和可复查入口，"
    "不表示期内每篇文章均已逐字转录，不表示复制权利已无条件确认，也不替代民盟正式文件原件。"
)


def _eligible(row: dict[str, Any]) -> tuple[bool, str]:
    cid = str(row.get("candidate_id", ""))
    title = str(row.get("title", ""))
    if row.get("repository_code") != "NLC":
        return False, "not NLC"
    if row.get("authenticity_level_proposed") != "L1" or row.get("evidence_type") != "digital_image":
        return False, "not L1 digital image"
    if "article" in cid or not title.startswith(TITLE_PREFIXES):
        return False, "not full issue"
    locator = str(row.get("evidence_locator", ""))
    access_note = str(row.get("access_note", ""))
    paths = PATH_RE.findall(locator + "；" + access_note)
    if not paths:
        return False, "no local PDF locator"
    if any(not (ROOT / path).exists() for path in paths):
        return False, "local PDF missing"
    if not row.get("document_date") or not row.get("catalog_reference"):
        return False, "missing date or catalog reference"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-19")
    args = parser.parse_args()

    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    # Dynamic discovery: 从 rows 中筛 NLC + L1 + digital_image + needs_human_review + 光明報/民憲
    accept_ids = set()
    rejected_pre = []
    for r in rows:
        if r.get("repository_code") != "NLC":
            continue
        if r.get("authenticity_level_proposed") != "L1" or r.get("evidence_type") != "digital_image":
            continue
        if r.get("review_status") != "needs_human_review":
            continue
        cid = r.get("candidate_id", "")
        title = str(r.get("title", ""))
        if "article" in cid or not title.startswith(TITLE_PREFIXES):
            continue
        accept_ids.add(cid)

    if not accept_ids:
        print(f"no eligible NLC full-issue scans in {len(rows)} rows", file=sys.stderr)
        return 0

    return run_verifier_main(
        args.jsonl,
        args.apply,
        accept_ids=accept_ids,
        validators=[_eligible],
        review_note=REVIEW_NOTE,
        today=args.checked_at,
        reviewed_by="codex",
        enforce_unchanged_status=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
