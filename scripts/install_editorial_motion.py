"""Prepare a selective animation content update, or apply its rows to a public DB."""
import argparse,base64,hashlib,json,re,shutil,sqlite3,sys
from contextlib import closing
from pathlib import Path
from standardize_editorial_code import public_database,checksum,dump,digest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'));sys.path.insert(0,str(ROOT/'backend/common'))
from insights import canonical_url

def programs(markdown):return re.findall(r'^ {0,3}(`{3,}|~{3,})[^\n]*\n(.*?)^ {0,3}\1\s*$',markdown,re.M|re.S)

def add(markdown,case,key):
 start='<!-- tb-motion:'+case['id']+':start -->';end='<!-- tb-motion:'+case['id']+':end -->'
 block=start+'\n\n!['+case['title']+']('+key+')\n\n'+end+'\n\n'
 if start in markdown:
  old=re.search(re.escape(start)+r'.*?'+re.escape(end)+r'\n\n',markdown,re.S);assert old
  result=markdown[:old.start()]+block+markdown[old.end():]
 else:
  at=markdown.find(case['after']) if case['after'] else -1
  if at>=0:
   stop=markdown.find('\n\n',at);position=len(markdown) if stop<0 else stop+2
  else:
   heading=re.search(r'^###\s+参考代码\s*$',markdown,re.M);assert heading,case['problemId'];position=heading.start()
  result=markdown[:position]+block+markdown[position:]
  assert result.replace(block,'',1)==markdown
 assert programs(result)==programs(markdown),'Reference or teaching code changed'
 return result

def prepare(args):
 source=args.library.resolve();work=args.work.resolve();assert not (work/'plan.json').exists() or args.refresh
 previous=json.loads((work/'plan.json').read_text('utf8')) if args.refresh else {'rows':[]}
 previous_rows={(r['table'],r['id']):r for r in previous['rows']}
 catalog=json.loads((ROOT/'data/editorial-motions.json').read_text('utf8'))['cases'];problems={r['id']:r for r in json.loads((source/'problems.json').read_text('utf8'))}
 urls={pid:canonical_url(r.get('url')) for pid,r in problems.items()};known={urls[c['problemId']]:c for c in catalog if urls[c['problemId']]}
 by_id={c['problemId']:c for c in catalog};changes=[];stats={};readers={};backup=work/'source-before'
 for table in ['solutions','detailed_solutions']:
  path=source/(table+'.json');raw=path.read_bytes();rows=json.loads(raw.decode('utf-8-sig'));count=0
  original={r['problem_id']:r for r in json.loads((work/'source-before'/path.name).read_text('utf8'))} if args.refresh else {}
  for row in rows:
   case=by_id.get(row['problem_id']) or known.get(urls.get(row['problem_id']))
   if not case:continue
   asset=ROOT/case['asset'];payload=asset.read_bytes();assert hashlib.sha256(payload).hexdigest()==case['sha256']
   key='assets/editorial-motion/'+case['id']+'-'+case['sha256'][:10]+'.svg';data='data:image/svg+xml;base64,'+base64.b64encode(payload).decode()
   if args.refresh:
    prior=previous_rows[(table,row['problem_id'])];assert row['markdown']==prior['markdown'] and row['images']==prior['images'],'Concurrent source edit'
   base=original.get(row['problem_id'],row);old=base['markdown'];images=dict(base.get('images',{}));new=add(old,case,key);updated={**images,key:data}
   if old==new and images==updated:continue
   assert all(updated.get(k)==v for k,v in images.items())
   changes.append({'table':table,'id':row['problem_id'],'oldMarkdown':old,'oldImages':images,'markdown':new,'images':updated,'motion':case['id']})
   row['markdown']=new;row['images']=updated;count+=1
  assert path.read_bytes()==raw,'Source changed during review'
  if count:
   backup.mkdir(parents=True,exist_ok=True)
   if not args.refresh:shutil.copy2(path,backup/path.name)
   dump(path,rows)
  stats[table]=count
  for row in rows:
   if row['problem_id'] in by_id:readers.setdefault(row['problem_id'],{})[table]=row
 methods=json.loads((source/'solution_methods.json').read_text('utf8'))
 for row in methods:
  if row['problem_id'] in by_id:assert all(not item.get('markdown') and not item.get('detailedSolution') for item in row['content'].get('methods',[])),'Review embedded alternate methods separately'
 assert len(readers)==len(catalog)
 dump(work/'plan.json',{'version':1,'source':str(source),'rows':changes,'counts':stats})
 fixtures=[]
 for case in catalog:
  pair=readers[case['problemId']];default=pair['solutions'];detail=pair['detailed_solutions'];fixtures.append({**case,'reader':{'title':case['title'],'markdown':default['markdown'],'images':default['images'],'detailedSolution':{'markdown':detail['markdown'],'images':detail['images']}}})
 dump(work/'reader-cases.json',fixtures)
 print(json.dumps({'cases':len(catalog),'changed':stats,'problemIdentities':len({r['id'] for r in changes}),'codeAndOldImagesPreserved':True},ensure_ascii=False))

def apply_database(path,plan,backup):
 path=Path(path).resolve();backup=Path(backup).resolve();assert not backup.exists();backup.parent.mkdir(parents=True,exist_ok=True)
 with closing(sqlite3.connect(path,timeout=30)) as db:
  db.row_factory=sqlite3.Row;public_database(db)
  with closing(sqlite3.connect(backup)) as saved:db.backup(saved);assert saved.execute('PRAGMA quick_check').fetchone()[0]=='ok'
  counts={};skipped=[]
  with db:
   db.execute('BEGIN IMMEDIATE')
   for change in plan['rows']:
    table=change['table'];assert table in ['solutions','detailed_solutions'];identity=change['id']
    row=db.execute('SELECT * FROM '+table+' WHERE problem_id=?',(identity,)).fetchone();assert row is not None,identity
    old=dict(row);images=json.loads(old['images'])
    if old['markdown']==change['markdown'] and images==change['images']:continue
    if old['markdown']!=change['oldMarkdown'] or images!=change['oldImages']:skipped.append({'table':table,'id':identity});continue
    assert programs(old['markdown'])==programs(change['markdown'])
    new={**old,'markdown':change['markdown'],'images':json.dumps(change['images'],ensure_ascii=False),'digest':digest(change['markdown'])}
    db.execute('UPDATE '+table+' SET markdown=?,images=?,digest=? WHERE problem_id=?',(new['markdown'],new['images'],new['digest'],identity))
    db.execute('UPDATE bundled_items SET digest=? WHERE table_name=? AND item_id=? AND digest=?',(checksum(new),table,identity,checksum(old)))
    counts[table]=counts.get(table,0)+1
   db.execute("UPDATE library_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
   assert not db.execute('PRAGMA foreign_key_check').fetchall()
  assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
 return {'path':str(path),'changed':counts,'customRowsPreserved':skipped,'integrity':True,'backup':str(backup)}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','apply']);parser.add_argument('--library',type=Path,default=ROOT/'data/library');parser.add_argument('--work',type=Path,required=True);parser.add_argument('--database',type=Path);parser.add_argument('--backup',type=Path);parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
 if args.action=='prepare':prepare(args)
 else:
  assert args.database and args.backup;print(json.dumps(apply_database(args.database,json.loads((args.work/'plan.json').read_text('utf8')),args.backup),ensure_ascii=False))
