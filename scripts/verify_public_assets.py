"""Verify each deployed immutable resource before allowing a slim installer."""
import argparse
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from contextlib import closing
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
from urllib.error import HTTPError,URLError
from urllib.request import Request
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'backend'))
from public_assets import validate_reference

def verify(library,output,workers=3,previous_library=None,previous_receipt=None):
    from leaderboard import service_opener
    library=Path(library).resolve();output=Path(output)
    if output.exists():raise ValueError('Choose a new verification receipt path')
    def descriptors(path):
        with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:return db.execute('SELECT sha256,mime,bytes,url FROM remote_statement_assets ORDER BY sha256').fetchall()
    rows=descriptors(library);expected={row[0]:row for row in rows};verified=set();reused=0
    for row in rows:validate_reference(*row)
    # Text-only seed changes retain byte-for-byte identical immutable resource
    # descriptors. Reuse only a complete receipt bound to its exact old seed.
    if bool(previous_library)!=bool(previous_receipt):raise ValueError('Provide both prior library and receipt')
    if previous_library:
        old=json.loads(Path(previous_receipt).read_text('utf8'))
        with Path(previous_library).open('rb') as stream:old_sha=hashlib.file_digest(stream,'sha256').hexdigest()
        prior=descriptors(previous_library)
        if old.get('schema')!=1 or old.get('librarySha256')!=old_sha or set(old.get('verifiedSha256',[]))!={row[0] for row in prior}:raise ValueError('Prior resource proof does not match its seed')
        verified={row[0] for row in prior if expected.get(row[0])==row};reused=len(verified)
    checkpoint=output.with_suffix('.progress.jsonl');output.parent.mkdir(parents=True,exist_ok=True)
    if checkpoint.exists():
        for line in checkpoint.read_text('utf8').splitlines():
            item=json.loads(line)
            if expected.get(item['sha256'])==tuple(item['descriptor']):verified.add(item['sha256'])
    def download(row):
        sha,mime,size,url=row
        for attempt in range(4):
            digest=hashlib.sha256();received=0
            try:
                with service_opener(url).open(Request(url,headers={'Accept-Encoding':'identity'}),timeout=30) as response:
                    if response.status!=200:raise ValueError('Resource download failed')
                    while chunk:=response.read(65536):
                        received+=len(chunk)
                        if received>size:raise ValueError('Resource exceeded its declared size')
                        digest.update(chunk)
                if received!=size or digest.hexdigest()!=sha:raise ValueError('Server resource checksum mismatch: '+sha)
                return row
            except (HTTPError,URLError,OSError) as error:
                if attempt==3 or isinstance(error,HTTPError) and error.code not in (429,502,503,504):raise
                time.sleep(1+attempt*2)
    with checkpoint.open('a',encoding='utf8') as progress,ThreadPoolExecutor(max_workers=workers) as pool:
        remaining=iter(row for row in rows if row[0] not in verified);pending={}
        def schedule():
            row=next(remaining,None)
            if row:pending[pool.submit(download,row)]=row
        for _ in range(workers):schedule()
        while pending:
            completed,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in completed:
                row=pending.pop(future)
                try:future.result()
                except Exception as error:
                    print(json.dumps({'failedResource':row[0],'error':type(error).__name__,'status':getattr(error,'code',None)}),flush=True)
                    for queued in pending:queued.cancel()
                    raise
                verified.add(row[0]);progress.write(json.dumps({'sha256':row[0],'descriptor':row})+'\n');progress.flush()
                if len(verified)%25==0:print(json.dumps({'verified':len(verified),'total':len(rows)}),flush=True)
                schedule()
    with library.open('rb') as stream:library_sha=hashlib.file_digest(stream,'sha256').hexdigest()
    receipt={'schema':1,'librarySha256':library_sha,'verifiedSha256':sorted(verified),'verifiedAt':datetime.now(timezone.utc).isoformat(),'reusedImmutableProofs':reused}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    return len(verified)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--workers',type=int,choices=range(1,9),default=3);p.add_argument('--previous-library',type=Path);p.add_argument('--previous-receipt',type=Path);a=p.parse_args();print('Verified resources:',verify(a.library,a.output,a.workers,a.previous_library,a.previous_receipt))
