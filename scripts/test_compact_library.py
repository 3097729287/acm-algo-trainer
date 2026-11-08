"""Compact resource placement and the private-data publication boundary."""
from contextlib import closing
import hashlib,json
from pathlib import Path
import shutil,sqlite3,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts')]
from library import LibraryDatabase
from build_compact_library import build
from public_assets import validate_reference

def digest(raw):return hashlib.sha256(raw).hexdigest()

class CompactLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.old=self.root/'baseline.sqlite3';self.source=self.root/'source.sqlite3'
        library=LibraryDatabase(self.old);self.original=b'original immutable local asset'
        with library.connection() as db:
            db.execute('INSERT INTO problems VALUES(?,?,?,?)',('fixture','https://example.invalid/problem',json.dumps({'状态':'未做','日期':''}),json.dumps({'id':'fixture'})))
            db.execute('INSERT INTO statement_assets VALUES(?,?,?)',(digest(self.original),'application/pdf',self.original))
        shutil.copyfile(self.old,self.source)

    def test_small_and_non_download_assets_stay_local_and_existing_placement_is_unchanged(self):
        entries=[('image/svg+xml',b'<svg xmlns="http://www.w3.org/2000/svg"/>'),
                 ('application/octet-stream',b'// historical reference header'),
                 ('application/zip',b'PK-small-public-sample-fixture'),
                 ('application/pdf',b'%PDF-small-new-public-fixture'),
                 ('image/png',b'large-public-image-placement-fixture'*3000)]
        with closing(sqlite3.connect(self.source)) as db,db:
            db.executemany('INSERT INTO statement_assets VALUES(?,?,?)',[(digest(raw),mime,raw) for mime,raw in entries])
        before=self.source.read_bytes();old=self.old.read_bytes();output=self.root/'compact.sqlite3';assets=self.root/'exported'
        result=build(self.source,self.old,output,assets)
        self.assertEqual(self.source.read_bytes(),before);self.assertEqual(self.old.read_bytes(),old)
        self.assertEqual((result['localResources'],result['remoteResources']),(4,2));self.assertEqual(len(result['newInlineResources']),3)
        with closing(sqlite3.connect(output)) as db:
            local={sha:(mime,bytes(raw)) for sha,mime,raw in db.execute('SELECT * FROM statement_assets')};remote=list(db.execute('SELECT * FROM remote_statement_assets'))
            self.assertEqual(local[digest(self.original)],('application/pdf',self.original))
            for mime,raw in entries[:3]:self.assertEqual(local[digest(raw)],(mime,raw))
            self.assertEqual(set(local)|{r[0] for r in remote},{digest(self.original)}|{digest(raw) for _,raw in entries})
            for row in remote:validate_reference(*row)
            self.assertEqual({p.name for p in assets.iterdir()},{r[0]+'.bin' for r in remote})
            for sha,_,size,_ in remote:self.assertEqual((assets/(sha+'.bin')).stat().st_size,size)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')

    def test_personal_tables_are_rejected_without_exporting_their_contents(self):
        with closing(sqlite3.connect(self.source)) as db,db:
            db.execute('CREATE TABLE drafts(code TEXT)');db.execute("INSERT INTO drafts VALUES('private fixture')")
        before=self.source.read_bytes();assets=self.root/'exported'
        with self.assertRaisesRegex(ValueError,'public-only'):build(self.source,self.old,self.root/'rejected.sqlite3',assets)
        self.assertEqual(self.source.read_bytes(),before);self.assertEqual(list(assets.iterdir()),[])

if __name__=='__main__':unittest.main()
