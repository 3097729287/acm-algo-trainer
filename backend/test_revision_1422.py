import datetime as dt,json,unittest
from unittest.mock import patch
import test_training as fixtures
from training import iso
from daily_rotation import tasks_for,annotate,record_action
from progression import task_progress,official_first_xp
from preferences import save_preferences,read_preferences
from custom_training_lists import save_list

class DailyVarietyTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def receipt(self,identity='fixture::A'):
        return self.service.record_official({'id':identity,'url':self.assets.problem(identity)['url'],'code':'accepted'},
          {'status':'finished','verdict':'AC','submissionId':str(fixtures._next_official_id()),'acceptedAt':iso(self.clock())})

    def test_rotations_stay_fixed_within_day_and_change_over_dates(self):
        first=tasks_for('2026-10-27','account')
        self.assertEqual(first,tasks_for('2026-10-27','account'))
        self.assertEqual([t['id'] for t in first[:3]],['solve-1','solve-3','independent-2'])
        self.assertEqual(len(first),6);self.assertEqual(len({t['id'] for t in first}),6)
        variants={tuple(t['id'] for t in tasks_for(f'2026-10-{day:02d}','account')[3:]) for day in range(1,28)}
        self.assertGreater(len(variants),10)

    def test_new_only_excludes_yesterdays_problem_after_repeat_ac(self):
        self.receipt();self.clock.advance(days=1);self.receipt();self.receipt('fixture::B')
        day=self.clock().date().isoformat();evidence=self.service._daily_evidence(day)
        task={'kind':'solve','target':3,'newOnly':True}
        self.assertEqual(task_progress(task,evidence,day)[0],1)
        self.assertEqual(task_progress(dict(task,newOnly=False),evidence,day)[0],2)

    def test_actual_preference_changes_and_list_creation_record_actions_once(self):
        save_preferences(self.service,{'preferences':{'theme':'light','favorites':['fixture::A'],'learnedLectures':['foundation:one']}})
        save_preferences(self.service,{'preferences':{'theme':'light','favorites':['fixture::A'],'learnedLectures':['foundation:one']}})
        save_list(self.service,{'title':'自己的路径','problemIds':['fixture::B']})
        day=self.clock().date().isoformat();events=self.service._daily_evidence(day)
        for kind in ['appearance','favorite','learn','create-list']:
            with self.subTest(kind=kind):self.assertEqual(task_progress({'kind':'action','event':kind,'target':2},events,day)[0],1)
        self.assertEqual(read_preferences(self.service)['preferences']['theme'],'light')

    def test_hidden_unselected_mission_cannot_be_claimed_as_a_seventh_task(self):
        visible={task['id'] for task in self.service.daily_tasks(goal_tasks=[])['tasks']}
        self.assertEqual(len(visible),6)
        from daily_rotation import CHALLENGES
        absent=next(task for task in CHALLENGES if task['id'] not in visible)
        with self.service._write() as db:
            db.execute('INSERT INTO daily_missions(day,id,definition) VALUES(?,?,?)',(self.clock().date().isoformat(),absent['id'],json.dumps(absent)))
        self.assertEqual(len(self.service.daily_tasks(goal_tasks=[])['tasks']),6)
        from training import ServiceError
        with self.assertRaises(ServiceError):self.service.claim_daily_task(absent['id'])

    def test_first_ac_xp_remains_difficulty_based_without_regranting_old_solve(self):
        self.assertEqual([official_first_xp(value) for value in [900,1500,1800,2100]],[100,150,200,300])
        self.receipt();before=self.service.insights()['growth']['xp']
        self.clock.advance(days=1);self.receipt()
        self.assertEqual(self.service.insights()['growth']['xp'],before)

    def test_recovery_achievement_requires_failure_before_the_first_ac(self):
        def failed(identity):
            self.service.record_official({'id':identity,'url':self.assets.problem(identity)['url'],'code':'wrong'},
              {'status':'finished','verdict':'WA','submissionId':str(fixtures._next_official_id()),'acceptedAt':iso(self.clock())})
        self.receipt();self.clock.advance(minutes=1);failed('fixture::A')
        failed('fixture::B');self.clock.advance(minutes=1);self.receipt('fixture::B')
        from daily_rotation import action_achievements
        recovery=next(item for item in action_achievements(self.service,self.service._evidence()) if item['id']=='recovery-3')
        self.assertEqual(recovery['progress'],1)
