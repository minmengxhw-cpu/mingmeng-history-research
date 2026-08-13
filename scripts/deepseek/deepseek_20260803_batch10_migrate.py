#!/usr/bin/env python3
"""Batch 10: remove five invalid event stubs and verify 22 Guangmingbao articles."""
from __future__ import annotations
import csv, hashlib, json, shutil, sqlite3
from datetime import datetime
from pathlib import Path
from _guard import guard
guard()
BASE=Path(__file__).resolve().parents[2]; AN=BASE/'work/deepseek-20260803/02_analysis'; OUT=BASE/'work/deepseek-20260803/04_migration'; OUT.mkdir(parents=True,exist_ok=True)
DB=BASE/'data/research_index.sqlite'
EXPECTED='e8df06ae53fbe8a4d997e57472d21e0d24fe913ffa26ff76d271de97899329ec'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def main():
 before=sha(DB)
 if before!=EXPECTED: raise SystemExit(f'hash mismatch: {before}')
 # Derive exact 22 from frozen duplicate report, not a hand-entered list.
 dup=list(csv.DictReader(open(BASE/'work/deepseek-20260803/01_inputs/manifest_duplicate_report.csv',encoding='utf-8-sig')))
 rows=[r for r in dup if r['cluster_id'] in {f'DCL-{i:04d}' for i in range(19,25)}]
 ids=[r['duplicate_candidate_id'] for r in rows]
 if len(ids)!=22 or len(set(ids))!=22: raise SystemExit(f'expected 22, got {len(ids)}/{len(set(ids))}')
 stamp=datetime.now().strftime('%Y%m%dT%H%M%S'); backup=DB.with_name(DB.name+f'.pre_deepseek_batch10_{stamp}.bak'); shutil.copy2(DB,backup)
 if sha(backup)!=before: raise SystemExit('backup mismatch')
 con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; con.execute('PRAGMA foreign_keys=ON'); con.execute('BEGIN IMMEDIATE')
 try:
  ev=con.execute('SELECT * FROM research_events WHERE id BETWEEN 315 AND 319 ORDER BY id').fetchall()
  if len(ev)!=5 or any((x['event_summary'] or '').strip() not in {'--- page break ---','抱歉，您似乎只提供了“--- page break ---”这一行，没有提供需要翻译的英文档案正文。请提供完整的英文档案内容，我将严格按照您的要求进行学术级中文翻译。'} for x in ev): raise RuntimeError('event stubs changed')
  deleted=con.execute('DELETE FROM research_events WHERE id BETWEEN 315 AND 319').rowcount
  q=','.join('?'*len(ids)); found=con.execute(f'''SELECT c.candidate_id,c.title,c.review_status,c.ingested_document_id,d.id document_id,COUNT(p.id) page_count,SUM(length(p.text)) text_chars,SUM(CASE WHEN pp.citation_ready=1 THEN 1 ELSE 0 END) citation_pages FROM domestic_candidates c LEFT JOIN documents d ON d.id=c.ingested_document_id LEFT JOIN pages p ON p.document_id=d.id LEFT JOIN page_provenance pp ON pp.page_id=p.id WHERE c.candidate_id IN ({q}) GROUP BY c.candidate_id ORDER BY c.candidate_id''',ids).fetchall()
  if len(found)!=22 or any(not x['document_id'] or not x['page_count'] or not x['citation_pages'] for x in found): raise RuntimeError('22 article verification failed')
  # Record recovery from erroneous duplicate classification in candidate audit fields.
  note='DeepSeek Batch10: verified distinct article-level item; DCL-0019—0024 container-vs-article false duplicate; retained as independent document.'
  updated=con.execute(f'''UPDATE domestic_candidates SET review_status='accepted', review_note=?, reviewed_at=?, reviewed_by='deepseek-domestic-audit-20260803', check_outcome='false_duplicate_recovered' WHERE candidate_id IN ({q})''',[note,datetime.now().isoformat(timespec='seconds'),*ids]).rowcount
  fk=con.execute('PRAGMA foreign_key_check').fetchall(); unexpected=[tuple(x) for x in fk]
  integ=con.execute('PRAGMA integrity_check').fetchone()[0]
  if unexpected or integ!='ok': raise RuntimeError(f'validation fk={unexpected}, integrity={integ}')
  con.commit()
 except: con.rollback(); con.close(); raise
 con.close()
 # Evidence CSV
 with open(AN/'guangmingbao_22_recovery_verification.csv','w',encoding='utf-8-sig',newline='') as f:
  fields=found[0].keys(); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(dict(x) for x in found)
 after=sha(DB); result={'before_sha256':before,'after_sha256':after,'backup':str(backup),'invalid_events_deleted':deleted,'guangmingbao_articles_verified':len(found),'candidate_rows_updated':updated,'foreign_key_violations':0,'integrity_check':'ok','timestamp':datetime.now().isoformat()}
 (OUT/'batch10_apply_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
