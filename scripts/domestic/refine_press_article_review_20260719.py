#!/usr/bin/env python3
"""Write page-image review findings back to domestic candidate records."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "data/domestic/candidates.jsonl"


UPDATES = {
    "domestic:NLC:observer-1947-v3n11": {
        "evidence_note": "已完成人工目视复核：PDF第3页为《我们对于政府压迫民盟的看法》正文首页及‘周炳琳等四十八人’联署栏，第4页为声明续页；第4页后半转入董时进文章，第5页另起韩德培文章。该期为1947-11-08同期政论周刊原刊，不是内政部宣布非法公函。",
        "evidence_locator": "NLC404-01J000332-6817；本地PDF第1、3—5页；work/domestic/observer_v3n11_pages/page3.png、page4.png；work/domestic/observer_dagongbao_transcription_index_20260719.md",
        "uncertainty_note": "联署名单逐名转录、声明全文转录、期刊出版日的馆藏元数据和原刊复制权利仍待逐项核对；OCR只作导航。",
    },
    "domestic:NLC:observer-1947-v3n11-dong-shijin": {
        "evidence_note": "已完成人工目视复核：PDF第4页右侧竖排题名为《我对于政府取缔民盟的感想》，正文承接声明之后开始并在该页内完成，页末署‘董时进’；PDF第5页已另起韩德培文章。",
        "evidence_locator": "NLC404-01J000332-6817；本地PDF第4页；work/domestic/observer_v3n11_pages/page4.png；work/domestic/observer_v3n11_ocr/page4.ocr.md",
        "uncertainty_note": "文章全文仍未逐字转录；OCR存在竖排分栏顺序和异体字误识，正式引用必须回到第4页图像核对。",
    },
    "domestic:NLC:observer-1947-v3n11-han-depei": {
        "evidence_note": "已完成人工目视复核：PDF第5页右侧竖排题名为《人身自由的问题》，页末署‘韩德培’；该文不是董时进《我对于政府取缔民盟的感想》的续页。",
        "evidence_locator": "NLC404-01J000332-6817；本地PDF第5页（由原PDF页定位）；work/domestic/observer_dagongbao_transcription_index_20260719.md",
        "uncertainty_note": "文章与1947年民盟事件的论证关系、全文转录和原刊复制权利仍待核对；本条只确认题名、署名和页界。",
    },
    "domestic:NLC:dagongbao-hankow-1947-11-04-zhang-qun-notice": {
        "evidence_note": "已完成人工目视复核：汉口版1947-11-04第1版目标标题可见，报道位于同日民盟解散前的新闻版面；其内容属于报刊对张群书面通知的报道，不等同于张群原件或内政部公函。",
        "evidence_locator": "NLC1080-00N001037-7604；本地PDF第1页；work/domestic/dagongbao_nlc_7604_7606/issue7604-1.png；work/domestic/dagongbao_nlc_7604_7606/ocr_full/issue7604-1.ocr.md",
        "uncertainty_note": "正文逐字转录、消息电头、报道来源链和原刊复制权利仍待核对；OCR只作定位。",
    },
    "domestic:NLC:dagongbao-hankow-1947-11-04-league-dissolution-meeting": {
        "evidence_note": "已完成人工目视复核：汉口版1947-11-04第1版可见‘民盟将召开中常会讨论解散’标题，记录的是解散前会议消息与同期传播语境，不是民盟总部解散公告原件。",
        "evidence_locator": "NLC1080-00N001037-7604；本地PDF第1页；work/domestic/dagongbao_nlc_7604_7606/issue7604-1.png；work/domestic/dagongbao_nlc_7604_7606/ocr_full/issue7604-1.ocr.md",
        "uncertainty_note": "正文逐字转录、中央社电头及消息来源链仍待核对；报刊影像的复制权利待核。",
    },
    "domestic:NLC:dagongbao-hankow-1947-11-06-league-dissolution": {
        "title": "民盟正式宣告解散·通告各地盟员停止政治活动",
        "evidence_note": "已完成人工目视复核：汉口版1947-11-06第1版版头、日期和刊名可见，目标大标题为‘民盟正式宣告解散’，副标题为‘通告各地盟员停止政治活动’；该页同时编排报道、公告转引和其他中央社材料，须分栏引用。",
        "evidence_locator": "NLC1080-00N001037-7606；本地PDF第1页；work/domestic/dagongbao_nlc_7604_7606/issue7606-1.png；work/domestic/dagongbao_nlc_7604_7606/ocr_full/issue7606-1.ocr.md",
        "uncertainty_note": "报道与公告转引的逐栏边界、全文逐字转录及原刊复制权利仍待核对；本条是同期报刊报道，不等同于民盟总部原始解散公告。",
    },
}


def main() -> int:
    rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen = set()
    for row in rows:
        update = UPDATES.get(row["candidate_id"])
        if update:
            row.update(update)
            row["checked_at"] = "2026-07-19"
            row["checked_by"] = "codex"
            row["reviewed_at"] = "2026-07-19"
            row["reviewed_by"] = "codex"
            seen.add(row["candidate_id"])
    missing = sorted(set(UPDATES) - seen)
    if missing:
        raise SystemExit("missing candidate IDs: " + ", ".join(missing))
    PATH.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"updated": len(seen), "path": str(PATH)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
