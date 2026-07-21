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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import (
    dedupe_by_cid,
    read_jsonl,
    upgrade_level,
    validate_after_write,
    write_jsonl_atomic,
)


TODAY = "2026-07-19"

REVIEW_NOTE = (
    "通过 history.state.gov 在线核读升级 L3 → L2：file number / 印刷页码 / despatch 号 / "
    "作者-日期-收件人 / 正文摘要 全部与官方 FRUS 数字版匹配；"
    "accepted 表示 FRUS 官方外交档案级别的研究入口已稳定，"
    "不表示附件（如『未刊印』Service 备忘录、Sprouse 草案译文）已取到完整正文。"
)

EVIDENCE_NOTE_PREFIX = "【FRUS 官方核读 2026-07-19】"

# Mapping: candidate_id → upgrade info
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


def _build_upgrade_dict() -> dict[str, dict]:
    """将 UPGRADES 映射到 upgrade_level 期望的格式."""
    result = {}
    for cid, info in UPGRADES.items():
        evidence_note_addition = EVIDENCE_NOTE_PREFIX + info["additional_notes"]
        doc_num = cid.split("-d")[1].split("-")[0]
        catalog_reference = (
            f"{info['frus_volume']}, Document {doc_num}, "
            f"{info['frus_file_number']}, printed page {info['frus_printed_page']}"
        )
        result[cid] = {
            "field_updates": {
                "authenticity_level_accepted": "L2",
                "evidence_note": evidence_note_addition,
                "catalog_reference": catalog_reference,
            },
            "review_note": REVIEW_NOTE,
            "append_evidence_note": True,
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    upgrade_specs = _build_upgrade_dict()
    rows, upgraded, skipped = upgrade_level(
        rows,
        upgrade_specs,
        today=TODAY,
        reviewed_by="claude-code",
    )

    backup_path = None
    if args.apply:
        backup_path = write_jsonl_atomic(args.jsonl, rows)
        if not validate_after_write(args.jsonl):
            return 3

    summary = {
        "upgraded": upgraded,
        "skipped": skipped,
        "applied": args.apply,
        "backup": str(backup_path) if backup_path else None,
        "total_records": len(rows),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
