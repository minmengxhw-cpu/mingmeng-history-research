#!/usr/bin/env python3
"""Build the first open-source acquisition queue for three new source lines."""

from __future__ import annotations

import csv
import html
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
CSV_OUT = ROOT / "data" / "open_source_probe.csv"
REPORT_OUT = ROOT / "docs" / "_open-source-probe.md"


@dataclass(frozen=True)
class Seed:
    priority: str
    source_line: str
    archive: str
    query: str
    title: str
    url: str
    access: str
    next_action: str
    note: str


GPA_BASE = "https://gpa.eastview.com/crl/lqrcn/"
NUS_NAN_CHIAU = "https://linc.nus.edu.sg/record=b2011354"
NUS_SAMPLE = "https://oa.nus.libnova.com/view/264373"
JACAR_SEARCH = "https://www.jacar.archives.go.jp/aj/search/"


def gpa_search_url(query: str) -> str:
    params = {
        "a": "q",
        "hs": "1",
        "r": "1",
        "results": "1",
        "txf": "txIN",
        "txq": query,
        "sf": "byDA",
        "l": "zh",
    }
    return GPA_BASE + "?" + urllib.parse.urlencode(params)


SEEDS: list[Seed] = [
    Seed(
        "A1",
        "GPA 民国报刊开放库",
        "East View / CRL Late Qing and Republican-Era Chinese Newspapers",
        "中國民主同盟",
        "中国民主同盟 / 民盟直接命中",
        gpa_search_url("中國民主同盟"),
        "开放访问；Veridian 全文检索；可继续按中文关键词抓候选页",
        "先按繁体关键词跑命中清单，再抽取 1944-1949 结果",
        "中文报刊库不适合用英文 Democratic League 检索，应以繁体中文为主。",
    ),
    Seed(
        "A2",
        "GPA 民国报刊开放库",
        "East View / CRL Late Qing and Republican-Era Chinese Newspapers",
        "中國民主政團同盟",
        "中国民主政团同盟 / 民盟前身",
        gpa_search_url("中國民主政團同盟"),
        "开放访问；适合抓 1941-1944 前身材料",
        "将结果与 FRUS 的 Federation of Chinese Democratic Parties 对照",
        "用于补足民盟成立前后公开舆论与政团同盟阶段。",
    ),
    Seed(
        "A3",
        "GPA 民国报刊开放库",
        "East View / CRL Late Qing and Republican-Era Chinese Newspapers",
        "張瀾 OR 羅隆基 OR 沈鈞儒 OR 章伯鈞",
        "民盟核心人物报刊线索",
        gpa_search_url('"張瀾" OR "羅隆基" OR "沈鈞儒" OR "章伯鈞"'),
        "开放访问；人物关键词可能比组织名命中更多",
        "分人物建候选表，优先张澜、罗隆基、沈钧儒、章伯钧",
        "用于构建人物档案链与事件时间线。",
    ),
    Seed(
        "A4",
        "NUS 南侨日报",
        "NUS Libraries Digital Gems",
        "南侨日报 / Nan Chiau Jit Pao",
        "南侨日报 1946-1950 在线版本",
        NUS_NAN_CHIAU,
        "NUS 目录确认在线版本；命令行抓取需进一步处理 TLS/页面接口",
        "用浏览器或备用接口确认期号列表，再按日期抓取图像/OCR",
        "《南侨日报》是新加坡/马来亚民盟支部的重要公开舆论源。",
    ),
    Seed(
        "A5",
        "NUS 南侨日报",
        "NUS Libraries Digital Gems",
        "南侨日报 1948-10-04",
        "南侨日报样本页",
        NUS_SAMPLE,
        "样本页公开；当前 curl 对 oa.nus.libnova.com TLS 握手失败",
        "用浏览器验证样本页资源结构，提取图片/文本接口",
        "先做一页样本，确认能否批量镜像。",
    ),
    Seed(
        "A6",
        "JACAR 日本亚洲历史资料中心",
        "Japan Center for Asian Historical Records",
        "中国民主政団同盟",
        "日方战时档案中的中国民主政团同盟",
        JACAR_SEARCH,
        "免费检索与在线图像；需使用 JACAR 正式检索参数",
        "用日文关键词和 JACAR 前台检索确认命中，再下载图像",
        "重点查外务省、陆军、情报部门对民盟前身和第三势力的评估。",
    ),
    Seed(
        "A7",
        "JACAR 日本亚洲历史资料中心",
        "Japan Center for Asian Historical Records",
        "第三勢力 / 張瀾 / 羅隆基 / 沈鈞儒",
        "日方对第三势力与民盟人物的观察",
        JACAR_SEARCH,
        "免费检索与在线图像；关键词需日文/旧字形组合",
        "建立日文关键词表，先抓题名和摘要，再筛图像",
        "JACAR 可能不直接用中国民主同盟命中，人物和第三势力可能更有效。",
    ),
]


def fetch_status(url: str, timeout: float = 8.0) -> tuple[int | None, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "mingmeng-research-probe/1.0"})
    try:
        context = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            raw = resp.read(160_000)
            text = raw.decode("utf-8", errors="replace")
            return resp.status, classify_html(text), text
    except urllib.error.HTTPError as exc:
        return exc.code, f"HTTP {exc.code}", ""
    except Exception as exc:  # network/TLS diagnostics are part of the queue.
        return None, f"{type(exc).__name__}: {exc}", ""


def classify_html(text: str) -> str:
    lower = text.lower()
    if "no results for" in lower or "未找到" in text:
        return "可访问；本关键词暂无命中"
    if "searchpagesearchresults" in lower or "search" in lower:
        return "可访问；检索页已返回"
    if "online version" in lower or "digital gems" in lower:
        return "可访问；含在线版本线索"
    if text:
        return "可访问"
    return "无正文"


def text_result_count(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"([0-9,]+)\s+results?\s+for", text, flags=re.I)
    if match:
        return match.group(1)
    if "No results for" in text:
        return "0"
    return ""


def write_outputs(rows: list[dict[str, str]]) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "priority",
        "source_line",
        "archive",
        "query",
        "title",
        "url",
        "access",
        "probe_status",
        "result_count",
        "next_action",
        "note",
    ]
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["source_line"], []).append(row)
    lines = [
        "# 全球开放资料源第一轮探勘",
        "",
        "本清单只收录可以免费访问、原则上可继续抓取全文或图像的资料源；未数字化或需付费调档的资料继续放在外部调档队列。",
        "",
        f"- CSV：`{CSV_OUT.relative_to(ROOT)}`",
        f"- 生成脚本：`scripts/probe/probe_open_sources.py`",
        "",
    ]
    for source_line, items in grouped.items():
        lines.extend([f"## {source_line}", "", "| 优先级 | 检索/题名 | 探测状态 | 下一步 |", "|---|---|---|---|"])
        for row in items:
            title = row["title"].replace("|", "/")
            status = row["probe_status"].replace("|", "/")
            action = row["next_action"].replace("|", "/")
            lines.append(f"| {row['priority']} | {title} | {status} | {action} |")
        lines.append("")
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows: list[dict[str, str]] = []
    for seed in SEEDS:
        status_code, status, text = fetch_status(seed.url)
        probe_status = f"{status_code or '-'} · {status}"
        rows.append({
            "priority": seed.priority,
            "source_line": seed.source_line,
            "archive": seed.archive,
            "query": seed.query,
            "title": seed.title,
            "url": seed.url,
            "access": seed.access,
            "probe_status": probe_status,
            "result_count": text_result_count(text),
            "next_action": seed.next_action,
            "note": seed.note,
        })
    write_outputs(rows)
    print(f"open source probe rows: {len(rows)}")
    print(f"csv: {CSV_OUT.relative_to(ROOT)}")
    print(f"report: {REPORT_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
