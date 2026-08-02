#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build locator-only evidence-card drafts for local primary candidates.

The cards are research work products, not historical conclusions. They are
derived from the machine signal table and preserve source/text SHA, line
locators, and explicit review gates. No body excerpt is copied into the
cards, and nothing is written to the formal research database.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/local_private_ocr_metadata_20260730/evidence_cards"


def load_signal_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT l.object_id, l.title, l.document_date, l.source_path,
               l.source_sha256, l.derived_text_path, l.derived_text_sha256,
               l.document_class, l.relation_status, l.evidence_status,
               l.citation_ready, l.human_verified,
               s.text_sha256, s.signal_json, s.machine_signal_status,
               s.semantic_validation_done
        FROM local_source_objects l
        JOIN local_semantic_signals s ON s.object_id=l.object_id
        WHERE l.document_class IN ('historical_primary_candidate', 'historical_primary_related_source')
        ORDER BY l.object_id
        """
    ).fetchall()


def card_from_row(row: sqlite3.Row) -> dict:
    signals = json.loads(row["signal_json"] or "{}")
    term_counts = signals.get("term_counts", {})
    total_hits = sum(sum(values.values()) for values in term_counts.values())
    dates = signals.get("date_signals", [])
    headings = signals.get("headings", [])
    events = term_counts.get("event", {})
    questions = []
    if events:
        questions.append("核对事件词对应的原始语境、主体和时间范围，避免把词频当作事件断言")
    if dates:
        questions.append("核对日期信号是否为成文日期、引用日期或历史回顾日期")
    if not headings:
        questions.append("补充原件目录、页码或版式信息，确认文本结构与原件一致")
    questions.append("补来源原件或可靠页级图像后，再决定是否进入 citation gate")
    return {
        "card_id": f"LOCAL-CARD-{row['object_id']}",
        "object_id": row["object_id"],
        "title": row["title"],
        "document_date": row["document_date"],
        "document_class": row["document_class"],
        "relation_status": row["relation_status"],
        "evidence_status": row["evidence_status"],
        "source_path": row["source_path"],
        "source_sha256": row["source_sha256"],
        "derived_text_path": row["derived_text_path"],
        "derived_text_sha256": row["derived_text_sha256"],
        "text_sha256_audited": row["text_sha256"],
        "machine_signal_status": row["machine_signal_status"],
        "signal_summary": {
            "line_count": signals.get("line_count", 0),
            "heading_count": signals.get("heading_count", 0),
            "date_signal_count": signals.get("date_signal_count", 0),
            "term_hit_total": total_hits,
            "category_counts": {category: sum(values.values()) for category, values in term_counts.items()},
            "event_terms": events,
            "organization_terms": term_counts.get("organization", {}),
            "person_terms": term_counts.get("person", {}),
            "place_terms": term_counts.get("place", {}),
        },
        "locators": {
            "headings": headings,
            "dates": dates,
            "term_locations": signals.get("term_locations", {}),
        },
        "research_questions": questions,
        "card_status": "MACHINE_DRAFT_REVIEW_REQUIRED",
        "body_excerpts_persisted": False,
        "semantic_validation_done": int(row["semantic_validation_done"] or 0),
        "citation_ready": int(row["citation_ready"] or 0),
        "human_verified": int(row["human_verified"] or 0),
    }


def markdown(card: dict) -> str:
    summary = card["signal_summary"]
    def terms(name: str) -> str:
        values = summary.get(name, {})
        return "、".join(f"{k}({v})" for k, v in values.items()) or "无"
    headings = "；".join(f"L{h['line_no']} {h['heading']}" for h in card["locators"]["headings"][:20]) or "无结构标题信号"
    dates = "、".join(f"L{d['line_no']} {d['date']}" for d in card["locators"]["dates"][:30]) or "无日期信号"
    return f"""# {card['card_id']}：{card['title']}\n\n- 卡片状态：`{card['card_status']}`\n- 文献对象：`{card['object_id']}`\n- 日期字段：{card['document_date'] or '未登记'}\n- 文献分类：`{card['document_class']}`\n- 关系状态：`{card['relation_status']}`\n- 证据状态：`{card['evidence_status']}`\n- 原件/来源 SHA：`{card['source_sha256'] or '缺失'}`\n- 派生文本 SHA：`{card['derived_text_sha256'] or '缺失'}`\n- 审计文本 SHA：`{card['text_sha256_audited'] or '缺失'}`\n\n## 机器信号摘要\n\n- 行数：{summary['line_count']}\n- 标题信号：{summary['heading_count']}\n- 日期信号：{summary['date_signal_count']}\n- 事件词：{terms('event_terms')}\n- 机构词：{terms('organization_terms')}\n- 人物词：{terms('person_terms')}\n- 地点词：{terms('place_terms')}\n\n## 定位\n\n- 标题行：{headings}\n- 日期行：{dates}\n\n## 待处理问题\n\n""" + "\n".join(f"- {q}" for q in card["research_questions"]) + f"""\n\n## 闸门\n\n- 正文摘录已持久化：`false`\n- semantic validation：`{card['semantic_validation_done']}`\n- citation-ready：`{card['citation_ready']}`\n- human-verified：`{card['human_verified']}`\n\n本卡片只表达机器提取到的候选信号和定位，不构成历史事实、人物关系或事件结论。\n"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS local_evidence_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL UNIQUE,
            object_id TEXT NOT NULL UNIQUE,
            title TEXT,
            card_json TEXT NOT NULL,
            card_status TEXT NOT NULL,
            body_excerpts_persisted INTEGER NOT NULL DEFAULT 0,
            semantic_validation_done INTEGER NOT NULL DEFAULT 0,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cards = [card_from_row(row) for row in load_signal_rows(conn)]
    for card in cards:
        conn.execute(
            """
            INSERT INTO local_evidence_cards
            (card_id,object_id,title,card_json,card_status,body_excerpts_persisted,
             semantic_validation_done,citation_ready,human_verified)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(card_id) DO UPDATE SET
              object_id=excluded.object_id,
              title=excluded.title,
              card_json=excluded.card_json,
              card_status=excluded.card_status,
              body_excerpts_persisted=0,
              semantic_validation_done=excluded.semantic_validation_done,
              citation_ready=0,
              human_verified=0
            """,
            (card["card_id"], card["object_id"], card["title"], json.dumps(card, ensure_ascii=False),
             card["card_status"], 0, card["semantic_validation_done"], 0, 0),
        )
        safe_name = card["card_id"].replace("/", "_")
        (OUT / f"{safe_name}.md").write_text(markdown(card), encoding="utf-8")
    conn.commit()
    report = {
        "run_id": "local_primary_evidence_cards_20260730",
        "input_signal_rows": len(cards),
        "cards_written": len(cards),
        "status_counts": dict(Counter(card["card_status"] for card in cards)),
        "body_excerpts_persisted": False,
        "semantic_validation_done": sum(card["semantic_validation_done"] for card in cards),
        "citation_ready": sum(card["citation_ready"] for card in cards),
        "human_verified": sum(card["human_verified"] for card in cards),
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "CARDS.jsonl").write_text("\n".join(json.dumps(card, ensure_ascii=False) for card in cards) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
