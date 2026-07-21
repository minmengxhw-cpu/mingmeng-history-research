#!/usr/bin/env python3
"""Upgrade 6 FRUS records from L3 (project-group internal compilation) to L2
after WebFetch verification against official history.state.gov digital edition.

Each FRUS record's underlying content was independently verified against the
official FRUS digital publication at history.state.gov on 2026-07-19:
- file number matches (e.g. 893.00/15104)
- page reference in printed FRUS confirmed
- despatch number confirmed
- author/date/recipient confirmed
- body text paraphrases match the local PDF's content

After this upgrade, the records become L2 (officially published US State
Department Foreign Relations of the United States volume) with review_status
= "accepted". The local PDF in 研究平台史料长编/ is still the project-group
internal compilation (L3 in its own right) but the verified content maps
directly to L2 archives.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-19"

# Mapping: candidate_id → upgrade info (verified file_no, page, original_verified_url)
UPGRADES = {
    "domestic:FRUS:1943-07-31-d232-ringwalt-liang-shuming-interview": {
        "frus_volume": "FRUS 1943 China",
        "frus_file_number": "893.00/15104",
        "frus_printed_page": "299",
        "frus_digital_url": "https://history.state.gov/historicaldocuments/frus1943China/d232",
        "additional_notes": (
            "WebFetch 2026-07-19 核读：原文完整包括 Ringwalt 梁漱溟访谈 + Perkins 1943-09-23 备忘录"
            "（page 299）；正文『Here follows detailed report』标注但内容已部分展开；"
            "完整详细报告访问 history.state.gov/d232 或 NARA 缩微。"
        ),
    },
    "domestic:FRUS:1943-09-18-d272-atcheson-federation-platform": {
        "frus_volume": "FRUS 1943 China",
        "frus_file_number": "893.00/15145",
        "frus_printed_page": "298",
        "frus_digital_url": "https://history.state.gov/historicaldocuments/frus1943China/d272",
        "additional_notes": (
            "WebFetch 2026-07-19 核读：原文确认；含 1941 末香港成立 + 4 个成员团体"
            "（中国青年党、国家社会党、乡村建设派、中华职业教育社）+ 5 点政治纲领"
            "（国民大会制、国防政府、军队国家化、地方民主化等）；"
            "附 Kweilin 1943-09-02 despatch No. 41 政治纲领详述（page 298）。"
        ),
    },
    "domestic:FRUS:1944-04-21-d329-gauss-service-minority-parties": {
        "frus_volume": "FRUS 1944 China v06",
        "frus_file_number": "893.00/15370",
        "frus_printed_page": "398",
        "frus_digital_url": "https://history.state.gov/historicaldocuments/frus1944v06/d329",
        "additional_notes": (
            "WebFetch 2026-07-19 核读：原文确认；附件 Service 备忘录（1944-04-14）涉及"
            "青年党左舜生、救国会沈钧儒访谈；青年党在自由中国约 20,000 党员，多数在四川；"
            "民主同盟等少数党派影响力远超实际党员数；附件未刊印。"
        ),
    },
    "domestic:FRUS:1944-07-11-d380-langdon-kunming-democratic-league": {
        "frus_volume": "FRUS 1944 China v06",
        "frus_file_number": "893.00/7-1144",
        "frus_printed_page": "470",
        "frus_digital_url": "https://history.state.gov/historicaldocuments/frus1944v06/d380",
        "additional_notes": (
            "WebFetch 2026-07-19 核读：原文确认；"
            "涉及昆明『宪政研究会文化界协会』（约 40 人，以大学教师为主），"
            "作为中国民主同盟的外围掩护组织运作；征集 1,500 签名向重庆宪政实施委员会请愿；"
            "1943-10 在国防最高委员会下设立。"
        ),
    },
    "domestic:FRUS:1944-09-22-d445-sprouse-democratic-league-principles": {
        "frus_volume": "FRUS 1944 China v06",
        "frus_file_number": "893.00/9-2244",
        "frus_printed_page": "584-585",
        "frus_digital_url": "https://history.state.gov/historicaldocuments/frus1944v06/d445",
        "additional_notes": (
            "WebFetch 2026-07-19 核读：原文确认；含 Sprouse 评《民主同盟政治原则草案》（罗隆基起草）"
            "全文摘要；草案在昆明民主同盟成员中代表想法；"
            "提及『民主同盟成都代表会议』召集在即；附件（草案译文）未刊印。"
        ),
    },
    "domestic:FRUS:1944-10-30-d478-gauss-war-final-stage-proposals": {
        "frus_volume": "FRUS 1944 China v06",
        "frus_file_number": "893.00/10-3144",
        "frus_printed_page": "663",
        "frus_digital_url": "https://history.state.gov/historicaldocuments/frus1944v06/d478",
        "additional_notes": (
            "WebFetch 2026-07-19 核读：原文确认；含民盟抗战最后阶段 5 点政治纲领"
            "（军队调整、终止一党政府建立联合政府、对英美苏友好、经济改革、教育改革）；"
            "Gauss 评论民盟纲领与中国共产党延安纲领『精神上甚至实际上的亲和』；"
            "附件（民盟提案译文）未刊印。"
        ),
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]

    upgraded, skipped = [], []
    for row in rows:
        cid = row.get("candidate_id", "")
        if cid not in UPGRADES:
            continue
        if row.get("review_status") == "accepted" and row.get("authenticity_level_accepted") == "L2":
            skipped.append(f"{cid} (already accepted L2)")
            continue

        u = UPGRADES[cid]

        # Update evidence_note to incorporate WebFetch verification details
        old_note = row.get("evidence_note", "")
        if "[FRUS 核读 2026-07-19]" not in old_note:
            new_note = (
                old_note.rstrip() + "\n\n"
                "【FRUS 官方核读 2026-07-19】" + u["additional_notes"]
            )
            row["evidence_note"] = new_note

        # Update catalog_reference to include page reference
        old_cat = row.get("catalog_reference", "")
        if "p." not in old_cat and "pp." not in old_cat and "Page" not in old_cat:
            row["catalog_reference"] = (
                f"{u['frus_volume']}, Document {cid.split('-d')[1].split('-')[0]}, "
                f"{u['frus_file_number']}, printed page {u['frus_printed_page']}"
            )

        # Promote to accepted L2
        row["authenticity_level_accepted"] = "L2"
        row["relevance_grade_accepted"] = row.get("relevance_grade_proposed", "core")
        row["review_status"] = "accepted"
        row["check_outcome"] = "pass"
        row["reviewed_at"] = TODAY
        row["reviewed_by"] = "claude-code"
        row["review_note"] = (
            "通过 history.state.gov 在线核读升级 L3 → L2：file number / 印刷页码 / despatch 号 / "
            "作者-日期-收件人 / 正文摘要 全部与官方 FRUS 数字版匹配；"
            "accepted 表示 FRUS 官方外交档案级别的研究入口已稳定，"
            "不表示附件（如『未刊印』Service 备忘录、Sprouse 草案译文）已取到完整正文。"
        )

        upgraded.append(cid)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {"upgraded": upgraded, "skipped": skipped, "applied": args.apply, "total_records": len(rows)},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
