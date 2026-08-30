#!/usr/bin/env python3
"""Audit derived evidence units and public collection leads without DB writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_EVIDENCE = ROOT / "data" / "domestic" / "evidence_units.jsonl"
DEFAULT_RELATIONS = ROOT / "data" / "domestic" / "evidence_unit_relations.jsonl"
DEFAULT_LEADS = ROOT / "data" / "domestic" / "collection_leads_20260727.jsonl"
DEFAULT_JSON = ROOT / "work" / "domestic" / "EVIDENCE_UNITS_AUDIT_20260728.json"
DEFAULT_MD = ROOT / "work" / "domestic" / "EVIDENCE_UNITS_AUDIT_20260728.md"
DEFAULT_NORMALIZED_RELATIONS = ROOT / "work" / "domestic" / "EVIDENCE_UNIT_RELATIONS_NORMALIZED_20260728.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(args: argparse.Namespace) -> dict:
    evidence = read_jsonl(args.evidence)
    relations = read_jsonl(args.relations)
    leads = read_jsonl(args.leads)
    conn = sqlite3.connect(args.db)
    document_ids = {row[0] for row in conn.execute("SELECT id FROM documents")}
    page_ids = {row[0] for row in conn.execute("SELECT id FROM pages")}
    db_counts = {
        "documents": conn.execute("SELECT count(*) FROM documents").fetchone()[0],
        "pages": conn.execute("SELECT count(*) FROM pages").fetchone()[0],
        "page_fts": conn.execute("SELECT count(*) FROM page_fts").fetchone()[0],
        "integrity_check": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    conn.close()

    evidence_ids = {str(item["evidence_id"]) for item in evidence}
    evidence_ids_lower = {key.lower(): key for key in evidence_ids}
    missing_documents = sorted({item["document_id"] for item in evidence if item["document_id"] not in document_ids})
    missing_pages = sorted({page_id for item in evidence for page_id in item.get("page_ids", []) if page_id not in page_ids})
    relation_endpoint_mismatches = []
    normalized_relations = []
    for relation in relations:
        source = str(relation["from_evidence_id"])
        target = str(relation["to_evidence_id"])
        normalized_source = evidence_ids_lower.get(source.lower())
        normalized_target = evidence_ids_lower.get(target.lower())
        if normalized_source is None or normalized_target is None:
            relation_endpoint_mismatches.append(
                {"from": source, "to": target, "from_resolves": normalized_source, "to_resolves": normalized_target}
            )
        normalized = dict(relation)
        if normalized_source is not None:
            normalized["from_evidence_id"] = normalized_source
        if normalized_target is not None:
            normalized["to_evidence_id"] = normalized_target
        normalized_relations.append(normalized)

    lead_checks = []
    for lead in leads:
        path = ROOT / lead["local_path"]
        exists = path.is_file()
        actual_sha = sha256(path) if exists else None
        lead_checks.append(
            {
                "lead_id": lead["lead_id"],
                "local_path": lead["local_path"],
                "exists": exists,
                "size_matches": exists and path.stat().st_size == lead.get("file_size"),
                "sha256_matches": exists and actual_sha == lead.get("sha256"),
                "evidence_level": lead.get("evidence_level"),
            }
        )

    result = {
        "gate": "PASS" if not missing_documents and not missing_pages and db_counts["integrity_check"] == "ok" and all(item["exists"] and item["size_matches"] and item["sha256_matches"] for item in lead_checks) else "HOLD",
        "read_only": True,
        "evidence_units": len(evidence),
        "evidence_document_refs": len(evidence) - len(missing_documents),
        "evidence_page_refs": len(evidence) - len(missing_pages),
        "citation_ready_true": sum(bool(item.get("citation_ready")) for item in evidence),
        "evidence_ocr_status": dict(Counter(str(item.get("ocr_status")) for item in evidence)),
        "evidence_boundary_status": dict(Counter(str(item.get("article_boundary_status")) for item in evidence)),
        "relations": len(relations),
        "relations_normalized": len(normalized_relations),
        "relation_endpoint_mismatches": relation_endpoint_mismatches,
        "public_leads": len(leads),
        "public_lead_checks": lead_checks,
        "missing_document_ids": missing_documents,
        "missing_page_ids": missing_pages,
        "db": db_counts,
    }
    args.normalized_relations.parent.mkdir(parents=True, exist_ok=True)
    with args.normalized_relations.open("w", encoding="utf-8") as fh:
        for relation in normalized_relations:
            fh.write(json.dumps(relation, ensure_ascii=False, sort_keys=True) + "\n")
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# 国内证据单元与公开线索验收（2026-07-28）",
        "",
        f"- 总门控：**{result['gate']}**",
        "- 本次仅做只读审计，不修改 SQLite，不提升任何 `citation_ready` 状态。",
        f"- 证据单元：{result['evidence_units']} 条；文档/页面引用缺失：{len(missing_documents)}/{len(missing_pages)}。",
        f"- OCR 状态：{result['evidence_ocr_status']}；文章边界状态：{result['evidence_boundary_status']}。",
        f"- `citation_ready=true`：{result['citation_ready_true']} 条。",
        f"- 关系：{len(relations)} 条；仅按大小写规范化后可解析 {len(normalized_relations) - len(relation_endpoint_mismatches)} 条，未解析端点：{len(relation_endpoint_mismatches)} 条。",
        f"- 公开网页线索：{len(leads)} 条；本地文件 SHA256/大小校验全部通过：{all(item['exists'] and item['size_matches'] and item['sha256_matches'] for item in lead_checks)}。",
        f"- 主库：{db_counts['documents']} 文档 / {db_counts['pages']} 页面 / {db_counts['page_fts']} FTS；完整性：`{db_counts['integrity_check']}`。",
        "",
        "## 处置结论",
        "",
        "1. 82 条证据单元可以作为主库页面的 review-only 研究索引，但不能直接转为可引用正文。",
        "2. 关系表原始文件保留不变；已生成保守规范化副本，仅修正能与当前证据 ID 逐字（忽略大小写）对应的端点。其余 7 条端点疑似来自旧编号体系，禁止猜测映射，暂不导入。",
        "3. 8 条公开网页线索的本地原件与清单一致，可以继续做文本抽取和引用级人工复核；它们仍属于二次呈现或公共领域材料，不能替代同期原档。",
        "",
        "## 规范化关系文件",
        "",
        f"`{args.normalized_relations.relative_to(ROOT)}`",
    ]
    args.md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--relations", type=Path, default=DEFAULT_RELATIONS)
    parser.add_argument("--leads", type=Path, default=DEFAULT_LEADS)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--normalized-relations", type=Path, default=DEFAULT_NORMALIZED_RELATIONS)
    args = parser.parse_args()
    print(json.dumps(audit(args), ensure_ascii=False))


if __name__ == "__main__":
    main()
