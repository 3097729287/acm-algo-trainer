"""Actual local HTTP, retained private fixtures, real template judge; no cloud writes."""
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch
import uuid

import backend
from library import LibraryDatabase
from test_library import record
from test_recycle_policy import retained_fixture
from test_training import Assets, Judge, Clock


class AdminScenarioTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(retained_fixture('admin-scenarios').name)
        self.library = LibraryDatabase(self.root / 'library.sqlite3')
        self.library.import_records([record()], {}, {})
        self.judge, self.clock = Judge(), Clock()
        self.start()

    def start(self, admin=True):
        self.server = backend.create_server(admin_mode=admin, require_account=False,
            training_file=self.root/'personal.sqlite3', library_file=self.library.path,
            data_file=self.root/'absent.md', data_root=self.root, integration_auto_start=False,
            backup_dir=self.root/'backups', assets=Assets(None), judge=self.judge, clock=self.clock)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.token = self.server.store.token

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(3)

    def tearDown(self):
        self.judge.release.set();self.stop()

    def call(self, path, body=None, token=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=6)
        connection.request('GET' if body is None else 'POST', path,
            body=None if body is None else json.dumps(body).encode(), headers={
                'Content-Type':'application/json','X-TB-Token':self.token if token is None else token})
        response=connection.getresponse();value=json.loads(response.read());status=response.status
        connection.close();return status,value

    def account(self):
        status, value = self.call('/api/account');self.assertEqual(status, 200, value)
        self.token=value['token'];return value

    def fresh(self, identity=None):
        identity=identity or str(uuid.uuid4())
        status,value=self.call('/api/admin/scenario',{'action':'fresh','requestId':identity})
        self.assertEqual(status,200,value);self.account();return identity

    def protected(self, service):
        return {name:[tuple(row) for row in service.connection.execute('SELECT * FROM '+name+' ORDER BY rowid')]
            for name in ['training','drafts','submissions','ranking_profile','daily_missions','achievement_xp_claims']}

    def test_identity_matches_confirmed_growth_and_level_changes_are_readable(self):
        owner=self.account()['account']['userId']
        self.assertNotEqual(owner,'local-admin')
        for level in (1,7,42,100):
            self.assertEqual(self.call('/api/admin',{'level':level,'tier':2,'allAchievements':False})[0],200)
            status,value=self.call('/api/insights');self.assertEqual(status,200,value)
            self.assertEqual(value['growth']['level'],level)
            self.assertEqual(value['growth']['authority']['owner'],owner)
            self.assertTrue(value['growth']['confirmed'])

    def test_reset_creates_an_empty_journal_and_retains_maintenance_and_prior_drafts(self):
        base=self.server.training;base.save_draft('fixture::A','private maintenance code')
        before=self.protected(base);old_token=self.token;identity=self.fresh()
        self.assertNotEqual(self.server.training,base)
        self.assertEqual(self.protected(base),before)
        self.assertTrue(self.account()['scenario']['newAccount'])
        self.assertEqual(self.call('/api/workspace')[1]['summary']['total'],0)
        growth=self.call('/api/insights')[1]['growth']
        self.assertEqual(growth['level'],1);self.assertFalse(growth['rankedEligible'])
        self.assertTrue(growth['experienceChallenge']['eligible'])
        self.assertEqual(self.call('/api/draft',{'id':'fixture::A','code':'stale'},token=old_token)[0],403)
        self.server.training.save_draft('fixture::A','sandbox draft')
        self.assertEqual(self.call('/api/admin/scenario',{'action':'maintenance'})[0],200);self.account()
        self.assertIs(self.server.training,base);self.assertEqual(self.protected(base),before)
        self.assertEqual(self.call('/api/admin/scenario',{'action':'fresh','requestId':identity})[0],200)
        self.assertIs(self.server.training,base,'A delayed duplicate reset cannot switch away from a later choice')
        self.assertEqual(self.call('/api/admin/scenario',{'action':'select','id':identity})[0],200);self.account()
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'sandbox draft')
        self.stop();self.start()
        self.assertEqual(self.account()['scenario']['active'],identity)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'sandbox draft')
        self.assertEqual(self.protected(self.server.admin_scenarios.original),before)

    def test_reset_waits_for_inflight_work_and_rechecks_the_old_write_token(self):
        manager=self.server.admin_scenarios;base=self.server.training;identity=str(uuid.uuid4())
        with ThreadPoolExecutor(1) as pool:
            with manager.request_context():
                request=pool.submit(self.call,'/api/admin/scenario',{'action':'fresh','requestId':identity})
                time.sleep(.1);self.assertFalse(request.done())
                base.save_draft('fixture::A','saved before the switch')
            self.assertEqual(request.result()[0],200)
        self.account();self.assertEqual(base.problem('fixture::A')['draft'],'saved before the switch')
        self.assertEqual(self.server.training.connection.execute('SELECT COUNT(*) FROM drafts').fetchone()[0],0)

    def test_invalid_user_and_bounded_recycle_paths_do_not_delete_any_original(self):
        identity=self.fresh();folder=self.server.admin_scenarios.root/identity
        self.assertEqual(self.call('/api/admin/scenario',{'action':'recycle','id':identity})[0],409)
        self.call('/api/admin/scenario',{'action':'maintenance'});self.account()
        with patch('system_recycle.recycle',return_value=False),patch('shutil.rmtree',side_effect=AssertionError('permanent delete')),patch('pathlib.Path.unlink',side_effect=AssertionError('permanent delete')):
            self.assertEqual(self.call('/api/admin/scenario',{'action':'recycle','id':identity})[0],409)
        self.assertTrue((folder/'tb-personal.sqlite3').is_file())
        self.assertEqual(len(self.call('/api/admin/scenario')[1]['workspaces']),1)
        self.assertEqual(self.call('/api/admin/scenario',{'action':'fresh','requestId':'../original'})[0],400)
        for _ in range(4):self.fresh()
        self.assertEqual(self.call('/api/admin/scenario',{'action':'fresh','requestId':str(uuid.uuid4())})[0],409)
        self.assertEqual(len(list(self.server.admin_scenarios.root.iterdir())),5)
        self.stop();self.start(admin=False)
        self.assertEqual(self.call('/api/admin/scenario')[0],404)
        self.assertEqual(self.call('/api/admin/scenario',{'action':'fresh','requestId':str(uuid.uuid4())})[0],404)

    def test_fresh_scenario_reaches_level_six_only_after_the_real_prefix_judge(self):
        base=self.server.training;before=self.protected(base);self.fresh();service=self.server.training
        from experience_challenge import PROBLEMS,update
        from judge import Judge as ActualJudge
        from template_drills import bundle
        problem=record(PROBLEMS[1], 'Prefix fixture')
        problem[0]['场次']='模板练习';problem[1].update(contest='模板练习',url='',templatePractice=True)
        self.library.import_records([problem],{}, {})
        original=service.assets.problem
        service.assets.problem=lambda identity:dict(original(identity),judge={'scope':'template','cases':24},templatePractice=True)
        service.assets.bundle=bundle;service.judge=ActualJudge(service.assets,self.root/'native-judge')
        with patch('experience_challenge.secrets.choice',return_value=PROBLEMS[1]):
            update(service,{'action':'choose','choice':'experienced'})
        code='import sys\nv=list(map(int,sys.stdin.buffer.read().split()));n,q=v[:2];p=[0]\nfor x in v[2:2+n]:p.append(p[-1]+x)\nprint(*(p[v[i+1]]-p[v[i]] for i in range(2+n,len(v),2)))\n'
        answer=service.submit(PROBLEMS[1],code,language='python3');deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            result=service.submission(answer['submission']['id'])['submission']
            if result['finishedAt']:break
            time.sleep(.01)
        self.assertEqual((result['verdict'],result['passed'],result['total']),('AC',24,24))
        for _ in range(2):
            growth=service.insights()['growth'];self.assertEqual((growth['level'],growth['totalXp']),(6,1500))
        self.assertEqual(self.protected(base),before)
        self.assertEqual(service.connection.execute('SELECT COUNT(*) FROM official_first_xp_awards').fetchone()[0],0)
        self.assertEqual(self.call('/api/admin',{'level':2,'tier':0,'allAchievements':False})[0],200)
        self.assertEqual(service.insights()['growth']['level'],2)


if __name__=='__main__':unittest.main()
