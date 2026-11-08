"""Build a small public SQLite delta; installed base libraries remain unchanged."""
from contextlib import closing
import argparse,gzip,hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from library import LibraryDatabase
from public_library_update import TABLES,MAX_DATABASE,MAX_WIRE,validate_database

CONTENT={
 'problems':('id',('id','url','raw','encoded')),
 'lectures':('id',('id','content','digest')),
 'solutions':('problem_id',('problem_id','markdown','source_path','images','digest')),
 'statements':('problem_id',('problem_id','content')),
 'detailed_solutions':('problem_id',('problem_id','markdown','source_path','images','digest')),
 'solution_methods':('problem_id',('problem_id','content')),
 'training_lists':('id',('id','content')),
}
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def public(db):
 tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
 if tables!=TABLES:raise ValueError('A content update needs a public-only library')
 if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Public library integrity failure')
 for raw, in db.execute('SELECT raw FROM problems'):
  row=json.loads(raw)
  if row.get('状态')!='未做' or row.get('日期'):raise ValueError('Public library contains personal progress')
def asset_map(db):
 values={r[0]:(r[1],r[2]) for r in db.execute('SELECT sha256,mime,length(data) FROM statement_assets')}
 for digest,mime,size in db.execute('SELECT sha256,mime,bytes FROM remote_statement_assets'):
  if digest in values and values[digest]!=(mime,size):raise ValueError('Conflicting public asset descriptors')
  values[digest]=(mime,size)
 return values
def inline_map(db):
 from statement_asset_store import dehydrate
 values={}
 def save(digest,mime,data):
  item=(mime,len(data))
  if digest in values and values[digest]!=item:raise ValueError('Conflicting embedded public resources')
  values[digest]=item
 for content, in db.execute("SELECT content FROM statements WHERE instr(content,';base64,')>0"):
  dehydrate(json.loads(content),save)
 return values

def links(connection):
 result={}
 for row in connection.execute('SELECT * FROM problem_lectures ORDER BY problem_id,position'):result.setdefault(row[0],[]).append(row)
 return result
def build(bases,target,output):
 bases=[Path(path).resolve(strict=True) for path in bases];target=Path(target).resolve(strict=True);output=Path(output)
 if not 1<=len(bases)<=8 or len(set(bases))!=len(bases) or output.exists():raise ValueError('Use 1 to 8 distinct approved public bases and a new output directory')
 output.mkdir(parents=True);thin=output/'public-library-update.sqlite3';LibraryDatabase(thin)
 fingerprints=[sha(path) for path in bases];target_sha=sha(target)
 with closing(sqlite3.connect(bases[0].as_uri()+'?mode=ro',uri=True)) as baseline,closing(sqlite3.connect(target.as_uri()+'?mode=ro',uri=True)) as current:
  public(baseline);public(current)
  baseline_assets=[];embedded=[];old_links=[]
  for index,path in enumerate(bases):
   with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as other:
    public(other);known=asset_map(other);inline=inline_map(other)
    for digest,item in inline.items():
     if digest in known and known[digest]!=item:raise ValueError('Embedded public resource identity changed')
    baseline_assets.append(known|inline);embedded.append({digest:item for digest,item in inline.items() if digest not in known});old_links.append(links(other))
   current.execute('ATTACH DATABASE ? AS previous'+str(index),(path.as_uri()+'?mode=ro',))
  with closing(sqlite3.connect(thin)) as db,db:
   db.execute('PRAGMA foreign_keys=OFF')
   for table,(key,columns) in CONTENT.items():
    # A single superset is safe for every approved release, including bases
    # with different content. Literal public rows have no binary dependency.
    joins=[];changed=[]
    for index in range(len(bases)):
     alias='p'+str(index);joins.append(' LEFT JOIN previous'+str(index)+'.'+table+' '+alias+' ON '+alias+'.'+key+'=n.'+key)
     changed.extend([alias+'.'+key+' IS NULL',*(alias+'.'+column+' IS NOT n.'+column for column in columns)])
    query='SELECT n.* FROM main.'+table+' n'+''.join(joins)+' WHERE '+' OR '.join(changed)+' ORDER BY n.rowid'
    db.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for _ in columns)+')',current.execute(query))
   new_links=links(current);subjects=set()
   for previous in old_links:
    subjects.update(pid for pid in previous.keys()|new_links.keys() if previous.get(pid,[])!=new_links.get(pid,[]))
   subjects.update(row[0] for row in db.execute('SELECT id FROM problems'))
   subjects=sorted(subjects)
   for pid in subjects:db.executemany('INSERT INTO problem_lectures VALUES(?,?,?,?)',new_links.get(pid,[]))
   reused=[{} for _ in bases]
   def available(digest,mime,size):
    item=(mime,size)
    for known in baseline_assets:
     if digest in known and known[digest]!=item:raise ValueError('Existing public resource identity changed')
    if not all(digest in known for known in baseline_assets):return False
    for index,inline in enumerate(embedded):
     if digest in inline:reused[index][digest]={'sha256':digest,'mime':mime,'bytes':size}
    return True
   for digest,mime,data in current.execute('SELECT sha256,mime,data FROM statement_assets ORDER BY sha256'):
    if available(digest,mime,len(data)):continue
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('New public resource is corrupt')
    db.execute('INSERT INTO statement_assets VALUES(?,?,?)',(digest,mime,data))
   for row in current.execute('SELECT sha256,mime,bytes,url FROM remote_statement_assets ORDER BY sha256'):
    if available(row[0],row[1],row[2]):continue
    db.execute('INSERT INTO remote_statement_assets VALUES(?,?,?,?)',row)
   db.execute('UPDATE catalog_generation SET identity=?,generation=0 WHERE id=1',(hashlib.sha256((target_sha+''.join(sorted(fingerprints))).encode()).hexdigest()[:32],))
   counts={table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in sorted(TABLES)}
  membership={'lectureIds':[r[0] for r in current.execute('SELECT id FROM lectures ORDER BY id')],'problemLectureSubjects':subjects}
 if thin.stat().st_size>MAX_DATABASE:raise ValueError('Public delta needs a new full base; partial source exceeds its bound')
 raw=output/'payload.gz'
 with thin.open('rb') as source,raw.open('xb') as destination:
  with gzip.GzipFile(filename='',mode='wb',fileobj=destination,compresslevel=9,mtime=0) as stream:
   while block:=source.read(65536):stream.write(block)
 if raw.stat().st_size>MAX_WIRE:raise ValueError('Public delta transport exceeds its bound')
 payload_sha=sha(raw);name='public-library-update-'+payload_sha+'.sqlite3.gz';raw.rename(output/name)
 descriptor={'schema':1,'baseSeeds':fingerprints,'targetSeedSha256':target_sha,'payload':name,'payloadSha256':payload_sha,'payloadBytes':(output/name).stat().st_size,
             'databaseSha256':sha(thin),'databaseBytes':thin.stat().st_size,'membership':membership,'rowCounts':counts,
             'baseInlineAssets':{fingerprint:sorted(items.values(),key=lambda item:item['sha256']) for fingerprint,items in zip(fingerprints,reused)}}
 validate_database(thin,descriptor)
 (output/'public-library-update.json').write_text(json.dumps(descriptor,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 result={'ok':True,'bases':list(map(str,bases)),'target':str(target),'targetSeedSha256':target_sha,'output':str(output.resolve()),'descriptor':descriptor,'privateStateReadOrWritten':False}
 (output/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,action='append',required=True);p.add_argument('--target',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=build(a.base,a.target,a.output);print(json.dumps({k:v for k,v in result.items() if k!='descriptor'},ensure_ascii=False),flush=True);print(json.dumps({'payloadBytes':result['descriptor']['payloadBytes'],'databaseBytes':result['descriptor']['databaseBytes'],'changedRows':result['descriptor']['rowCounts']},ensure_ascii=False),flush=True)
