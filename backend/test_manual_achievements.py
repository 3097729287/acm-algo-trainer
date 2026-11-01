import datetime as dt
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import test_training as fixtures
from fun_achievements import fun_achievements
from progression import extra_achievements
from training import ServiceError,TrainingService


class ManualAchievementTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def test_reading_unlocks_without_granting_and_claim_is_atomic(self):
        self.accept()
        before=self.service.insights()
        achievement=next(item for item in before['achievements'] if item['id']=='official-1')
        self.assertTrue(achievement['unlocked']);self.assertFalse(achievement['rewardClaimed'])
        self.assertEqual(before['growth']['achievementXp'],0)
        with ThreadPoolExecutor(max_workers=6) as workers:
            results=list(workers.map(lambda _:self.service.claim_achievement('official-1'),range(6)))
        self.assertEqual(sum(item['awardedXp'] for item in results),25)
        self.assertEqual(self.service.insights()['growth']['achievementXp'],25)
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM achievement_xp_claims WHERE achievement_id='official-1'").fetchone()[0],1)
        self.service.close();self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual(self.service.claim_achievement('official-1')['awardedXp'],0)

    def test_unknown_and_unearned_claims_never_write_a_reward(self):
        for identity in ('unknown','official-100',{},None):
            with self.subTest(identity=identity),self.assertRaises(ServiceError):self.service.claim_achievement(identity)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0],0)

    def test_unclaimed_completion_and_its_date_survive_evidence_becoming_unavailable(self):
        self.accept();first=next(item for item in self.service.insights()['achievements'] if item['id']=='official-1')
        with self.service._write() as connection:connection.execute('DELETE FROM submissions')
        self.clock.advance(days=2)
        earned=next(item for item in self.service.insights()['achievements'] if item['id']=='official-1')
        self.assertTrue(earned['unlocked']);self.assertEqual(earned['unlockedAt'],first['unlockedAt'])
        self.assertFalse(earned['rewardClaimed']);self.assertEqual(self.service.claim_achievement('official-1')['awardedXp'],25)

    def test_difficulty_ladder_ends_at_2300_and_claim_awards_medal(self):
        self.library.rows[0]['difficulty']=2300;self.accept()
        result=self.service.insights()
        ladder=[item for item in result['achievements'] if item['id'].startswith('difficulty-')]
        self.assertEqual(len(ladder),8);self.assertTrue(all(item['unlocked'] for item in ladder))
        claimed=self.service.claim_achievement('difficulty-3600')
        self.assertEqual(claimed['awardedXp'],200)
        self.assertTrue(any(title['category']=='difficulty' and title['target']==2300 for title in claimed['titles']))

    def test_fun_milestones_use_beijing_time_and_ignore_local_runs(self):
        def record(index,stamp,verdict='WA',**extra):return dict(id=str(index),scope='official',mode='submit',submitted_at=stamp,finished_at=stamp,verdict=verdict,**extra)
        records=[record(index,'2026-10-31T22:15:00+00:00') for index in range(10)]
        records.append(record('night','2026-11-01T13:00:00+00:00'))
        records.extend([{**record('sample','2026-11-01T13:00:00+00:00'),'scope':'local'}, {**record('run','2026-11-01T13:00:00+00:00'),'mode':'run'}])
        values={item['id']:item for item in fun_achievements(self.service,records)}
        self.assertTrue(values['morning-submit']['unlocked']);self.assertTrue(values['evening-submit']['unlocked'])
        self.assertTrue(values['day-submissions-10']['unlocked']);self.assertTrue(values['day-wa-10']['unlocked'])
        self.assertEqual(values['day-submissions-30']['progress'],11)

    def test_failed_review_cycles_need_distinct_spaced_days(self):
        for index,day in enumerate((1,1,3)):
            task=dict(problemKey='same-problem',openedAt=f'2026-10-{day:02}T00:00:00+00:00',completedAt=f'2026-10-{day:02}T00:01:00+00:00',failures=['wa'],independent=True)
            self.service.connection.execute('INSERT INTO account_preferences VALUES(?,?,?)',('review-task:'+str(index),json.dumps(task),task['completedAt']))
        values={item['id']:item for item in fun_achievements(self.service,[])}
        self.assertTrue(values['review-rebound-2']['unlocked']);self.assertFalse(values['review-rebound-3']['unlocked'])

    def test_social_milestones_record_only_successful_service_actions(self):
        client=self.service.leaderboard;profile={'endpoint':'http://127.0.0.1:18000','auth_token':'fixture','user_id':'self'}
        with patch.object(self.service,'_ranking_profile',return_value=profile):
            for target in ('one','two','three'):
                with patch.object(client,'_request',return_value={'likes':{'likedToday':True}}):client.social({'targetId':target},'likes')
            with patch.object(client,'_request',side_effect=[{'entries':[{'userId':'leader','rank':1,'count':8}]},{'ok':True}]):
                client.social({'targetId':'leader','text':'就这?','requestId':'fixture'},'comments')
        values={item['id']:item for item in fun_achievements(self.service,[])}
        self.assertTrue(values['hearts-given-3']['unlocked']);self.assertTrue(values['leader-tease']['unlocked'])


if __name__=='__main__':unittest.main()
