"""Verify actual Store responses and seed upgrades in disposable databases."""
import hashlib
from contextlib import closing
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

from core7_authoring import ROOT,OUT,source_hash
os.environ['TB_OFFLINE']='1'
os.environ['TB_STATE_DIR']=str(OUT/'isolated-state')
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from library import LibraryDatabase
from store import Store


def main():
    authored=json.loads((OUT/'authored.json').read_text('utf-8'))
    grouped={}
    for entry in authored:grouped.setdefault(entry['problemId'],[]).append(entry)
    with tempfile.TemporaryDirectory(prefix='core7-library-') as temporary:
        temp=Path(temporary)
        public=LibraryDatabase(ROOT/'data/library.sqlite3',readonly=True)
        target=temp/'reader.sqlite3'
        with public.connection() as src,closing(sqlite3.connect(target)) as dest:src.backup(dest)
        store=Store(data_file=temp/'absent.md',library_file=target,history_file=temp/'history.jsonl')
        methods=0
        for identity,entries in grouped.items():
            value=store.solution(identity);found={m['id']:m for m in value['methods']}
            assert value['primaryMethod']==entries[0]['method'],identity
            for entry in entries:
                method=found[entry['method']]
                assert method['markdown']==entry['variants']['default']['markdown'],identity
                assert method['detailedSolution']==entry['variants']['detailed'],identity
                assert method['markdown']!=method['detailedSolution']['markdown'],identity
                assert set(method['lectureIds'])=={'lecture:foundation-'+x for x in entry['lessons']},identity
                for variant in [method,method['detailedSolution']]:
                    program=re.findall(r'^```cpp\s*\n(.*?)^```',variant['markdown'],re.S|re.M)
                    assert len(program)==1 and source_hash(program[0])==entry['programSha256'],identity
                methods+=1
        # The real merge path must retain a user's editorial amendment and imports.
        upgrade=LibraryDatabase(temp/'upgrade.sqlite3')
        upgrade.merge_seed(public.path)
        identity='luogu-training-P5707'
        note='Private annotation remains intact after a public editorial update.'
        with upgrade.connection() as db:
            db.execute('UPDATE solutions SET markdown=?,digest=? WHERE problem_id=?',(note,source_hash(note),identity))
            db.execute('CREATE TABLE private_fixture(key TEXT PRIMARY KEY,value TEXT)')
            db.execute('INSERT INTO private_fixture VALUES(?,?)',('draft-code','int main(){return 7;}'))
        upgrade.merge_seed(public.path)
        assert upgrade.solution(identity)['markdown']==note
        with upgrade.connection() as db:assert db.execute('SELECT value FROM private_fixture').fetchone()[0]=='int main(){return 7;}'
        assert upgrade.check()==public.check()
        fields=['id','url','title','difficulty','knowledge','tags','aliasIds']
        catalog=[{k:v for k,v in row.items() if k in fields} for row in store.data()['rows']]
        (OUT/'runtime-rows.json').write_text(json.dumps(catalog,ensure_ascii=False)+'\n',encoding='utf-8')
        report={'problems':len(grouped),'methods':methods,'variantResponses':methods*2,
                'referenceProgramsMatch':True,'preciseLessonAssociations':True,
                'privateEditorialAndFixturePreserved':True,'counts':public.check(),'liveDatabasesOpened':False}
        (OUT/'library-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
