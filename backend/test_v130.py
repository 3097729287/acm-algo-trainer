"""New flows use disposable personal stores and synthetic browser receipts."""
import datetime as dt
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from training import TrainingService, ServiceError, UTC
from test_training import Library, Assets, Judge as FixtureJudge
from test_judge import FixtureAssets
from judge import Judge
from external_browser import ExternalBrowserBridge
from admin import controls

class WorkbenchUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='tb-v130-')
        self.root=Path(self.temporary.name)
        self.library=Library()
        self.clock=dt.datetime(2026,10,21,16,0,tzinfo=UTC)
        self.user=TrainingService(self.library,self.root/'user'/'personal.sqlite3',assets=Assets(self.library),judge=FixtureJudge(),clock=lambda:self.clock)
        self.admin=TrainingService(self.library,self.root/'admin'/'personal.sqlite3',assets=Assets(self.library),judge=FixtureJudge(),clock=lambda:self.clock,admin_mode=True)
    def tearDown(self):
        self.admin.close();self.user.close();self.temporary.cleanup()
    def test_admin_controls_are_isolated_and_do_not_forge_user_records(self):
        with self.assertRaises(ServiceError) as error:controls(self.user,{'level':100,'tier':9,'allAchievements':True})
        self.assertEqual(error.exception.status,404)
        before=self.user.insights()
        controls(self.admin,{'level':42,'tier':6,'allAchievements':True})
        value=self.admin.insights()
        self.assertEqual(value['growth']['level'],42)
        self.assertEqual(value['growth']['ranked']['badge'],'tier-6')
        self.assertTrue(all(item['unlocked'] for item in value['achievements']))
        self.assertEqual(len(value['titles']),10)
        self.assertEqual(self.user.insights()['growth']['level'],before['growth']['level'])
        self.assertEqual(self.admin.connection.execute('SELECT COUNT(*) FROM submissions').fetchone()[0],0)
        with patch.object(self.admin.leaderboard,'_request',side_effect=AssertionError('admin cloud access')):
            self.admin.leaderboard.queue_sync(force=True)
    def test_python_draft_language_survives_reopen_and_old_drafts_default_to_cpp(self):
        identity=self.library.rows[0]['id']
        self.user.save_draft(identity,'print(3)','',language='python3')
        self.assertEqual(self.user.problem(identity)['draftLanguage'],'python3')
        self.user.close()
        self.user=TrainingService(self.library,self.root/'user'/'personal.sqlite3',assets=Assets(self.library),judge=FixtureJudge(),clock=lambda:self.clock)
        self.assertEqual(self.user.problem(identity)['draft'],'print(3)')
        self.assertEqual(self.user.problem(identity)['draftLanguage'],'python3')
        self.assertEqual(self.user.problem(self.library.rows[1]['id'])['draftLanguage'],'cpp17')
    def test_export_retains_python_metadata_but_excludes_admin_controls(self):
        from data_export import export_data
        identity=self.library.rows[0]['id']
        self.user.save_draft(identity,'print(3)',language='python3')
        exported=export_data(self.user)
        metadata=exported['tables']['account_preferences']
        self.assertTrue(any(row['key'].startswith('draft-language:') and row['value']=='python3' for row in metadata))
        controls(self.admin,{'level':42,'tier':6,'allAchievements':True})
        self.assertFalse(any(row['key'].startswith('admin-') for row in export_data(self.admin)['tables']['account_preferences']))

    def test_streak_uses_beijing_midnight_and_excludes_runs_and_drafts(self):
        identity=self.library.rows[0]['id']
        self.user.save_draft(identity,'draft only')
        self.assertEqual(self.user.workspace()['summary']['streak'],0)
        with self.user._write() as db:
            for index,(at,mode) in enumerate([('2026-10-20T15:59:59Z','submit'),('2026-10-20T16:00:00Z','submit'),('2026-10-21T16:00:00Z','run')]):
                db.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope) VALUES(?,?,?,?,?,?,'AC','official')",(str(index),identity,mode,'code',at,at))
        self.assertEqual(self.user.workspace()['summary']['streak'],2)
        self.clock+=dt.timedelta(days=1)
        self.assertEqual(self.user.workspace()['summary']['streak'],0)
    def test_auto_close_requires_durable_receipt_and_display_ack(self):
        closed=[]
        browser=SimpleNamespace(close_page=lambda target:closed.append(target) or True)
        bridge=ExternalBrowserBridge(self.root/'browser',browser_process=browser,on_receipt=lambda *_:False)
        bridge.sessions['s']={'sessionId':'s','target':'owned-tab','status':'submitted','autoClose':True,'intent':False}
        bridge._update('s',{'status':'finished','verdict':'WA','submissionId':'123'})
        self.assertFalse(bridge.acknowledge('s')['closed'])
        self.assertEqual(closed,[])
        bridge.on_receipt=lambda *_:True
        bridge._update('s',{'status':'finished','verdict':'WA','submissionId':'123'})
        self.assertEqual(closed,[])
        self.assertTrue(bridge.acknowledge('s')['closed'])
        self.assertTrue(bridge.acknowledge('s')['closed'])
        self.assertEqual(closed,['owned-tab'])
        bridge.on_closing()

@unittest.skipUnless(os.name=='nt','Windows Job resource limits')
class PythonRunnerTests(unittest.TestCase):
    def execute(self,code,**options):
        with tempfile.TemporaryDirectory(prefix='Python 中文 空格 ') as temporary:
            runner=Judge(FixtureAssets(time_ms=300,memory_mb=64),temporary)
            runner.python=os.environ.get('TB_TEST_PYTHON3') or runner.python
            result=runner.execute('fixture',code,language='python3',**options)
            self.assertEqual(list(Path(temporary).iterdir()),[])
            return result
    def test_sample_input_and_unicode_output(self):
        result=self.execute('a,b=map(int,input().split())\nprint(a+b)')
        self.assertEqual(result['verdict'],'SAMPLE_PASS',result)
        result=self.execute('print("中文")',mode='run',input_text='',sample_run=False)
        self.assertEqual(result['output'].strip(),'中文')
        self.assertEqual(result['verdict'],'RUN_OK')
    def test_python_failure_modes(self):
        self.assertEqual(self.execute('if True print(1)')['verdict'],'CE')
        self.assertEqual(self.execute('raise RuntimeError("fixture")')['verdict'],'RE')
        self.assertEqual(self.execute('while True: pass')['verdict'],'TLE')
        self.assertEqual(self.execute('print(0)')['verdict'],'WA')
