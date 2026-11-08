"""An edited local default survives while the independent detailed row upgrades."""
from contextlib import closing
import hashlib,json,sqlite3,tempfile
from pathlib import Path
from install_editorial_motion import ROOT,apply_database
from standardize_editorial_code import checksum

def main():
 plan=json.loads((ROOT/'.backups/editorial-motion-20261108/content/plan.json').read_text('utf8'));identity=plan['rows'][0]['id'];rows=[r for r in plan['rows'] if r['id']==identity]
 assert len(rows)==2
 with tempfile.TemporaryDirectory(prefix='tb-motion-storage-') as temporary:
  path=Path(temporary)/'library.sqlite3'
  with closing(sqlite3.connect(path)) as c:
   c.executescript('CREATE TABLE library_meta(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE bundled_items(table_name TEXT,item_id TEXT,digest TEXT,PRIMARY KEY(table_name,item_id)); CREATE TABLE solution_methods(problem_id TEXT PRIMARY KEY,content TEXT); CREATE TABLE lectures(id TEXT PRIMARY KEY,content TEXT,digest TEXT);')
   for change in rows:
    table=change['table'];c.execute('CREATE TABLE '+table+'(problem_id TEXT PRIMARY KEY,markdown TEXT,source_path TEXT,images TEXT,digest TEXT)')
    old={'problem_id':identity,'markdown':change['oldMarkdown'],'source_path':'original.md','images':json.dumps(change['oldImages'],ensure_ascii=False),'digest':hashlib.sha256(change['oldMarkdown'].encode()).hexdigest()}
    c.execute('INSERT INTO '+table+' VALUES(?,?,?,?,?)',tuple(old.values()));c.execute('INSERT INTO bundled_items VALUES(?,?,?)',(table,identity,checksum(old)))
   c.execute("UPDATE solutions SET markdown=markdown||'\nLocal addition' WHERE problem_id=?",(identity,));c.commit()
  result=apply_database(path,{'rows':rows},Path(temporary)/'before.sqlite3');assert result['customRowsPreserved']==[{'table':'solutions','id':identity}]
  with closing(sqlite3.connect(path)) as c:
   assert c.execute('SELECT markdown FROM solutions').fetchone()[0].endswith('Local addition')
   detail=next(r for r in rows if r['table']=='detailed_solutions');assert c.execute('SELECT markdown,source_path FROM detailed_solutions').fetchone()==(detail['markdown'],'original.md')
   assert json.loads(c.execute('SELECT images FROM detailed_solutions').fetchone()[0])==detail['images']
   c.execute('CREATE TABLE drafts(id TEXT PRIMARY KEY)');c.commit()
  try:apply_database(path,{'rows':rows},Path(temporary)/'must-not-exist.sqlite3')
  except ValueError:pass
  else:raise AssertionError('Personal database was accepted')
  assert not (Path(temporary)/'must-not-exist.sqlite3').exists()
 print(json.dumps({'ok':True,'editedDefaultPreserved':True,'independentDetailUpgraded':True,'personalDatabaseRejected':True}))

if __name__=='__main__':main()
