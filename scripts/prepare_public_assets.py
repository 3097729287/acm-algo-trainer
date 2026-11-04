"""Create a slim PUBLIC seed and immutable server assets without changing the input.

No upload is performed. Deploy and verify the generated manifest before using
the slim database in an installer. Personal databases are rejected.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'backend'))
from public_assets import validate_reference,PUBLIC_COMMIT,PUBLIC_ROOT

def prepare(source,destination,assets,origin,*,pdf_only=False,minimum=65536,direct=False):
    source,destination,assets=Path(source).resolve(),Path(destination).resolve(),Path(assets).resolve()
    if source==destination or destination.exists():raise ValueError('Choose a new slim seed path')
    destination.parent.mkdir(parents=True,exist_ok=True);assets.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original:
        tables={name:sql for name,sql in original.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if set(tables)&{'accounts','drafts','submissions','training','account_preferences','documents'}:raise ValueError('Refusing to publish private state')
        if original.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Invalid source library')
        manifest=[]
        with closing(sqlite3.connect(destination)) as slim, slim:
            for sql in tables.values():slim.execute(sql)
            slim.execute('CREATE TABLE IF NOT EXISTS remote_statement_assets(sha256 TEXT PRIMARY KEY,mime TEXT NOT NULL,bytes INTEGER NOT NULL,url TEXT NOT NULL)')
            for table in tables:
                if table=='statement_assets':continue
                placeholders=','.join('?' for _ in original.execute('PRAGMA table_info('+table+')'))
                slim.executemany('INSERT INTO '+table+' VALUES('+placeholders+')',original.execute('SELECT * FROM '+table))
            for sha,mime,data in original.execute('SELECT sha256,mime,data FROM statement_assets'):
                if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('Source asset checksum mismatch')
                external=mime=='application/pdf' or not pdf_only and len(data)>=minimum and mime in {'image/png','image/jpeg','image/webp','image/gif','image/bmp','application/zip'}
                if not external:slim.execute('INSERT INTO statement_assets VALUES(?,?,?)',(sha,mime,data));continue
                url=PUBLIC_ROOT+sha+'.bin' if direct else origin.rstrip('/')+'/updates/library-assets/'+sha+'.bin';validate_reference(sha,mime,len(data),url)
                path=assets/(sha+'.bin')
                if path.exists():
                    with path.open('rb') as stream:
                        if hashlib.file_digest(stream,'sha256').hexdigest()!=sha:raise ValueError('Existing server asset conflicts')
                else:
                    with path.open('xb') as stream:stream.write(data)
                slim.execute('INSERT INTO remote_statement_assets VALUES(?,?,?,?)',(sha,mime,len(data),url))
                manifest.append({'sha256':sha,'mime':mime,'bytes':len(data),'url':url,'file':path.name})
            for (sql,) in original.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"):
                slim.execute(sql)
            if slim.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or slim.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Slim seed failed integrity validation')
    report={'schema':1,'sourceBytes':source.stat().st_size,'slimBytes':destination.stat().st_size,'externalBytes':sum(item['bytes'] for item in manifest),'assets':manifest,'deployed':False}
    (assets/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--origin',required=True);p.add_argument('--pdf-only',action='store_true');p.add_argument('--direct',action='store_true',help='Use the pinned public original source, with the account server as a verified fallback');a=p.parse_args()
    r=prepare(a.source,a.output,a.assets,a.origin,pdf_only=a.pdf_only,direct=a.direct)
    print(json.dumps({key:value for key,value in r.items() if key!='assets'}))
