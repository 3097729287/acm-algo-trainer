import json
import sqlite3
import threading
import unittest
from types import SimpleNamespace
from lecture_queue import project, foundation_ids
from submission_history import preserve, KEY


class LearningGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript('''CREATE TABLE training(id TEXT,active_at TEXT);
            CREATE TABLE drafts(problem_id TEXT,saved_at TEXT); CREATE TABLE submissions(problem_id TEXT,submitted_at TEXT);
            CREATE TABLE account_preferences(key TEXT,value TEXT,updated_at TEXT);''')
        self.training = SimpleNamespace(connection=self.db, lock=threading.RLock(),
            _ranking_profile=lambda:{'user_id':'owner-a'})

    def test_new_account_starts_with_ordered_language_route_and_no_problem_lectures(self):
        rows=[{'id':identity} for identity in foundation_ids()]+[{'id':'unseen','sourceProblemIds':['problem-a']}]
        before=self.db.total_changes
        result=project(self.training,{'lectures':rows},SimpleNamespace(references={}))
        self.assertEqual(len(result['learningQueue']['foundationIds']),23)
        self.assertEqual(result['learningQueue']['foundationIds'][:3],['lecture:foundation-io-basics','lecture:foundation-basic-arithmetic','lecture:foundation-integer'])
        self.assertEqual(result['learningQueue']['encounteredIds'],[])
        self.assertEqual(result['lectures'],rows)
        self.assertEqual(self.db.total_changes,before)

    def test_reached_problem_keeps_own_and_explicit_reference_lessons_without_exposing_code(self):
        self.db.execute('INSERT INTO training VALUES(?,?)',('problem-a','2026-11-02'))
        self.db.execute('INSERT INTO drafts VALUES(?,?)',('older-problem','2026-11-01'))
        entries=[{'id':'own','sourceProblemIds':['problem-a']},{'id':'unseen','sourceProblemIds':['problem-b']}]
        result=project(self.training,{'lectures':entries},SimpleNamespace(references={'problem-a':['shared'],'older-problem':['restored']}))
        self.assertEqual(result['learningQueue']['encounteredIds'],['restored','shared','own'])
        self.assertNotIn('code',result['learningQueue'])

    def test_explicit_history_cutoff_survives_an_older_device_and_preserves_new_records(self):
        marker={'version':1,'before':'2026-09-30T16:00:00Z','date':'2026-10-01','timezone':'Asia/Shanghai'}
        self.db.execute('INSERT INTO account_preferences VALUES(?,?,?)',(KEY,json.dumps(marker),'now'))
        old={'id':'may','submitted_at':'2026-05-13T08:48:00Z'}
        new={'id':'october','submitted_at':'2026-09-30T16:00:00Z'}
        source={'tables':{'submissions':[old,new], 'account_preferences':[{'key':'unrelated','value':'preserved'}]}}
        result,changed=preserve(self.training,source)
        self.assertTrue(changed)
        self.assertEqual(result['tables']['submissions'],[new])
        self.assertEqual(source['tables']['submissions'],[old,new])
        self.assertIn({'key':'unrelated','value':'preserved'},result['tables']['account_preferences'])
        self.assertEqual(next(row for row in result['tables']['account_preferences'] if row['key']==KEY)['value'],json.dumps(marker))

    def test_foreign_owner_marker_never_filters_this_accounts_records(self):
        self.db.execute('INSERT INTO account_preferences VALUES(?,?,?)',(KEY,json.dumps({'version':1,'owner':'other','before':'2026-10-01T00:00:00Z'}),'now'))
        source={'tables':{'submissions':[{'id':'kept','submitted_at':'2026-05-01T00:00:00Z'}]}}
        result,changed=preserve(self.training,source)
        self.assertFalse(changed)
        self.assertEqual(result,source)
