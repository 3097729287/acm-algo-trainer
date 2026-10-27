"""Precision, review exclusions, bounded storage and native profile recovery."""
import base64,gzip,hashlib,json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from account_sync import snapshot_payload,encoded
from bounded_cache import bounded_cache
from difficulty import normalize_practice_difficulty
from external_browser import BrowserProcess
from knowledge import normalize_tags

class Revision1420Tests(unittest.TestCase):
    def test_paper_eligibility_uses_fresh_catalog_without_loading_statement_images(self):
        from assets import AssetLibrary
        rows=[{'id':'ready','catalogContentReady':True},{'id':'absent','catalogContentReady':False}]
        store=SimpleNamespace(raw_rows=lambda:self.fail('Known catalog rows must not reload the raw library'))
        library=AssetLibrary(store)
        with patch.object(library,'_cached',side_effect=AssertionError('Paper preview must not decode Markdown/images')):
            self.assertEqual(library.candidates(rows),[dict(rows[0],judgeScope='samples')])
        # An older or imported row without indexed metadata still uses its own
        # saved statement, while preserving the order of the incoming catalog.
        legacy={'id':'legacy'}
        with patch.object(store,'raw_rows',return_value=[]),patch.object(library,'_cached',return_value={'statementAvailable':True,'samples':[{'input':'','output':'1'}]}) as reader:
            self.assertEqual([row['id'] for row in library.candidates([legacy,*rows])],['legacy','ready'])
            reader.assert_called_once_with('legacy')

    def test_nontrivial_atcoder_retains_native_evidence_and_distinct_reference_level(self):
        row=normalize_practice_difficulty({'url':'https://atcoder.jp/contests/abc480/tasks/abc480_b','difficulty':800,'nativeDifficulty':124,'platform':'AtCoder'})
        self.assertEqual((row['difficulty'],row['nativeDifficulty']),(1200,124))
        self.assertNotIn('reviewTrivial',row)
        self.assertEqual(normalize_practice_difficulty(row),row)
        self.assertTrue(normalize_practice_difficulty({'url':'https://www.luogu.com.cn/problem/P1001'})['reviewTrivial'])
        self.assertNotIn('reviewTrivial',normalize_practice_difficulty({'url':'https://www.luogu.com.cn/problem/P1228'}))

    def test_divide_and_conquer_survives_normalization_as_its_own_topic(self):
        self.assertIn('分治',normalize_tags(['递归','分治'])['tags'])
        self.assertEqual(normalize_tags(['divide and conquer'])['tags'],['分治'])

    def test_streamed_snapshot_matches_canonical_bytes_unicode_and_escaping(self):
        state={'tables':{'drafts':[{'code':'cout << "中文\\n";\n'*10000}],'preferences':[]},'publicAccounts':{},'format':'tb-account-state-v1'}
        before=json.loads(encoded(state));value=snapshot_payload(state);raw=gzip.decompress(base64.b64decode(value['payload']))
        self.assertEqual(raw,encoded(state).encode('utf-8'))
        self.assertEqual(value['sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(value['uncompressedBytes'],len(raw));self.assertEqual(state,before)

    def test_image_cache_evicts_old_content_and_does_not_retain_oversized_result(self):
        calls=[]
        @bounded_cache(maxsize=10,maxbytes=2500)
        def load(identity):calls.append(identity);return {'image':identity+'x'*1000,'samples':['1 2']}
        first=load('first');self.assertIs(first,load('first'))
        for n in range(6):load(str(n))
        self.assertEqual(load('first'),first);self.assertEqual(calls.count('first'),2)
        self.assertLessEqual(load.cache_bytes(),2500)
        load('oversized'*1000);self.assertLessEqual(load.cache_bytes(),2500)

    def test_cache_clear_during_a_fetch_cannot_reinsert_stale_statement(self):
        @bounded_cache()
        def load():load.cache_clear();return {'markdown':'old'}
        self.assertEqual(load()['markdown'],'old');self.assertEqual(load.cache_info().currsize,0)

    def test_recovery_accepts_only_a_profile_process_matching_the_cdp_browser_pid(self):
        with TemporaryDirectory(prefix='tb-recover-unit-') as folder:
            browser=BrowserProcess(Path(folder)/'profile');browser.profile.mkdir(parents=True)
            active=browser.profile/'DevToolsActivePort';version={'webSocketDebuggerUrl':'ws://127.0.0.1:1234/devtools/browser/owned'}
            browser.request=lambda _:version
            with patch('browser_endpoint.candidates',return_value=[(10,1234)]),patch('external_browser.DevToolsPage') as page,patch.object(browser,'_memory'):
                page.return_value.call.return_value={'processInfo':[{'type':'browser','id':11}]}
                self.assertFalse(browser._recover(Path('edge.exe'),active));self.assertFalse(active.exists())
                page.return_value.call.return_value={'processInfo':[{'type':'browser','id':10}]}
                self.assertTrue(browser._recover(Path('edge.exe'),active));self.assertEqual(active.read_text(),'1234\n/devtools/browser/owned')
