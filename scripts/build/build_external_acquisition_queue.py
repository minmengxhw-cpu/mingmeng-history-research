#!/usr/bin/env python3
"""Build a cross-archive acquisition queue for offline/assisted sources."""

from __future__ import annotations

import csv
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent.parent
SINICA_XLSX = ROOT / "docs" / "sinica" / "sinica_request_list.xlsx"
CSV_OUT = ROOT / "data" / "external_acquisition_queue.csv"
REPORT = ROOT / "docs" / "_external-acquisition-queue.md"

KWEW_ITEMS = [
    {
        "priority": "A1",
        "archive": "The National Archives, Kew",
        "ref": "WO 208/4770",
        "title": "Reports on political parties: Democratic League",
        "date": "1947 Sept-1948 Oct",
        "access": "未数字化；需 Kew 付费扫描或现场代查",
        "next_action": "先询价全卷扫描；同时询问页数和复制限制",
        "url": "https://discovery.nationalarchives.gov.uk/details/r/C4414285",
        "note": "英方军事情报部对民盟专项评估，覆盖 1947 非法化与 1948 在港改组。",
    },
    {
        "priority": "A2",
        "archive": "The National Archives, Kew",
        "ref": "FCO 141/16965",
        "title": "Singapore: Chinese Democratic League branch in Hong Kong",
        "date": "1947",
        "access": "未数字化；开放状态 A；需扫描或现场代查",
        "next_action": "优先询价，因公开状态较好，可能最快取得",
        "url": "https://discovery.nationalarchives.gov.uk/details/r/C14050228",
        "note": "新加坡殖民政府视角下的香港民盟分支，贴近 1947 非法化事件。",
    },
    {
        "priority": "A3",
        "archive": "The National Archives, Kew",
        "ref": "CO 537/3724",
        "title": "China Democratic League",
        "date": "1948",
        "access": "未数字化；需 Kew 付费扫描或现场代查",
        "next_action": "与 CO 537/4820 一并询价",
        "url": "https://discovery.nationalarchives.gov.uk/details/r/C1252251",
        "note": "1948 民盟在港复盘与改组，殖民部高密级通信。",
    },
    {
        "priority": "A4",
        "archive": "The National Archives, Kew / HKPRO",
        "ref": "CO 537/4820 / HKMS184-3-10",
        "title": "China Democratic League",
        "date": "1949",
        "access": "Kew 未数字化；HKPRO 显示 HKMS184-3-10 可查",
        "next_action": "优先走 HKPRO 检索/预约，Kew 作为备份路径",
        "url": "https://search.grs.gov.hk/en/search.xhtml?q=HKMS184-3-10",
        "note": "1949 民盟在港总部、北上与新政协前后港英殖民政府视角。",
    },
]


def read_sinica_a_items() -> list[dict[str, str]]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    items: list[dict[str, str]] = []
    if not SINICA_XLSX.exists():
        return items
    with ZipFile(SINICA_XLSX) as z:
        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows: list[list[str]] = []
    for row in root.iter(ns + "row"):
        vals = []
        for cell in row.findall(ns + "c"):
            inline = cell.find(ns + "is")
            value = cell.find(ns + "v")
            if inline is not None:
                vals.append("".join(t.text or "" for t in inline.iter(ns + "t")))
            elif value is not None:
                vals.append(value.text or "")
            else:
                vals.append("")
        rows.append(vals)
    if not rows:
        return items
    headers = rows[0]
    for row in rows[1:]:
        data = dict(zip(headers, row))
        if data.get("优先级") != "A":
            continue
        items.append({
            "priority": "B1",
            "archive": "中研院近代史研究所档案馆",
            "ref": data.get("馆藏号", ""),
            "title": data.get("题名", ""),
            "date": "",
            "access": data.get("提供方式", ""),
            "next_action": "委托台湾合作学者代查阅览室数字档",
            "url": "",
            "note": data.get("学术用途说明", ""),
        })
    return items


def build_rows() -> list[dict[str, str]]:
    return KWEW_ITEMS + read_sinica_a_items()


def write_csv(rows: list[dict[str, str]]) -> None:
    fields = ["priority", "archive", "ref", "title", "date", "access", "next_action", "url", "note"]
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, str]]) -> None:
    kew_hk = [r for r in rows if "Kew" in r["archive"] or "HKPRO" in r["archive"]]
    sinica = [r for r in rows if "近代史" in r["archive"]]
    lines = [
        "# 外部档案获取优先队列",
        "",
        "本队列用于推进未能直接在线批量入库的高价值档案，避免继续泛搜。",
        "",
        "## 总览",
        "",
        f"- Kew / HKPRO：{len(kew_hk)} 条",
        f"- Sinica 阅览室 A 档：{len(sinica)} 条",
        f"- CSV 队列：`{CSV_OUT.relative_to(ROOT)}`",
        "",
        "## 第一优先级：Kew / HKPRO",
        "",
        "| 优先级 | 馆藏号 | 标题 | 时间 | 下一步 |",
        "|---|---|---|---|---|",
    ]
    for row in kew_hk:
        lines.append(
            f"| {row['priority']} | {row['ref']} | {row['title']} | {row['date']} | {row['next_action']} |"
        )
    lines.extend([
        "",
        "## 第二优先级：Sinica 阅览室 A 档",
        "",
        "| 馆藏号 | 题名 | 下一步 |",
        "|---|---|---|",
    ])
    for row in sinica:
        lines.append(f"| {row['ref']} | {row['title']} | {row['next_action']} |")
    lines.extend([
        "",
        "## 执行原则",
        "",
        "1. Kew/HKPRO 先问价格、页数、复制限制，再决定是否全卷扫描。",
        "2. Sinica 先发 24 件 A 档清单，不把 B/C 档混入第一轮。",
        "3. 拿到扫描件后按既有流程做 OCR、原文全文、中文翻译、页码引用和来源卡。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_report(rows)
    print(f"external acquisition rows: {len(rows)}")
    print(f"report: {REPORT.relative_to(ROOT)}")
    print(f"csv: {CSV_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
