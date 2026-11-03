"""Pack eligibility and shared daily study budget; disposable accounts only."""
import json
import unittest
from unittest.mock import patch
import test_training as fixtures
from daily_chains import _sticker_task
from gameplay import daily_pack_rarity
from goals import Goals

class PackPolicyTests(unittest.TestCase):
    def test_native_and_service_share_the_exact_pack_policy(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        policy=json.loads((root/'backend/resources/sticker-rewards.json').read_text('utf-8'))
        self.assertEqual(policy,json.loads((root/'server/leaderboard/src/sticker-rewards.json').read_text('utf-8')))
        self.assertEqual([policy['cardPacks'][tier]['quantity'] for tier in ['common','rare','epic','legendary']],[3,4,5,6])
        self.assertEqual(policy['dailyPacks']['maxPerDay'],3)
        self.assertEqual(sum(policy['dailyPacks']['probabilities'].values()),10000)
        self.assertGreater(policy['dailyPacks']['probabilities']['legendary'],0)
        self.assertLessEqual(policy['dailyPacks']['probabilities']['legendary'],10)

    def test_task_difficulty_and_amount_follow_pack_rarity_and_freeze_after_issue(self):
        base={'id':'fixture-task','kind':'solve','target':1,'xp':30,'description':'New problem'}
        results=[]
        for rarity,quantity in [('common',3),('rare',4),('epic',5),('legendary',6)]:
            with patch('gameplay.daily_pack_rarity',return_value=rarity):
                value=_sticker_task(base,'fixed','owner','2026-11-04',1200)
            self.assertEqual(value['rewardPack'],{'rarity':rarity,'quantity':quantity})
            self.assertEqual(value['xp'],0)
            self.assertEqual(_sticker_task(value,'fixed','owner','2026-11-04',2000),value)
            results.append(value)
        self.assertEqual([v['minDifficulty'] for v in results],[1100,1300,1400,1500])
        self.assertEqual([v['target'] for v in results],[1,1,2,3])
        with patch('gameplay.daily_pack_rarity',return_value='legendary'):
            learning=_sticker_task({**base,'kind':'learning'},'review-0','owner','2026-11-04',1200)
        self.assertEqual((learning['kind'],learning['target'],learning['minDifficulty']),('learning',40,0))
        self.assertFalse(learning['difficultyEvidenceRequired'])

class GoalBudgetTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_a_previously_paused_goal_resumes_when_remaining_time_fits_one_new_problem(self):
        paused={'date':'2026-10-08','tasks':[],'dueCount':14,'deferredCount':6,'minutes':143,'dailyMinutes':240,'newMinutes':97,'reviewOnly':True}
        goals=Goals(self.service)
        with patch.object(self.service,'review_plan',return_value=paused):
            goals.save({'title':'Practice','kind':'custom','deadline':'2026-11-30','dailyMinutes':240,'totalProblems':40,'minutesPerProblem':60})
            zero=goals.list(assign=True)
        self.assertEqual(zero['goalTasks'],[])
        with patch.object(self.service,'review_plan',return_value={**paused,'reviewOnly':False}):
            restored=goals.list(assign=True)
            again=goals.list(assign=True)
        self.assertEqual(len(restored['goalTasks']),1)
        self.assertEqual([t['id'] for t in again['goalTasks']],[t['id'] for t in restored['goalTasks']])
        self.assertEqual(restored['goals'][0]['dailyTask']['target'],1)

    def test_two_goals_share_remaining_minutes_instead_of_each_spending_the_entire_budget(self):
        plan={'date':'2026-10-08','tasks':[],'dueCount':14,'deferredCount':6,'minutes':143,'dailyMinutes':240,'newMinutes':97,'reviewOnly':False}
        goals=Goals(self.service)
        with patch.object(self.service,'review_plan',return_value=plan):
            for title in ['First','Second']:goals.save({'title':title,'kind':'cf','currentRating':1000,'targetRating':1200,'deadline':'2026-11-30','dailyMinutes':240})
            value=goals.list(assign=True)
        self.assertEqual(len(value['goalTasks']),1)
        self.assertLessEqual(sum(len(g['dailyTask']['problems'])*g['minutesPerProblem'] for g in value['goals']),97)
