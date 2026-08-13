#!/usr/bin/env python3
"""Batch 8: canonical entity mapping and normalized relation tables."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
from _guard import guard

guard()
BASE = Path(__file__).resolve().parents[2]
IN = BASE / "work/deepseek-20260803/02_analysis/relations_events_1941_1950.csv"
OUT = BASE / "work/deepseek-20260803/02_analysis"

# Conservative mappings only: no ambiguous surname/title inference.
ALIASES = {
    "organization": {
        "民盟": "中国民主同盟", "民主同盟": "中国民主同盟", "中国民盟": "中国民主同盟",
        "中共": "中国共产党", "共产党": "中国共产党", "中国共产党中央委员会": "中国共产党",
        "国民党": "中国国民党", "中国国民党": "中国国民党", "国民党中央": "中国国民党",
        "政协": "政治协商会议", "旧政协": "政治协商会议",
        "美国国务院": "美国国务院", "美国务院": "美国国务院",
    },
    "theme": {
        "民盟": "中国民主同盟", "民主同盟": "中国民主同盟",
        "政协": "政治协商会议", "政治协商": "政治协商会议",
        "马歇尔调处": "马歇尔调停", "马歇尔调停": "马歇尔调停",
        "联合政府": "联合政府", "北平接触": "北平接触", "第三方面": "第三方面", "昆明暗杀": "昆明暗杀",
    },
    "person": {},
}


def split(v):
    if not v: return []
    for sep in ("；", ";", "、", "|"): v = v.replace(sep, ",")
    return [x.strip() for x in v.split(",") if x.strip()]


def main():
    events=list(csv.DictReader(open(IN,encoding='utf-8-sig')))
    fields=events[0].keys()
    # Batch5 fields are actors / organizations / tags.
    specs=(("person","actors"),("organization","organizations"),("theme","tags"))
    map_rows=[]
    normalized={}
    for kind,field in specs:
        seen=set()
        for e in events: seen.update(split(e.get(field,"")))
        for raw in sorted(seen):
            canon=ALIASES[kind].get(raw,raw)
            map_rows.append({"entity_type":kind,"raw_name":raw,"canonical_name":canon,"mapping_status":"mapped" if canon!=raw else "identity","mapping_basis":"controlled exact alias" if canon!=raw else "no unambiguous alias"})
        normalized[field]={r["raw_name"]:r["canonical_name"] for r in map_rows if r["entity_type"]==kind}
    with open(OUT/'entity_alias_map.csv','w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=map_rows[0].keys()); w.writeheader(); w.writerows(map_rows)

    event_rows=[]
    indexes={k:defaultdict(set) for k,_ in specs}
    years={k:defaultdict(list) for k,_ in specs}
    for e in events:
        row=dict(e)
        for kind,field in specs:
            vals=sorted(set(normalized[field].get(x,x) for x in split(e.get(field,""))))
            row[field+"_canonical"]=";".join(vals)
            for v in vals:
                indexes[kind][v].add(e['event_id'])
                if e.get('event_year'): years[kind][v].append(int(e['event_year']))
        event_rows.append(row)
    with open(OUT/'relations_events_1941_1950_canonical.csv','w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=event_rows[0].keys()); w.writeheader(); w.writerows(event_rows)

    for kind,_ in specs:
        rows=[]
        for name,ids in indexes[kind].items():
            yy=years[kind][name]
            rows.append({"canonical_name":name,"event_count":len(ids),"event_ids":";".join(sorted(ids,key=lambda x:int(x))),"year_min":min(yy) if yy else "","year_max":max(yy) if yy else ""})
        rows.sort(key=lambda r:(-r['event_count'],r['canonical_name']))
        with open(OUT/f'relations_{kind}_canonical.csv','w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

    merged=sum(r['mapping_status']=='mapped' for r in map_rows)
    report=["# Batch 8 · 实体同义异名规范映射","",f"- 事件：{len(events)}",f"- 原始实体：{len(map_rows)}",f"- 精确别名映射：{merged}","- 原则：仅合并无歧义的精确别名；人名未做简称/同姓推断。","","## 输出","","- `entity_alias_map.csv`","- `relations_events_1941_1950_canonical.csv`","- `relations_person_canonical.csv`","- `relations_organization_canonical.csv`","- `relations_theme_canonical.csv`","","本批只写研究层产物，未修改正式 SQLite。",""]
    (OUT/'batch8_entity_normalization_report.md').write_text('\n'.join(report),encoding='utf-8')
    print(f"events={len(events)}, entities={len(map_rows)}, aliases_mapped={merged}")

if __name__=='__main__': main()
