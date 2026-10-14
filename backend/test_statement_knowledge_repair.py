"""Real response shapes in disposable state; no account or model requests."""
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from assets import AssetLibrary
from integrations import IntegrationService
from knowledge import KnowledgeAnalysisCache, enrich_row, public_knowledge
from public_platforms import row, statement
from store import Store as CatalogStore
from test_integrations import Store, Client, NOW
from translation import TranslationService


class StatementRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tb-statement-repair-')
        self.root=Path(self.temp.name)
        self.url='https://www.luogu.com.cn/problem/P17645'
        self.value=row('luogu',{'id':358583,'name':'Fixture','end':100},'N','Fibonacci Sequence',self.url,900,'fixture')
        self.payload={'data':{'problem':{'pid':'P17645','content':{'description':'Print the first five numbers in the Fibonacci sequence.','formatI':'There is no input for this problem.','formatO':'Print five integers.','locale':'en'},'contenu':{'description':'输出斐波那契数列的前五项。','formatI':'本题没有输入。','formatO':'输出五个整数。','locale':'zh-CN'},'samples':[['','1 1 2 3 5']]}}}
        self.store=CatalogStore(data_file=self.root/'none.md',history_file=self.root/'history.jsonl',library_file=self.root/'library.sqlite3')
        self.client=Client({self.url:self.payload})
        self.service=IntegrationService(self.store,self.root,auto_start=False,client=self.client,clock=lambda:NOW)
        self.store.extensions=self.service;self.service.state['rows'][self.value['id']]=self.value
        self.assets=AssetLibrary(self.store,self.root/'assets')

    def tearDown(self):
        self.service.close();self.temp.cleanup()

    def test_empty_input_is_an_official_sample_and_is_cached(self):
        result=self.assets.problem(self.value['id'])
        self.assertTrue(result['statementAvailable'])
        self.assertEqual(result['samples'],[{'name':'样例 1','input':'','output':'1 1 2 3 5'}])
        self.assertEqual(result['judge']['cases'],1)
        self.assets.problem(self.value['id'])
        self.assertEqual(self.client.calls,[self.url])

    def test_no_examples_does_not_hide_the_public_text_or_repeat_fetch(self):
        self.payload['data']['problem']['samples']=[]
        result=self.assets.problem(self.value['id'])
        self.assertTrue(result['statementAvailable']);self.assertEqual(result['samples'],[])
        self.assets.problem(self.value['id'])
        self.assertEqual(self.client.calls,[self.url])

    def test_failed_fetch_exposes_error_and_can_be_retried(self):
        self.client.responses[self.url]=RuntimeError('fixture temporary network failure')
        first=self.assets.problem(self.value['id'])
        self.assertFalse(first['statementAvailable']);self.assertIn('temporary',first['statementError'])
        self.client.responses[self.url]=self.payload
        self.assertTrue(self.assets.problem(self.value['id'])['statementAvailable'])

    def test_malformed_sample_is_reported_and_not_cached_as_an_empty_sample(self):
        for invalid in ([['input only']], [[None,'answer']], {'input':'1'}):
            self.payload['data']['problem']['samples']=invalid
            result=self.assets.problem(self.value['id'])
            self.assertFalse(result['statementAvailable'])
            self.assertIn('样例格式',result['statementError'])

    def test_luogu_chinese_version_is_used_without_model_or_private_data(self):
        self.assets.problem(self.value['id'])
        class Provider:
            name='never called'
            def __call__(self,_):raise AssertionError('Site translation needs no model')
        answer=TranslationService(self.assets,self.root,Provider()).translate(self.value['id'])
        self.assertEqual(answer['kind'],'site');self.assertIn('本题没有输入',answer['markdown'])
        self.assertNotIn('draft',answer)

    def test_old_luogu_statement_cache_refreshes_chinese_without_losing_original(self):
        old=statement(self.client,self.value['id'],self.value['title'],self.url)
        old.pop('translation');old.pop('statementVersion')
        from integrations import atomic
        import hashlib
        atomic(self.root/'statements'/(hashlib.sha256(self.value['id'].encode()).hexdigest()+'.json'),old)
        self.assertIn('本题没有输入',self.assets.localized_statement(self.value['id'])['markdown'])
        self.assertIn('There is no input',self.assets._cached(self.value['id'])['markdown'])

    def test_english_luogu_and_nowcoder_are_translatable(self):
        class Assets:
            lock=threading.RLock()
            def _cached(inner,_):return {'markdown':'Given the integer $n$, find the answer and print it.','url':inner.url,'statementAvailable':True,'draft':'PRIVATE'}
        class Provider:
            name='fixture'
            def __call__(inner,text):
                self.assertNotIn('PRIVATE',text)
                return text.replace('Given the integer','给定整数').replace('find the answer and print it.','求出答案并输出。')
        for url in [self.url,'https://ac.nowcoder.com/acm/contest/1/A']:
            with self.subTest(url=url):
                assets=Assets();assets.url=url
                self.assertIn('给定整数',TranslationService(assets,self.root,Provider()).translate(url)['markdown'])


class KnowledgeRepairTests(unittest.TestCase):
    def test_reencoding_captured_broad_topics_keeps_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            store=CatalogStore(data_file=root/'none.md',history_file=root/'history.jsonl',library_file=root/'library.sqlite3')
            service=IntegrationService(store,root,auto_start=False,client=Client(),clock=lambda:NOW)
            store.extensions=service
            try:
                value=row('codeforces',{'id':90001,'name':'Fixture','end':100},'A','Task','https://codeforces.com/contest/90001/problem/A',1000,'fixture',['dp','strings'])
                service.state['rows'][value['id']]=value
                result=store.data()['rows'][0]
                self.assertEqual(result['tags'],[])
                self.assertEqual(set(result['knowledgeCategories']),{'动态规划','字符串'})
            finally:service.close()

    def test_old_local_problem_is_supplemented_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            value={'id':'old::A','title':'Old task','url':'https://www.luogu.com.cn/problem/P999000','tags':[],'knowledgeCategories':[]}
            store=Store();store.knowledge_analysis=KnowledgeAnalysisCache(root/'knowledge.json');store.data=lambda:{'rows':[store.knowledge_analysis.apply(value)]}
            service=IntegrationService(store,root,auto_start=False,client=Client(),clock=lambda:NOW)
            saved={'statementAvailable':True,'markdown':'Public statement','officialTags':['深度优先搜索 DFS'],'url':value['url'],'id':value['id']}
            try:
                with patch('public_platforms.statement',return_value=saved) as fetch:
                    service._refresh_knowledge('luogu');service._refresh_knowledge('luogu')
                    self.assertEqual(fetch.call_count,1)
                restored=KnowledgeAnalysisCache(root/'knowledge.json')
                self.assertIn('DFS',restored.apply(value)['tags'])
            finally:service.close()

    def test_public_seed_uses_exact_urls_with_reviewable_sources(self):
        evidence=public_knowledge()
        self.assertGreaterEqual(len(evidence),174)
        for url,entry in evidence.items():
            with self.subTest(url=url):
                result=enrich_row({'url':url,'tags':[]})
                self.assertTrue(result['tags'] or result['knowledgeCategories'])
                self.assertTrue(entry['source'].startswith('https://'))
                self.assertTrue(entry['reason'])
        fake=enrich_row({'url':'https://example.com/abc479_f','title':'Narrow Passage','tags':[]})
        self.assertEqual(fake['tags'],[])


if __name__=='__main__':unittest.main()
