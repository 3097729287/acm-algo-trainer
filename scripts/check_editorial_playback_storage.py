"""Exercise lossless public-row rollback, edited rows, idempotence and isolation."""
import gzip
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from refresh_editorial_motion import ROOT, apply_database
from standardize_editorial_code import checksum, digest


def main():
    work=ROOT/'.backups/editorial-playback-20261108'
    plan=json.loads((work/'content/plan.json').read_text('utf8'))
    identity=plan['rows'][0]['id'];rows=[r for r in plan['rows'] if r['id']==identity];assert len(rows)==2
    with tempfile.TemporaryDirectory(prefix='row-migration-',dir=work) as directory:
        path=Path(directory)/'library.sqlite3'
        with closing(sqlite3.connect(path)) as db:
            db.executescript('CREATE TABLE library_meta(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE bundled_items(table_name TEXT,item_id TEXT,digest TEXT,PRIMARY KEY(table_name,item_id)); CREATE TABLE solution_methods(problem_id TEXT PRIMARY KEY,content TEXT); CREATE TABLE lectures(id TEXT PRIMARY KEY,content TEXT,digest TEXT);')
            db.execute("INSERT INTO library_meta VALUES('revision','42')")
            for change in rows:
                table=change['table'];db.execute('CREATE TABLE '+table+'(problem_id TEXT PRIMARY KEY,markdown TEXT,source_path TEXT,images TEXT,digest TEXT)')
                old={'problem_id':identity,'markdown':change['oldMarkdown'],'source_path':'original.md','images':json.dumps(change['oldImages'],ensure_ascii=False),'digest':digest(change['oldMarkdown'])}
                db.execute('INSERT INTO '+table+' VALUES(?,?,?,?,?)',tuple(old.values()));db.execute('INSERT INTO bundled_items VALUES(?,?,?)',(table,identity,checksum(old)))
            db.execute("INSERT INTO lectures VALUES('unrelated','preserve','abc')")
            db.execute("CREATE TRIGGER reject_update BEFORE UPDATE ON detailed_solutions BEGIN SELECT RAISE(ABORT,'fixture failure'); END");db.commit()
        try:apply_database(path,{'rows':rows},Path(directory)/'rollback.json.gz')
        except sqlite3.IntegrityError:pass
        else:raise AssertionError('Expected transaction failure')
        with closing(sqlite3.connect(path)) as db:
            for change in rows:assert db.execute('SELECT markdown FROM '+change['table']).fetchone()[0]==change['oldMarkdown']
            assert db.execute("SELECT value FROM library_meta WHERE key='revision'").fetchone()[0]=='42'
            db.execute('DROP TRIGGER reject_update');db.execute("UPDATE solutions SET markdown=markdown||'\nLocal addition'");db.commit()
        backup=Path(directory)/'public-rows.json.gz'
        result=apply_database(path,{'rows':rows},backup)
        assert result['customRowsPreserved']==[{'table':'solutions','id':identity}] and result['changed']=={'detailed_solutions':1}
        with gzip.open(backup,'rt',encoding='utf8') as stream:snapshot=json.load(stream)
        repeated=apply_database(path,{'rows':rows},backup);assert not repeated['changed'] and repeated['rowBackup'] is None
        with closing(sqlite3.connect(path)) as db:
            assert db.execute('SELECT markdown FROM solutions').fetchone()[0].endswith('Local addition')
            assert db.execute('SELECT * FROM lectures').fetchone()==('unrelated','preserve','abc')
            for saved in snapshot['rows']:
                row=saved['row'];db.execute('UPDATE '+saved['table']+' SET markdown=?,images=?,digest=? WHERE problem_id=?',(row['markdown'],row['images'],row['digest'],row['problem_id']))
            detail=next(r for r in rows if r['table']=='detailed_solutions')
            assert db.execute('SELECT markdown FROM detailed_solutions').fetchone()[0]==detail['oldMarkdown']
            db.execute('CREATE TABLE drafts(id TEXT PRIMARY KEY)');db.commit()
        try:apply_database(path,{'rows':rows},Path(directory)/'private-must-not-exist.json.gz')
        except ValueError:pass
        else:raise AssertionError('Personal database was accepted')
        assert not (Path(directory)/'private-must-not-exist.json.gz').exists()
    report={'ok':True,'atomicRollback':True,'editedDefaultPreserved':True,'independentDetailUpdated':True,'rowBackupRoundTrip':True,'unrelatedRowsPreserved':True,'idempotent':True,'personalDatabaseRejected':True}
    (work/'storage.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__=='__main__':main()
