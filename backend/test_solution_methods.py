"""Multiple editorial methods share identities without replacing legacy programs."""
import json,tempfile,unittest
from pathlib import Path
from library import LibraryDatabase
from store import Store
from test_library import record

class SolutionMethodTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.database=LibraryDatabase(self.root/'library.sqlite3');self.database.import_records([record()],{}, {})
        self.config={'primaryMethod':'regular','methods':[{'id':'regular','title':'常规解法','tags':['差分'],'markdown':'# Regular','detailedSolution':{'markdown':'# Regular detail'}},{'id':'alternative','title':'补充思路','tags':['二分查找'],'legacy':True}]}
        with self.database.connection() as db:db.execute('INSERT INTO solution_methods VALUES(?,?)',('fixture::A',json.dumps(self.config)))
    def tearDown(self):self.temp.cleanup()
    def store(self):return Store(data_file=self.root/'absent.md',library_file=self.database.path,history_file=self.root/'history.jsonl')
    def test_variants_and_old_reference_program_remain_independent(self):
        store=self.store();value=store.solution('fixture::A')
        self.assertEqual(value['primaryMethod'],'regular');self.assertEqual(len(value['methods']),2)
        self.assertEqual(value['methods'][0]['detailedSolution']['markdown'],'# Regular detail')
        self.assertEqual(value['methods'][1]['markdown'],self.database.solution('fixture::A')['markdown'])
        self.assertEqual(store.solution_summary('fixture::A'),[{'id':'regular','title':'常规解法'},{'id':'alternative','title':'补充思路'}])
        self.assertTrue({'差分','二分查找'}<=set(store.data()['rows'][0]['tags']))
    def test_export_roundtrip_and_older_text_seed(self):
        directory=self.database.export_source(self.root/'export')
        rebuilt=LibraryDatabase.from_source(directory,self.root/'rebuilt.sqlite3')
        self.assertEqual(rebuilt.solution_methods('fixture::A'),self.config)
        (directory/'solution_methods.json').unlink()
        old=LibraryDatabase.from_source(directory,self.root/'old.sqlite3')
        self.assertEqual(old.solution_methods(),{})
    def test_seed_upgrade_preserves_local_method_edits(self):
        live=LibraryDatabase(self.root/'live.sqlite3');live.merge_seed(self.database.path)
        local={**self.config,'primaryMethod':'alternative'}
        with live.connection() as db:db.execute('UPDATE solution_methods SET content=?',(json.dumps(local),))
        with self.database.connection() as db:db.execute('UPDATE solution_methods SET content=?',(json.dumps({**self.config,'extra':'new public metadata'}),))
        live.merge_seed(self.database.path)
        self.assertEqual(live.solution_methods('fixture::A'),local)

if __name__=='__main__':unittest.main()
