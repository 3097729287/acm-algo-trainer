"""Verify each deployed immutable resource before allowing a slim installer."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from urllib.request import Request
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'backend'))
from public_assets import validate_reference

def verify(library,output):
    from leaderboard import service_opener
    library=Path(library).resolve();output=Path(output)
    if output.exists():raise ValueError('Choose a new verification receipt path')
    with sqlite3.connect(library.as_uri()+'?mode=ro',uri=True) as db:rows=db.execute('SELECT sha256,mime,bytes,url FROM remote_statement_assets ORDER BY sha256').fetchall()
    verified=[]
    for sha,mime,size,url in rows:
        validate_reference(sha,mime,size,url);digest=hashlib.sha256();received=0
        with service_opener(url).open(Request(url,headers={'Accept-Encoding':'identity'}),timeout=20) as response:
            if response.status!=200:raise ValueError('Resource download failed')
            while True:
                chunk=response.read(65536)
                if not chunk:break
                received+=len(chunk)
                if received>size:raise ValueError('Resource exceeded its declared size')
                digest.update(chunk)
        if received!=size or digest.hexdigest()!=sha:raise ValueError('Server resource checksum mismatch: '+sha)
        verified.append(sha)
    with library.open('rb') as stream:library_sha=hashlib.file_digest(stream,'sha256').hexdigest()
    receipt={'schema':1,'librarySha256':library_sha,'verifiedSha256':verified,'verifiedAt':datetime.now(timezone.utc).isoformat()}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    return len(verified)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print('Verified resources:',verify(a.library,a.output))
