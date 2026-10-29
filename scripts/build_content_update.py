"""Build a cumulative public-only patch against the shipped client baseline.

Publishing is separate. A later revision must still compare to the same
baseline so clients which missed intermediate revisions receive all changes.
"""
import argparse
from contextlib import closing
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from content_updates import TABLES,MAX_PACKED,MAX_UNPACKED,validate

def require_unchanged_lessons(before,after):
    # Schema 1 cannot transport lesson bodies or their relational links. Never
    # acknowledge a successful cumulative patch which silently drops either.
    dependencies={'lectures':('id','content','digest'),
                  'problem_lectures':('problem_id','lecture_id','kind','position')}
    for table,columns in dependencies.items():
        query='SELECT '+','.join(columns)+' FROM '+table+' ORDER BY 1,2'
        if [tuple(row) for row in before.execute(query)] != [tuple(row) for row in after.execute(query)]:
            raise ValueError('Schema-1 content patch cannot deliver changed '+table+
                             '; publish a program update or extend the content protocol first')

def build(baseline,source,revision,minimum,output):
    tables={}
    with closing(sqlite3.connect(Path(baseline).resolve().as_uri()+'?mode=ro',uri=True)) as before,closing(sqlite3.connect(Path(source).resolve().as_uri()+'?mode=ro',uri=True)) as after:
        before.row_factory=after.row_factory=sqlite3.Row
        for database in (before,after):
            if database.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Invalid SQLite source')
        require_unchanged_lessons(before,after)
        for table,(key,columns) in TABLES.items():
            old={row[key]:dict(row) for row in before.execute('SELECT '+','.join(columns)+' FROM '+table)}
            changed=[dict(row) for row in after.execute('SELECT '+','.join(columns)+' FROM '+table+' ORDER BY '+key) if dict(row)!=old.get(row[key])]
            if changed:tables[table]=changed
    payload={'schema':1,'revision':revision,'minClientVersion':minimum,'tables':tables}
    validate(payload,minimum)
    raw=json.dumps(payload,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode('utf8')
    if len(raw)>MAX_UNPACKED:raise ValueError('Public patch exceeds expanded limit')
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    if len(packed)>MAX_PACKED:raise ValueError('Public patch exceeds packed limit')
    checksum=hashlib.sha256(packed).hexdigest();folder=Path(output).resolve();folder.mkdir(parents=True,exist_ok=True)
    path=folder/(checksum+'.json.gz')
    if path.exists() and path.read_bytes()!=packed:raise ValueError('Immutable patch collision')
    path.write_bytes(packed)
    manifest={'schema':1,'revision':revision,'minClientVersion':minimum,'sha256':checksum,'size':len(packed)}
    (folder/'manifest-v1.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return {**manifest,'counts':{table:len(rows) for table,rows in tables.items()},'uncompressedBytes':len(raw)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',required=True,type=Path);parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--revision',required=True,type=int);parser.add_argument('--minimum-client-version',default='1.4.29')
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.baseline,args.source,args.revision,args.minimum_client_version,args.output),ensure_ascii=False))

if __name__=='__main__':main()
