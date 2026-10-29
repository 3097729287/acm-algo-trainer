import unittest
from daily_rotation import adapt_challenge,CHALLENGES,EXPLORATIONS,tasks_for
from progression import task_progress
class DailyPersonalizationTests(unittest.TestCase):
    def test_difficulty_is_close_to_confirmed_ability_and_never_a_ui_action(self):
        for score in (800,1000,1700,3900):
            for task in CHALLENGES:
                value=adapt_challenge(task,score)
                if task.get('minDifficulty'):
                    self.assertGreaterEqual(value['minDifficulty'],score)
                    self.assertLessEqual(value['minDifficulty'],min(4000,score+200))
                    self.assertTrue(value['difficultyEvidenceRequired'])
        self.assertTrue(all(task['kind']!='action' for task in EXPLORATIONS))
        for day in range(1,29):
            self.assertTrue(all(task['kind']!='action' for task in tasks_for(f'2026-10-{day:02d}','account')))
    def test_unknown_ability_has_a_conservative_start_not_a_fabricated_score(self):
        task=adapt_challenge(next(item for item in CHALLENGES if item.get('minDifficulty')),None)
        self.assertIsNone(task['abilityReference'])
        self.assertLessEqual(task['minDifficulty'],1000)
    def test_low_confidence_rating_cannot_complete_an_adaptive_difficulty_task(self):
        task=adapt_challenge(next(item for item in CHALLENGES if item['id']=='hard-1800'),1000)
        day='2026-10-29'
        item={'problemKey':'one','day':day,'scope':'official','verdict':'AC','difficulty':2000,'abilityDifficulty':None,'newProblem':True}
        self.assertEqual(task_progress(task,[item],day)[0],0)
        self.assertEqual(task_progress(task,[dict(item,abilityDifficulty=1100)],day)[0],0)
        self.assertEqual(task_progress(task,[dict(item,abilityDifficulty=1200)],day)[0],1)
