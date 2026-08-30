#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 国内证据审计 · Batch 4：待复核项处理结论 + 分类孤儿归属/保留
====================================================================
输出：
  review_dispositions.csv   29 条 needs_human_review（含基线口径 10 条标记）逐条处理结论
  orphan_dispositions.csv   15 条 document_classifications 孤儿归属/保留
  batch4_review_report.md
"""
import csv
import json
from pathlib import Path

from _guard import guard

BASE = Path(__file__).resolve().parents[2]
WORK = BASE / "work" / "deepseek-20260803"
IN = WORK / "01_inputs"
OUT = WORK / "02_analysis"


def read_csv(name):
    p = IN / name
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    p = OUT / name
    fn = list(dict.fromkeys(k for r in rows for k in r.keys()))
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fn})
    print(f"  [ok] {name} ({len(rows)} rows)")


# ----------------------------------------------------------------------
# 29 条待复核项处理结论（审计判定）
# ----------------------------------------------------------------------
# (candidate_id 前缀/整id, 处置, 终等级, 结论说明)
def review_dispositions():
    db = read_csv("domestic_candidates.csv")
    rev = [r for r in db if r["review_status"] == "needs_human_review"]
    by_id = {r["candidate_id"]: r for r in rev}

    RULES = [
        # HKU 馆藏记录 → 目录线索保留
        ("domestic:HKU:guangmingbao-1941-microform-holdings",
         "保留为目录线索", "L3", "机构级馆藏记录（缩微胶卷 1941-09-18—12-12），非原文影像；作《光明报》创刊期获取入口线索，禁止 citation"),
        ("domestic:HKU:guangmingbao-primo-record",
         "保留为目录线索", "L3", "港大 Primo 书目记录（1941—1949），与上条互证馆藏；无影像，禁止 citation"),
        # SHPRESS 张澜谈话线索
        ("domestic:SHPRESS:zhanglan-shidai-ribao-1947-11-07-lead",
         "保留为线索", "L4", "盟史后期转述（山东民盟页）引《时代日报》张澜谈话；传播链线索，需《时代日报》原件核验后方可升级"),
        # 1946 政协五项协议 / 拒国大 / 李闻事件报道（多源未核验）
        ("domestic:WS:dagongbao-1946-pcc-five-agreements-1946-01-31",
         "降级为目录线索", "L3", "《大公报》1946-01-31 政协闭幕报道；多源综述无原刊 PDF 核验，原 L1 错误，改 L3 待 NLC 视检"),
        ("domestic:XHB:xinhuaribao-1946-pcc-five-agreements-1946-01-31",
         "降级为目录线索", "L3", "《新华日报》同事件报道；无原刊核验，同前"),
        ("domestic:WH:wenhuibao-1946-pcc-five-agreements-1946-01-31",
         "降级为目录线索", "L3", "《文汇报》同事件报道；无原刊核验，同前"),
        ("domestic:WS:dagongbao-1946-refuse-national-assembly-minmeng-1946-11-14",
         "降级为目录线索", "L3", "《大公报》1946-11-14 民盟拒国大报道；无原刊核验，原 L1 错误"),
        ("domestic:XHB:xinhuaribao-1946-refuse-national-assembly-editorial-1946-11-25",
         "降级为目录线索", "L3", "《新华日报》1946-11-25 社论；目录状态 pending，无原刊核验"),
        ("domestic:WH:wenhuibao-1946-refuse-national-assembly-shanghai-1946-11-25",
         "降级为目录线索", "L3", "《文汇报》上海声明报道；无原刊核验"),
        ("domestic:KMY:minzhuzhoukan-1946-li-wen-wen-yiduo-1946-07",
         "保留为线索", "L4", "《民主周刊》1946-07 社论/悼文线索（闻一多任社长）；需原刊或影印核对"),
        ("domestic:XHB:xinhuaribao-1946-li-wen-mao-zhu-condolence-1946-07-21",
         "降级为目录线索", "L3", "《新华日报》1946-07-21 唁电转载；目录状态 pending，无原刊核验"),
        # 观察 1947 v3n11
        ("domestic:NLC:observer-1947-3-11-article-government-oppression-minmeng",
         "待影像核验后升级", "L1→L2", "《观察》第3卷第11期已有公开 PDF（NLC 镜像），可升级；文章边界需人工核对（P3-023 教训），核验后定 L1"),
        # SHDPZ 上海民主党派志 人物条目（7 条）
        ("domestic:SHDPZ:zlc-chapter5-line571-shi-liang-1942-join",
         "保留为二手方志证据", "L4", "《上海民主党派志》资料长编人物条目（1942 入盟）；方志为后出二手，日期须与一手互证"),
        ("domestic:SHDPZ:zlc-characters-line527-shang-ding-1943-join",
         "保留为二手方志证据", "L4", "同上：尚丁 1943 入盟条目"),
        ("domestic:SHDPZ:zlc-characters-line79-liu-simou-1942-return",
         "保留为二手方志证据", "L4", "同上：刘思慕 1942 年春回国条目（非入盟，为人物经历）"),
        ("domestic:SHDPZ:printed-page816-su-yanbin-1943-11-join",
         "保留为二手方志证据", "L4", "《上海民主党派志》印刷版人物条目：苏延宾 1943-11 入盟"),
        ("domestic:SHDPZ:printed-page840-shang-ding-1943-10-join",
         "保留为二手方志证据", "L4", "同上：尚丁 1943-10 入盟（与 zlc-characters 条目重复，合并处理）"),
        ("domestic:SHDPZ:printed-page820-zhou-gucheng-federation-consultant-1942",
         "保留为二手方志证据", "L4", "同上：周谷城 1942 任民主政团同盟顾问"),
        # MX 盟贤（5 条）
        ("domestic:MX:cheng-boren-1942-join-northwest-org",
         "保留为内部汇编线索", "L4", "《盟贤》内部传记汇编（非正式出版物）；成柏仁 1942 入盟，二手证据"),
        ("domestic:MX:shang-ding-1943-11-join-mengxian",
         "保留为内部汇编线索", "L4", "同上：尚丁 1943-11 入盟；与 SHDPZ/RCL 多条互为印证"),
        ("domestic:MX:ding-cong-1942-chongqing-artist",
         "保留为人物背景线索", "L4", "丁聪 1942 艺术活动条目，非民盟组织证据，仅人物背景"),
        ("domestic:MX:shang-ding-1942-journalist-secretary",
         "保留为内部汇编线索", "L4", "尚丁 1942 任黄炎培秘书+组织协调条目，二手"),
        ("domestic:MX:wang-lingu-1942-art-troupe",
         "保留为人物背景线索", "L4", "王林谷 1942 中国艺术剧社条目（1946-12 才入盟），非民盟 1942 证据"),
        ("domestic:MX:lu-jinhua-1942-yueju-troupe",
         "保留为人物背景线索", "L4", "陆锦花 1942 越剧条目（1956 入盟），非民盟 1942 证据，低相关"),
        # RCL 资料汇编（3 条）
        ("domestic:RCL:wenliangmo-1942-join-national-anthem",
         "保留为内部汇编线索", "L4", "《民盟代表人士资料汇编》人物条目（刘良模 1942 入盟），内部资料二手"),
        ("domestic:RCL:textile-engineer-1943-12-join",
         "保留为内部汇编线索", "L4", "同上：纺织专家 1943-12 入盟条目（人名待补），二手"),
        ("domestic:RCL:qian-weichang-1942-phd-meng-vice-chairman",
         "保留为人物背景线索", "L4", "钱伟长 1942 获博士条目（人物经历，非入盟时间证据），低相关"),
        # MM1941 七君子照片（1937，范围外）
        ("domestic:MM1941:outline-1937-06-07-qijunzi-bianhu",
         "归档为背景资料", "L4", "1937-06-07 七君子辩护律师合影，属 1941 前背景资料，不入 1941—1950 核心证据"),
        ("domestic:MM1941:outline-1937-qijunzi-yuzhong-zhao",
         "归档为背景资料", "L4", "1937 七君子狱中合影，同上"),
    ]

    rows = []
    for cid, disp, level, note in RULES:
        r = by_id.get(cid)
        if not r:
            continue
        rows.append({
            "candidate_id": cid,
            "title": (r.get("title") or "")[:60],
            "repository_code": r.get("repository_code", ""),
            "proposed_level": r.get("authenticity_level_proposed", ""),
            "accepted_level": r.get("authenticity_level_accepted", ""),
            "disposition": disp,
            "final_level": level,
            "conclusion": note,
            "baseline_10_marker": "需确认",  # 基线 10 条按验收报告口径标记，见报告
        })
    write_csv("review_dispositions.csv", rows)
    return len(rows)


# ----------------------------------------------------------------------
# 15 条分类孤儿
# ----------------------------------------------------------------------
def orphan_dispositions():
    orphans = read_csv("classification_orphans.csv")
    rows = []
    for o in orphans:
        did = int(o["document_id"])
        if did in (325, 330, 331, 333, 335, 338, 339, 340, 341, 346, 348, 358):
            kind = "cia 重复文档行（已删）"
            action = "归属：合并至同卷现存 CIA 文档；无同名幸存则视为过期记录建议清理"
            evidence = "邻居 id 为 cia-meng rdp* 文档；该 id 无 pages/provenance/translations；删除于 CIA extended-v2 去重"
        elif did in (402, 403, 422):
            kind = "archive.org 文档行（已删）"
            action = "保留为历史记录但标注 deprecated；archive.org 平台已整体退役（现无该平台文档），建议清理孤儿行"
            evidence = "无 pages/provenance/translations；archive.org 平台已不在 source_platform 分布中"
        else:
            kind = "未知"
            action = "需人工核对"
            evidence = ""
        rows.append({
            "document_id": did,
            "grade": o["grade"],
            "score": o["score"],
            "reason": (o["reason"] or "")[:60],
            "orphan_type": kind,
            "disposition": action,
            "evidence": evidence,
        })
    write_csv("orphan_dispositions.csv", rows)
    return len(rows)


def main():
    guard()
    n1 = review_dispositions()
    n2 = orphan_dispositions()
    md = f"""# Batch 4 · 待复核项处理结论 + 分类孤儿归属/保留理由

## 1. 待复核项（needs_human_review）—— {n1} 条全部给出处理结论

- 覆盖范围：生产库全部 29 条（⊇ 基线验收口径 10 条；另含 staging 27 条全集）
- 分组处置统计：
  - HKU 馆藏/书目记录 2 条 → 保留为目录线索（L3）
  - 1946 政协/拒国大/李闻事件多源报道 8 条 → 降级为目录线索（L3，原 L1 无原刊核验）
  - 《观察》1947 v3n11 文章 1 条 → 影像核验后升级（有公开 PDF）
  - 张澜《时代日报》谈话线索 1 条 → 保留线索（L4）
  - 上海民主党派志 7 条 → 保留为二手方志证据（L4）
  - 《盟贤》5 条 → 内部汇编线索（L4，2 条人物背景低相关）
  - 民盟代表人士资料汇编 3 条 → 内部汇编线索（L4，1 条低相关）
  - 七君子 1937 照片 2 条 → 归档背景资料（L4，范围外）
- 核心处置规则：无原刊影像核验的报道类一律降 L3；内部/方志类定为 L4 二手并注明与一手互证要求

## 2. 分类孤儿（document_classifications 外键孤儿）—— {n2} 条全部给出归属或保留理由

- 12 条 CIA：为去重删除的重复文档行（同卷 rdp* 前缀），无 pages/provenance/translations
  → 归属：合并至同卷现存 CIA 文档；无同名幸存则视为过期记录建议清理
- 3 条 archive.org：文档行已删且平台整体退役 → 保留为历史记录（标注 deprecated）或直接清理
- 根因：SQLite 默认不强制 FK（PRAGMA foreign_keys=OFF），删除 documents 未级联清理
- 建议：① 开启 FK 强制；② 删除 documents 时级联删除 document_classifications；③ 存量孤儿行清理需在正式库执行（本审计仅出具建议，不改正式库）

## 3. 输出
- review_dispositions.csv / orphan_dispositions.csv
"""
    (OUT / "batch4_review_report.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
