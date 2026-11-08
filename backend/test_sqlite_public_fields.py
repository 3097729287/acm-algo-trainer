from contextlib import closing
import json,sqlite3,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sqlite_public_fields import image_spans

class SQLiteFieldSpanTests(unittest.TestCase):
    def test_sql_decoded_fields_match_physical_spans_across_btrees_and_overflow_pages(self):
        for size in (512,4096,65536):
            with self.subTest(page_size=size),tempfile.TemporaryDirectory() as temporary:
                path=Path(temporary)/'public.sqlite3';images=json.dumps({'图':'abcde'+('0123456789'*1700)},ensure_ascii=False);expected=images.encode()
                with closing(sqlite3.connect(path)) as db,db:
                    db.execute('PRAGMA page_size='+str(size));db.execute('CREATE TABLE solutions(problem_id TEXT PRIMARY KEY,markdown TEXT,source_path TEXT,images TEXT,digest TEXT)')
                    db.executemany('INSERT INTO solutions VALUES(?,?,?,?,?)',[(str(i),'中文'*45,'relative/path',images if i in (1,83,150) else '{}','public hash') for i in range(200)])
                before=path.read_bytes();located=image_spans(path,{'solutions':{'1','83','150'}})
                self.assertEqual(len(located),3)
                for item in located:self.assertEqual(b''.join(before[at:at+n] for at,offset,n in item['spans']),expected)
                self.assertEqual(path.read_bytes(),before)

if __name__=='__main__':unittest.main()
