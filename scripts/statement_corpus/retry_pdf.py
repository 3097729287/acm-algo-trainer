import os
import json,sys,concurrent.futures,time
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_all import collect,PARSED,LOG
import hashlib
rows=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'))
rows=[r for r in rows if '/gym/' in (r['url'] or '') and 'missing' in r['issues']]
for i,result in enumerate(concurrent.futures.ThreadPoolExecutor(4).map(collect,rows),1):
    if i%10==0:print({'done':i,'total':len(rows),'last':result},flush=True)
