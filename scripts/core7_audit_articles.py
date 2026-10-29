"""Recheck the final prose against programs already validated by the DSH runner."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
from core7_authoring import OUT,CONTENT,load_all,source_hash

proof={(r['pid'],r['method']):r for r in json.loads((OUT/'verification.json').read_text('utf-8'))}
env={**os.environ,'PYTHONIOENCODING':'utf-8','TB_OFFLINE':'1'}
def audit(spec):
    record=proof[spec.pid,spec.key]
    assert record['passed'] and source_hash(spec.code)==record['programSha256']
    hashes=[]
    for name in ['default','detailed']:
        article=CONTENT/spec.pid/spec.key/(name+'.md')
        result=subprocess.run([sys.executable,str(Path.home()/'.dsh/tools/md_full.py'),str(article),'A'],capture_output=True,text=True,encoding='utf-8',env=env,timeout=90)
        (OUT/'verification'/spec.pid/spec.key/(name+'-md-full.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        assert result.returncode==0,(spec.pid,spec.key,name,result.stdout[-800:],result.stderr[-800:])
        hashes.append(source_hash(article.read_text('utf-8')))
    record['articleFileSha256']=hashes
    return record

with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(audit,load_all()))
records.sort(key=lambda r:(r['pid'],r['method']))
(OUT/'verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verifiedPrograms':len(records),'finalArticlesMatchProgram':len(records)*2,'allPassed':True}))
