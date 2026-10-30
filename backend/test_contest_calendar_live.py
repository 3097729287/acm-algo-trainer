"""Live publication boundaries, bounded retries and catalogue invalidation.

Only synthetic HTTP responses and disposable SQLite state are used.
"""
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from contest_calendar import ContestCalendar, event
from contest_imports import StartedContestClient, import_contest, roster
from integrations import IntegrationService, PublicClient
from library import LibraryDatabase
from persistence import load_document, save_document
from store import Store
from test_library import record

COMPLETE = {'markdown':'# Fixture\n\n## 题目描述\n\n给定两个整数，输出它们的和。输入中只包含这两个整数，每个整数的绝对值不超过一百。\n\n## 输入描述\n\n一行两个整数。\n\n## 输出描述\n\n一行一个整数，表示输入两个数的和。',
            'samples':[{'name':'样例 1','input':'1 2','output':'3'}], 'statementAvailable':True}


class CalendarLiveTests(unittest.TestCase):
    def make_calendar(self, directory, clock, importer):
        calendar = ContestCalendar(directory, clock=lambda:clock[0], offline=False, client=object(), importer=importer)
        for provider in calendar.providers:
            calendar.providers[provider] = {'checkedAt':clock[0], 'status':'ready', 'contests':[]}
        self.addCleanup(calendar.close)
        return calendar

    def wait(self, predicate):
        deadline=time.monotonic()+3
        while not predicate() and time.monotonic()<deadline: time.sleep(.005)
        self.assertTrue(predicate())

    def test_future_is_not_fetched_active_wins_and_only_one_job_runs(self):
        with tempfile.TemporaryDirectory() as directory, patch('contest_imports.SCHOOL_CONTESTS',()):
            clock=[1800000000]; entered=threading.Event();release=threading.Event();seen=[]
            def importer(row):
                seen.append(row['id']);entered.set();release.wait(2)
                return {'status':'ready','ready':1,'total':1}
            calendar=self.make_calendar(directory,clock,importer)
            upcoming=event('nowcoder',2,'Future',clock[0]+1,clock[0]+3600,'https://ac.nowcoder.com/acm/contest/2')
            calendar.providers['nowcoder']['contests']=[upcoming]
            calendar.snapshot();self.assertEqual(seen,[])
            clock[0]+=1
            old=event('codeforces',1,'Old',clock[0]-7200,clock[0]-3600,'https://codeforces.com/contest/1')
            calendar.providers['codeforces']['contests']=[old]
            started=time.monotonic();value=calendar.snapshot()
            self.assertLess(time.monotonic()-started,.25)
            self.assertTrue(value['importing']);self.assertTrue(entered.wait(1))
            for _ in range(5):calendar.snapshot(refresh=True)
            self.assertEqual(seen,['nowcoder:2'])
            release.set();self.wait(lambda:not calendar.import_running)

    def test_opening_backoff_is_bounded_and_manual_refresh_can_retry(self):
        with tempfile.TemporaryDirectory() as directory, patch('contest_imports.SCHOOL_CONTESTS',()):
            clock=[1800000000];calls=[]
            calendar=self.make_calendar(directory,clock,lambda row:(calls.append(row['id']) or {'status':'partial','ready':0,'total':1,'error':'not public'}))
            row=event('nowcoder',2,'Fixture',clock[0],clock[0]+7200,'https://ac.nowcoder.com/acm/contest/2')
            calendar.providers['nowcoder']['contests']=[row]
            calendar.snapshot();self.wait(lambda:not calendar.import_running)
            self.assertEqual(calendar.imports[row['id']]['retryAt']-clock[0],15)
            calendar.snapshot();self.assertEqual(len(calls),1)
            calendar.snapshot(refresh=True);self.wait(lambda:not calendar.import_running)
            self.assertEqual(len(calls),2)
            calendar.snapshot(refresh=True);self.assertEqual(len(calls),2,'manual retry also has a cooldown')
            clock[0]+=601
            calendar.snapshot();self.wait(lambda:not calendar.import_running)
            self.assertEqual(calendar.imports[row['id']]['retryAt']-clock[0],300,'opening fast retries end after ten minutes')
            calendar.imports[row['id']].update(attempts=8,retryAt=0)
            clock[0]=1800000100
            calendar.snapshot();self.wait(lambda:not calendar.import_running)
            self.assertEqual(calendar.imports[row['id']]['retryAt']-clock[0],300,'fast retries have an independent attempt cap')

    def test_changed_start_time_does_not_inherit_an_old_failure_deadline(self):
        with tempfile.TemporaryDirectory() as directory, patch('contest_imports.SCHOOL_CONTESTS',()):
            clock=[1800000000];calls=[]
            calendar=self.make_calendar(directory,clock,lambda row:(calls.append(row['id']) or {'status':'ready','ready':1,'total':1}))
            row=event('nowcoder',2,'Fixture',clock[0],clock[0]+7200,'https://ac.nowcoder.com/acm/contest/2')
            calendar.providers['nowcoder']['contests']=[row]
            calendar.imports[row['id']]={'status':'error','attempts':7,'retryAt':clock[0]+3600,'scheduledStartAt':event('nowcoder',2,'Fixture',clock[0]-3600,clock[0],'x')['startAt']}
            calendar.snapshot();self.wait(lambda:not calendar.import_running)
            self.assertEqual(calls,[row['id']]);self.assertEqual(calendar.imports[row['id']]['attempts'],1)

    def test_started_roster_does_not_reuse_cached_prepublication_http_200(self):
        reads=[]
        def transport(url, headers):
            reads.append(url)
            tasks=[] if len(reads)==1 else [{'index':'A','title':'Fixture'}]
            return json.dumps({'code':0,'data':{'data':tasks,'basicInfo':{'contestId':141882,'problemCount':1}}}).encode(),None
        with tempfile.TemporaryDirectory() as directory:
            client=PublicClient(directory,transport=transport,spacing=0)
            url='https://ac.nowcoder.com/acm/contest/problem-list?token=&id=141882'
            self.assertEqual(client.json(url)['data']['data'],[])
            row=event('nowcoder',141882,'小白月赛139',1800000000,1800007200,'https://ac.nowcoder.com/acm/contest/141882')
            values=roster(StartedContestClient(client),row)
            self.assertEqual(len(reads),2);self.assertEqual(len(values),1)
            self.assertEqual(values[0]['id'],'remote:nowcoder:141882::A')

    def test_partial_official_roster_is_not_marked_complete(self):
        class Client:
            def json(self,url):return {'code':0,'data':{'data':[{'index':'A','title':'Fixture'}],'basicInfo':{'contestId':141882,'problemCount':6}}}
        with self.assertRaisesRegex(ValueError,'完整题单'):
            roster(Client(),{'id':'nowcoder:141882','platform':'nowcoder','title':'小白月赛139','url':'https://ac.nowcoder.com/acm/contest/141882'})

    def test_malformed_import_response_releases_worker_and_remains_retryable(self):
        with tempfile.TemporaryDirectory() as directory, patch('contest_imports.SCHOOL_CONTESTS',()):
            clock=[1800000000]
            calendar=self.make_calendar(directory,clock,lambda row:[])
            row=event('nowcoder',2,'Fixture',clock[0],clock[0]+7200,'https://ac.nowcoder.com/acm/contest/2')
            calendar.providers['nowcoder']['contests']=[row]
            calendar.snapshot();self.wait(lambda:not calendar.import_running)
            self.assertEqual(calendar.imports[row['id']]['status'],'error')
            clock[0]+=15
            calendar.importer=lambda row:{'status':'ready','ready':1,'total':1}
            calendar.snapshot();self.wait(lambda:not calendar.import_running)
            self.assertEqual(calendar.imports[row['id']]['status'],'ready')

    def test_import_invalidates_warm_compact_catalog_and_keeps_original_metadata(self):
        payload={'code':0,'data':{'data':[{'index':'A','title':'Fresh A'},{'index':'B','title':'Fresh B'}],
                                  'basicInfo':{'contestId':141882,'problemCount':2}}}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);database=LibraryDatabase(root/'library.sqlite3');database.import_records([record()],{}, {})
            store=Store(data_file=root/'absent.md',library_file=database.path)
            client=PublicClient(root/'http',transport=lambda *args:(json.dumps(payload).encode(),None),spacing=0)
            service=IntegrationService(store,root/'overlay',client=client,auto_start=False);store.extensions=service
            self.addCleanup(service.close)
            before=json.loads(store.data_response_bytes(compact=True))
            row=event('nowcoder',141882,'小白月赛139',1800000000,1800007200,'https://ac.nowcoder.com/acm/contest/141882')
            initial=roster(StartedContestClient(client),row)[0]
            initial.update(difficulty=1400,difficultySource='reviewed fixture',firstAdded='2026-01-01')
            service.state['rows'][initial['id']]=initial
            path=service.state_dir/'statements'/(__import__('hashlib').sha256(initial['id'].encode()).hexdigest()+'.json')
            save_document(path,dict(COMPLETE,id=initial['id'],url=initial['url']))
            with patch('public_platforms.statement',return_value=COMPLETE) as fetch:
                result=import_contest(service,row)
            self.assertEqual(result['status'],'ready');self.assertEqual(result['ready'],2);self.assertEqual(fetch.call_count,1,'complete A is retained, only B is fetched')
            after=json.loads(store.data_response_bytes(compact=True))
            ids={x['id'] for x in after['rows']}
            self.assertTrue(set(result['problemIds'])<=ids)
            self.assertNotEqual(before['revision'],after['revision'])
            old=service.state['rows'][initial['id']]
            self.assertEqual((old['difficulty'],old['difficultySource'],old['firstAdded']),(1400,'reviewed fixture','2026-01-01'))
            self.assertEqual(load_document(path,{})['markdown'],COMPLETE['markdown'])

    def test_empty_or_access_notice_statement_is_partial_and_never_cached_complete(self):
        class Client:
            def json(self,url):return {'code':0,'data':{'data':[{'index':'A','title':'Fixture'}],'basicInfo':{'contestId':141882,'problemCount':1}}}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);database=LibraryDatabase(root/'library.sqlite3');database.import_records([record()],{}, {})
            store=Store(data_file=root/'absent.md',library_file=database.path)
            service=IntegrationService(store,root/'overlay',client=Client(),auto_start=False);self.addCleanup(service.close)
            row=event('nowcoder',141882,'小白月赛139',1800000000,1800007200,'https://ac.nowcoder.com/acm/contest/141882')
            with patch('public_platforms.statement',return_value={'markdown':'登录后查看','samples':[]}):result=import_contest(service,row)
            self.assertEqual((result['status'],result['ready']),('partial',0))
            self.assertTrue(all(not value['catalogContentReady'] for value in service.state['rows'].values()))

if __name__=='__main__':unittest.main()
