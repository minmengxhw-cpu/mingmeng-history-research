#!/usr/bin/env python3
"""Batch 9: build, dry-run and optionally apply a formal SQLite migration.

Safety: exact DB hash guard, backup, transaction, FK/integrity verification.
No OCR. Candidate dispositions are written to domestic_candidates; orphan rows are removed.
Citation pass is reconciled to page provenance without blindly promoting unverifiable pages.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, shutil, sqlite3
from datetime import datetime
from pathlib import Path
from _guard import guard

guard()
BASE=Path(__file__).resolve().parents[2]
WORK=BASE/'work/deepseek-20260803'
AN=WORK/'02_analysis'; OUT=WORK/'04_migration'; OUT.mkdir(parents=True,exist_ok=True)
DEFAULT_DB=BASE/'data/research_index.sqlite'
EXPECTED_SHA='bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def readcsv(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def map_level(v): return v.split('→')[0] if '→' in v else v

def migrate(db:Path, apply:bool):
 before=sha(db)
 if apply and before!=EXPECTED_SHA: raise SystemExit(f'hash changed; expected {EXPECTED_SHA}, got {before}')
 target=db
 backup=None
 if not apply:
  target=OUT/'research_index.batch9.dryrun.sqlite'; shutil.copy2(db,target)
 else:
  stamp=datetime.now().strftime('%Y%m%dT%H%M%S'); backup=db.with_name(db.name+f'.pre_deepseek_batch9_{stamp}.bak'); shutil.copy2(db,backup)
  if sha(backup)!=before: raise SystemExit('backup hash mismatch')
 reviews=readcsv(AN/'review_dispositions.csv'); orphans=readcsv(AN/'orphan_dispositions.csv'); passes=readcsv(AN/'citation_gate_pass.csv')
 con=sqlite3.connect(target); con.row_factory=sqlite3.Row
 con.execute('PRAGMA foreign_keys=ON'); con.execute('BEGIN IMMEDIATE')
 stats={}
 try:
  # Candidate decisions: exact candidate ID update, retaining full audit explanation.
  n=0
  for r in reviews:
   level=map_level(r['final_level'])
   status='accepted' if r['disposition'] not in ('待影像核验后升级',) else 'needs_human_review'
   note=f"DeepSeek audit: {r['disposition']}; {r['conclusion']}"
   cur=con.execute('''UPDATE domestic_candidates SET authenticity_level_accepted=?, review_status=?, review_note=?, reviewed_at=?, reviewed_by=?, check_outcome=? WHERE candidate_id=?''',(level,status,note,datetime.now().isoformat(timespec='seconds'),'deepseek-domestic-audit-20260803',r['disposition'],r['candidate_id']))
   n+=cur.rowcount
  stats['review_rows_updated']=n
  # Delete only documented orphan PKs and assert they are still orphaned.
  ids=[int(r['document_id']) for r in orphans]
  live=con.execute(f"SELECT document_id FROM document_classifications WHERE document_id IN ({','.join('?'*len(ids))}) AND EXISTS(SELECT 1 FROM documents d WHERE d.id=document_id)",ids).fetchall()
  if live: raise RuntimeError(f'orphan IDs became live: {[x[0] for x in live]}')
  stats['orphans_deleted']=con.execute(f"DELETE FROM document_classifications WHERE document_id IN ({','.join('?'*len(ids))})",ids).rowcount
  # Citation reconciliation: pass candidates already linked to documents. Promote only pages
  # whose provenance is machine/human verified and does not require human review.
  passids=[r['candidate_id'] for r in passes]
  linked=con.execute(f"SELECT id,ingested_candidate_id FROM documents WHERE ingested_candidate_id IN ({','.join('?'*len(passids))})",passids).fetchall()
  docids=[x['id'] for x in linked]
  stats['citation_pass_candidates']=len(passids); stats['citation_linked_documents']=len(docids)
  promotable=0
  if docids:
   promotable=con.execute(f'''UPDATE page_provenance SET citation_ready=1, updated_at=? WHERE document_id IN ({','.join('?'*len(docids))}) AND needs_human_review=0 AND review_status IN ('machine_verified','human_verified')''',[datetime.now().isoformat(timespec='seconds'),*docids]).rowcount
  stats['provenance_rows_reconciled']=promotable
  fk=con.execute('PRAGMA foreign_key_check').fetchall(); integ=con.execute('PRAGMA integrity_check').fetchone()[0]
  remaining=con.execute('SELECT COUNT(*) FROM document_classifications dc LEFT JOIN documents d ON d.id=dc.document_id WHERE d.id IS NULL').fetchone()[0]
  # Five pre-existing research_events->pages violations are outside this migration's
  # classification scope. Record them, but reject any new/non-baseline violation.
  tolerated=[tuple(x) for x in fk if x[0]=='research_events' and x[1] in (315,316,317,318,319) and x[2]=='pages']
  unexpected=[tuple(x) for x in fk if tuple(x) not in tolerated]
  stats.update(foreign_key_violations=len(fk),tolerated_preexisting_fk_violations=len(tolerated),unexpected_fk_violations=len(unexpected),integrity_check=integ,remaining_classification_orphans=remaining)
  if unexpected or integ!='ok' or remaining: raise RuntimeError(f'verification failed unexpected_fk={len(unexpected)} integrity={integ} orphans={remaining}')
  con.commit()
 except: con.rollback(); con.close(); raise
 con.close()
 after=sha(target)
 result={'mode':'apply' if apply else 'dry-run','database':str(target),'source_sha256':before,'result_sha256':after,'backup':str(backup) if backup else None,'stats':stats,'timestamp':datetime.now().isoformat()}
 (OUT/('batch9_apply_result.json' if apply else 'batch9_dryrun_result.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return result

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,default=DEFAULT_DB); ap.add_argument('--apply',action='store_true'); a=ap.parse_args()
 print(json.dumps(migrate(a.db,a.apply),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
