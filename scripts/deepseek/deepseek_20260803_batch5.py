#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek 国内证据审计 · Batch 5：1941—1950 事件—人物—机构—主题关联
==================================================================
输入：01_inputs/research_events_all.csv（1914 条事件，;分隔多值）
输出（02_analysis/）：
  relations_events_1941_1950.csv  范围事件明细 + 清洗后的实体
  relations_people.csv            人物 → 关联事件数/年份区间/机构/主题
  relations_organizations.csv     机构 → 关联事件数/年份区间/人物
  relations_places.csv            地名 → 关联事件数/年份区间
  relations_themes.csv            主题 → 关联事件数/年份区间
  batch5_relations_report.md
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from _guard import guard

BASE = Path(__file__).resolve().parents[2]
IN = BASE / "work" / "deepseek-20260803" / "01_inputs"
OUT = BASE / "work" / "deepseek-20260803" / "02_analysis"

YEAR_MIN, YEAR_MAX = 1941, 1950


def split(v):
    if not v:
        return []
    return [s.strip() for s in v.split(";") if s.strip()]


def read_events():
    with open(IN / "research_events_all.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    p = OUT / name
    fn = list(dict.fromkeys(k for r in rows for k in r.keys()))
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fn})
    print(f"  [ok] {name} ({len(rows)} rows)")


def main():
    guard()
    events = read_events()
    print("events total:", len(events))

    in_scope = []
    no_year = 0
    for e in events:
        y = e.get("event_year", "").strip()
        if not y:
            no_year += 1
            continue
        try:
            yi = int(y)
        except ValueError:
            continue
        if YEAR_MIN <= yi <= YEAR_MAX:
            in_scope.append(e)

    print(f"in scope 1941-1950: {len(in_scope)} (no_year: {no_year})")

    # ---------- 事件明细 + 实体抽取 ----------
    detail = []
    for e in in_scope:
        detail.append({
            "event_id": e.get("id", ""),
            "event_year": e["event_year"],
            "event_date": e.get("event_date", ""),
            "event_title": (e.get("event_title") or "").strip(),
            "event_summary": (e.get("event_summary") or "").strip()[:200],
            "scope_type": e.get("scope_type", ""),
            "scope_name": (e.get("scope_name") or "").strip(),
            "actors": e.get("actors", ""),
            "tags": e.get("tags", ""),
            "organizations": e.get("organizations", ""),
            "places": e.get("places", ""),
            "importance": e.get("importance", ""),
        })
    write_csv("relations_events_1941_1950.csv", detail)

    # ---------- 实体统计 ----------
    people, orgs, places, themes = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for e in in_scope:
        y = int(e["event_year"])
        evid = e.get("id", "")
        for p in split(e.get("actors")):  people[p].append((y, evid))
        for o in split(e.get("organizations")): orgs[o].append((y, evid))
        for pl in split(e.get("places")): places[pl].append((y, evid))
        for t in split(e.get("tags")): themes[t].append((y, evid))

    def rows_for(counter, label):
        rows = []
        for name, items in counter.items():
            years = sorted({y for y, _ in items})
            evids = {e for _, e in items}
            rows.append({
                label: name,
                "event_count": len(evids),
                "event_ids": ";".join(sorted(evids)[:40]),
                "year_min": min(years),
                "year_max": max(years),
                "year_span": f"{min(years)}-{max(years)}",
            })
        rows.sort(key=lambda r: -r["event_count"])
        return rows

    write_csv("relations_people.csv", rows_for(people, "person"))
    write_csv("relations_organizations.csv", rows_for(orgs, "organization"))
    write_csv("relations_places.csv", rows_for(places, "place"))
    write_csv("relations_themes.csv", rows_for(themes, "theme"))

    # ---------- 人物—机构、机构—主题 共现 ----------
    person_org = defaultdict(set)
    org_theme = defaultdict(set)
    person_theme = defaultdict(set)
    for e in in_scope:
        ps = split(e.get("actors")); os_ = split(e.get("organizations")); ts = split(e.get("tags"))
        for p in ps:
            for o in os_: person_org[(p, o)].add(e.get("id", ""))
            for t in ts: person_theme[(p, t)].add(e.get("id", ""))
        for o in os_:
            for t in ts: org_theme[(o, t)].add(e.get("id", ""))

    def pair_rows(counter, a, b):
        rows = []
        for (x, y), evs in counter.items():
            rows.append({a: x, b: y, "cooccurrence_events": len(evs)})
        rows.sort(key=lambda r: -r["cooccurrence_events"])
        return rows

    write_csv("relations_person_org.csv", pair_rows(person_org, "person", "organization"))
    write_csv("relations_person_theme.csv", pair_rows(person_theme, "person", "theme"))
    write_csv("relations_org_theme.csv", pair_rows(org_theme, "organization", "theme"))

    top_p = rows_for(people, "person")[:12]
    top_o = rows_for(orgs, "organization")[:12]
    top_t = rows_for(themes, "theme")[:12]
    top_po = pair_rows(person_org, "person", "organization")[:12]

    def md_table(headers, rows, keys):
        lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
        for r in rows:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
        return "\n".join(lines)

    n_topic = sum(1 for e in in_scope if e.get("scope_type") == "topic")
    n_person = sum(1 for e in in_scope if e.get("scope_type") == "person")
    md = f"""# Batch 5 · 1941—1950 事件—人物—机构—主题关联

## 范围
- 输入：research_events_all.csv 共 {len(events)} 条事件；取 1941—1950 共 {len(in_scope)} 条（无年份 {no_year} 条排除）
- scope_type：topic {n_topic} / person {n_person}

## 实体规模
- 人物 {len(people)} 人、机构 {len(orgs)} 个、地名 {len(places)} 个、主题 {len(themes)} 个（均按事件计数）

## Top 人物（事件数）
{md_table(["人物", "事件数", "年份区间"], top_p, ["person", "event_count", "year_span"])}

## Top 机构
{md_table(["机构", "事件数", "年份区间"], top_o, ["organization", "event_count", "year_span"])}

## Top 主题
{md_table(["主题", "事件数", "年份区间"], top_t, ["theme", "event_count", "year_span"])}

## 人物—机构共现 Top
{md_table(["人物", "机构", "共现事件数"], top_po, ["person", "organization", "cooccurrence_events"])}

## 输出文件
- relations_events_1941_1950.csv / relations_people.csv / relations_organizations.csv / relations_places.csv / relations_themes.csv
- relations_person_org.csv / relations_person_theme.csv / relations_org_theme.csv

## 说明
- 实体值为原始 events 表字段；同义异名（如 民盟/中国民主同盟）未合并，命名规范合并属 Batch 2 元数据层后续事项
- 事件级关联已保留 event_ids 便于溯源
"""
    (OUT / "batch5_relations_report.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
