"""Metadata-only research packets for domestic topics.

The packet is a reproducible map from a research question to evidence layers,
page-level provenance, academic explanation candidates, and open primary-source
targets.  It intentionally does not export page bodies, OCR, translations, or
verbatim quotations.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote


def _app():
    # Imported lazily so the application can import this module without a
    # circular import.  The route calls below happen after app.py is loaded.
    loaded = sys.modules.get("app") or sys.modules.get("__main__")
    if loaded is not None and hasattr(loaded, "_research_topic_rows"):
        return loaded
    import app

    return app


def _page_row(connection, page_id: int):
    return connection.execute(
        """
        SELECT p.id AS page_id, p.page_label, p.page_url,
               d.doc_key, d.title, d.date_guess, d.volume_title, d.doc_id,
               d.source_platform,
               COALESCE(pp.source_file, '') AS source_file,
               COALESCE(pp.source_sha256, '') AS source_sha256,
               pp.source_file_size, pp.pdf_page_no, pp.physical_page_no,
               pp.printed_page,
               COALESCE(pp.review_status, 'missing') AS provenance_review_status,
               COALESCE(pp.citation_ready, 0) AS citation_ready,
               COALESCE(pp.needs_human_review, 1) AS needs_human_review,
               COALESCE(pp.human_review_note, '') AS human_review_note,
               COALESCE(pp.event_tags, '') AS event_tags
        FROM pages p
        JOIN documents d ON d.id=p.document_id
        LEFT JOIN page_provenance pp ON pp.page_id=p.id
        WHERE p.id=?
        """,
        (page_id,),
    ).fetchone()


def build_research_packet(event_id: str) -> dict[str, Any] | None:
    """Build one domestic topic packet using metadata and page provenance only."""
    app = _app()
    staging_db = getattr(app, "DOMESTIC_STAGING_DB_PATH", None)
    if staging_db is not None and not Path(staging_db).exists():
        # The formal checkout may be clean while the staging corpus lives on
        # the sibling data worktree. Use it only when it really exists.
        sibling = (
            app.ROOT.parent / "mingmeng-history-research" / "work" / "domestic"
            / "staging_20260730" / "domestic_staging.sqlite"
        )
        if sibling.exists():
            app.DOMESTIC_STAGING_DB_PATH = sibling
    topics = app._research_topic_rows()
    topic = next(
        (item for item in topics if str(item["item"].get("event_id")) == str(event_id)),
        None,
    )
    if not topic:
        return None

    item = topic["item"]
    comparison = topic.get("comparison") or {}
    chain = topic.get("evidence_chain") or {}
    layers = chain.get("layers") if isinstance(chain, dict) else {}
    if not isinstance(layers, dict):
        layers = {}

    page_ids = sorted(
        {
            int(value["page_id"])
            for values in layers.values()
            if isinstance(values, list)
            for value in values
            if isinstance(value, dict) and value.get("page_id") is not None
        }
    )
    manifest_path = app.DATA_ROOT / "research_index.manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = {}

    public = bool(getattr(app._request, "public_mode", False))
    with app.conn() as connection:
        page_rows = {
            page_id: _page_row(connection, page_id) for page_id in page_ids
        }

    def page_record(raw: dict[str, Any], layer: str) -> dict[str, Any]:
        page_id = int(raw["page_id"])
        db_row = page_rows.get(page_id)
        base = {
            "layer": layer,
            "status": str(raw.get("status") or "open"),
            "label": str(raw.get("label") or "未命名证据"),
            "role": str(raw.get("role") or raw.get("why_it_matters") or ""),
            "caveat": str(raw.get("caveat") or raw.get("next_action") or ""),
            "page_id": page_id,
            "body_text_included": False,
        }
        if db_row is None:
            base.update({"resolved": False, "citation_gate_passed": False})
            return base

        domestic = str(db_row["source_platform"] or "") == "domestic"
        strict = app._domestic_citation_is_strict(db_row) if domestic else False
        source_file = str(db_row["source_file"] or "未绑定")
        if public:
            source_file = "内部 provenance 已保存（公开模式隐藏本地路径）"
        review_scope = ""
        for part in str(db_row["event_tags"] or "").split(";"):
            if part.startswith("review_scope="):
                review_scope = part.split("=", 1)[1]
                break
        base.update(
            {
                "resolved": True,
                "domestic_source": domestic,
                "citation_gate_passed": strict,
                "doc_key": str(db_row["doc_key"] or ""),
                "title": str(db_row["title"] or ""),
                "date_guess": str(db_row["date_guess"] or ""),
                "page_label": str(db_row["page_label"] or ""),
                "page_url": app.source_href(db_row["page_url"] or ""),
                "source_file": source_file,
                "source_sha256": str(db_row["source_sha256"] or ""),
                "source_file_size": int(db_row["source_file_size"] or 0),
                "pdf_page_no": db_row["pdf_page_no"],
                "physical_page_no": db_row["physical_page_no"],
                "printed_page": db_row["printed_page"],
                "provenance_review_status": str(db_row["provenance_review_status"] or "missing"),
                "human_review_note": str(db_row["human_review_note"] or ""),
                "review_scope": review_scope,
                "reader_url": f"/doc/{quote(str(db_row['doc_key']))}?page_id={page_id}",
                "citation_url": f"/cite/{page_id}",
            }
        )
        return base

    evidence_chain: dict[str, list[dict[str, Any]]] = {}
    for layer in app.CHAIN_LAYER_META:
        values = layers.get(layer, [])
        if not isinstance(values, list):
            values = []
        evidence_chain[layer] = [
            page_record(value, layer)
            for value in values
            if isinstance(value, dict) and value.get("page_id") is not None
        ]

    open_targets = [
        {
            "target": str(value.get("target") or ""),
            "why_it_matters": str(value.get("why_it_matters") or ""),
            "status": str(value.get("status") or "open"),
            "next_action": str(value.get("next_action") or ""),
        }
        for value in layers.get("missing_primary", [])
        if isinstance(value, dict)
    ]

    foreign_routes = [
        {
            "name": str(entry["definition"].get("name") or ""),
            "slug": str(entry["definition"].get("slug") or ""),
            "entry": str(entry["definition"].get("entry") or ""),
            "documents": int(entry["stats"].get("documents") or 0),
            "pages": int(entry["stats"].get("pages") or 0),
        }
        for entry in topic.get("foreign_stats", [])
    ]

    all_page_rows = [row for values in evidence_chain.values() for row in values]
    strict_count = sum(
        1
        for row in all_page_rows
        if row.get("status") == "strict_citation"
        and row.get("citation_gate_passed") is True
    )
    resolved_count = sum(1 for row in all_page_rows if row.get("resolved") is True)
    topic_event_rows = [
        {
            key: row[key]
            for key in (
                "page_id",
                "event_title",
                "event_date",
                "event_year",
                "event_tags",
                "page_label",
                "page_url",
                "doc_key",
                "title",
                "date_guess",
                "volume_title",
                "source_file",
                "source_sha256",
                "source_file_size",
                "pdf_page_no",
                "physical_page_no",
                "printed_page",
                "provenance_review_status",
                "citation_ready",
                "needs_human_review",
                "human_review_note",
                "review_scope",
                "strict",
                "machine_readable",
                "file_backed",
                "status_label",
                "status_class",
                "reader_url",
                "citation_url",
            )
            if key in row
        }
        | {"body_text_included": False}
        for row in topic.get("topic_event_rows", [])
    ]

    raw_matrix = topic.get("research_matrix") or {}
    matrix_questions: list[dict[str, Any]] = []
    if isinstance(raw_matrix, dict):
        for raw_question in raw_matrix.get("questions", []):
            if not isinstance(raw_question, dict):
                continue
            matrix_questions.append(
                {
                    "id": str(raw_question.get("id") or ""),
                    "question": str(raw_question.get("question") or ""),
                    "status": str(raw_question.get("status") or "partial"),
                    "evidence_page_ids": sorted(
                        {
                            int(value)
                            for value in raw_question.get("evidence_page_ids", [])
                            if str(value).isdigit()
                        }
                    ),
                    "negative_page_ids": sorted(
                        {
                            int(value)
                            for value in raw_question.get("negative_page_ids", [])
                            if str(value).isdigit()
                        }
                    ),
                    "evidence_scope": str(raw_question.get("evidence_scope") or ""),
                    "caveat": str(raw_question.get("caveat") or ""),
                    "next_action": str(raw_question.get("next_action") or ""),
                    "body_text_included": False,
                }
            )

    return {
        "schema_version": 2,
        "packet_type": "domestic_topic_research_packet",
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .astimezone()
        .isoformat(timespec="seconds"),
        "event_id": str(item.get("event_id") or event_id),
        "event_name": str(item.get("event_name") or ""),
        "research_question": str(
            comparison.get("research_question") or item.get("event_name") or ""
        ),
        "scope": {
            "domestic_status": str(item.get("domestic_status") or ""),
            "review_note": str(item.get("review_note") or ""),
            "primary_evidence_status": str(
                item.get("primary_evidence_status") or "unclassified"
            ),
            "primary_evidence_label": str(item.get("primary_evidence_label") or ""),
            "primary_evidence_gap": str(item.get("primary_evidence_gap") or ""),
            "domestic_anchor": str(comparison.get("domestic_anchor") or ""),
            "foreign_anchor": str(comparison.get("foreign_anchor") or ""),
            "difference": str(comparison.get("difference") or ""),
            "boundary": str(comparison.get("boundary") or ""),
            "next_action": str(comparison.get("next_action") or ""),
            "academic_use": str(comparison.get("academic_use") or ""),
        },
        "database": {
            "filename": str(manifest.get("database_filename") or app.DB_PATH.name),
            "sha256": str(manifest.get("sha256") or ""),
            "size_bytes": int(manifest.get("database_size_bytes") or 0),
        },
        "counts": {
            "domestic_candidate_rows": len(topic.get("domestic_rows", [])),
            "domestic_documents": int(topic.get("domestic_documents") or 0),
            "domestic_pages": int(topic.get("domestic_pages") or 0),
            "domestic_strict_pages": int(topic.get("domestic_citation_pages") or 0),
            "topic_event_domestic_pages": int(topic.get("topic_event_domestic_pages") or 0),
            "topic_event_domestic_file_backed_pages": int(
                topic.get("topic_event_domestic_file_backed_pages") or 0
            ),
            "topic_event_domestic_strict_pages": int(
                topic.get("topic_event_domestic_strict_pages") or 0
            ),
            "evidence_chain_page_items": len(all_page_rows),
            "evidence_chain_resolved_page_items": resolved_count,
            "evidence_chain_strict_gate_passed": strict_count,
            "topic_event_sample_rows": len(topic_event_rows),
            "academic_candidates": int(topic.get("academic_total") or 0),
            "foreign_machine_pages": int(topic.get("foreign_pages") or 0),
        },
        "evidence_chain": evidence_chain,
        "research_matrix": {
            "schema_version": 1,
            "status": "metadata_only",
            "body_read_by_builder": False,
            "questions": matrix_questions,
        },
        "topic_event_pages": topic_event_rows,
        "open_primary_targets": open_targets,
        "academic_candidates": [
            {
                key: value
                for key, value in academic.items()
                if key
                in {
                    "external_id",
                    "title",
                    "author",
                    "institution",
                    "publication_date",
                    "research_type",
                    "quality_tier",
                    "source_url",
                    "fulltext_status",
                    "review_status",
                    "citation_ready",
                    "human_verified",
                    "matched_terms",
                    "match_score",
                }
            }
            for academic in topic.get("academic_rows", [])
        ],
        "foreign_routes": foreign_routes,
        "audit": {
            "body_text_included": False,
            "ocr_text_included": False,
            "translation_text_included": False,
            "verbatim_quote_included": False,
            "page_rows_all_resolved": resolved_count == len(all_page_rows),
            "strict_page_rows_gate_checked": True,
            "research_matrix_body_text_included": False,
            "research_matrix_questions": len(matrix_questions),
            "source_sha256_exported": True,
            "citation_policy": "正式引文仍须打开 /cite/<page_id>，并遵守该页明确的 review_scope。",
        },
    }


def packet_json_bytes(event_id: str) -> bytes | None:
    packet = build_research_packet(event_id)
    if packet is None:
        return None
    return json.dumps(packet, ensure_ascii=False, indent=2).encode("utf-8")


def research_packet_page(event_id: str) -> bytes:
    """Render a readable packet while keeping the body out of the export."""
    app = _app()
    packet = build_research_packet(event_id)
    if packet is None:
        return app.layout(
            "研究包未找到",
            '<div class="notice">没有找到该专题研究包，请返回 <a href="/research">多源专题研究</a>。</div>',
            active_path="/research",
        )

    def esc(value: object) -> str:
        return app.h(value)

    layer_titles = {
        "primary": "主证据（页级）",
        "cross_source": "同期交叉",
        "negative_checks": "负向核查",
    }
    sections: list[str] = []
    for layer, title in layer_titles.items():
        cards: list[str] = []
        for row in packet["evidence_chain"].get(layer, []):
            strict = row.get("status") == "strict_citation" and row.get("citation_gate_passed")
            status_label = "正式可引用页" if strict else "待人工复核"
            status_class = "ok" if strict else "warn"
            links = ""
            if row.get("resolved"):
                links = (
                    f'<a href="{esc(row["reader_url"])}">回到原文页</a> · '
                    f'<a href="{esc(row["citation_url"])}">引用门禁</a>'
                )
            cards.append(
                f"""
<article class="result compact-result"><div>
  <h3>{esc(row.get('label'))}</h3>
  <div class="meta">页 {esc(row.get('page_id'))} · {esc(row.get('title'))} · {esc(row.get('page_label') or '页码未标注')} · SHA256 {esc(row.get('source_sha256') or '缺失')}</div>
  <div class="tagline"><span class="pstatus {status_class}">{esc(status_label)}</span><span class="tag">{esc(row.get('date_guess') or '日期未标注')}</span><span class="tag">正文未复制</span></div>
  <div class="snippet">{esc(row.get('role'))}</div>
  <div class="snippet"><strong>边界：</strong>{esc(row.get('caveat'))}</div>
</div><div class="cite">{links}</div></article>"""
            )
        rendered = "".join(cards) or '<div class="notice">当前没有登记页级记录。</div>'
        sections.append(
            f'<div class="section-head"><h2>{esc(title)}</h2><span class="meta">{len(cards)} 条页级记录</span></div>'
            f'<section class="result-list">{rendered}</section>'
        )

    targets = "".join(
        f'<article class="result compact-result"><div><h3>{esc(target.get("target"))}</h3>'
        f'<div class="snippet"><strong>为什么重要：</strong>{esc(target.get("why_it_matters"))}</div>'
        f'<div class="snippet"><strong>下一步：</strong>{esc(target.get("next_action"))}</div>'
        f'</div><div class="cite"><span class="pstatus warn">开放目标</span></div></article>'
        for target in packet["open_primary_targets"]
    ) or '<div class="notice">当前专题没有登记开放目标。</div>'
    academic = "".join(
        f'<article class="result compact-result"><div><h3>{esc(row.get("title") or row.get("external_id"))}</h3>'
        f'<div class="meta">{esc(row.get("author") or "作者未标注")} · {esc(row.get("institution") or "机构未标注")} · {esc(row.get("publication_date") or "日期未标注")}</div>'
        f'<div class="tagline"><span class="tag">学术 {esc(row.get("quality_tier") or "未分级")}</span><span class="tag">解释层候选</span></div>'
        f'</div><div class="cite"><a href="{esc(app.source_href(row.get("source_url") or "#"))}" target="_blank" rel="noreferrer">来源入口</a></div></article>'
        for row in packet["academic_candidates"]
    ) or '<div class="notice">当前没有匹配到学术解释候选。</div>'

    matrix_html = app._topic_research_matrix_html(
        packet.get("research_matrix"), packet.get("evidence_chain")
    )

    topic_event_cards = "".join(
        f'''<article class="result compact-result"><div>
  <h3>{esc(row.get("event_title") or row.get("title") or row.get("doc_key"))}</h3>
  <div class="meta">{esc(row.get("event_date") or row.get("date_guess") or "日期未注明")} · {esc(row.get("title") or row.get("doc_key"))} · {esc(row.get("page_label") or "页码未标注")} · page_id={esc(row.get("page_id"))}</div>
  <div class="tagline"><span class="pstatus {esc(row.get("status_class"))}">{esc(row.get("status_label"))}</span><span class="tag">专题回接</span><span class="tag">源文件 {"已锚定" if row.get("file_backed") else "待补"}</span><span class="tag">正文未复制</span></div>
  <div class="snippet">该条目来自共享专题事件索引，只提供页级定位和 provenance，不自动证明事件定义原件。</div>
</div><div class="cite"><a href="{esc(row.get("reader_url"))}">打开原文页</a><br><a href="{esc(row.get("citation_url"))}">引用门禁</a></div></article>'''
        for row in packet.get("topic_event_pages", [])
    ) or '<div class="notice">当前没有可展示的专题事件索引页。</div>'

    scope = packet["scope"]
    counts = packet["counts"]
    event_id_safe = app.quote(str(packet["event_id"]))
    body = app.breadcrumb_html(
        [("/research", "多源专题研究"), (None, "专题研究包")]
    ) + f"""
<section class="doc-head"><div><h1>{esc(packet['event_name'])} · 研究包</h1><div class="meta">元数据和页级证据导航包 · 生成于 {esc(packet['generated_at'])}</div></div><div class="doc-tools"><a class="button" href="/research/{event_id_safe}">返回专题</a><a class="button secondary" href="/research/{event_id_safe}/packet.json">下载 JSON</a></div></section>
<section class="stats"><div class="stat"><strong>{counts['evidence_chain_page_items']}</strong><span>证据链页级记录</span></div><div class="stat"><strong>{counts['evidence_chain_strict_gate_passed']}</strong><span>严格门禁通过</span></div><div class="stat"><strong>{counts['topic_event_domestic_strict_pages']}</strong><span>专题回接严格页</span></div><div class="stat"><strong>{counts['academic_candidates']}</strong><span>学术解释候选</span></div><div class="stat"><strong>{len(packet['open_primary_targets'])}</strong><span>开放原件目标</span></div></section>
<div class="notice"><strong>研究问题：</strong>{esc(packet['research_question'])}<br><strong>证据状态：</strong>{esc(scope['primary_evidence_label'])}。{esc(scope['primary_evidence_gap'])}<br><strong>边界：</strong>本包只导出题目、证据层、页级定位、来源 SHA256、复核范围和缺口；不复制正文、OCR、译文或逐字引文。正式引用必须打开对应的引用门禁页，并遵守该页的 review_scope。</div>
<div class="section-head"><h2>国内—境外对读摘要</h2></div><section class="result-list"><article class="result compact-result"><div><h3>国内材料</h3><div class="snippet">{esc(scope['domestic_anchor'])}</div></div></article><article class="result compact-result"><div><h3>境外材料</h3><div class="snippet">{esc(scope['foreign_anchor'])}</div></div></article><article class="result compact-result"><div><h3>差异与下一步</h3><div class="snippet"><strong>差异：</strong>{esc(scope['difference'])}<br><strong>下一步：</strong>{esc(scope['next_action'])}</div></div></article></section>
{matrix_html}
{"".join(sections)}
<div class="section-head"><h2>仍待补原件</h2><span class="meta">{len(packet['open_primary_targets'])} 项</span></div><section class="result-list">{targets}</section>
<div class="section-head"><h2>学术研究（解释层）</h2><span class="meta">不替代一手证据</span></div><section class="result-list">{academic}</section>
<div class="section-head"><h2>专题事件索引页</h2><span class="meta">显示 {len(packet.get('topic_event_pages', []))} 条 / 共 {counts['topic_event_domestic_pages']} 页 · 严格 {counts['topic_event_domestic_strict_pages']} 页</span></div>
<div class="notice">专题事件索引页与候选资料回接是不同路径。本节只提供页级导航、来源 SHA256 和引用门禁，不复制正文；正式引用仍须遵守对应页面的 review_scope。</div>
<section class="result-list">{topic_event_cards}</section>
<div class="notice">数据库 SHA256：{esc(packet['database']['sha256'])} · 所有页级记录已解析：{esc(packet['audit']['page_rows_all_resolved'])} · 正文原件未复制：是。</div>
"""
    return app.layout(f"{packet['event_name']}研究包", body, active_path="/research")
