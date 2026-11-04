from pathlib import Path
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs,urlsplit
from shared_translations import SharedStatementTranslations
from translation import TranslationService
from training import ServiceError

ORIGINAL='# Task\n\nGiven a positive integer $n$, print its value.\n'
CHINESE='# Task\n\n给定一个正整数 $n$，输出它的值。\n'


class Assets:
    lock=threading.RLock()
    def _cached(self,identity):return {'id':identity,'url':'https://codeforces.com/contest/1/problem/A','statementAvailable':True,'markdown':ORIGINAL}
    def localized_statement(self,identity):return None


class Provider:
    name='fixture-provider'
    calls=0
    def __call__(self,text):
        self.calls+=1
        return text.replace('Given a positive integer','给定一个正整数').replace('print its value.','输出它的值。')


class Shared:
    def __init__(self,markdown=None):self.markdown=markdown;self.downloads=0;self.started=threading.Event();self.release=threading.Event();self.finished=threading.Event();self.payload=None
    def owner(self):return 'fixture-owner'
    def get(self,*args):self.downloads+=1;return self.markdown
    def publish(self,problem,original,markdown,format,owner):
        self.started.set();self.release.wait(2);self.payload={'problem':problem,'original':original,'markdown':markdown,'format':format,'owner':owner};self.finished.set();return True


class SharedTranslationTests(unittest.TestCase):
    def test_one_paid_translation_is_reused_by_another_account_without_api_configuration(self):
        values={};uploaded=threading.Event();requests=[]
        def request(profile,method,path,body=None,timeout=None):
            requests.append((profile['user_id'],method,path,body))
            if method=='POST':
                self.assertEqual(set(body),{'url','sourceHash','format','language','original','markdown'})
                values[body['sourceHash']]={key:body[key] for key in ('url','sourceHash','format','language','markdown')}
                uploaded.set();return {'saved':True}
            identity=parse_qs(urlsplit(path).query)
            return {'translation':values.get(identity['sourceHash'][0])}
        def shared(owner):
            return SharedStatementTranslations(SimpleNamespace(_ranking_profile=lambda:{'user_id':owner,'auth_token':owner+'-token','endpoint':'https://isolated.invalid'},leaderboard=SimpleNamespace(_request=request)))
        with tempfile.TemporaryDirectory(prefix='tb-two-account-translation-') as folder:
            provider=Provider();alice=TranslationService(Assets(),Path(folder)/'alice',provider,shared('alice'))
            bob=TranslationService(Assets(),Path(folder)/'bob',shared=shared('bob'))
            try:
                first=alice.translate('fixture');self.assertTrue(uploaded.wait(1))
                with patch('translation_config.existing_provider',return_value=None),patch('translation_config.local_key',side_effect=ServiceError(503,'未配置')):
                    self.assertFalse(bob.status()['configured'])
                    second=bob.translate('fixture')
                self.assertEqual(second['markdown'],first['markdown']);self.assertEqual(second['kind'],'shared');self.assertEqual(provider.calls,1)
                count=len(requests);bob.translate('fixture');self.assertEqual(len(requests),count,'Later reads are instant local-cache reads')
                self.assertTrue(any(owner=='bob' and method=='GET' for owner,method,*_ in requests))
            finally:alice.close();bob.close()

    def test_failed_upload_is_retried_when_saved_translation_is_reopened(self):
        with tempfile.TemporaryDirectory(prefix='tb-retry-translation-') as folder:
            shared=Shared();shared.release.set();shared.publish=lambda *_:False
            first=TranslationService(Assets(),Path(folder),Provider(),shared)
            first.translate('fixture');first.close()
            shared.finished.clear()
            def publish(*args):shared.finished.set();return True
            shared.publish=publish
            provider=Provider();second=TranslationService(Assets(),Path(folder),provider,shared)
            try:
                value=second.translate('fixture');self.assertTrue(value['cached']);self.assertTrue(shared.finished.wait(1));self.assertEqual(provider.calls,0)
            finally:second.close()

    def test_shared_download_works_without_calling_personal_provider(self):
        with tempfile.TemporaryDirectory(prefix='tb-shared-translation-') as folder:
            shared=Shared(CHINESE);provider=Provider();service=TranslationService(Assets(),Path(folder),provider,shared)
            value=service.translate('fixture');self.assertEqual(value['markdown'],CHINESE);self.assertEqual(value['kind'],'shared');self.assertEqual(provider.calls,0)
            service.translate('fixture');self.assertEqual(shared.downloads,1)
            service.close()

    def test_paid_translation_is_saved_before_background_upload_and_reused_offline(self):
        with tempfile.TemporaryDirectory(prefix='tb-shared-translation-') as folder:
            shared=Shared();provider=Provider();service=TranslationService(Assets(),Path(folder),provider,shared)
            start=time.monotonic();value=service.translate('fixture')
            self.assertLess(time.monotonic()-start,1)
            self.assertIn('给定',value['markdown']);self.assertTrue(shared.started.wait(1));self.assertFalse(shared.finished.is_set())
            shared.release.set();self.assertTrue(shared.finished.wait(1))
            self.assertEqual(set(shared.payload['problem']),{'url'});self.assertEqual(shared.payload['original'],ORIGINAL)
            shared.get=lambda *_:self.fail('Saved translation should not require another network lookup')
            service.translate('fixture');self.assertEqual(provider.calls,1)
            service.close()


if __name__=='__main__':unittest.main()
