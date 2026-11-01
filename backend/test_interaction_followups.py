"""Fast local claims and live A-first entry, using only disposable fixtures."""
import datetime as dt
import json
import hashlib
from pathlib import Path
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

from training import ServiceError
import test_training as fixtures
import test_account_sync as cloud_fixtures


class InteractionFollowupTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def test_displayed_reward_claim_skips_expensive_insights_and_is_idempotent(self):
        self.accept()
        first=next(item for item in self.service.insights()['achievements'] if item['id']=='official-1')
        with patch.object(self.service,'_compute_insights',side_effect=AssertionError('must not rebuild radar')):
            with ThreadPoolExecutor(max_workers=6) as pool:
                results=list(pool.map(lambda _:self.service.claim_achievement('official-1',compact=True),range(6)))
        self.assertEqual(sum(item['awardedXp'] for item in results),25)
        self.assertTrue(all(item['achievement']['rewardClaimed'] for item in results))
        self.assertTrue(all(item['achievement']['unlockedAt']==first['unlockedAt'] for item in results))
        self.assertTrue(all(item['achievement']['earnedRewardXp']==25 for item in results))
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0],1)

    def test_compact_unearned_or_malformed_completion_cannot_award(self):
        with self.service._write() as connection:
            connection.execute('INSERT INTO account_preferences VALUES(?,?,?)',('achievement-unlock:official-100','{}',self.clock().isoformat()))
        for identity in ('official-1','official-100','unknown'):
            with self.subTest(identity=identity),self.assertRaises(ServiceError):
                self.service.claim_achievement(identity,compact=True)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0],0)

    def test_live_freezes_roster_without_fetching_B_and_preserves_deadline(self):
        rows=self.library.rows
        for index,row in enumerate(rows):row['catalogContentReady']=index==0
        began=self.clock()-dt.timedelta(minutes=25);ended=self.clock()+dt.timedelta(minutes=95)
        event={'id':'codeforces:123','url':'https://codeforces.com/contest/123','contest':'fixture',
               'startAt':began.isoformat(),'endAt':ended.isoformat(),'problemIds':[row['id'] for row in rows],
               'entryId':rows[0]['id'],'partial':True}
        def ready(selected,official=False):
            self.assertEqual([row['id'] for row in selected],[rows[0]['id']],'Only A is validated before entry')
            return [dict(selected[0],judgeScope='official')]
        with patch.object(self.assets,'candidates',side_effect=ready),patch.object(self.assets,'problem',side_effect=AssertionError('no network statement fetch')):
            result=self.service.start_calendar_contest(event)['contest']
        self.assertEqual(result['name'],'fixture')
        self.assertEqual(result['total'],8)
        self.assertEqual(dt.datetime.fromisoformat(result['deadline'].replace('Z','+00:00')),ended)
        self.assertEqual([row['statementReady'] for row in result['slots']],[True]+[False]*7)
        self.library.rows[1]['catalogContentReady']=True
        self.assertTrue(self.service.contest(result['id'])['contest']['slots'][1]['statementReady'])
        self.service.save_draft(rows[0]['id'],'A code',result['id'])
        self.service.save_draft(rows[1]['id'],'B code',result['id'])
        with self.assertRaises(ServiceError):self.service.start_calendar_contest(event)

    def test_history_removes_replay_prefix_only_with_verified_live_timestamps(self):
        plan=self.service.preview_contest({'count':1,'duration':120,'min':1000,'max':2100})['plan']
        result=self.service.start_contest({'ids':[slot['id'] for slot in plan['slots']],'duration':120,'name':'重现赛 · fixture'})['contest']
        row=next(row for row in self.library.rows if row['id']==result['slots'][0]['id'])
        self.assertEqual(self.service.contest(result['id'])['contest']['name'],'重现赛 · fixture')
        row.update(startedAt=(self.clock()-dt.timedelta(minutes=1)).isoformat(),endedAt=(self.clock()+dt.timedelta(minutes=119)).isoformat())
        self.assertEqual(self.service.contest(result['id'])['contest']['name'],'fixture')
        row['endedAt']=(self.clock()-dt.timedelta(seconds=1)).isoformat()
        self.assertEqual(self.service.contest(result['id'])['contest']['name'],'重现赛 · fixture')
        # Display adaptation never rewrites historical scoring/ownership.
        self.assertEqual(self.service.connection.execute('SELECT name FROM contests').fetchone()[0],'重现赛 · fixture')


class IncrementalPublicationTests(unittest.TestCase):
    def test_real_local_catalog_publishes_A_while_B_fetch_is_blocked(self):
        from contest_calendar import ContestCalendar,event
        from contest_imports import import_contest
        from integrations import IntegrationService
        from library import LibraryDatabase
        from store import Store
        from training import TrainingService
        from test_library import record
        from test_contest_calendar_live import COMPLETE
        entered=threading.Event();release=threading.Event();values=[]
        class Client:
            def json(self,url):return {'code':0,'data':{'data':[{'index':'B','title':'B task'},{'index':'A','title':'A task'}],'basicInfo':{'contestId':141882,'problemCount':2}}}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);database=LibraryDatabase(root/'library.sqlite3');database.import_records([record()],{}, {})
            store=Store(data_file=root/'absent.md',library_file=database.path)
            service=IntegrationService(store,root/'overlay',client=Client(),auto_start=False);store.extensions=service
            now=1800000030
            calendar=ContestCalendar(root/'calendar',clock=lambda:now,offline=True,importer=lambda item,on_progress=None:import_contest(service,item,on_progress))
            row=event('nowcoder',141882,'小白月赛139',now-30,now+7170,'https://ac.nowcoder.com/acm/contest/141882')
            calendar.providers['nowcoder']={'contests':[row],'checkedAt':now,'status':'ready'}
            calendar.import_running.add(row['id'])
            def statement(client,identity,title,url):
                values.append(identity)
                if identity.endswith('::B'):entered.set();release.wait(5)
                return dict(COMPLETE,id=identity,title=title,url=url)
            training=TrainingService(store,root/'personal.sqlite3',clock=lambda:dt.datetime.fromtimestamp(now,dt.timezone.utc),backup_dir=root/'backups')
            worker=threading.Thread(target=calendar._import,args=(row,))
            try:
                with patch('public_platforms.statement',side_effect=statement):
                    worker.start();self.assertTrue(entered.wait(3))
                    imported=calendar.snapshot()['contests'][0]['import']
                    self.assertEqual(imported['readyProblemIds'],['remote:nowcoder:141882::A'])
                    self.assertEqual(imported['status'],'partial');self.assertTrue(imported['entryReady'])
                    public=training._row('remote:nowcoder:141882::A');self.assertFalse(public.get('catalogHidden'),repr(public))
                    cached=training._asset_library()._cached(public['id']);self.assertTrue(__import__('statement_integrity').content_complete(cached),repr(cached))
                    result=training.start_calendar_contest(calendar.ongoing(row['id']))['contest']
                    self.assertEqual([slot['letter'] for slot in result['slots']],['A','B'])
                    self.assertEqual([slot['statementReady'] for slot in result['slots']],[True,False])
                    release.set();worker.join(5);self.assertFalse(worker.is_alive())
                self.assertEqual(values,['remote:nowcoder:141882::A','remote:nowcoder:141882::B'])
                self.assertEqual(calendar.imports[row['id']]['status'],'ready')
                self.assertTrue(training.contest(result['id'])['contest']['slots'][1]['statementReady'])
            finally:
                release.set();worker.join(5);training.close();calendar.close();service.close()

class MultipleAccountSyncTests(unittest.TestCase):
    setUp=cloud_fixtures.CloudStateTests.setUp
    tearDown=cloud_fixtures.CloudStateTests.tearDown
    start=cloud_fixtures.CloudStateTests.start
    stop=cloud_fixtures.CloudStateTests.stop
    call=cloud_fixtures.CloudStateTests.call
    signup=cloud_fixtures.CloudStateTests.signup
    login=cloud_fixtures.CloudStateTests.login
    other_computer=cloud_fixtures.CloudStateTests.other_computer
    call_other=cloud_fixtures.CloudStateTests.call_other

    def test_two_accounts_two_devices_keep_code_templates_and_pending_preferences_separate(self):
        self.signup();self.assertEqual(self.login()[0],200)
        for name,theme,code in [('account_a','woodfish-neon','// A private source'),('account_b','github-light','// B private source')]:
            if name=='account_b':
                self.assertEqual(self.call('/api/account/logout',{})[0],200)
                self.signup(name,'Account B');self.assertEqual(self.login(name)[0],200)
            self.server.training.save_draft('fixture::A',code)
            self.assertEqual(self.call('/api/preferences',{'preferences':{'editorTheme':theme,'theme':'dark' if name=='account_a' else 'light'}})[0],200)
            status,created=self.call('/api/initial-code/save',{'title':name,'language':'cpp17','code':code+'\nint main() {}'})
            self.assertEqual(status,200,created)
            self.server.accounts.sync_pending(wait=True)
        self.assertEqual(self.call('/api/account/logout',{})[0],200)
        self.assertEqual(self.login()[0],200)
        original=self.server.accounts._remote
        def offline_upload(method,path,*args,**kwargs):
            if method in ('PUT','POST') and ('state' in path or 'chunk' in path):raise ServiceError(503,'isolated offline upload')
            return original(method,path,*args,**kwargs)
        with patch.object(self.server.accounts,'_remote',side_effect=offline_upload):
            self.server.training.save_draft('fixture::A','// A unsent edit')
            with self.assertRaises(ServiceError):self.server.accounts.sync_pending(wait=True)
            self.assertEqual(self.server.training.problem('fixture::A')['draft'],'// A unsent edit')
        self.server.accounts.sync_pending(wait=True)
        self.assertEqual(self.call('/api/account/logout',{})[0],200)
        other=self.other_computer()
        for name,theme,code in [('account_b','github-light','// B private source'),('account_a','woodfish-neon','// A unsent edit')]:
            status,value=self.call_other(other,'/api/account/login',{'loginId':name,'password':'fixture-password'})
            self.assertEqual(status,200,value)
            self.assertEqual(other.training.problem('fixture::A')['draft'],code)
            self.assertEqual(self.call_other(other,'/api/preferences')[1]['preferences']['editorTheme'],theme)
            templates=self.call_other(other,'/api/initial-code')[1]['templates']
            private=[item for item in templates if not item.get('builtin')]
            self.assertEqual([item['title'] for item in private],[name])
            self.assertTrue(all(('A private' if name=='account_a' else 'B private') in item['code'] for item in private))
            self.assertEqual(self.call_other(other,'/api/account/logout',{})[0],200)

if __name__=='__main__':unittest.main()

