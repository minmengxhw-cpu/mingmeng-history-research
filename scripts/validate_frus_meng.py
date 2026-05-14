#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path.cwd()
DATA_DIR = ROOT / "data" / "frus_meng"
HITS_CSV = DATA_DIR / "frus_meng_hits.csv"
REPORT = DATA_DIR / "frus_meng_validation.md"

DIRECT_RE = re.compile(
    r"China Democratic League|Chinese Democratic League|Democratic League|"
    r"Democratic Political League|Federation of Chinese Democratic Parties",
    re.IGNORECASE,
)

CHINA_CONTEXT_RE = re.compile(
    r"China|Chinese|Chungking|Nanking|Peking|Peiping|Shanghai|Kuomintang|"
    r"Communist|PCC|Political Consultative|National Assembly|Marshall",
    re.IGNORECASE,
)


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def confidence(row: dict[str, str], text: str) -> str:
    terms = row["matched_terms"].lower()
    if "federation of chinese democratic parties" in terms:
        return "high"
    if "china democratic league" in terms or "chinese democratic league" in terms:
        return "high"
    if row["hit_type"] == "direct_org" and "china" in row["volume_title"].lower():
        return "high"
    if row["hit_type"] == "direct_org" and CHINA_CONTEXT_RE.search(text):
        return "medium"
    return "candidate"


def page_anchor_count(html_path: Path) -> int:
    if not html_path.exists():
        return 0
    return len(re.findall(r'id="pg_\d+"', html_path.read_text(encoding="utf-8", errors="replace")))


def main() -> None:
    rows = list(csv.DictReader(HITS_CSV.open(encoding="utf-8")))
    issues: list[str] = []
    counts = Counter()
    volume_counts: dict[str, Counter] = defaultdict(Counter)
    samples: dict[str, list[dict[str, str]]] = defaultdict(list)
    exact_page_docs = 0

    for row in rows:
        txt_path = Path(row["local_txt"])
        html_path = Path(row["local_html"])
        text = txt_path.read_text(encoding="utf-8", errors="replace") if txt_path.exists() else ""
        if not text:
            issues.append(f"Missing text: {row['volume_id']}/{row['doc_id']}")
            continue
        if row["hit_type"] == "direct_org" and not DIRECT_RE.search(text):
            issues.append(f"Direct row lacks direct term: {row['volume_id']}/{row['doc_id']}")
        if row["hit_type"] == "person_candidate" and DIRECT_RE.search(text):
            issues.append(f"Candidate row contains direct org term: {row['volume_id']}/{row['doc_id']}")
        level = confidence(row, text)
        counts[level] += 1
        volume_counts[row["volume_id"]][level] += 1
        if page_anchor_count(html_path):
            exact_page_docs += 1
        if len(samples[level]) < 8:
            samples[level].append(row)

    lines = [
        "# FRUS 民盟资料校验",
        "",
        f"- 校验对象：`{HITS_CSV}`",
        f"- 命中总数：{len(rows)}",
        f"- 高置信：{counts['high']}",
        f"- 中置信：{counts['medium']}",
        f"- 候选：{counts['candidate']}",
        f"- 含官方页码锚点的命中文档：{exact_page_docs}",
        f"- 结构性问题：{len(issues)}",
        "",
        "## 按卷册分布",
        "",
        "| 卷册 | 高置信 | 中置信 | 候选 |",
        "|---|---:|---:|---:|",
    ]
    for volume_id in sorted(volume_counts):
        c = volume_counts[volume_id]
        lines.append(f"| {volume_id} | {c['high']} | {c['medium']} | {c['candidate']} |")

    lines.extend(["", "## 校验结论", ""])
    if issues:
        lines.append("存在需要复查的结构性问题：")
        lines.extend(f"- {issue}" for issue in issues[:50])
    else:
        lines.append(
            "未发现结构性异常：直接组织命中均能在本地原文中复现对应组织词；人物候选未混入直接组织词。"
        )
    lines.append(
        "说明：`high` 表示直接出现中国/中华相关组织名，或出现在 FRUS 中国卷中的 Democratic League；"
        "`medium` 表示出现在非中国专卷但上下文仍指向中国政治语境；`candidate` 主要是人物异写，需要人工确认。"
    )

    for level in ["high", "medium", "candidate"]:
        lines.extend(["", f"## {level} 样本", ""])
        for row in samples[level]:
            text = Path(row["local_txt"]).read_text(encoding="utf-8", errors="replace")
            m = DIRECT_RE.search(text) or re.search(re.escape(row["matched_terms"].split(";")[0]), text, re.I)
            excerpt = compact(text[max(0, (m.start() if m else 0) - 180):(m.end() if m else 0) + 260])
            lines.append(f"### {row['volume_id']}/{row['doc_id']} - {row['date_guess']}")
            lines.append(f"- 链接：{row['url']}")
            lines.append(f"- 命中词：{row['matched_terms']}")
            lines.append(f"- 摘录：{excerpt}")
            lines.append("")

    REPORT.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
