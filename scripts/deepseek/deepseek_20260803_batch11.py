#!/usr/bin/env python3
"""Batch 11: enrich bibliography using frozen, already-checked source metadata."""
from __future__ import annotations
import csv,re
from pathlib import Path
from _guard import guard
guard()
BASE=Path(__file__).resolve().parents[2]; IN=BASE/'work/deepseek-20260803/01_inputs'; AN=BASE/'work/deepseek-20260803/02_analysis'
def rows(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def main():
 bib=rows(AN/'bibliography_secondary.csv'); cand={r['candidate_id']:r for r in rows(IN/'domestic_candidates.csv')}
 out=[]
 for b in bib:
  c=cand[b['candidate_id']]; blob=' '.join([c.get('catalog_reference',''),c.get('evidence_note',''),c.get('evidence_locator','')])
  urls=re.findall(r'https?://[^\s；]+', ' '.join([c.get('source_url',''),c.get('evidence_locator','')]))
  isbn=b['isbn'] or next(iter(re.findall(r'97[89][\d\-]{10,20}',blob)), '')
  year=b['year']
  # Do not infer publication year from historical coverage mentioned in notes.
  # A year is added only when catalog_reference itself states one without “待核/待查”.
  if not year and not re.search(r'出版年待核|具体出版年待核|出版年待查|具体出版年待查',c.get('catalog_reference','')):
   candidates=[x for x in re.findall(r'(?<!\d)(19\d{2}|20\d{2})(?!\d)',c.get('catalog_reference','')) if x!='2026']
   year=candidates[0] if candidates else ''
  status=[]
  status.append('stable_link_present' if urls else 'no_stable_link')
  status.append('isbn_present' if isbn else 'isbn_missing')
  status.append('year_present' if year else 'year_missing')
  out.append({**b,'year':year,'isbn':isbn,'stable_url':urls[0] if urls else '', 'source_locator':c.get('evidence_locator',''),'catalog_reference':c.get('catalog_reference',''),'verification_status':';'.join(status),'verified_at':c.get('checked_at',''),'bibliographic_use':'secondary_only_not_primary_substitute'})
 fields=list(out[0])
 with open(AN/'bibliography_secondary_enriched.csv','w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 no_url=sum(not x['stable_url'] for x in out); no_isbn=sum(not x['isbn'] for x in out); no_year=sum(not x['year'] for x in out)
 md=['# Batch 11 · 二手书目补录与核验','',f'- 书目：{len(out)}',f'- 稳定链接缺失：{no_url}',f'- ISBN 缺失：{no_isbn}',f'- 出版年缺失：{no_year}','- 数据来源：冻结候选的 `source_url / evidence_locator / catalog_reference / evidence_note`。','- 未凭空补造 DOI；图书 DOI 继续留空。','- 所有条目维持 L4、secondary-only，不替代一手证据。','','## 核验状态','', '| 题名 | 年 | ISBN | 链接 |','|---|---:|---|---|']
 for x in out: md.append(f"| {x['title']} | {x['year']} | {x['isbn']} | {'有' if x['stable_url'] else '缺'} |")
 (AN/'batch11_bibliography_enrichment_report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
 print({'count':len(out),'no_url':no_url,'no_isbn':no_isbn,'no_year':no_year})
if __name__=='__main__':main()
