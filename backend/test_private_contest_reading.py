"""Registered-source reads use isolated browser/page fixtures and account SQL."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from contest_calendar import event
from contest_imports import import_contest
from integrations import IntegrationService,PublicClient
from library import LibraryDatabase
from persistence import load_document
from private_contest_reading import AccountContestImport,private_rows,remember
from statement_access import StatementAccessRequired,nowcoder_access_notice
from store import Store
from test_contest_calendar_live import COMPLETE
from test_library import record
from training import TrainingService

GATE='<title>牛客网-报名后才能查看题目</title><div class="null-tip"> 报名后才能查看题目</div>'
HTML='<div class="subject-describe">registered-content</div>'

class PrivateContestTests(unittest.TestCase):
    def setUp(self):
        parent=Path(__file__).resolve().parents[1]/'.backups/feedback-1435/test-state';parent.mkdir(parents=True,exist_ok=True)
        self.root=Path(tempfile.mkdtemp(prefix='account-reading-',dir=parent))
        library=LibraryDatabase(self.root/'library.sqlite3');library.import_records([record()],{}, {})
        self.store=Store(data_file=self.root/'absent.md',library_file=library.path)
        payload={'code':0,'data':{'data':[{'index':'A','title':'A task'},{'index':'B','title':'B task'}],'basicInfo':{'contestId':142559,'problemCount':2}}}
        def transport(url,headers):return (json.dumps(payload).encode() if 'problem-list?' in url else GATE.encode(),None)
        self.public=IntegrationService(self.store,self.root/'public',client=PublicClient(self.root/'http',transport=transport,spacing=0),auto_start=False)
        self.store.extensions=self.public
        self.owner=TrainingService(self.store,self.root/'owner/personal.sqlite3',backup_dir=self.root/'owner/backups')
        self.other=TrainingService(self.store,self.root/'other/personal.sqlite3',backup_dir=self.root/'other/backups')
        self.current=self.owner
        self.row=event('nowcoder',142559,'周赛168',1800000000,1800007200,'https://ac.nowcoder.com/acm/contest/142559')
        self.reads=[]
    def tearDown(self):
        self.owner.close();self.other.close();self.public.close()
        # Retained for the workspace's reviewed Windows Recycle Bin cleanup.
    def context(self,reader=None):
        def read(url,owner):self.assertIs(owner,self.current);self.reads.append(url);return HTML
        def save(owner,rows,statements):
            if owner is not self.current:raise RuntimeError('account switched')
            remember(owner,rows,statements)
        return AccountContestImport(self.public,self.owner,self.row,reader or read,lambda owner:owner is self.current,save)
    def statement(self,client,identity,title,url):
        self.assertIn('registered-content',client.text(url))
        return dict(COMPLETE,id=identity,title=title,url=url,limits={'timeMs':2000,'memoryMb':256})
    def test_registered_read_is_available_only_to_the_requesting_account(self):
        context=self.context()
        with patch('public_platforms.statement',side_effect=self.statement):result=import_contest(context,self.row)
        self.assertEqual((result['status'],result['ready']),('ready',2));self.assertEqual(len(self.reads),2)
        identity=result['entryId']
        self.assertFalse(self.public.state['rows'][identity]['catalogContentReady'])
        public_path=self.public.state_dir/'statements'/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
        self.assertFalse(load_document(public_path,{}).get('statementAvailable'))
        self.assertNotIn('registered-content',self.store.data_response_bytes().decode())
        self.assertTrue(self.owner._row(identity)['catalogContentReady']);self.assertFalse(self.owner._row(identity)['catalogHidden'])
        self.assertTrue(self.owner._asset_library().problem(identity,fetch=False)['statementAvailable'])
        self.assertFalse(self.other._asset_library().problem(identity,fetch=False)['statementAvailable'])
        self.assertEqual(private_rows(self.other),[])
        self.assertEqual(len(private_rows(self.owner)),2)
        self.assertTrue(self.owner.portable_problem(identity)['statement']['accountReading'])
    def test_saved_account_statement_survives_an_unavailable_browser(self):
        with patch('public_platforms.statement',side_effect=self.statement):first=import_contest(self.context(),self.row)
        with patch('public_platforms.statement',side_effect=AssertionError('cached statements must remain offline')):
            second=import_contest(self.context(lambda *_:self.fail('browser must not open')),self.row)
        self.assertEqual(second['readyProblemIds'],first['readyProblemIds'])
    def test_account_switch_discards_a_late_original_page(self):
        def late(url,owner):self.current=self.other;return HTML
        with patch('public_platforms.statement',side_effect=self.statement),self.assertRaises(RuntimeError):import_contest(self.context(late),self.row)
        self.assertEqual(private_rows(self.owner),[]);self.assertEqual(private_rows(self.other),[])
    def test_registration_denial_never_sets_entry_ready(self):
        def denied(*_):raise StatementAccessRequired('请先在原站报名，再重试题面')
        context=self.context(denied)
        with patch('public_platforms.statement',side_effect=self.statement):result=import_contest(context,self.row)
        self.assertFalse(result['entryReady']);self.assertEqual(result['ready'],0);self.assertTrue(context.access_required)
        self.assertEqual(private_rows(self.owner),[])
    def test_current_account_can_enter_with_A_while_B_waits(self):
        def read(url,owner):
            if url.endswith('/B'):raise StatementAccessRequired('请先在原站报名，再重试题面')
            return HTML
        with patch('public_platforms.statement',side_effect=self.statement):result=import_contest(self.context(read),self.row)
        self.assertEqual(result['ready'],1);self.assertTrue(result['entryReady'])
        now=dt.datetime.fromtimestamp(1800000030,dt.timezone.utc)
        self.owner.clock=lambda:now
        trusted={**self.row,'contest':'周赛168',**{key:result[key] for key in ('problemIds','entryId')}}
        contest=self.owner.start_calendar_contest(trusted)['contest']
        self.assertEqual(contest['total'],2)
        self.assertEqual(dt.datetime.fromisoformat(contest['deadline'].replace('Z','+00:00')).timestamp(),1800007200)

class NativeContestReadingTests(unittest.TestCase):
    def reader(self,*,owner='12345',url='https://ac.nowcoder.com/acm/contest/142559/A',bound=True,html=HTML):
        from contest_reading import ContestReading
        expected=object();self.closed=[];self.calls=[]
        value={'url':url,'ready':'complete','identity':{'platform':'牛客','state':'logged_in','owner':owner,'url':url},'html':html}
        class Page:
            def evaluate(page,script):self.calls.append('evaluate');return value
            def close(page):self.calls.append('disconnect')
        browser=SimpleNamespace(new_probe_page=lambda target:{'id':'owned-hidden','webSocketDebuggerUrl':'ws://127.0.0.1/fixture'},close_page=lambda identity:self.closed.append(identity))
        bridge=SimpleNamespace(browser=browser,stopping=threading.Event())
        reader=ContestReading(bridge,lambda:expected,lambda *_:bound,page_factory=lambda _:Page(),timeout=.1)
        return reader,expected
    def test_native_read_checks_identity_and_closes_only_its_hidden_target(self):
        reader,owner=self.reader()
        self.assertEqual(reader('https://ac.nowcoder.com/acm/contest/142559/A',owner),HTML)
        self.assertEqual(self.closed,['owned-hidden']);self.assertEqual(self.calls,['evaluate','disconnect'])
    def test_wrong_bound_account_and_registration_gate_are_not_read(self):
        for options in ({'bound':False},{'html':GATE},{'owner':''}):
            with self.subTest(options=options):
                reader,owner=self.reader(**options)
                with self.assertRaises(StatementAccessRequired):reader('https://ac.nowcoder.com/acm/contest/142559/A',owner)
                self.assertEqual(self.closed,['owned-hidden'])
    def test_redirect_to_another_task_is_rejected(self):
        reader,owner=self.reader(url='https://ac.nowcoder.com/acm/contest/142559/B')
        with self.assertRaises(ValueError):reader('https://ac.nowcoder.com/acm/contest/142559/A',owner)
    def test_notice_is_not_inferred_from_ordinary_statement_prose(self):
        self.assertTrue(nowcoder_access_notice(GATE))
        self.assertFalse(nowcoder_access_notice('<div class="subject-describe">报名后才能查看题目，是本题的输出字符串。</div>'))
