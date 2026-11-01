from pathlib import Path
import tempfile
import threading
import time
import unittest
from translation import TranslationService

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
