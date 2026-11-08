"""Refresh only owned motion blocks, with reversible public-row migrations."""
import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from install_editorial_motion import ROOT, add, programs
from standardize_editorial_code import public_database, checksum, digest, dump


def prepare(work,refresh=False):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    plan_path=work/'plan.json'
    previous=json.loads(plan_path.read_text('utf8')) if refresh else None
    assert previous or not plan_path.exists()
    previous_rows={(r['table'],r['id']):r for r in previous['rows']} if previous else {}
    catalog=json.loads((ROOT/'data/editorial-motions.json').read_text('utf8'))['cases']
    cases={c['problemId']:c for c in catalog};changes=[];counts={};readers={}
    for table in ['solutions','detailed_solutions']:
        path=ROOT/'data/library'/(table+'.json');raw=path.read_bytes();rows=json.loads(raw);count=0
        for row in rows:
            case=cases.get(row['problem_id'])
            if not case:continue
            prior=previous_rows.get((table,row['problem_id']))
            if prior:
                assert (row['markdown'],row['images'])==(prior['markdown'],prior['images']),'Concurrent source edit'
                old=prior['oldMarkdown'];images=prior['oldImages']
            else:old=row['markdown'];images=row['images']
            start='<!-- tb-motion:'+case['id']+':start -->';end='<!-- tb-motion:'+case['id']+':end -->'
            block=re.search(re.escape(start)+r'.*?'+re.escape(end)+r'\n\n',old,re.S);assert block
            keys=re.findall(r'\]\((assets/editorial-motion/[^)]+)\)',block[0]);assert len(keys)==1
            old_key=keys[0];assert old.count(old_key)==1 and old_key in images
            old_payload=base64.b64decode(images[old_key].split(',',1)[1]);old_hash=hashlib.sha256(old_payload).hexdigest()
            assert old_key=='assets/editorial-motion/'+case['id']+'-'+old_hash[:10]+'.svg'
            payload=(ROOT/case['asset']).read_bytes();assert hashlib.sha256(payload).hexdigest()==case['sha256']
            key='assets/editorial-motion/'+case['id']+'-'+case['sha256'][:10]+'.svg'
            updated={k:v for k,v in images.items() if k!=old_key};updated[key]='data:image/svg+xml;base64,'+base64.b64encode(payload).decode()
            markdown=add(old,case,key)
            assert programs(markdown)==programs(old)
            assert re.sub(re.escape(start)+r'.*?'+re.escape(end)+r'\n\n','',markdown,flags=re.S)==re.sub(re.escape(start)+r'.*?'+re.escape(end)+r'\n\n','',old,flags=re.S)
            assert all(updated[k]==v for k,v in images.items() if k!=old_key)
            if markdown!=old or updated!=images:
                changes.append({'table':table,'id':row['problem_id'],'motion':case['id'],'oldMarkdown':old,'oldImages':images,'markdown':markdown,'images':updated});count+=1
            row['markdown']=markdown;row['images']=updated
            readers.setdefault(row['problem_id'],{})[table]=row
        if count:
            backup=work/'source-before'/(path.name+'.gz');backup.parent.mkdir(exist_ok=True)
            if not backup.exists():
                with gzip.open(backup,'wb',compresslevel=6) as stream:stream.write(raw)
                with gzip.open(backup,'rb') as stream:assert stream.read()==raw
            assert path.read_bytes()==raw,'Concurrent library write';dump(path,rows)
        counts[table]=count
    fixtures=[]
    for case in catalog:
        pair=readers[case['problemId']];default=pair['solutions'];detail=pair['detailed_solutions']
        fixtures.append({**case,'reader':{'title':case['title'],'markdown':default['markdown'],'images':default['images'],'detailedSolution':{'markdown':detail['markdown'],'images':detail['images']}}})
    dump(plan_path,{'version':1,'rows':changes,'counts':counts});dump(work/'reader-cases.json',fixtures)
    print(json.dumps({'reviewedCases':len(catalog),'continuous':sum(c['mode']=='continuous' for c in catalog),'changed':counts,'codeAndNonMotionContentPreserved':True}))


def apply_database(path,plan,backup):
    """Back up changed public rows durably before an atomic transaction.

    No personal DB is opened here. The public migration changes no other rows
    or schema, so the row snapshot is sufficient to reverse this exact update.
    """
    path=Path(path).resolve();backup=Path(backup).resolve();changed={};skipped=[];snapshots=[]
    with closing(sqlite3.connect(path,timeout=30)) as db:
        db.row_factory=sqlite3.Row;public_database(db)
        with db:
            db.execute('BEGIN IMMEDIATE')
            for change in plan['rows']:
                table=change['table'];assert table in {'solutions','detailed_solutions'}
                row=db.execute('SELECT * FROM '+table+' WHERE problem_id=?',(change['id'],)).fetchone();assert row is not None
                old=dict(row);images=json.loads(old['images'])
                if (old['markdown'],images)==(change['markdown'],change['images']):continue
                if (old['markdown'],images)!=(change['oldMarkdown'],change['oldImages']):skipped.append({'table':table,'id':change['id']});continue
                bundled=db.execute('SELECT * FROM bundled_items WHERE table_name=? AND item_id=?',(table,change['id'])).fetchone()
                snapshots.append({'table':table,'row':old,'bundled':dict(bundled) if bundled else None})
            if snapshots:
                assert not backup.exists();backup.parent.mkdir(parents=True,exist_ok=True)
                before={'database':str(path),'rows':snapshots,'meta':[dict(r) for r in db.execute('SELECT * FROM library_meta')]}
                temporary=backup.with_suffix(backup.suffix+'.tmp');assert not temporary.exists()
                with temporary.open('xb') as raw:
                    with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=6) as stream:stream.write(json.dumps(before,ensure_ascii=False).encode())
                    raw.flush();os.fsync(raw.fileno())
                with gzip.open(temporary,'rt',encoding='utf8') as stream:assert json.load(stream)==before
                os.replace(temporary,backup)
                changes={(r['table'],r['id']):r for r in plan['rows']}
                for snapshot in snapshots:
                    table=snapshot['table'];old=snapshot['row'];identity=old['problem_id'];change=changes[(table,identity)]
                    new={**old,'markdown':change['markdown'],'images':json.dumps(change['images'],ensure_ascii=False),'digest':digest(change['markdown'])}
                    db.execute('UPDATE '+table+' SET markdown=?,images=?,digest=? WHERE problem_id=?',(new['markdown'],new['images'],new['digest'],identity))
                    db.execute('UPDATE bundled_items SET digest=? WHERE table_name=? AND item_id=? AND digest=?',(checksum(new),table,identity,checksum(old)))
                    changed[table]=changed.get(table,0)+1
                db.execute("UPDATE library_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
            assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    return {'path':str(path),'changed':changed,'customRowsPreserved':skipped,'integrity':True,'rowBackup':str(backup) if snapshots else None}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--refresh',action='store_true');args=parser.parse_args();prepare(args.work,args.refresh)
