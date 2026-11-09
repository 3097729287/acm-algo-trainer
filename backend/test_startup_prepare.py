"""Update preparation warms actual catalog inputs without personal migrations."""
from contextlib import closing
import hashlib,json,sqlite3,unittest
from unittest.mock import patch

from integrations import IntegrationService
from knowledge import KnowledgeAnalysisCache
from persistence import load_document,save_document
from test_loading_cache import LoadingCacheTests
import startup_prepare


class StartupPreparationTests(unittest.TestCase):
    setUp=LoadingCacheTests.setUp
    tearDown=LoadingCacheTests.tearDown
    open=LoadingCacheTests.open

    def test_public_inputs_match_normal_store_and_personal_state_is_untouched(self):
        private=self.root/'tb-personal.sqlite3'
        with closing(sqlite3.connect(private)) as db:
            db.execute('CREATE TABLE untouched(value BLOB)')
            db.execute('INSERT INTO untouched VALUES (?)',(b'private sentinel',));db.commit()
        before=hashlib.sha256(private.read_bytes()).hexdigest()
        save_document(self.root/'account-session.json','opaque personal sentinel')
        def store_factory():return self.open()
        with patch.object(startup_prepare,'STATE',self.root),patch.object(startup_prepare,'Store',side_effect=store_factory):
            startup_prepare.prepare()
        self.assertEqual(hashlib.sha256(private.read_bytes()).hexdigest(),before)
        self.assertEqual(load_document(self.root/'account-session.json',None),'opaque personal sentinel')
        prepared=load_document(self.root/'startup-preparation.json',{})
        self.assertTrue(prepared['publicCatalogReady'])
        self.assertEqual(prepared['schema'],1)
        self.assertEqual(tuple(prepared['catalogSignature']),self.library.content_signature())
        self.assertGreaterEqual(prepared['seconds'],0)
        restarted=self.open();extensions=IntegrationService(restarted,self.root,auto_start=False)
        restarted.extensions=extensions
        restarted.knowledge_analysis=KnowledgeAnalysisCache(self.root/'tb-knowledge-analysis.json')
        try:
            actual=json.loads(restarted.data_response_bytes(compact=True))
            self.assertIsNone(restarted._data_json)
            self.assertEqual(actual['rows'][0]['title'],'Fixture')
            self.assertFalse(extensions.worker)
        finally:extensions.close()


if __name__=='__main__':unittest.main()
