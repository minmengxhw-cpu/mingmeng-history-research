#!/usr/bin/env python3
"""Record Codex page-level checks for the early-period compilation entries."""

import json
from pathlib import Path


PATH = Path("data/domestic/candidates.jsonl")
UPDATES = {
    "domestic:LNU:guangmingbao-index-1941": (
        "已下载并人工核读岭南大学公开索引 PDF：索引第2页为《光明报》1941年10—11月香港工运剪报手写记录，共13条，条目均标注原刊第3版；可辨认日期为1941-10-14、10-18、11-01、11-04、11-08、11-10、11-11、11-12、11-14、11-22、11-23、11-26等。索引中未见1941-10-10成立宣言或1941-10-16成立社论条目，因此本轮形成明确负向结果，不把该索引当作民盟成立原刊。",
        "机构页面与本地 PDF 第2页；SHA256 7ff54b899dddbfe4f089aca87c3ca98b4de1fcd0074e0ae571f598bdcceb3a9；data/domestic/press_scans/LNU_PROFMKCHAN_INDEXLIST_14_光明報_1941.pdf",
    ),
    "domestic:MMHIST:formation-declaration-1941": (
        "正文页界已核读：公开扫描 PDF 第35—37页（书内第5—7页）连续构成《中国民主政团同盟成立宣言》，第35页有标题和1941年10月10日日期，第37页正文结束；第38页已转入下一份《中国民主同盟纲领》。",
        "PDF第35—37页（书内第5—7页）本地页图：work/domestic/mmhist_formation_1941_pages/page-035.png；page-036.png；page-037.png；PDF第38页为下一文边界核验：work/domestic/mmhist_formation_1941_pages/page-038.png；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:program-draft-1944-09-19": (
        "正文页已核读：公开扫描 PDF 扫描书内第26页（PDF 第56页）标题为《中国民主同盟纲领草案》，标注‘一九四四年九月十九日全国代表会议通过’；该页正文可见。",
        "PDF扫描书内第26页（PDF第56页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:platform-1945": (
        "正文页界已核读：公开扫描 PDF 第96—100页（书内第66—70页）连续构成《中国民主同盟纲领》，第96页有标题和‘一九四五年十月临时全国代表大会通过’，第100页正文结束；第101页已转入《中国民主同盟临时全国代表大会政治报告》。",
        "PDF第96—100页（书内第66—70页）本地页图：work/domestic/mmhist_platform_1945_pages/page-096.png至page-100.png；PDF第101页为下一文边界核验：work/domestic/mmhist_platform_1945_pages/page-101.png；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:political-report-1945": (
        "正文页已核读：公开扫描 PDF 扫描书内第71页（PDF 第101页）标题为《中国民主同盟临时全国代表大会政治报告》，日期为1945年10月11日；该页正文可见。",
        "PDF扫描书内第71页（PDF第101页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:congress-declaration-1945": (
        "正文页界已核读：公开扫描 PDF 第118—123页（书内第88—93页）连续构成《中国民主同盟临时全国代表大会宣言》，第118页有标题和1945年10月16日日期，第123页以‘谨此宣言’收束；第124页已转入《中国民主同盟组织规程》。",
        "PDF第118—123页（书内第88—93页）本地页图：work/domestic/mmhist_congress_1945_pages/page-118.png至page-123.png；PDF第124页为下一文边界核验：work/domestic/mmhist_congress_1945_pages/page-124.png；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:chang-lan-pcc-opening-1946-01-10": (
        "正文页已核读：公开扫描 PDF 扫描书内第117页（PDF 第147页）标题为《中国民主同盟主席张澜在政治协商会议开幕式上的讲话》，日期为1946年1月10日；该页正文可见。",
        "PDF扫描书内第117页（PDF第147页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:lo-lung-chi-national-assembly-1946-01-17": (
        "正文页已核读：公开扫描 PDF 扫描书内第130页（PDF 第160页）标题为《罗隆基在政协讨论国民大会问题时重申民盟主张》，日期为1946年1月17日；该页正文可见。",
        "PDF扫描书内第130页（PDF第160页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:chang-po-chun-national-assembly-1946-01-17": (
        "正文页已核读：公开扫描 PDF 扫描书内第132页（PDF 第162页）标题为《章伯钧重申中国民主同盟关于国民大会的五项主张》，日期为1946年1月17日至18日；该页正文可见。",
        "PDF扫描书内第132页（PDF第162页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:li-gongpu-protest-1946-07-12": (
        "正文页已核读：公开扫描 PDF 扫描书内第182页（PDF 第212页）标题为《中国民主同盟云南省支部为李公朴同志被暴徒暗杀事件提出严重抗议》，日期为1946年7月12日；该页正文可见。",
        "PDF扫描书内第182页（PDF第212页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:wen-yiduo-emergency-statement-1946-07-16": (
        "正文页已核读：公开扫描 PDF 扫描书内第191页（PDF 第221页）标题为《中国民主同盟云南省支部为闻一多同志复遭暗杀紧急声明》，日期为1946年7月16日；该页正文可见。",
        "PDF扫描书内第191页（PDF第221页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:situation-talk-1946-01-02": (
        "正文页已核读：公开扫描 PDF 扫描书内第115页（PDF 第145页）标题为《中国民主同盟发言人对时局发表谈话》，日期为1946年1月2日；该页正文可见。",
        "PDF扫描书内第115页（PDF第145页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:chang-dong-sun-freedom-1946-01-14": (
        "正文页已核读：公开扫描 PDF 扫描书内第120页（PDF 第150页）标题为《张东荪在政协讨论人民基本自由权利的发言》，日期为1946年1月14日；该页正文可见。",
        "PDF扫描书内第120页（PDF第150页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:lo-lung-chi-government-reorganization-1946-01-14": (
        "正文页已核读：公开扫描 PDF 扫描书内第121页（PDF 第151页）标题为《罗隆基在政协会上提出改组政府三原则》，日期为1946年1月14日；该页正文可见。",
        "PDF扫描书内第121页（PDF第151页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:league-military-proposal-1946-01-16": (
        "正文页已核读：公开扫描 PDF 扫描书内第123页（PDF 第153页）标题为《中国民主同盟关于军事问题的提案》，日期为1946年1月16日；该页正文可见。",
        "PDF扫描书内第123页（PDF第153页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:zhang-bo-jun-common-program-1946-01-16": (
        "正文页已核读：公开扫描 PDF 扫描书内第127页（PDF 第157页）标题为《章伯钧在政协讨论共同纲领问题的发言》，日期为1946年1月16日；该页正文可见。",
        "PDF扫描书内第127页（PDF第157页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:huang-yan-pei-common-program-1946-01-16": (
        "正文页已核读：公开扫描 PDF 扫描书内第128页（PDF 第158页）标题为《黄炎培在政协讨论共同纲领问题的发言》，日期为1946年1月16日；该页正文可见。",
        "PDF扫描书内第128页（PDF第158页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:lo-lung-chi-common-program-1946-01-16": (
        "正文页已核读：公开扫描 PDF 扫描书内第129页（PDF 第159页）标题为《罗隆基在政协讨论共同纲领问题的发言》，日期为1946年1月16日；该页正文可见。",
        "PDF扫描书内第129页（PDF第159页）正文首页；目录页同时定位该条目。",
    ),
    "domestic:MMHIST:huang-yan-pei-constitution-draft-1946-01-19": (
        "正文页已核读：公开扫描 PDF 扫描书内第135页（PDF 第165页）标题为《黄炎培在政协讨论修改宪草问题的发言》，日期为1946年1月19日；该页正文可见。",
        "PDF扫描书内第135页（PDF第165页）正文首页；目录页同时定位该条目。",
    ),
}


def main() -> None:
    updated = 0
    lines = []
    seen = set()
    for raw in PATH.read_text(encoding="utf-8").splitlines():
        item = json.loads(raw)
        cid = item.get("candidate_id")
        if cid in UPDATES:
            note, locator = UPDATES[cid]
            item["evidence_note"] = note
            item["evidence_type"] = "digital_image"
            item["evidence_locator"] = locator
            if cid == "domestic:LNU:guangmingbao-index-1941":
                item["catalog_reference"] = (
                    "Lingnan Digital Commons item 14：《光明报，1941》；机构描述为1页、13条索引；"
                    "下载 PDF 共2页（第2页为索引原图）"
                )
                item["access_note"] = (
                    "岭南大学页面提供索引下载；本地副本："
                    "data/domestic/press_scans/LNU_PROFMKCHAN_INDEXLIST_14_光明報_1941.pdf；"
                    "第2页为手写索引原图，SHA256 7ff54b899dddbbfe4f089aca87c3ca98b4de1fcd0074e0ae571f598bdcceb3a9"
                )
                item["uncertainty_note"] = (
                    "该索引实际只覆盖香港工运剪报，不能据此证明《光明报》1941-10-10或1941-10-16没有民盟文件；"
                    "原刊影像、剪报原件保存位置和复制权利仍待人工核验。"
                )
                item["review_note"] = (
                    "Codex于2026-07-18完成索引 PDF 第2页人工核读；已提取可辨认日期和第3版定位，"
                    "确认该页未覆盖1941-10-10或1941-10-16两个民盟成立目标日期；保持L3追索入口，"
                    "下一步转向香港大学缩微胶卷或国家图书馆具体原刊影像。"
                )
            suffix = "" if cid == "domestic:LNU:guangmingbao-index-1941" else " Codex于2026-07-18完成正文首页页级核读；L2不变。"
            if suffix not in item.get("review_note", ""):
                item["review_note"] = item.get("review_note", "") + suffix
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
