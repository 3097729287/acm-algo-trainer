"""Slow public GETs never block saved drafts, cached problems or catalogue reads."""
from contextlib import closing
import http.client
import gc
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
import weakref
from unittest.mock import patch
from urllib.parse import urlencode

from assets import AssetLibrary
import backend
from library import LibraryDatabase
from persistence import load_document
from store import Store
import store as store_module


def public_statement(identity, title='Fixture'):
    return {'id':identity,'title':title,'url':'https://codeforces.com/contest/1/problem/'+identity[-1],
            'markdown':'# '+title+'\n\nRead two integers and print their sum.',
            'samples':[{'name':'Sample 1','input':'1 2\n','output':'3\n'}],
            'limits':{'timeMs':1000,'memoryMb':128},'statementAvailable':True,'statementVersion':2}


def record(letter, cached=False):
    identity='loading::'+letter
    raw={'场次':'loading','题号':letter,'题名':'Fixture '+letter,'知识点':'枚举','难度':'1200','状态':'未做','日期':''}
    encoded={'id':identity,'contest':'Div.2 1','problem':letter,'title':raw['题名'],
             'url':'https://codeforces.com/contest/1/problem/'+letter,'source':'archive',
             'platform':'Codeforces','series':'Div.2','difficulty':1200,'difficultyEstimated':False,
             'difficultySource':'Fixture official rating','difficultyBand':[1200,1200],
             'difficultyConfidence':'HIGH','difficultyEvidence':['https://codeforces.com/api/problemset.problems'],
             'tags':['枚举'],'knowledge':'枚举','knowledgeCategories':['思维与策略'],'status':'未做','date':'',
             'contestDate':'2026-10-11T18:35:00Z','startedAt':'2026-10-11T18:35:00Z',
             'endedAt':'2026-10-11T20:35:00Z','contestDateSource':'Fixture public schedule',
             'knowledgeAnalysis':{'evidence':[{'reason':'Full detail evidence, absent from list view'}]}}
    return raw,encoded,None,public_statement(identity,raw['题名']) if cached else None


def eventually(predicate, timeout=2):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if predicate():return True
        threading.Event().wait(.005)
    return bool(predicate())


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tb-nonblocking-loading-');self.root=Path(self.temp.name)
        self.library=LibraryDatabase(self.root/'library.sqlite3')
        self.library.import_records([record('A'),record('B',cached=True),record('C'),record('D'),record('E')],{}, {})
        self.store=Store(data_file=self.root/'absent.md',data_root=self.root/'imports',library_file=self.library.path)
        self.assets=AssetLibrary(self.store,self.root/'assets')
        self.releases=[];self.servers=[]

    def tearDown(self):
        for release in self.releases:release.set()
        for server,thread in self.servers:
            server.shutdown();thread.join(3);server.server_close()
        self.assets.close();self.temp.cleanup()

    def slow_statement(self):
        entered=threading.Event();release=threading.Event();self.releases.append(release);calls=[]
        def fetch(_client,identity,title,url):
            calls.append(identity);entered.set()
            # The test/tearDown always releases the worker. A slow CI machine
            # must not turn a deliberately blocked GET into a fetch failure.
            release.wait()
            return public_statement(identity,title)
        return entered,release,calls,fetch

    def assert_returns_while_fetch_is_blocked(self,call,timeout=1):
        result=[];errors=[];done=threading.Event()
        def run():
            try:result.append(call())
            except Exception as error:errors.append(error)
            finally:done.set()
        thread=threading.Thread(target=run,daemon=True);thread.start()
        self.assertTrue(done.wait(timeout),'a cached/local request waited for the slow public GET')
        thread.join(1)
        if errors:raise errors[0]
        return result[0]


class BackgroundProblemTests(Fixture):
    def test_closed_workspace_assets_are_not_retained_by_method_caches(self):
        retired=AssetLibrary(self.store,self.root/'retired-assets')
        self.assertTrue(retired.problem('loading::B',fetch=False)['statementAvailable'])
        reference=weakref.ref(retired)
        retired.close();del retired;gc.collect()
        self.assertIsNone(reference(),'cached bound methods must release a closed account workspace')

    def test_metadata_returns_immediately_and_cached_other_problem_stays_available(self):
        entered,release,calls,fetch=self.slow_statement()
        with patch('public_platforms.statement',side_effect=fetch):
            first=self.assert_returns_while_fetch_is_blocked(lambda:self.assets.background_problem('loading::A'))
            self.assertTrue(entered.wait(1));self.assertFalse(release.is_set())
            self.assertEqual((first['id'],first['title']),('loading::A','Fixture A'))
            self.assertFalse(first['statementAvailable']);self.assertTrue(first['statementLoading'])
            cached=self.assert_returns_while_fetch_is_blocked(lambda:self.assets.problem('loading::B'))
            self.assertTrue(cached['statementAvailable']);self.assertEqual(cached['samples'][0]['output'],'3\n')
            for _ in range(8):self.assets.background_problem('loading::A')
            self.assertEqual(calls,['loading::A'],'concurrent openings must share one original-site request')
            pending=self.assets._fetches['loading::A']
            release.set()
            self.assertIsNone(pending.result(timeout=15))
            self.assertTrue(self.assets.problem('loading::A',fetch=False)['statementAvailable'])
            recovered=self.assets.background_problem('loading::A')
            self.assertTrue(recovered['statementAvailable']);self.assertFalse(recovered.get('statementLoading',False))
            self.assertEqual(calls,['loading::A'])

    def test_failure_negative_cache_expires_and_explicit_retry_can_recover(self):
        clock=[100.0];calls=[]
        def fail(_client,identity,title,url):calls.append(identity);raise RuntimeError('Fixture HTTP 403')
        with patch('assets.time',SimpleNamespace(monotonic=lambda:clock[0])),patch('public_platforms.statement',side_effect=fail):
            self.assets.background_problem('loading::A')
            self.assertTrue(eventually(lambda:'loading::A' not in self.assets._fetches))
            for _ in range(5):
                result=self.assets.background_problem('loading::A')
                self.assertFalse(result['statementLoading']);self.assertIn('403',result['statementError'])
            self.assertEqual(len(calls),1)
            clock[0]+=59
            self.assets.background_problem('loading::A');self.assertEqual(len(calls),1)
            clock[0]+=2
            self.assets.background_problem('loading::A')
            self.assertTrue(eventually(lambda:'loading::A' not in self.assets._fetches));self.assertEqual(len(calls),2)
            with patch('public_platforms.statement',side_effect=lambda _c,i,t,_u:public_statement(i,t)) as retry:
                self.assets.background_problem('loading::A',refresh=True)
                self.assertTrue(eventually(lambda:'loading::A' not in self.assets._fetches))
                result=self.assets.background_problem('loading::A')
                self.assertTrue(result['statementAvailable']);self.assertNotIn('statementError',result)
                self.assertEqual(retry.call_count,1)

    def test_close_cancels_queued_fetches_and_reclaims_running_worker_threads(self):
        entered=threading.Event();release=threading.Event();self.releases.append(release);calls=[];clients=[]
        def fetch(client,identity,title,url):
            if client.stop.is_set():raise RuntimeError('Fixture GET stopped before network')
            calls.append(identity);clients.append(client)
            if len(calls)>=2:entered.set()
            while not client.stop.is_set() and not release.wait(.005):pass
            raise RuntimeError('Fixture cooperative GET stopped')
        with patch('public_platforms.statement',side_effect=fetch):
            for identity in ('loading::A','loading::C','loading::D','loading::E'):
                self.assets.background_problem(identity)
            self.assertTrue(entered.wait(1))
            executor=self.assets._fetch_executor
            closed=threading.Event()
            thread=threading.Thread(target=lambda:(self.assets.close(),closed.set()),daemon=True);thread.start()
            self.assertTrue(closed.wait(1),'close must stop and join all workers; active clients: '
                            +str(len({id(client) for client in clients})))
            thread.join(1)
            self.assertTrue(all(not worker.is_alive() for worker in executor._threads))
            self.assertEqual(self.assets._fetches,{})
            count=len(calls);self.assertLessEqual(count,2,'queued network requests must be cancelled')
            result=self.assets.background_problem('loading::D',refresh=True)
            self.assertFalse(result['statementLoading']);self.assertEqual(len(calls),count)


class TrainingBackgroundHTTPTests(Fixture):
    def test_background_api_returns_saved_code_and_keeps_workspace_live_until_statement_arrives(self):
        server=backend.create_server(data_file=self.root/'absent.md',data_root=self.root/'imports',
                                     library_file=self.library.path,training_file=self.root/'personal.sqlite3',
                                     assets=self.assets,require_account=False,integration_auto_start=False)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();self.servers.append((server,thread))
        server.training.start_training('loading::A');server.training.save_draft('loading::A','// saved before network\nint main() { return 0; }')
        def get(path):
            connection=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=1)
            try:
                connection.request('GET',path);response=connection.getresponse();body=json.loads(response.read())
                self.assertEqual(response.status,200,body);return body
            finally:connection.close()
        entered,release,calls,fetch=self.slow_statement()
        with patch('public_platforms.statement',side_effect=fetch):
            first=get('/api/problem?'+urlencode({'id':'loading::A','background':1}))
            self.assertTrue(entered.wait(1));self.assertFalse(release.is_set())
            self.assertIn('saved before network',first['draft']);self.assertTrue(first['statementLoading'])
            self.assertFalse(first['statementAvailable']);self.assertEqual(first['samples'],[])
            workspace=get('/api/workspace')
            self.assertIn('loading::A',[row['id'] for row in workspace['training']])
            second=get('/api/problem?'+urlencode({'id':'loading::B','background':1}))
            self.assertTrue(second['statementAvailable']);self.assertIn('Read two integers',second['markdown'])
            server.training.save_draft('loading::A','// newer code while original site is slow')
            pending=self.assets._fetches['loading::A']
            release.set()
            self.assertIsNone(pending.result(timeout=15))
            self.assertTrue(self.assets.problem('loading::A',fetch=False)['statementAvailable'])
            loaded=get('/api/problem?'+urlencode({'id':'loading::A','background':1}))
            self.assertEqual(loaded['draft'],'// newer code while original site is slow')
            self.assertTrue(loaded['statementAvailable']);self.assertFalse(loaded.get('statementLoading',False))
            self.assertEqual(calls,['loading::A'])


class CatalogueByteResponseTests(Fixture):
    def test_write_during_rebuild_returns_newly_read_view_instead_of_old_cached_bytes(self):
        with closing(sqlite3.connect(self.library.path)) as writer:
            writer.execute('PRAGMA journal_mode=WAL')
            def update(title):
                encoded=json.loads(writer.execute('SELECT encoded FROM problems WHERE id=?',('loading::A',)).fetchone()[0])
                encoded['title']=title
                writer.execute('UPDATE problems SET encoded=? WHERE id=?',(json.dumps(encoded,ensure_ascii=False),'loading::A'))
                writer.commit()
            for compact in (False,True):
                with self.subTest(compact=compact):
                    update('Baseline before rebuild '+str(compact))
                    baseline=json.loads(self.store.data_response_bytes(compact=compact))
                    update('First external change '+str(compact))
                    build=self.store._catalog_rows
                    def write_after_read():
                        rows=build();update('Second change while rebuilding '+str(compact));return rows
                    with patch.object(self.store,'_catalog_rows',side_effect=write_after_read) as rebuild:
                        raced=json.loads(self.store.data_response_bytes(compact=compact))
                    self.assertEqual(rebuild.call_count,1)
                    self.assertEqual(raced['rows'][0]['title'],'First external change '+str(compact))
                    self.assertNotEqual(raced['revision'],baseline['revision'])
                    current=json.loads(self.store.data_response_bytes(compact=compact))
                    self.assertEqual(current['rows'][0]['title'],'Second change while rebuilding '+str(compact))
                    self.assertNotEqual(current['revision'],raced['revision'])

    def test_full_and_compact_warm_bytes_skip_full_decode_and_reencode_and_use_current_token(self):
        full=json.loads(self.store.data_response_bytes())
        compact=json.loads(self.store.data_response_bytes(compact=True))
        self.assertEqual([row['id'] for row in full['rows']],[row['id'] for row in compact['rows']])
        original_loads=json.loads;original_dumps=json.dumps;old_token=full['token']
        def guarded_loads(value,*args,**kwargs):
            if value is self.store._data_json or value is self.store._compact_json:
                raise AssertionError('warm catalogue bytes must not decode the full object graph')
            return original_loads(value,*args,**kwargs)
        def guarded_dumps(value,*args,**kwargs):
            if isinstance(value,dict) and 'rows' in value:
                raise AssertionError('warm catalogue bytes must not reserialize all rows')
            return original_dumps(value,*args,**kwargs)
        self.store.token='new-account-token-"quoted"-中文'
        with patch.object(self.store,'data',side_effect=AssertionError('warm bytes must reuse the catalogue')), \
             patch.object(store_module.json,'loads',side_effect=guarded_loads), \
             patch.object(store_module.json,'dumps',side_effect=guarded_dumps):
            responses=[self.store.data_response_bytes(compact=small) for small in (False,True,False,True)]
        for raw in responses:
            value=json.loads(raw);self.assertEqual(value['token'],self.store.token)
            self.assertNotIn(old_token.encode(),raw)
            self.assertEqual(value['revision'],full['revision'])
        disk=load_document(self.library.path.with_name('tb-catalog-cache.json'),{})
        cached=json.loads(disk['catalog']);self.assertNotIn('token',cached);self.assertNotIn('today',cached)

    def test_external_wal_commit_invalidates_full_and_compact_without_losing_identity_or_tooltips(self):
        with closing(sqlite3.connect(self.library.path)) as writer:
            writer.execute('PRAGMA journal_mode=WAL');writer.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            before=json.loads(self.store.data_response_bytes())
            self.store.data_response_bytes(compact=True)
            identity='loading::B'
            previous=next(row for row in before['rows'] if row['id']==identity)
            encoded=json.loads(writer.execute('SELECT encoded FROM problems WHERE id=?',(identity,)).fetchone()[0])
            encoded.update(title='Changed by an external WAL writer',difficulty=1700,difficultyBand=[1700,1700],
                           difficultyEvidence=['https://codeforces.com/api/problemset.problems','fresh exact official evidence'])
            writer.execute('UPDATE problems SET encoded=? WHERE id=?',(json.dumps(encoded,ensure_ascii=False),identity));writer.commit()
            self.assertTrue(Path(str(self.library.path)+'-wal').exists())
            after_full=json.loads(self.store.data_response_bytes())
            after_compact=json.loads(self.store.data_response_bytes(compact=True))
            self.assertNotEqual(after_full['revision'],before['revision'])
            self.assertEqual(after_full['revision'],after_compact['revision'])
            self.assertEqual([row['id'] for row in before['rows']],[row['id'] for row in after_compact['rows']])
            for response in (after_full,after_compact):
                changed=next(row for row in response['rows'] if row['id']==identity)
                self.assertEqual(changed['title'],encoded['title']);self.assertEqual(changed['difficulty'],1700)
                for key in ('url','contest','problem','tags','knowledgeCategories','contestDate','startedAt','endedAt',
                            'difficultySource','difficultyConfidence','difficultyEstimated'):
                    self.assertEqual(changed[key],previous[key],key)
                self.assertEqual(changed['difficultyBand'],[1700,1700])
                self.assertEqual(changed['difficultyEvidence'],encoded['difficultyEvidence'])
            self.assertNotIn('knowledgeAnalysis',after_compact['rows'][0])


if __name__=='__main__':unittest.main()
