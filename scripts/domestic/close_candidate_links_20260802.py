#!/usr/bin/env python3
"""S3 闭合链路：候选 ↔ 入库文档 双向关联（2026-08-02 下午）

背景（CORPUS_ADVERSARIAL_REVIEW_20260802.md S3 节）：
- domestic_candidates 的 check_outcome='pass' 只是「审核通过」，不等于「真正入库」。
- S3 上午已把 8 个 full_item_online + 现成 OCR 的候选真实写入 documents/pages/FTS（doc 1301-1308）。
- 本脚本做两件事：

  A) 闭合链路（S3 处置建议③）：
     - ALTER TABLE domestic_candidates ADD COLUMN ingested_document_id INTEGER
     - 回填 8 个已入库候选 → documents.id
     - 同时给 documents 加 ingested_candidate_id 反向指针（新增列）

  B) 降级登记（S3 处置建议②）：
     - surrogate_online + catalogue_only_online 的 pass 候选没有可采集全文，
       仅「线索登记」。把 check_outcome 从 'pass' 降为 'lead_only'，
       避免「登记=入库」的虚报；full_item_online 保持 pass。
     - 附 review_note 说明降级原因与时间。

安全：
- 默认 dry-run（只打印，不写）；--commit 才写。
- --commit 前自动备份正式库。
- 幂等：重复运行不会重复加列（先查 schema）、不会重复降级（WHERE check_outcome='pass' 才命中）。
"""
import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
MANIFEST = ROOT / "work" / "domestic" / "S3_BACKFILL_MANIFEST.json"
NOTE_TEMPLATE = (
    "2026-08-02 降级 lead_only：{avail} 无可采集全文，仅线索登记；"
    "未真正进入 documents/pages，不再计入已收集。"
)
DEGRADE_AVAILS = ("surrogate_online", "catalogue_only_online")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def has_column(conn, table: str, column: str) -> bool:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    return column in cols


def plan(conn) -> dict:
    """收集计划：A 回填映射、B 降级候选列表。只读。"""
    # A) 8 个已入库候选 → document_id
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    backfill = []
    for it in manifest["items"]:
        doc = conn.execute(
            "SELECT id FROM documents WHERE doc_key=?",
            (f"domestic-ocr/S3:{it['candidate_id']}",),
        ).fetchone()
        backfill.append({
            "candidate_id": it["candidate_id"],
            "document_id": doc[0] if doc else None,
        })

    # B) 待降级候选
    degrade = []
    for r in conn.execute(
        "SELECT candidate_id, title, online_availability FROM domestic_candidates "
        "WHERE check_outcome='pass' AND online_availability IN (?,?) "
        "ORDER BY online_availability, candidate_id",
        DEGRADE_AVAILS,
    ):
        degrade.append({
            "candidate_id": r[0],
            "title": r[1],
            "online_availability": r[2],
        })
    return {"backfill": backfill, "degrade": degrade}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="真正写库（否则 dry-run）")
    ap.add_argument("--db", type=Path, default=DB, help="正式库路径")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    p = plan(conn)
    missing = [b for b in p["backfill"] if b["document_id"] is None]
    avail_counts: dict[str, int] = {}
    for d in p["degrade"]:
        avail_counts[d["online_availability"]] = (
            avail_counts.get(d["online_availability"], 0) + 1
        )

    print("=== A) 闭合链路：已入库候选 → ingested_document_id ===")
    print(f"  回填 {len(p['backfill'])} 条；缺 document 匹配 {len(missing)} 条")
    for b in p["backfill"]:
        print(f"    {b['candidate_id'][:58]:58s} -> doc {b['document_id']}")
    if missing:
        for m in missing:
            print(f"    !! 未匹配: {m['candidate_id']}")

    print("\n=== B) 降级 lead_only（无全文仅线索）===")
    print(f"  合计 {len(p['degrade'])} 条: {json.dumps(avail_counts, ensure_ascii=False)}")
    for d in p["degrade"][:8]:
        print(f"    [{d['online_availability']}] {d['candidate_id'][:58]}")
    if len(p["degrade"]) > 8:
        print(f"    ... 其余 {len(p['degrade'])-8} 条略")

    if not args.commit:
        print("\n[dry-run] 未写库。加 --commit 生效。")
        conn.close()
        return 0

    backup = args.db.with_name(
        f"{args.db.name}.close_links_20260802.{datetime.now().strftime('%Y%m%d_%H%M%S')}.pre.bak"
    )
    shutil.copy2(args.db, backup)
    print(f"\n已备份: {backup}")

    # A1) documents 加 ingested_candidate_id 反向指针
    if not has_column(conn, "documents", "ingested_candidate_id"):
        conn.execute("ALTER TABLE documents ADD COLUMN ingested_candidate_id TEXT")
        print("documents 新增列: ingested_candidate_id TEXT")
    # A2) domestic_candidates 加 ingested_document_id
    if not has_column(conn, "domestic_candidates", "ingested_document_id"):
        conn.execute("ALTER TABLE domestic_candidates ADD COLUMN ingested_document_id INTEGER")
        print("domestic_candidates 新增列: ingested_document_id INTEGER")
    conn.commit()

    # A3) 回填
    n_b = 0
    for b in p["backfill"]:
        if b["document_id"] is None:
            continue
        conn.execute(
            "UPDATE domestic_candidates SET ingested_document_id=? WHERE candidate_id=?",
            (b["document_id"], b["candidate_id"]),
        )
        conn.execute(
            "UPDATE documents SET ingested_candidate_id=? WHERE id=?",
            (b["candidate_id"], b["document_id"]),
        )
        n_b += 1
    conn.commit()

    # B) 降级
    n_d = 0
    for d in p["degrade"]:
        note = NOTE_TEMPLATE.format(avail=d["online_availability"])
        conn.execute(
            "UPDATE domestic_candidates SET check_outcome='lead_only', review_note=? "
            "WHERE candidate_id=? AND check_outcome='pass'",
            (note, d["candidate_id"]),
        )
        n_d += 1
    conn.commit()

    # 校验
    still_pass = conn.execute(
        "SELECT count(*) FROM domestic_candidates WHERE check_outcome='pass'"
    ).fetchone()[0]
    still_full = conn.execute(
        "SELECT count(*) FROM domestic_candidates WHERE check_outcome='pass' "
        "AND online_availability='full_item_online'"
    ).fetchone()[0]
    filled = conn.execute(
        "SELECT count(*) FROM domestic_candidates WHERE ingested_document_id IS NOT NULL"
    ).fetchone()[0]
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()

    print(f"\n=== 完成 ===")
    print(f"  回填 ingested_document_id: {n_b}")
    print(f"  降级 lead_only: {n_d}")
    print(f"  剩余 pass: {still_pass}（其中 full_item_online {still_full}）")
    print(f"  ingested_document_id 非空: {filled}")
    print(f"  integrity_check: {integrity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
