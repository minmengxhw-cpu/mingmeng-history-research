#!/usr/bin/env python3
"""Write verified open-source records that can become real acquisition targets."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
CSV_OUT = ROOT / "data" / "open_source_records.csv"
REPORT_OUT = ROOT / "docs" / "_open-source-records.md"


RECORDS = [
    {
        "record_id": "nus-ncj-1947-03-01",
        "source_line": "NUS 南侨日报",
        "archive": "NUS Libraries Digital Gems",
        "title": "南侨日报 1947年03月01日",
        "date": "1947-03-01",
        "url": "https://oa.nus.libnova.com/view/263319",
        "pages": "4",
        "access": "Open Access / Open",
        "relevance": "《南侨日报》是新加坡、马来亚民盟活动和海外民主运动的重要报刊线索；本条为具体开放期号，可进入 OCR 和全文筛查。",
        "status": "可入库候选；已确认具体日期、页数、开放状态",
        "next_action": "提取 PDF/JPG 下载接口，跑 OCR 后按“民盟、民主同盟、胡愈之、张楚琨、联合政府”等词筛页",
    },
    {
        "record_id": "nus-ncj-1948-10-04",
        "source_line": "NUS 南侨日报",
        "archive": "NUS Libraries Digital Gems",
        "title": "南侨日报 1948年10月04日",
        "date": "1948-10-04",
        "url": "https://oa.nus.libnova.com/view/264373",
        "pages": "8",
        "access": "Open Access / Open",
        "relevance": "具体开放期号；适合验证 NUS 下载、OCR、页码引用流程。",
        "status": "可入库候选；已确认具体日期、页数、开放状态",
        "next_action": "作为样本页优先破解下载接口，生成 PDF/图片本地镜像",
    },
    {
        "record_id": "nus-ncj-1949-09-06",
        "source_line": "NUS 南侨日报",
        "archive": "NUS Libraries Digital Gems",
        "title": "南侨日报 1949年09月06日",
        "date": "1949-09-06",
        "url": "https://oa.nus.libnova.com/view/264957",
        "pages": "9",
        "access": "Open Access / Open",
        "relevance": "1949 年民盟海外组织和新政协相关报道的高概率期号；需 OCR 后筛具体版面。",
        "status": "可入库候选；已确认具体日期、页数、开放状态",
        "next_action": "下载全期并按“政协、民盟、胡愈之、民主党派”做全文筛查",
    },
    {
        "record_id": "nus-ncj-1950-07-20",
        "source_line": "NUS 南侨日报",
        "archive": "NUS Libraries Digital Gems",
        "title": "南侨日报 1950年07月20日",
        "date": "1950-07-20",
        "url": "https://oa.nus.libnova.com/view/265391",
        "pages": "8",
        "access": "Open Access / Open",
        "relevance": "1950 年南洋民盟、报刊封禁前后舆论线索的候选期号；需 OCR 确认单篇内容。",
        "status": "可入库候选；已确认具体日期、页数、开放状态",
        "next_action": "下载全期并与 1950 年 9 月《南侨日报》封禁线索交叉核对",
    },
]


def write_csv() -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "record_id",
        "source_line",
        "archive",
        "title",
        "date",
        "url",
        "pages",
        "access",
        "relevance",
        "status",
        "next_action",
    ]
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(RECORDS)


def write_report() -> None:
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 开放资料源真实候选记录",
        "",
        "本表只放已经落到具体题名、日期、URL、开放状态的记录。GPA/JACAR 如果仅有入口或无命中，不放入本表。",
        "",
        "| 编号 | 题名 | 日期 | 页数 | 状态 |",
        "|---|---|---|---|---|",
    ]
    for row in RECORDS:
        lines.append(f"| {row['record_id']} | [{row['title']}]({row['url']}) | {row['date']} | {row['pages']} | {row['status']} |")
    lines.append("")
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    write_csv()
    write_report()
    print(f"open source records: {len(RECORDS)}")
    print(f"csv: {CSV_OUT.relative_to(ROOT)}")
    print(f"report: {REPORT_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
