"""Preserve immutable old resource pages while updating the exact public corpus.

New resource bytes are emitted by SHA-256 for verified immutable publication.
The public seed is rebuilt from current source rows, never from personal state.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

TABLES={'library_meta','bundled_items','problems','problem_urls','solutions','detailed_solutions','solution_methods','statements','statement_assets','remote_statement_assets','lectures','training_lists','problem_lectures','catalog_generation'}


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def build(source,baseline,output,assets):
    source,baseline,output,assets=map(Path,(source,baseline,output,assets))
    source=source.resolve(strict=True);baseline=baseline.resolve(strict=True)
    if output.exists() or assets.exists():raise ValueError('Choose new public seed and resource destinations')
    assets.mkdir(parents=True)
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as current,closing(sqlite3.connect(baseline.as_uri()+'?mode=ro',uri=True)) as old,closing(sqlite3.connect(output)) as target:
        for db in [current,old]:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            if tables!=TABLES:raise ValueError('Not the known public-only library schema')
            for (raw,) in db.execute('SELECT raw FROM problems'):
                row=json.loads(raw)
                if row.get('状态')!='未做' or row.get('日期'):raise ValueError('Public source contains progress')
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Public library is corrupt')
        for table in ['solutions','detailed_solutions']:
            ids={r[0] for r in current.execute('SELECT problem_id FROM '+table)}
            if not {r[0] for r in old.execute('SELECT problem_id FROM '+table)}<=ids:raise ValueError('Public editorials would be removed')
        # Online backup includes any committed WAL content and leaves the source alone.
        old.backup(target);target.execute('PRAGMA foreign_keys=OFF');target.execute('PRAGMA journal_mode=DELETE')
        local={r[0] for r in old.execute('SELECT sha256 FROM statement_assets')}
        remote={r[0]:r for r in old.execute('SELECT sha256,mime,bytes,url FROM remote_statement_assets')}
        original_assets={r[0] for r in current.execute('SELECT sha256 FROM statement_assets')}
        if not (local|set(remote))<=original_assets:raise ValueError('A retained resource is absent from current source')
        fresh=[]
        for digest,mime,data in current.execute('SELECT sha256,mime,data FROM statement_assets'):
            if digest in local or digest in remote:continue
            if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('New resource digest mismatch')
            (assets/(digest+'.bin')).write_bytes(data)
            remote[digest]=(digest,mime,len(data),'https://47.82.84.74/updates/library-assets/'+digest+'.bin')
            fresh.append({'sha256':digest,'mime':mime,'bytes':len(data)})
        changes={}
        with target:
            for table in sorted(TABLES-{'statement_assets','remote_statement_assets','catalog_generation'}):
                columns=list(current.execute('PRAGMA table_info('+table+')'));keys=[i for i,c in enumerate(columns) if c[5]]
                before={tuple(r[i] for i in keys):r for r in target.execute('SELECT * FROM '+table)}
                after={tuple(r[i] for i in keys):r for r in current.execute('SELECT * FROM '+table)}
                deleted=sorted(set(before)-set(after));changed=[after[k] for k in sorted(after) if before.get(k)!=after[k]]
                key_names=[columns[i][1] for i in keys]
                for key in deleted:target.execute('DELETE FROM '+table+' WHERE '+' AND '.join(k+'=?' for k in key_names),key)
                if changed:
                    names=[c[1] for c in columns];assignments=','.join(n+'=excluded.'+n for n in names if n not in key_names)
                    sql='INSERT INTO '+table+' VALUES('+','.join('?' for _ in names)+') ON CONFLICT('+','.join(key_names)+') DO '+('UPDATE SET '+assignments if assignments else 'NOTHING')
                    target.executemany(sql,changed)
                changes[table]={'upsert':len(changed),'removed':len(deleted)}
            target.executemany('INSERT OR REPLACE INTO remote_statement_assets VALUES(?,?,?,?)',remote.values())
            target.execute('DELETE FROM catalog_generation')
            target.executemany('INSERT INTO catalog_generation VALUES(?,?,?)',current.execute('SELECT * FROM catalog_generation'))
        for table in TABLES-{'statement_assets','remote_statement_assets'}:
            columns=list(current.execute('PRAGMA table_info('+table+')'));order=','.join(str(i+1) for i,c in enumerate(columns) if c[5])
            if list(current.execute('SELECT * FROM '+table+' ORDER BY '+order))!=list(target.execute('SELECT * FROM '+table+' ORDER BY '+order)):raise ValueError('Public table differs from current source: '+table)
        if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or target.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Updated public library failed validation')
        if local|set(remote)!=original_assets:raise ValueError('Public resource union changed')
        counts={table:target.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ['problems','statements','solutions','detailed_solutions']}
    return {'publicOnly':True,'source':str(source),'sourceSha256':sha(source),'baseline':str(baseline),'baselineSha256':sha(baseline),'library':str(output.resolve()),'librarySha256':sha(output),'bytes':output.stat().st_size,'counts':counts,'localResources':len(local),'remoteResources':len(remote),'newResources':fresh,'changes':changes,'resourceOutput':str(assets.resolve()),'personalStateReadOrWritten':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    value=build(a.source,a.baseline,a.output,a.assets);a.receipt.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in value.items() if k not in {'newResources','changes'}},ensure_ascii=False),flush=True)
