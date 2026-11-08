"""Prepare/apply a reviewed offline Markdown code-format migration.

Only educational Markdown fields change. Database backups include committed WAL;
personal databases are rejected. Unrelated rows, images and method metadata stay.
Run prepare, the frontend formatter, then apply using the same work directory.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

FILES=('solutions.json','detailed_solutions.json','solution_methods.json','lectures.json')
TABLES={'solutions':'problem_id','detailed_solutions':'problem_id','solution_methods':'problem_id','lectures':'id'}


def digest(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')


def markdowns(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='markdown' and isinstance(item,str):yield item
            else:yield from markdowns(item)
    elif isinstance(value,list):
        for item in value:yield from markdowns(item)


def transform(value,changes):
    if isinstance(value,dict):
        return {key:changes.get(digest(item),item) if key=='markdown' and isinstance(item,str) else transform(item,changes) for key,item in value.items()}
    if isinstance(value,list):return [transform(item,changes) for item in value]
    return value


def metadata(value):
    if isinstance(value,dict):return {key:'<markdown>' if key=='markdown' else metadata(item) for key,item in value.items()}
    if isinstance(value,list):return [metadata(item) for item in value]
    return value


def public_database(connection):
    names={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if names.intersection({'drafts','submissions','training','accounts','documents','account_preferences'}):
        raise ValueError('Refusing to change a personal database')
    assert set(TABLES).issubset(names)


def checksum(row):
    return digest(json.dumps(dict(row),ensure_ascii=False,sort_keys=True))


def prepare(args):
    assert not (args.work/'plan.json').exists(),'Use a new work directory'
    docs={};plan={'libraries':[],'databases':[]}
    def collect(value):
        for markdown in markdowns(value):docs[digest(markdown)]=markdown
    for directory in args.library:
        for name in FILES:
            path=(directory/name).resolve()
            if not path.exists():continue
            collect(json.loads(path.read_text('utf-8-sig')))
            plan['libraries'].append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for database in args.database:
        path=database.resolve()
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as connection:
            public_database(connection)
            for table in TABLES:
                for row in connection.execute('SELECT '+('markdown' if table in {'solutions','detailed_solutions'} else 'content')+' FROM '+table):
                    collect({'markdown':row[0]} if table in {'solutions','detailed_solutions'} else json.loads(row[0]))
        plan['databases'].append(str(path))
    dump(args.work/'input.json',[{'id':identity,'markdown':body} for identity,body in docs.items()])
    dump(args.work/'plan.json',plan)
    print(json.dumps({'documents':len(docs),'sources':len(plan['libraries']),'databases':len(plan['databases'])}))


def update_database(path,changes,backup):
    assert not backup.exists(),'Recovery file already exists'
    backup.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(path,timeout=30)) as connection:
        connection.row_factory=sqlite3.Row
        public_database(connection)
        with closing(sqlite3.connect(backup)) as saved:
            connection.backup(saved)
            assert saved.execute('PRAGMA quick_check').fetchone()[0]=='ok'
        counts={};preserved=0
        with connection:
            connection.execute('BEGIN IMMEDIATE')
            for table,key in TABLES.items():
                count=0
                for row in connection.execute('SELECT * FROM '+table).fetchall():
                    old=dict(row);new=dict(row)
                    if 'markdown' in new:
                        new['markdown']=changes.get(digest(old['markdown']),old['markdown'])
                        new['digest']=digest(new['markdown'])
                    else:
                        before=json.loads(old['content']);after=transform(before,changes)
                        assert metadata(before)==metadata(after)
                        if before!=after:
                            new['content']=json.dumps(after,ensure_ascii=False)
                            if table=='lectures':new['digest']=digest(after['markdown'])
                    if new==old:preserved+=1;continue
                    columns=[column for column in new if new[column]!=old[column]]
                    connection.execute('UPDATE '+table+' SET '+','.join(column+'=?' for column in columns)+' WHERE '+key+'=?',tuple(new[column] for column in columns)+(old[key],))
                    # Keep seed upgrade ownership for rows that were bundled.
                    connection.execute('UPDATE bundled_items SET digest=? WHERE table_name=? AND item_id=? AND digest=?',(checksum(new),table,old[key],checksum(old)))
                    count+=1
                counts[table]=count
            connection.execute("UPDATE library_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
            assert not connection.execute('PRAGMA foreign_key_check').fetchall()
        assert connection.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    return {'path':str(path),'changed':counts,'unchangedRows':preserved,'backup':str(backup),'integrity':True}


def apply(args):
    plan=json.loads((args.work/'plan.json').read_text('utf8'))
    output=json.loads((args.work/'formatted.json').read_text('utf8'))
    original={row['id']:row['markdown'] for row in json.loads((args.work/'input.json').read_text('utf8'))}
    changes={row['id']:row['markdown'] for row in output['documents'] if row['markdown']!=original[row['id']]}
    assert set(original)=={row['id'] for row in output['documents']}
    assert not output['report']['issues'],output['report']['issues']
    assert not output['report']['failures'],'Review formatter failures before applying'
    report={'sources':[],'databases':[],'format':output['report']}
    for index,item in enumerate(plan['libraries'] if args.scope in {'source','all'} else []):
        path=Path(item['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],'Source changed since inventory: '+str(path)
        old=json.loads(path.read_text('utf-8-sig'));new=transform(old,changes)
        assert metadata(old)==metadata(new)
        if old==new:continue
        backup=args.work/'before'/f'source-{index}'/path.name
        assert not backup.exists()
        backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
        dump(path,new)
        report['sources'].append({'path':str(path),'changedRows':sum(a!=b for a,b in zip(old,new)),'rows':len(new)})
    for index,name in enumerate(plan['databases'] if args.scope in {'database','all'} else []):
        report['databases'].append(update_database(Path(name),changes,args.work/'before'/f'database-{index}.sqlite3'))
    dump(args.work/('applied-'+args.scope+'.json'),report)
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','apply'])
    parser.add_argument('--library',type=Path,action='append',default=[])
    parser.add_argument('--database',type=Path,action='append',default=[])
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--scope',choices=['source','database','all'],default='source')
    arguments=parser.parse_args()
    (prepare if arguments.action=='prepare' else apply)(arguments)
