"""Catalogue policy and network isolation; all databases/services are fixtures."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from contest_names import contest_name, normalize_row
from contest_policy import apply_visibility, authorized, content_ready
import integrations as I
import public_platforms as P
from test_integrations import Client, Store, NOW
from library import LibraryDatabase


def candidate(index='A', name='Codeforces Round 1127 (Div. 2, Based on Mexican Olympiad in Informatics 2026)'):
    return P.row('codeforces', {'id':2274, 'name':name, 'start':1, 'end':2}, index,
                 'Fixture '+index, 'https://codeforces.com/contest/2274/problem/'+index,
                 None, '尚未评级')


class ScopeTests(unittest.TestCase):
    def test_names_use_registered_series_without_guessing_a_round_division(self):
        for original, expected in (
            ('Codeforces Round 1127 (Div. 1, Based on Mexican Olympiad in Informatics 2026)', 'Div.1 1127'),
            ('Codeforces Round 1127 (Div. 2, Based on Mexican Olympiad in Informatics 2026)', 'Div.2 1127'),
            ('DeepInfra Round 1 (Codeforces Round 1126, Div. 1 + Div. 2)', 'Div.1+Div.2 1126'),
            ('AtCoder 初学者赛 479', 'ABC 479'), ('AtCoder 常规赛 231', 'ARC 231'),
            ('洛谷月赛 LGR-309 · Div.2', '月赛 309'), ('洛谷基础赛 #40', '基础赛 40')):
            self.assertEqual(contest_name(original), expected)
        row=normalize_row({'id':'stable::B', 'contest':'Div.2 1127',
                           'contestFullName':'Codeforces Round 1127 (Div. 1)', 'series':'Div.2'})
        self.assertEqual((row['id'],row['contest'],row['series']), ('stable::B','Div.1 1127','Div.1'))
        self.assertEqual(contest_name('Codeforces Round 1127'),'Codeforces Round 1127')

    def test_unrequested_series_and_empty_tasks_hide_without_deleting_identity(self):
        for name in ('Codeforces Round 1127 (Div. 1)',
                     'DeepInfra Round 1 (Codeforces Round 1126, Div. 1 + Div. 2)'):
            value={**candidate(name=name),'catalogContentReady':True}
            self.assertFalse(authorized(value))
            hidden=apply_visibility(value)
            self.assertTrue(hidden['catalogHidden'])
            self.assertEqual(hidden['id'],value['id'])
            self.assertNotIn('catalogHidden',value)
        empty=candidate()
        self.assertTrue(apply_visibility(empty)['catalogHidden'])
        self.assertNotIn('catalogHidden',apply_visibility({**empty,'catalogContentReady':True}))
        self.assertNotIn('catalogHidden',apply_visibility({**empty,'solutionAvailable':True}))
        self.assertNotIn('catalogHidden',apply_visibility({**empty,'source':'user-import'}))
        self.assertNotIn('catalogHidden',apply_visibility({**empty,'source':'archive'}))
        for source, contest in (('xcpc-roster','ICPC 2026 南京区域赛'),('lanqiao-history','蓝桥杯 2026')):
            self.assertNotIn('catalogHidden',apply_visibility({**empty,'source':source,'contest':contest}))

    def test_ready_content_validates_examples_including_empty_standard_streams(self):
        self.assertTrue(content_ready({'markdown':'Public problem','samples':[{'input':'','output':''}]}))
        for content in ({}, {'markdown':'Public problem','samples':[]},
                        {'markdown':' ','samples':[{'input':'1','output':'2'}]},
                        {'markdown':'Public problem','samples':[{'input':'1'}]}):
            self.assertFalse(content_ready(content))
        self.assertTrue(authorized({'contest':'洛谷月赛 LGR-309 Div.2'},'luogu'))
        self.assertFalse(authorized({'contest':'洛谷月赛 LGR-309 Div.1'},'luogu'))

    def test_discovery_filters_official_divisions_even_when_ids_are_in_old_allowlist(self):
        contests=[{'id':2273,'name':'Codeforces Round 1127 (Div. 1)'},
                  {'id':2274,'name':'Codeforces Round 1127 (Div. 2)'},
                  {'id':2271,'name':'DeepInfra Round 1 (Codeforces Round 1126, Div. 1 + Div. 2)'},
                  {'id':2276,'name':'Educational Codeforces Round 195 (Rated for Div. 2)'}]
        for contest in contests:contest.update(phase='FINISHED',startTimeSeconds=1,durationSeconds=2)
        client=Client({'https://codeforces.com/api/contest.list?gym=false':{'status':'OK','result':contests},
                       'https://codeforces.com/api/problemset.problems':{'status':'OK','result':{
                           'problems':[{'contestId':contest['id'],'index':'A','name':'Task'} for contest in contests]}}})
        rows,_,_=P.discover_cf(client,NOW,{2271,2273,2274,2276})
        self.assertEqual([(row['contestId'],row['contest']) for row in rows],[('2274','Div.2 1127'),('2276','教育赛 195')])

    def test_split_division_roster_preserves_exact_original_task_letters(self):
        contest={'id':2274,'name':'Codeforces Round 1127 (Div. 2)','phase':'FINISHED','startTimeSeconds':1,'durationSeconds':2}
        client=Client({'https://codeforces.com/api/contest.list?gym=false':{'status':'OK','result':[contest]},
                       'https://codeforces.com/api/problemset.problems':{'status':'OK','result':{'problems':[
                           {'contestId':2273,'index':'A','name':'Lavencia Oranges'},
                           {'contestId':2274,'index':'A','name':'The Projections of Paco'}]}},
                       'https://codeforces.com/api/contest.standings?contestId=2274':{'status':'OK','result':{
                           'contest':contest,'problems':[{'contestId':2274,'index':'C','name':'Lavencia Oranges','tags':['binary search']}], 'rows':[]}}})
        rows,_,_=P.discover_cf(client,NOW)
        self.assertEqual([(row['problem'],row['title'],row['url']) for row in rows],
                         [('C','Lavencia Oranges','https://codeforces.com/contest/2274/problem/C')])
        self.assertTrue(all('from=' not in url and 'count=' not in url for url in client.calls))


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.store=Store();self.store.values=[];self.store.library=LibraryDatabase(self.root/'library.sqlite3')
        self.service=I.IntegrationService(self.store,self.root,auto_start=False,client=Client(),clock=lambda:NOW)
    def tearDown(self):
        self.service.close();self.temp.cleanup()

    def test_failed_statement_is_pending_and_never_a_visible_empty_task(self):
        value=candidate()
        with patch.dict(P.DISCOVERY_ADAPTERS,{'codeforces':lambda *_:([value],[],'fixture')}), \
             patch.object(P,'statement',side_effect=RuntimeError('HTTP 403')):
            result=self.service._catalog('codeforces',set())
        self.assertEqual(result['added'],0);self.assertEqual(result['pending'],1)
        self.assertEqual(self.service.rows(),[])
        self.assertFalse(self.service.state['notifications'])

    def test_admission_uses_cached_examples_and_skips_local_duplicates(self):
        value=candidate()
        self.store.library.save_statement(value['id'],{'markdown':'Public fixture statement','samples':[{'input':'','output':'2'}]})
        with patch.dict(P.DISCOVERY_ADAPTERS,{'codeforces':lambda *_:([value],[],'fixture')}), \
             patch.object(P,'statement',side_effect=AssertionError('cached task must not fetch')):
            result=self.service._catalog('codeforces',set())
            self.assertEqual(result['added'],1)
            self.assertTrue(self.service.rows()[0]['catalogContentReady'])
            self.service._catalog('codeforces',{I.canonical(value['url'])})

    def test_one_cycle_bounds_new_statement_fetches(self):
        values=[candidate(str(i)) for i in range(20)]
        public={'markdown':'Public statement','samples':[{'input':'1','output':'2'}],'statementAvailable':True}
        with patch.dict(P.DISCOVERY_ADAPTERS,{'codeforces':lambda *_:(values,[],'fixture')}), \
             patch.object(P,'statement',return_value=public) as fetch:
            result=self.service._catalog('codeforces',set())
        self.assertEqual(fetch.call_count,12)
        self.assertEqual((result['added'],result['pending']),(12,8))

    def test_official_tags_refresh_for_unrated_problems_without_erasing_known_rating(self):
        value=candidate();self.service.state['rows'][value['id']]=value
        self.service.state['difficultyMetadata'][I.canonical(value['url'])]={'difficulty':1700,'difficultySource':'Codeforces 官方 rating'}
        self.service.client=Client({'https://codeforces.com/api/problemset.problems':{
            'status':'OK','result':{'problems':[{'contestId':2274,'index':'A','tags':['math','greedy']}]}}})
        self.service._refresh_difficulties('codeforces')
        metadata=self.service.problem_metadata({},value['url'])
        self.assertEqual(metadata['difficulty'],1700)
        self.assertEqual(metadata['officialTags'],['数学','贪心'])

    def test_discovery_error_does_not_skip_existing_metadata_refresh(self):
        with patch.object(self.service,'_local',return_value=set()), \
             patch.object(self.service,'_catalog',side_effect=RuntimeError('blocked task list')), \
             patch.object(self.service,'_account'),patch.object(self.service,'_refresh_knowledge'), \
             patch.object(self.service,'_refresh_difficulties') as refresh:
            self.service._refresh({'codeforces'})
        refresh.assert_called_once_with('codeforces')

    def test_identity_rows_keep_hidden_aliases_without_catalogue_classification(self):
        value={**candidate(),'catalogHidden':True}
        self.service.state['rows'][value['id']]=value
        with patch.object(P,'classify_contest',side_effect=AssertionError('identity lookup must be lightweight')):
            rows=self.service.identity_rows()
        self.assertEqual(rows,[{'id':value['id'],'url':value['url'],'source':'remote'}])
        rows[0]['id']='consumer mutation'
        self.assertEqual(self.service.identity_rows()[0]['id'],value['id'])


class NetworkIsolationTests(unittest.TestCase):
    def test_standings_cache_retains_problem_metadata_without_participants(self):
        with tempfile.TemporaryDirectory() as root:
            payload={'status':'OK','result':{'contest':{'id':2274},'problems':[{'index':'C','name':'Task'}],
                                            'rows':[{'party':{'members':[{'handle':'fixture participant'}]}}]}}
            calls=[]
            def transport(url,_headers):
                calls.append(url);return json.dumps(payload).encode(),None
            client=I.PublicClient(root,transport=transport,spacing=0)
            for _ in range(2):
                result=client.contest_problems(2274)['result']
                self.assertEqual(set(result),{'contest','problems'})
            self.assertEqual(calls,['https://codeforces.com/api/contest.standings?contestId=2274'])
            import sqlite3
            db=sqlite3.connect(Path(root)/'http/tb-documents.sqlite3')
            try:stored=''.join(row[0] for row in db.execute('SELECT value FROM documents'))
            finally:db.close()
            self.assertNotIn('fixture participant',stored)

    def test_slow_cf_request_does_not_hold_other_platform_or_cache_reads(self):
        with tempfile.TemporaryDirectory() as root:
            entered=threading.Event();release=threading.Event();errors=[]
            def transport(url,_headers):
                if 'codeforces.com' in url:
                    entered.set();release.wait(3)
                return b'public response',None
            client=I.PublicClient(root,transport=transport,spacing=0)
            def slow():
                try:client.text('https://codeforces.com/api/problemset.problems')
                except Exception as error:errors.append(error)
            worker=threading.Thread(target=slow);worker.start()
            try:
                self.assertTrue(entered.wait(1))
                response=[];done=threading.Event()
                def other():
                    response.append(client.text('https://atcoder.jp/contests/archive?lang=en'));done.set()
                second=threading.Thread(target=other);second.start()
                self.assertTrue(done.wait(1),'an unrelated host must not wait for the slow request')
                self.assertEqual(response,['public response'])
                self.assertEqual(client.text('https://atcoder.jp/contests/archive?lang=en'),'public response')
                second.join(1)
            finally:release.set();worker.join(4)
            self.assertEqual(errors,[])


if __name__=='__main__':unittest.main()
