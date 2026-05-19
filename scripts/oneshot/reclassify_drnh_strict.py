#!/usr/bin/env python3
"""DRNH 严格重分级 + 剔除不相关条目

规则（按用户要求「只要真正和民盟有关系的」严格化）：
- A 档（核心保留 224）：
  · A1 题名直接含「民盟/民主同盟/中國民主同盟/民主政團同盟」
  · A2 题名同时含「政协/政治协商会议」+ 民盟领袖
  · B1 题名含民盟领袖 + 政治议题词（呈/电/函/咨等）
- B 档（背景保留 141）：
  · A3 题名含「政协」但无民盟领袖（同期事件，民盟也参与）
  · B2-保留 题名仅人物名命中（个人专档），但剔除「張瀾洲」同名异人 2 条
- 剔除（100）：
  · X 题名完全无民盟直接命中（如 1936 西安非法团体、1941 中印公路、1943 川康盐场等）
  · 同名异人「張瀾洲」/「張子柱（張瀾洲）」（非民盟主席张澜）
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "research_index.sqlite"

DIRECT = ["民盟", "民主同盟", "中國民主同盟", "中国民主同盟", "民主政團同盟", "民主政团同盟"]
POLI = ["政治協商會議", "政协會議", "政治协商会议", "政協"]
LEADERS = [
    "張瀾", "张澜", "沈鈞儒", "沈钧儒", "羅隆基", "罗隆基",
    "章伯鈞", "章伯钧", "張君勱", "张君劢", "左舜生",
    "黃炎培", "黄炎培", "黃任之", "梁漱溟",
]
POLITICAL = [
    "商談", "商谈", "會談", "会谈", "協商", "协商", "參政", "参政",
    "調解", "调解", "調停", "调停", "取締", "取缔", "解散", "宣告",
    "聲明", "声明", "抗議", "抗议", "陳情", "陈情", "和談", "和谈",
    "呈", "電", "电", "咨", "函", "簽", "签", "致", "覆", "复",
    "面見", "面见", "拜會", "拜会", "懇談", "恳谈", "面陳", "面陈",
    "演講", "演讲", "發言", "发言", "立場", "立场", "態度", "态度",
    "言論", "言论", "主張", "主张", "建議", "建议", "報告", "报告",
    "情報", "情报", "活動", "活动", "動態", "动态", "意見", "意见",
]
# 同名异人：张瀾洲（张子柱字瀾洲，非民盟主席张澜）
SAME_NAME_DIFFERENT_PERSON = ["張瀾洲", "张瀾洲", "张澜洲", "張子柱", "张子柱"]


def strict_grade(title: str) -> str:
    """返回 A / B / DROP"""
    t = title or ""
    # 优先剔除同名异人
    if any(w in t for w in SAME_NAME_DIFFERENT_PERSON):
        return "DROP_SAMENAME"
    # A1: 直接含民盟组织名
    if any(w in t for w in DIRECT):
        return "A"
    # A2: 含政协 + 民盟领袖
    has_poli = any(w in t for w in POLI)
    has_leader = any(w in t for w in LEADERS)
    if has_poli and has_leader:
        return "A"
    # B1: 民盟领袖 + 议题词（升 A）
    if has_leader and any(w in t for w in POLITICAL):
        return "A"
    # A3: 仅政协（民盟参与的关键事件背景）
    if has_poli:
        return "B"
    # B2-保留: 仅人名命中（人物专档）
    if has_leader:
        return "B"
    # X: 完全无关
    return "DROP_IRRELEVANT"


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # 取 drnh 全部
    rows = list(cur.execute(
        "SELECT id, doc_key, title FROM documents WHERE source_platform='drnh'"
    ).fetchall())
    print(f"DRNH 入库: {len(rows)} 条")

    plan = {"A": [], "B": [], "DROP_SAMENAME": [], "DROP_IRRELEVANT": []}
    for doc_id, doc_key, title in rows:
        g = strict_grade(title)
        plan[g].append((doc_id, doc_key, title))

    print(f"\n=== 重分级结果 ===")
    print(f"  A (核心保留): {len(plan['A'])}")
    print(f"  B (背景保留): {len(plan['B'])}")
    print(f"  剔除-同名异人: {len(plan['DROP_SAMENAME'])}")
    print(f"  剔除-完全无关: {len(plan['DROP_IRRELEVANT'])}")

    # 1. 更新 A/B 的 grade
    for doc_id, _, _ in plan["A"]:
        cur.execute(
            "UPDATE document_classifications SET grade='A', score=90 WHERE document_id=?",
            (doc_id,),
        )
    for doc_id, _, _ in plan["B"]:
        cur.execute(
            "UPDATE document_classifications SET grade='B', score=60 WHERE document_id=?",
            (doc_id,),
        )

    # 2. 删除 DROP 条目（联级删除 pages、translations、classifications）
    drop_ids = [d[0] for d in plan["DROP_SAMENAME"] + plan["DROP_IRRELEVANT"]]
    if drop_ids:
        placeholders = ",".join("?" * len(drop_ids))
        # 先删依赖表
        cur.execute(
            f"DELETE FROM translations WHERE page_id IN "
            f"(SELECT id FROM pages WHERE document_id IN ({placeholders}))",
            drop_ids,
        )
        n_t = cur.rowcount
        cur.execute(
            f"DELETE FROM pages WHERE document_id IN ({placeholders})", drop_ids
        )
        n_p = cur.rowcount
        cur.execute(
            f"DELETE FROM document_classifications WHERE document_id IN ({placeholders})",
            drop_ids,
        )
        n_c = cur.rowcount
        cur.execute(
            f"DELETE FROM documents WHERE id IN ({placeholders})", drop_ids
        )
        n_d = cur.rowcount
        print(f"\n=== 删除统计 ===")
        print(f"  documents: {n_d}, pages: {n_p}, translations: {n_t}, classifications: {n_c}")

    conn.commit()

    # 验证
    rem = cur.execute(
        "SELECT COUNT(*) FROM documents WHERE source_platform='drnh'"
    ).fetchone()[0]
    a_n = cur.execute(
        "SELECT COUNT(*) FROM documents d JOIN document_classifications c ON c.document_id=d.id "
        "WHERE d.source_platform='drnh' AND c.grade='A'"
    ).fetchone()[0]
    b_n = cur.execute(
        "SELECT COUNT(*) FROM documents d JOIN document_classifications c ON c.document_id=d.id "
        "WHERE d.source_platform='drnh' AND c.grade='B'"
    ).fetchone()[0]
    print(f"\n=== 验证 ===")
    print(f"  drnh 剩余: {rem} 条")
    print(f"  其中 A 档: {a_n}")
    print(f"  其中 B 档: {b_n}")

    conn.close()


if __name__ == "__main__":
    main()
