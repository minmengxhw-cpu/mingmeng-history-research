#!/usr/bin/env python3
"""Record Codex page-level checks for the 1947 Observer issue."""

import json
from pathlib import Path


PATH = Path("data/domestic/candidates.jsonl")
UPDATES = {
    "domestic:NLC:observer-1947-v3n11": {
        "evidence_note": (
            "逐页核读公开原刊扫描：PDF第1页为《观察》第三卷第十一期封面，"
            "主标题栏列出《我们对于政府压迫民盟的看法》并标注‘周炳琳等四十八人’；"
            "PDF第3页为该联署声明正文首页及署名栏，PDF第4页为正文续页；"
            "卷期页眉与后期官方出处所指1947年11月8日相符。"
        ),
        "evidence_locator": (
            "NLC404-01J000332-6817；本地PDF第1、3—4页；"
            "data/domestic/press_scans/NLC404-01J000332-6817_观察_1947年3卷11期.pdf"
        ),
        "review_note": (
            "Codex于2026-07-18完成封面、声明首页、续页和署名栏页级核读；"
            "已确认声明位于PDF第3—4页，四十八人署名栏位于第3页；"
            "全文逐字转录、出版日及签名完整名单仍待人工转录，L1不变。"
        ),
    },
    "domestic:NLC:observer-1947-v3n11-dong-shijin": {
        "evidence_note": (
            "逐页核读公开原刊扫描：PDF第4页在《我们对于政府压迫民盟的看法》续页之后，"
            "刊载董时进署名的《我对于政府取缔民盟的感想》；PDF第5页继续刊载同题文章，"
            "标题、署名和文章连续版面均可直接辨认。"
        ),
        "evidence_locator": (
            "NLC404-01J000332-6817；本地PDF第4—5页；"
            "data/domestic/press_scans/NLC404-01J000332-6817_观察_1947年3卷11期.pdf"
        ),
        "review_note": (
            "Codex于2026-07-18完成PDF第4—5页题名、署名和连续版面核读；"
            "全文逐字转录及与联署声明的起止边界仍待人工转录，L1不变。"
        ),
    },
}


def main() -> None:
    updated = 0
    lines = []
    seen = set()
    for raw in PATH.read_text(encoding="utf-8").splitlines():
        item = json.loads(raw)
        cid = item.get("candidate_id")
        if cid in UPDATES:
            update = UPDATES[cid]
            item["evidence_note"] = update["evidence_note"]
            item["evidence_type"] = "digital_image"
            item["evidence_locator"] = update["evidence_locator"]
            item["review_note"] = update["review_note"]
            updated += 1
            seen.add(cid)
        lines.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
    missing = set(UPDATES) - seen
    if missing:
        raise SystemExit(f"missing candidate IDs: {sorted(missing)}")
    tmp = PATH.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(PATH)
    print(f"updated={updated}")


if __name__ == "__main__":
    main()
