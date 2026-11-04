import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock,patch
import tempfile
from library import LibraryDatabase
from public_assets import read_asset
from scripts.prepare_public_assets import prepare
from test_library import record

class PublicAssetTests(unittest.TestCase):
    def test_slim_seed_roundtrip_and_download_cache_preserve_exact_originals(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=LibraryDatabase(root/'source.sqlite3');source.import_records([record()],{}, {})
            raw=b'%PDF-1.4\noriginal immutable fixture\n%%EOF';sha=hashlib.sha256(raw).hexdigest()
            with source.connection() as db:
                db.execute('INSERT INTO statement_assets VALUES(?,?,?)',(sha,'application/pdf',raw))
                db.execute('INSERT INTO statements VALUES(?,?)',('public-pdf',json.dumps({'markdown':'Original text','statementPdf':{'data':'tb-asset:'+sha},'samples':[]})))
            result=prepare(source.path,root/'slim.sqlite3',root/'server','http://127.0.0.1')
            self.assertEqual(result['externalBytes'],len(raw));self.assertEqual((root/'server'/f'{sha}.bin').read_bytes(),raw)
            slim=LibraryDatabase(root/'slim.sqlite3');value=slim.statement('public-pdf')
            self.assertEqual(value['statementPdf']['data'],'/api/library-assets/'+sha)
            response=MagicMock(status=200);response.read.return_value=raw;response.__enter__.return_value=response
            opener=MagicMock();opener.open.return_value=response
            with patch('public_assets.shutil.disk_usage',return_value=type('Disk',(),{'free':2*1024**3})()),patch.dict('os.environ',{'TB_OFFLINE':'0'}),patch('leaderboard.service_opener',return_value=opener):
                self.assertEqual(read_asset(slim,sha,root/'cache.sqlite3'),('application/pdf',raw))
            self.assertEqual(opener.open.call_count,1)
            request=opener.open.call_args.args[0];self.assertFalse(request.has_header('Authorization'))
            with patch.dict('os.environ',{'TB_OFFLINE':'1'}),patch('leaderboard.service_opener',side_effect=AssertionError('Cached PDF must stay offline')):
                self.assertEqual(read_asset(slim,sha,root/'cache.sqlite3')[1],raw)
            exported=slim.export_source(root/'export');rebuilt=LibraryDatabase.from_source(exported,root/'rebuilt.sqlite3')
            self.assertEqual(rebuilt.statement('public-pdf')['statementPdf']['data'],'/api/library-assets/'+sha)

    def test_wrong_download_is_not_cached_and_personal_databases_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);library=LibraryDatabase(root/'library.sqlite3');raw=b'%PDF expected';sha=hashlib.sha256(raw).hexdigest()
            with library.connection() as db:db.execute('INSERT INTO remote_statement_assets VALUES(?,?,?,?)',(sha,'application/pdf',len(raw),'http://127.0.0.1/updates/library-assets/'+sha+'.bin'))
            response=MagicMock(status=200);response.read.return_value=b'wrong';response.__enter__.return_value=response
            with patch('public_assets.shutil.disk_usage',return_value=type('Disk',(),{'free':2*1024**3})()),patch.dict('os.environ',{'TB_OFFLINE':'0'}),patch('leaderboard.service_opener') as factory:
                factory.return_value.open.return_value=response
                with self.assertRaisesRegex(ValueError,'checksum'):read_asset(library,sha,root/'cache.sqlite3')
            with library.connection() as db:db.execute('CREATE TABLE drafts(code TEXT)')
            with self.assertRaisesRegex(ValueError,'private'):prepare(library.path,root/'private-output.sqlite3',root/'server','http://127.0.0.1')
