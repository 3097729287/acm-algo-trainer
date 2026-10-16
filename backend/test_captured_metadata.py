import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from integrations import IntegrationService
from knowledge import enrich_row
from public_platforms import classify_contest, row, atcoder_knowledge
from test_integrations import Store, Client, NOW


class CaptureTests(unittest.TestCase):
    def test_contests_are_recognized_from_site_identity_without_changing_problem_id(self):
        value = row('atcoder', {'id':'abc479','name':'AtCoder Beginner Contest 479'}, 'A', 'Odd Index Sum', 'https://atcoder.jp/contests/abc479/tasks/abc479_a', 800, 'fixture')
        self.assertEqual(value['contest'], 'ABC 479')
        self.assertEqual(value['series'], 'ABC')
        self.assertEqual(value['id'], 'remote:atcoder:abc479::A')
        value = classify_contest({'contest':'【LGR-309-Div.2】洛谷 10 月月赛 III & Star OI', 'platform':'洛谷'})
        self.assertEqual(value['contestFamily'], '月赛')
        self.assertEqual(value['contest'], '月赛 309')
        self.assertIn('Star OI', value['contestFullName'])

    def test_public_statement_is_enriched_on_capture_and_reused_after_restart(self):
        value = row('atcoder', {'id':'abc999','name':'AtCoder Beginner Contest 999','end':100}, 'A', 'Odd Index Sum', 'https://atcoder.jp/contests/abc999/tasks/abc999_a', 800, 'fixture')
        statement = {'id':value['id'], 'url':value['url'], 'markdown':'Find the sum of the elements of an integer sequence at odd indices.', 'statementAvailable':True,
                     'samples':[{'input':'5\n1 2 3 4 5\n','output':'9\n'}], 'limits':{'timeMs':2000,'memoryMb':256}}
        with tempfile.TemporaryDirectory() as temporary:
            store = Store(); service = IntegrationService(store, Path(temporary), auto_start=False, client=Client(), clock=lambda:NOW)
            store.extensions = service
            try:
                with patch.dict('public_platforms.DISCOVERY_ADAPTERS', {'atcoder':lambda client, now:([value],[], 'fixture')}), patch('public_platforms.statement', return_value=statement) as fetch:
                    service._catalog('atcoder', set())
                    result=service.rows()[0]
                    self.assertEqual(result['contest'], 'ABC 999')
                    self.assertFalse(result.get('catalogHidden',False))
                    self.assertEqual(service.statement(value['id'])['samples'],statement['samples'])
                    self.assertIn('枚举', result['tags'])
                    service._catalog('atcoder', set())
                    self.assertEqual(fetch.call_count,1)
                service._save()
            finally: service.close()
            restored=IntegrationService(store, Path(temporary), auto_start=False, client=Client(), clock=lambda:NOW)
            try: self.assertIn('枚举', restored.rows()[0]['tags'])
            finally: restored.close()

    def test_title_letter_and_rating_alone_do_not_invent_knowledge(self):
        value={'id':'remote:atcoder:abc479::F','source':'remote','title':'Unknown','tags':[], 'difficulty':800}
        self.assertEqual(enrich_row(value)['tags'],[])
        self.assertIn('模拟', enrich_row(value, statement='Find the maximum number of consecutive days on which it rains.')['tags'])

    def test_editorial_classifies_only_the_official_task_link_and_retains_its_source(self):
        url='https://atcoder.jp/contests/abc479/tasks/abc479_c'
        source='https://atcoder.jp/contests/abc479/editorial/20000?lang=en'
        client=Client({url+'/editorial?editorialLang=en&lang=en':'<li><a href="/contests/abc479/editorial/1">User Editorial</a></li><li><a href="/contests/abc479/editorial/20000">Official Editorial</a></li>',source:'<p>Sort the values and use a greedy algorithm.</p><pre>dfs fake code cannot classify</pre>'})
        hint=atcoder_knowledge(client,{'url':url})
        self.assertIn('贪心',hint['tags'])
        self.assertIn('排序',hint['tags'])
        self.assertNotIn('DFS',hint['tags'])
        value=enrich_row({'id':'remote:fixture::C','source':'remote','tags':[]},algorithm_evidence=hint)
        value=enrich_row(value)
        self.assertTrue(any(e.get('reference')==source for e in value['knowledgeAnalysis']['evidence']))
