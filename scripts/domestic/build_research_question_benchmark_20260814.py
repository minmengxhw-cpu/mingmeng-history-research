#!/usr/bin/env python3
"""Run a metadata-only research-path benchmark against the formal database.

This is deliberately not an answer-generation test.  It checks whether a
researcher can start from a realistic question, reach the relevant domestic
topic, find domestic pages, see the evidence-chain state, and distinguish
strict citation support from an open primary-source gap.  Page text is used by
the existing search index but is never copied into the report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app  # noqa: E402  (the benchmark must use the production search path)


QUESTIONS = [
    # 1941 formation
    ("domestic-1941-formation", "1941年民盟成立宣言在哪里？", "成立宣言"),
    ("domestic-1941-formation", "成立宣言与早期对时局主张如何区分？", "对时局主张纲领"),
    ("domestic-1941-formation", "1941年成立材料使用了什么组织名称？", "民主政团同盟"),
    ("domestic-1941-formation", "如何定位1941年国内页级材料？", "1941年"),
    # 1944 reorganization
    ("domestic-1944-reorganization", "1944年民盟改组的国内材料在哪里？", "改组"),
    ("domestic-1944-reorganization", "民盟何时完成更名？", "更名"),
    ("domestic-1944-reorganization", "《民憲》能否作为1944年改组的线索？", "民憲"),
    ("domestic-1944-reorganization", "如何回查民盟改组相关文献？", "民盟改组"),
    # 1945 first congress
    ("domestic-1945-first-congress", "1945年民盟纲领的国内版本在哪里？", "中国民主同盟纲领"),
    ("domestic-1945-first-congress", "临时全国代表大会宣言如何定位？", "临时全国代表大会"),
    ("domestic-1945-first-congress", "1945年大会政治报告有哪些页级入口？", "政治报告"),
    ("domestic-1945-first-congress", "大会组织规程能否回到原文页？", "组织规程"),
    # 1946 PCC
    ("domestic-1946-pcc", "旧政协中的民盟材料如何检索？", "政治协商会议"),
    ("domestic-1946-pcc", "政协停战议题有哪些国内页？", "停战"),
    ("domestic-1946-pcc", "《光明報》能否作为政协对读材料？", "光明報"),
    ("domestic-1946-pcc", "政协筹备阶段有哪些可追踪记录？", "政协筹备"),
    # 1946 refusal of national assembly
    ("domestic-1946-refuse-national-assembly", "民盟拒绝参加国民大会的材料在哪里？", "国民大会"),
    ("domestic-1946-refuse-national-assembly", "如何检索民盟拒绝参加的同期表述？", "拒绝参加"),
    ("domestic-1946-refuse-national-assembly", "片面宪法争议有哪些国内页？", "片面宪法"),
    ("domestic-1946-refuse-national-assembly", "民盟拒绝出席国民大会的页级入口是什么？", "拒绝出席"),
    # Li Gongpu / Wen Yiduo
    ("domestic-1946-li-wen", "李公朴遇害后的国内材料在哪里？", "李公朴"),
    ("domestic-1946-li-wen", "闻一多遇害后的同期材料在哪里？", "闻一多"),
    ("domestic-1946-li-wen", "《民主周刊》有哪些相关页？", "民主周刊"),
    ("domestic-1946-li-wen", "各方抗议材料如何回查？", "抗议"),
    # 1947 dissolution
    ("domestic-1947-illegal-dissolution", "民盟被宣布非法的国内材料在哪里？", "宣布非法"),
    ("domestic-1947-illegal-dissolution", "民盟正式宣告解散的同期页在哪里？", "民盟正式宣告解散"),
    ("domestic-1947-illegal-dissolution", "政府压迫民盟的材料如何定位？", "政府压迫民盟"),
    ("domestic-1947-illegal-dissolution", "解散公告是否已有页级入口？", "解散公告"),
    # 1948 third plenum / May Day
    ("domestic-1948-third-plenum-may-day", "民盟三中全会的国内页在哪里？", "三中全会"),
    ("domestic-1948-third-plenum-may-day", "五一口号与民盟的关系如何检索？", "五一口号"),
    ("domestic-1948-third-plenum-may-day", "1948年香港相关材料有哪些入口？", "香港"),
    ("domestic-1948-third-plenum-may-day", "如何回查民盟三中全会记录？", "民盟三中全会"),
    # 1949 new PCC
    ("domestic-1949-new-pcc", "新政协筹备中的民盟材料在哪里？", "新政协"),
    ("domestic-1949-new-pcc", "民盟代表名单能否回到页级来源？", "代表名单"),
    ("domestic-1949-new-pcc", "北平阶段的国内材料如何检索？", "北平"),
    ("domestic-1949-new-pcc", "第一届全体会议有哪些页级入口？", "第一届全体会议"),
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _strict_page_ids(connection: sqlite3.Connection, page_ids: list[int]) -> set[int]:
    if not page_ids:
        return set()
    placeholders = ",".join("?" for _ in page_ids)
    rows = connection.execute(
        f"""
        SELECT pp.page_id
        FROM page_provenance pp
        JOIN pages p ON p.id=pp.page_id
        JOIN documents d ON d.id=p.document_id
        WHERE pp.page_id IN ({placeholders})
          AND d.source_platform='domestic'
          AND {app.DOMESTIC_STRICT_CITATION_SQL}
        """,
        page_ids,
    ).fetchall()
    return {int(row[0]) for row in rows}


def _topic_index() -> dict[str, dict[str, object]]:
    return {
        str(topic["item"]["event_id"]): topic
        for topic in app._research_topic_rows()
    }


def build_report() -> dict[str, object]:
    topics = _topic_index()
    db_path = app.DB_PATH
    with app.conn() as connection:
        checks: list[dict[str, object]] = []
        for index, (event_id, question, query) in enumerate(QUESTIONS, start=1):
            rows = app.rows_for_search(
                connection, query, limit=50, platform="domestic"
            )
            page_ids = [int(row["page_id"]) for row in rows]
            strict_ids = _strict_page_ids(connection, page_ids)
            topic = topics.get(event_id)
            chain = (topic or {}).get("evidence_chain_summary") or {}
            item = (topic or {}).get("item") or {}
            topic_event_stats = app._research_topic_event_page_stats(connection, event_id)
            search_hit = bool(page_ids)
            topic_route_ready = bool(topic and chain.get("page_items", 0) > 0)
            checks.append(
                {
                    "id": f"RQ-{index:02d}",
                    "event_id": event_id,
                    "question": question,
                    "query": query,
                    "domestic_search_hits": len(page_ids),
                    "sample_page_ids": page_ids[:5],
                    "strict_citation_hits": len(strict_ids),
                    "sample_strict_page_ids": sorted(strict_ids)[:5],
                    "evidence_chain_strict_pages": int(chain.get("strict_items", 0) or 0),
                    "topic_event_domestic_pages": topic_event_stats["domestic_pages"],
                    "topic_event_domestic_strict_pages": topic_event_stats["domestic_strict_pages"],
                    "topic_route_ready": topic_route_ready,
                    "evidence_chain_page_items": int(chain.get("page_items", 0) or 0),
                    "open_primary_targets": int(chain.get("open_targets", 0) or 0),
                    "primary_evidence_status": str(item.get("primary_evidence_status") or "unclassified"),
                    "path_status": (
                        "research_path_ready"
                        if search_hit and topic_route_ready
                        else "path_incomplete"
                    ),
                    "citation_status": (
                        "strict_page_available_in_query"
                        if strict_ids
                        else (
                            "strict_page_available_in_topic"
                            if topic_event_stats["domestic_strict_pages"]
                            else "no_strict_page_in_query_or_topic"
                        )
                    ),
                }
            )

    path_ready = [row for row in checks if row["path_status"] == "research_path_ready"]
    strict_ready = [row for row in checks if row["strict_citation_hits"]]
    topic_strict_ready = [
        row for row in checks if row["topic_event_domestic_strict_pages"]
    ]
    strict_support_ready = [
        row for row in checks
        if row["strict_citation_hits"] or row["topic_event_domestic_strict_pages"]
    ]
    failures = [
        {
            "id": row["id"],
            "event_id": row["event_id"],
            "query": row["query"],
            "reason": "国内搜索无命中" if not row["domestic_search_hits"] else "专题入口或证据链不完整",
        }
        for row in checks
        if row["path_status"] != "research_path_ready"
    ]
    by_topic: dict[str, dict[str, int]] = {}
    for row in checks:
        bucket = by_topic.setdefault(
            str(row["event_id"]),
            {
                "questions": 0,
                "path_ready": 0,
                "strict_page_queries": 0,
                "topic_strict_routes": 0,
            },
        )
        bucket["questions"] += 1
        bucket["path_ready"] += int(row["path_status"] == "research_path_ready")
        bucket["strict_page_queries"] += int(bool(row["strict_citation_hits"]))
        bucket["topic_strict_routes"] += int(
            bool(row["topic_event_domestic_strict_pages"])
        )

    return {
        "schema_version": "research_question_benchmark.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "formal_domestic_database_metadata_only",
        "body_read": False,
        "report_does_not_copy_page_text": True,
        "database": {
            "path": str(db_path),
            "sha256": _sha256(db_path),
        },
        "question_count": len(checks),
        "path_ready_count": len(path_ready),
        "strict_page_query_count": len(strict_ready),
        "topic_strict_route_count": len(topic_strict_ready),
        "strict_support_count": len(strict_support_ready),
        "failed_path_count": len(failures),
        "topic_count": len(by_topic),
        "topics": by_topic,
        "failures": failures,
        "checks": checks,
        "interpretation": {
            "path_ready": "搜索有国内命中，且可进入带证据链的专题入口。",
            "strict_page_available_in_query": "本次查询直接返回至少一页通过国内正式引用门禁的页面。",
            "strict_page_available_in_topic": "本次查询未直接返回严格页，但专题事件索引仍提供至少一页通过正式引用门禁的页级入口。",
            "not_primary_closure": "本报告不把搜索命中或专题入口当作事件定义原件闭环；primary_evidence_status 和开放目标仍以覆盖表/证据链为准。",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "work" / "domestic" / "research_question_benchmark_20260814" / "REPORT.json",
    )
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "question_count", "path_ready_count", "strict_page_query_count", "failed_path_count", "topic_count"
    )}, ensure_ascii=False))
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
