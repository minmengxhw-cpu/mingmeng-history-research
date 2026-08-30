#!/usr/bin/env python3
"""Audit a sibling domestic collection before any formal admission.

This is deliberately a metadata- and filename-only gate.  It reads JSON
sidecars, candidate/source metadata, and filesystem names/statistics.  It does
not open HTML, PDF, image, OCR, SQLite, or other source bodies; it does not
copy, delete, move, or write the formal database.

The sibling checkout is allowed to contain useful material, but its batches
mix source classes and evidence roles.  The report therefore recommends a
disposition for each sidecar record without promoting anything automatically.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPO = ROOT
DEFAULT_SIBLING = ROOT.parent / "mingmeng-history-research"

COLLECTIONS = (
    ("grok_public_collection_20260729", "public collection with JSON sidecars"),
    ("official_research_public_20260730", "official/public export"),
    ("academic_public_20260730", "academic export"),
    ("grok_next_stage_20260730", "follow-up collection"),
    ("grok_shanghai_wave_20260730", "Shanghai-query export with JSON sidecars"),
)

# A curated allow-list avoids treating every .org.cn/.gov.cn URL as equally
# authoritative.  The class is a routing aid, not a truth claim about a page.
DOMESTIC_OFFICIAL_HOSTS = {
    "www.saac.gov.cn",
    "www.nlc.cn",
    "www.cppcc.gov.cn",
    "www.93.gov.cn",
    "www.mmzy.org.cn",
    "www.zytzb.gov.cn",
    "www.dswxyjy.org.cn",
    "cpc.people.com.cn",
    "dangshi.people.com.cn",
    "www.rmzxb.com.cn",
    "www.rmzxw.com.cn",
    "www.dajs.gov.cn",
    "www.hnmm.gov.cn",
    "www.taimeng.org.cn",
    "www.bjdcmm.org.cn",
    "www.bjmm.org.cn",
    "www.hljmm.gov.cn",
    "www.hbmj.gov.cn",
    "www.bjtzb.gov.cn",
    "www.zl1872.cn",
    "mng.minmengsh.gov.cn",
    "www.minmengsh.gov.cn",
    "paper.minmengsh.gov.cn",
    "mm.yantai.gov.cn",
    "www.ynda.yn.gov.cn",
    "www.ahmm.gov.cn",
    "www.zjmm.gov.cn",
    "www.sdmm.org.cn",
    "www.ngd.org.cn",
    "www.xinhuanet.com",
    "epaper.gmw.cn",
    "news.gmw.cn",
    "www.qstheory.cn",
    "www.library.sh.cn",
}

ACADEMIC_HOST_MARKERS = (
    "cssn.cn",
    "aisixiang.com",
    "tsinghua.edu.cn",
    "cupk.edu.cn",
    "shukui.net",
)

PUBLIC_SURROGATE_HOSTS = {
    "zh.wikisource.org",
    "zh.wikipedia.org",
    "commons.wikimedia.org",
    "upload.wikimedia.org",
    "www.marxists.org",
    "archive.org",
    "www.sohu.com",
    "news.sohu.com",
    "book.kongfz.com",
    "www.csspw.com.cn",
}

FOREIGN_CONTEXT_HOSTS = {
    "history.state.gov",
    "npl.ly.gov.tw",
    "tk.dhcdb.com.tw",
    "lib.hku.hk",
    "commons.ln.edu.hk",
}

PRIORITY_TERMS = (
    "成立宣言",
    "政团同盟",
    "第一次全国代表大会",
    "全国代表大会",
    "会议记录",
    "共同纲领",
    "组织法",
    "宣言",
    "公报",
    "谈话",
    "发言",
    "光明报",
    "大公报",
    "人民日报",
    "解放日报",
    "1941",
    "1945",
    "1947",
    "1948",
    "1949",
)


def iter_files(root: Path) -> Iterable[Path]:
    """Yield regular files without following symlinked files."""
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        yield path


def url_key(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlsplit(text)
    if not parsed.scheme or not parsed.netloc:
        return text.rstrip("/")
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{parsed.scheme.lower()}://{host}{path}{query}{fragment}"


def host_of(value: Any) -> str:
    try:
        return urlsplit(str(value or "").strip()).netloc.lower().split("@")[-1].split(":")[0]
    except ValueError:
        return ""


def host_matches(host: str, values: set[str]) -> bool:
    return host in values or any(host.endswith("." + value) for value in values)


def source_class(source_url: str) -> str:
    host = host_of(source_url)
    if host_matches(host, FOREIGN_CONTEXT_HOSTS):
        return "foreign_context_or_catalogue"
    if host_matches(host, DOMESTIC_OFFICIAL_HOSTS):
        return "domestic_official_or_institutional"
    if any(host == marker or host.endswith("." + marker) for marker in ACADEMIC_HOST_MARKERS):
        return "academic_or_research_portal"
    if host_matches(host, PUBLIC_SURROGATE_HOSTS):
        return "public_surrogate_or_mirror"
    return "unclassified_public_source"


def load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, str(exc)


def load_canonical_metadata(repo: Path) -> dict[str, Any]:
    candidate_path = repo / "data" / "domestic" / "candidates.jsonl"
    candidate_urls: set[str] = set()
    candidate_lines = 0
    candidate_records = 0
    candidate_errors: list[str] = []
    if candidate_path.exists():
        for line_number, line in enumerate(candidate_path.read_text(encoding="utf-8").splitlines(), 1):
            candidate_lines += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                candidate_errors.append(f"line {line_number}: {exc}")
                continue
            candidate_records += 1
            if isinstance(record, dict):
                key = url_key(record.get("source_url"))
                if key:
                    candidate_urls.add(key)

    source_path = repo / "data" / "domestic" / "source_registry.json"
    source_registry_urls: set[str] = set()
    source_payload, source_error = load_json(source_path)
    if isinstance(source_payload, list):
        for record in source_payload:
            if not isinstance(record, dict):
                continue
            for field in ("official_url", "record_or_search_url"):
                key = url_key(record.get(field))
                if key:
                    source_registry_urls.add(key)

    academic_path = repo / "data" / "domestic" / "academic_layer_metadata.json"
    academic_payload, academic_error = load_json(academic_path)
    academic_records = (
        academic_payload.get("records", [])
        if isinstance(academic_payload, dict)
        else []
    )
    academic_ids = {
        str(record.get("external_id") or record.get("record_id") or "").strip()
        for record in academic_records
        if isinstance(record, dict)
    }

    queue_path = repo / "data" / "domestic" / "primary_retrieval_queue.json"
    queue_payload, queue_error = load_json(queue_path)
    if isinstance(queue_payload, dict):
        queue_records = queue_payload.get("records")
        if not isinstance(queue_records, list) or not queue_records:
            queue_records = queue_payload.get("topics", [])
    else:
        queue_records = []
    queue_open = sum(
        1
        for record in queue_records
        if isinstance(record, dict)
        and str(record.get("primary_evidence_status") or "") != "closed"
    )

    return {
        "candidate_line_count": candidate_lines,
        "candidate_record_count": candidate_records,
        "candidate_parse_errors": candidate_errors,
        "candidate_urls": candidate_urls,
        "source_registry_url_count": len(source_registry_urls),
        "source_registry_urls": source_registry_urls,
        "source_registry_error": source_error,
        "academic_metadata_record_count": len(academic_ids),
        "academic_metadata_ids": academic_ids,
        "academic_metadata_error": academic_error,
        "primary_queue_record_count": len(queue_records),
        "primary_queue_open_count": queue_open,
        "primary_queue_error": queue_error,
    }


def read_sidecars(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not root.exists():
        return records, errors
    for path in sorted(root.rglob("*.json")):
        if "metadata" not in path.parts and "meta" not in path.parts:
            continue
        payload, error = load_json(path)
        if error:
            errors.append(f"{path.name}: {error}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"{path.name}: metadata sidecar is not an object")
            continue
        record = dict(payload)
        record["_sidecar_name"] = path.name
        records.append(record)
    return records, errors


def title_hint(record: dict[str, Any]) -> str:
    local_path = str(record.get("local_path") or "")
    name = Path(local_path).name if local_path else str(record.get("title") or "")
    for suffix in (".html", ".pdf", ".jpg", ".jpeg", ".png", ".txt"):
        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


def recommend(record: dict[str, Any], canonical: dict[str, Any]) -> tuple[str, str]:
    source_url = url_key(record.get("source_url") or record.get("landing_url"))
    if source_url and source_url in canonical["candidate_urls"]:
        return "DUPLICATE_EXACT_URL", "already represented by a canonical candidate URL"
    if source_url and source_url in canonical["source_registry_urls"]:
        return "KNOWN_ROUTE_NOT_CANDIDATE", "known source route; reconcile with the candidate registry first"
    category = source_class(str(record.get("source_url") or record.get("landing_url") or ""))
    if category == "domestic_official_or_institutional":
        return "PROMOTE_METADATA_REVIEW", "official/institutional route is a metadata admission candidate"
    if category == "academic_or_research_portal":
        return "PROMOTE_ACADEMIC_METADATA_REVIEW", "academic identity and publication details are still required"
    if category == "public_surrogate_or_mirror":
        return "LEAD_ONLY_SURROGATE_REVIEW", "use as a public surrogate or discovery lead, not as an original"
    if category == "foreign_context_or_catalogue":
        return "CONTEXT_ONLY", "retain as foreign/context or catalogue evidence"
    return "UNCLASSIFIED_HOLD", "source class and identity need manual reconciliation"


def safe_intake_record(record: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    """Return a body-free queue record with no local filesystem fields."""
    source_url = str(record.get("source_url") or record.get("landing_url") or "").strip()
    category = source_class(source_url)
    disposition, reason = recommend(record, canonical)
    external_id = str(record.get("object_id") or record.get("_sidecar_name") or "").strip()
    raw_bytes = record.get("bytes")
    try:
        size_bytes = int(raw_bytes) if raw_bytes is not None else None
    except (TypeError, ValueError):
        size_bytes = None
    raw_status = record.get("http_status")
    try:
        http_status = int(raw_status) if raw_status is not None else None
    except (TypeError, ValueError):
        http_status = None
    return {
        "external_id": external_id,
        "title_hint": title_hint(record),
        "source_url": source_url,
        "source_host": host_of(source_url),
        "source_class": category,
        "disposition": disposition,
        "disposition_reason": reason,
        "content_type": str(record.get("content_type") or record.get("magic") or "").strip(),
        "http_status": http_status,
        "access_status": str(record.get("access_status") or "").strip(),
        "size_bytes": size_bytes,
        "file_sha256": str(record.get("sha256") or "").strip(),
        "rights_note": str(record.get("rights_note") or "").strip(),
        "retrieved_or_collected_at": str(
            record.get("retrieved_at") or record.get("collected_at") or ""
        ).strip(),
        "metadata_only": True,
        "body_read": False,
        "ocr_performed": False,
        "formal_db_written": False,
    }


def intake_payload(
    repo: Path,
    sibling: Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the unmatched sidecar queue without copying any source body."""
    generated_at = generated_at or dt.datetime.now(dt.timezone.utc).isoformat()
    canonical = load_canonical_metadata(repo)
    _, sidecars = inventory(sibling, canonical)
    records: list[dict[str, Any]] = []
    excluded_exact_url_count = 0
    for record in sidecars:
        disposition, _ = recommend(record, canonical)
        if disposition == "DUPLICATE_EXACT_URL":
            excluded_exact_url_count += 1
            continue
        records.append(safe_intake_record(record, canonical))
    records.sort(key=lambda item: (item["disposition"], item["external_id"], item["source_url"]))
    dispositions = Counter(str(record["disposition"]) for record in records)
    payload = {
        "schema_version": "domestic_sibling_collection_intake_queue.v1",
        "generated_at": generated_at,
        "scope": "unmatched sibling JSON sidecars; metadata-only admission queue",
        "body_read": False,
        "ocr_performed": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "files_copied": False,
        "files_deleted_or_moved": False,
        "canonical_candidate_record_count": canonical["candidate_record_count"],
        "sidecar_record_count": len(sidecars),
        "excluded_exact_candidate_url_count": excluded_exact_url_count,
        "queue_record_count": len(records),
        "disposition_counts": dict(dispositions.most_common()),
        "records": records,
    }
    serialized = json.dumps(payload, ensure_ascii=False)
    for marker in ("/Users/", "/private/", "/tmp/", '"local_path"', '"source_file"', '"page_image_path"'):
        if marker in serialized:
            raise ValueError(f"intake queue contains forbidden local marker: {marker}")
    return payload


def inventory(root: Path, canonical: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    summaries: list[dict[str, Any]] = []
    sidecar_records: list[dict[str, Any]] = []
    for name, role in COLLECTIONS:
        collection_root = root / "data" / "domestic" / name
        files = list(iter_files(collection_root))
        extensions = Counter(path.suffix.lower() or "[no_ext]" for path in files)
        top_dirs = Counter(
            str(path.relative_to(collection_root).parts[0])
            if path.relative_to(collection_root).parts
            else "."
            for path in files
        )
        logical_stems = {
            path.name.rsplit(".", 1)[0] if "." in path.name else path.name
            for path in files
        }
        records, errors = read_sidecars(collection_root)
        for record in records:
            record["_collection"] = name
        sidecar_records.extend(records)
        summaries.append(
            {
                "collection": name,
                "role": role,
                "exists": collection_root.exists(),
                "physical_file_count": len(files),
                "extension_counts": dict(sorted(extensions.items())),
                "top_level_counts": dict(sorted(top_dirs.items())),
                "filename_stem_count": len(logical_stems),
                "sidecar_count": len(records),
                "sidecar_error_count": len(errors),
                "sidecar_errors": errors[:10],
            }
        )
    return summaries, sidecar_records


def audit(repo: Path, sibling: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or dt.datetime.now(dt.timezone.utc).isoformat()
    canonical = load_canonical_metadata(repo)
    collections, sidecars = inventory(sibling, canonical)
    decisions: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    host_counts: Counter[str] = Counter()
    url_matches = 0
    sha_present = 0
    rights_present = 0
    examples: list[dict[str, Any]] = []

    for record in sidecars:
        source_url = str(record.get("source_url") or record.get("landing_url") or "")
        category = source_class(source_url)
        disposition, reason = recommend(record, canonical)
        classes[category] += 1
        decisions[disposition] += 1
        host_counts[host_of(source_url) or "[missing]"] += 1
        if url_key(source_url) in canonical["candidate_urls"]:
            url_matches += 1
        if str(record.get("sha256") or "").strip():
            sha_present += 1
        if str(record.get("rights_note") or "").strip():
            rights_present += 1

        hint = title_hint(record)
        score = sum(1 for term in PRIORITY_TERMS if term.lower() in hint.lower())
        if disposition in {"PROMOTE_METADATA_REVIEW", "PROMOTE_ACADEMIC_METADATA_REVIEW"} and score:
            examples.append(
                {
                    "object_id": str(record.get("object_id") or ""),
                    "title_hint": hint,
                    "source_url": source_url,
                    "source_class": category,
                    "disposition": disposition,
                    "reason": reason,
                    "priority_score": score,
                }
            )

    examples.sort(key=lambda item: (-int(item["priority_score"]), item["object_id"], item["source_url"]))
    examples = examples[:24]

    return {
        "schema_version": "domestic_sibling_collection_admission_audit.v1",
        "generated_at": generated_at,
        "scope": "sibling collection JSON sidecars, filenames, URLs, and filesystem statistics only",
        "body_read": False,
        "ocr_performed": False,
        "formal_db_written": False,
        "files_copied": False,
        "files_deleted_or_moved": False,
        "repo_role": "canonical closeout checkout",
        "sibling_role": "external data checkout under review",
        "canonical_baseline": {
            "candidate_line_count": canonical["candidate_line_count"],
            "candidate_record_count": canonical["candidate_record_count"],
            "candidate_parse_error_count": len(canonical["candidate_parse_errors"]),
            "source_registry_url_count": canonical["source_registry_url_count"],
            "academic_metadata_record_count": canonical["academic_metadata_record_count"],
            "primary_queue_record_count": canonical["primary_queue_record_count"],
            "primary_queue_open_count": canonical["primary_queue_open_count"],
        },
        "collection_inventory": collections,
        "sidecar_summary": {
            "sidecar_record_count": len(sidecars),
            "exact_candidate_url_matches": url_matches,
            "new_or_unmatched_url_count": len(sidecars) - url_matches,
            "sha256_present_count": sha_present,
            "rights_note_present_count": rights_present,
            "source_classes": dict(classes.most_common()),
            "dispositions": dict(decisions.most_common()),
            "top_hosts": host_counts.most_common(25),
        },
        "priority_examples": examples,
        "admission_policy": {
            "DUPLICATE_EXACT_URL": "do not copy or re-ingest; reconcile only if the canonical record is incomplete",
            "PROMOTE_METADATA_REVIEW": "create a body-free metadata candidate after title/date/creator/identity/rights reconciliation",
            "PROMOTE_ACADEMIC_METADATA_REVIEW": "attach author, institution, publication, year, DOI or stable URL before queue admission",
            "LEAD_ONLY_SURROGATE_REVIEW": "retain as surrogate/discovery evidence; never label it as the original",
            "CONTEXT_ONLY": "retain for context or catalogue navigation, outside domestic primary closure",
            "UNCLASSIFIED_HOLD": "do not promote until source class and identity are resolved",
        },
        "open_boundary": {
            "p0_status": "unchanged; this audit does not close any primary-original gap",
            "next_safe_action": "review metadata candidates and attach provenance before any copy, OCR, or SQLite write",
        },
    }


def markdown(report: dict[str, Any]) -> str:
    baseline = report["canonical_baseline"]
    summary = report["sidecar_summary"]
    lines = [
        f"# Sibling 采集包准入审计（{str(report.get('generated_at') or '')[:10]}）",
        "",
        "本审计只读取 JSON 元数据、公开 URL、文件名和文件统计；未读取 HTML/PDF/图片正文，未 OCR，未写入 SQLite，未复制、移动或删除文件。",
        "",
        "## 审计结论",
        "",
        "Sibling 工作区不是可整体导入的资料包，而是多类证据与中间产物的混合目录。准入必须先按来源身份和证据角色分流。当前审计不改变 P0 状态，也不产生正式库写入。",
        "",
        f"主线候选基线：{baseline['candidate_record_count']} 条可解析记录；Sibling 元数据 sidecar：{summary['sidecar_record_count']} 条；其中 {summary['exact_candidate_url_matches']} 条 URL 已与主线候选精确匹配，不能再次导入。",
        "",
        "## 当前目录盘点",
        "",
        "| 采集目录 | 文件数 | 后缀统计 | sidecar | 文件名逻辑组 |",
        "|---|---:|---|---:|---:|",
    ]
    for item in report["collection_inventory"]:
        ext = ", ".join(f"{key}={value}" for key, value in item["extension_counts"].items()) or "—"
        lines.append(
            f"| `{item['collection']}` | {item['physical_file_count']} | {ext} | "
            f"{item['sidecar_count']} | {item['filename_stem_count']} |"
        )
    lines.extend(
        [
            "",
            "说明：`academic_public_20260730`、`grok_next_stage_20260730` 等目录即使有 HTML/PDF 文件，若没有与之绑定的题名、作者、机构、刊物、日期、稳定 URL、权限和哈希元数据，也不能凭文件名进入学术层或正式库。",
            "",
            "## Sidecar 来源分流",
            "",
            "| 来源类别 | 数量 |",
            "|---|---:|",
        ]
    )
    for name, count in summary["source_classes"].items():
        lines.append(f"| `{name}` | {count} |")
    lines.extend(["", "| 准入建议 | 数量 |", "|---|---:|"])
    for name, count in summary["dispositions"].items():
        lines.append(f"| `{name}` | {count} |")
    lines.extend(
        [
            "",
            "## 可优先复核的元数据线索",
            "",
            "以下只是从 object_id、公开 URL 和文件名提示词筛出的复核入口，不代表正文已读、来源身份已闭合或已达到 citation-ready。",
            "",
            "| object_id | 文件名提示 | 来源类别 | 建议 | URL |",
            "|---|---|---|---|---|",
        ]
    )
    for item in report["priority_examples"]:
        lines.append(
            f"| `{item['object_id'] or '—'}` | {item['title_hint']} | `{item['source_class']}` | "
            f"`{item['disposition']}` | {item['source_url'] or '—'} |"
        )
    lines.extend(
        [
            "",
            "## 下一步准入顺序",
            "",
            "1. 对 `PROMOTE_METADATA_REVIEW` 记录补齐题名、作者/机构、日期、版本/档号、来源 URL、权限和 SHA256，再与主线 `candidates.jsonl` 去重。",
            "2. 对 `PROMOTE_ACADEMIC_METADATA_REVIEW` 记录补齐作者、985/中央研究机构等机构证据、刊物卷期或 DOI；未补齐前只留在发现层。",
            "3. `LEAD_ONLY_SURROGATE_REVIEW` 只作为公开转载、转录或镜像线索；不把它当作同期原件，不用它关闭 1941/1947 P0。",
            "4. 已有可靠文本层的资料不再 OCR；只有完成身份绑定且确认没有可复用文本层后，才建立定向 OCR 队列。",
            "5. 通过准入审计前，不复制原件、不写正式 SQLite、不提交本地正文或 OCR 派生物。",
            "",
            "## 机器复核",
            "",
            "```bash",
            "python3 scripts/domestic/audit_sibling_collection_admission.py \\",
            "  --sibling-root /path/to/mingmeng-history-research \\",
            "  --output-json /tmp/sibling_collection_admission.json \\",
            "  --output-md /tmp/sibling_collection_admission.md",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--sibling-root", type=Path, default=DEFAULT_SIBLING)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--output-intake-json", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    sibling = args.sibling_root.resolve()
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    report = audit(repo, sibling, generated_at=generated_at)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(payload, encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(report), encoding="utf-8")
    if args.output_intake_json:
        intake = intake_payload(repo, sibling, generated_at=generated_at)
        args.output_intake_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_intake_json.write_text(
            json.dumps(intake, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
