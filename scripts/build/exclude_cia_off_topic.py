#!/usr/bin/env python3
"""CIA 误匹配剔除：把与中国民盟无关的 CIA 档案标记为「前台不展示」

执行后效果：
- document_classifications.grade 改为 '前台不展示'
- app.py 的所有前台过滤逻辑（搜索、栏目页、列表）会自动隐藏这些档案
- 数据保留在 DB 内供内部检索 / 溯源，不真删

5/26 19:50 整理：
共剔除 24 篇 CIA 档案，剩余 78 篇真正与中国民盟相关。

剔除依据（4 组）：
- A 组（朝鲜，4 篇）：「Korean Democratic League」是朝鲜独立组织，
  与中国民盟名称巧合，但完全无关
- B 组（日本，1 篇）：1948 日本共产势力，主题与民盟无关
- C 组（东南亚，10 篇）：缅甸 / 越南 / 印尼 / 马来亚 / 泰国的共产党或
  华人活动，主题非民盟
- D 组（1956+ 远离民盟史时段，9 篇）：CIA 中央情报简报系列、1957 亚非
  团结会议、FACTBOOK 1982 等，与民盟 1941–1950 史关键期不在同一时段
- E 组（台湾系列名称相似，2 篇）：「台湾新民盟」「台湾民主自治同盟」「台湾
  再解放联盟」是与中国民盟分立的台籍政治组织，按收录边界应剔除
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent.parent / "data" / "research_index.sqlite"

# 24 篇待剔除：identifier → 分组
EXCLUDE_IDENTIFIERS = {
    # A 组 — 朝鲜主题（4 篇）
    "cia-rdp82-00457r001400250001-2": "A_朝鲜",  # 大连的朝鲜民主同盟（名称巧合）
    "cia-rdp82-00457r007300270002-4": "A_朝鲜",  # 为朝鲜招募与训练平民人员
    "cia-rdp80s01540r003200080003-1": "A_朝鲜",  # 朝鲜报纸译文
    "cia-rdp80t00246a072100330001-4": "A_朝鲜",  # 朝鲜社会、政治与军事信息
    # B 组 — 日本主题（1 篇）
    "cia-rdp78-01617a003300010001-3": "B_日本",  # 1948 日本的共产势力
    # C 组 — 东南亚共产党 / 华人主题（10 篇）
    "cia-rdp78-01617a003500050003-5": "C_马来亚",
    "cia-rdp78-01617a003700140001-5": "C_缅甸",
    "cia-rdp79-01082a000100030008-9": "C_缅甸",
    "cia-rdp79-01383a000200020002-1": "C_东南亚",
    "cia-rdp80-00810a001500240005-4": "C_印尼",
    "cia-rdp82-00457r002900580005-6": "C_泰国",
    "cia-rdp82-00457r007100570010-4": "C_缅甸",
    "cia-rdp82-00457r010100310001-8": "C_缅甸",
    "cia-rdp82-00457r010400160005-8": "C_越南",
    "cia-rdp82-00457r009400360001-2": "C_越南",
    # D 组 — 1956+ 远离民盟史时段（9 篇）
    "cia-rdp79t00975a000800420001-9": "D_56plus",  # 当前情报简报
    "03193795": "D_56plus",                          # CIB 1956/08/10
    "03192683": "D_56plus",                          # CIB 1957/11/21
    "cia-rdp78-00915r000700150013-4": "D_56plus",   # 亚非团结会议 1957
    "03003301": "D_56plus",                          # CIB 1958/10/15
    "02066870": "D_56plus",                          # CIB 1960/04/30
    "03174706": "D_56plus",                          # CIB 1960/05/07
    "cia-rdp79t00975a029600010002-1": "D_56plus",   # 国家情报简报
    "cia-rdp08-00534r000100180001-3": "D_56plus",   # 世界概况 1982
    # E 组 — 台湾系列名称相似但与中国民盟无关组织（2026-05-28 新增）
    # 按用户「收录边界」规则：Taiwan Democratic League / New Democratic League on Taiwan /
    # Formosan League / Democratic League for Taiwan Autonomy 均应剔除前台
    "cia-rdp82-00457r003500280004-3": "E_台湾",   # 台湾新民盟 + 台湾再解放联盟
    "cia-rdp82-00457r009900020008-7": "E_台湾",   # 台湾民主自治同盟（与中国民盟分立的台籍政治组织）
}


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    excluded = 0
    already_excluded = 0
    not_found = []

    for ident, group in EXCLUDE_IDENTIFIERS.items():
        # CIA 文档：doc_key = f"cia-meng:{ident}"
        doc_id_variants = (
            ident,
            f"cia-readingroom-document-{ident}",
            ident.upper(),
            f"cia-readingroom-document-{ident}".upper(),
        )
        doc_key_variants = tuple(f"cia-meng:{variant}" for variant in doc_id_variants)
        rows = cur.execute(
            """
            SELECT d.id, d.doc_key, d.title, dc.grade
            FROM documents d
            LEFT JOIN document_classifications dc ON dc.document_id = d.id
            JOIN sources s ON s.id = d.source_id
            WHERE s.source_type='cia'
              AND (d.doc_id IN (?, ?, ?, ?) OR d.doc_key IN (?, ?, ?, ?))
            """,
            (*doc_id_variants, *doc_key_variants),
        ).fetchall()

        if not rows:
            not_found.append(ident)
            continue

        for r in rows:
            doc_id = r["id"]
            if (r["grade"] or "") == "前台不展示":
                already_excluded += 1
                print(f"  ⊙ [{group}] {r['doc_key']} - 已是「前台不展示」，跳过")
                continue

            existing = cur.execute(
                "SELECT 1 FROM document_classifications WHERE document_id=?",
                (doc_id,),
            ).fetchone()
            reason_note = f"[剔除:{group}] 与中国民盟无关，5/26 整理时移出前台"
            if existing:
                cur.execute(
                    """
                    UPDATE document_classifications
                    SET grade='前台不展示',
                        reason=COALESCE(reason||'；','')||?
                    WHERE document_id=?
                    """,
                    (reason_note, doc_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO document_classifications (document_id, grade, score, reason, needs_review)
                    VALUES (?, '前台不展示', 0, ?, 0)
                    """,
                    (doc_id, reason_note),
                )
            excluded += 1
            print(f"  ✓ [{group}] {r['doc_key']} - {r['title'][:60]}")

    conn.commit()
    conn.close()

    print()
    print("=" * 60)
    print(f"  剔除统计")
    print("=" * 60)
    print(f"  本次新剔除  ：{excluded} 篇")
    print(f"  之前已剔除  ：{already_excluded} 篇")
    print(f"  数据库未找到：{len(not_found)} 篇")
    if not_found:
        print(f"    未找到列表：")
        for ident in not_found:
            print(f"      - {ident}")
    print(f"  ----")
    total_excluded = excluded + already_excluded
    print(f"  目前共剔除  ：{total_excluded} 篇")
    print(f"  CIA 仍展示  ：约 {102 - total_excluded} 篇真正与民盟相关")  # 102 → 76（剔 26 后）
    print()
    print("  幂等：本脚本可重复执行，已剔除的会被跳过。")


if __name__ == "__main__":
    main()
