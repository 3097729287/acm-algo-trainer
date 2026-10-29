import datetime as dt
import unittest
from unittest.mock import patch

from progression import public_progress
from tb_rank import LEVEL_COSTS, RANK_THRESHOLDS, RANK_UNLOCK_XP, TIERS, growth, ranked


class TBRankTests(unittest.TestCase):
    def test_level_boundaries_and_increasing_costs(self):
        total=0
        for level,cost in enumerate(LEVEL_COSTS,1):
            before=growth(total+cost-1)
            self.assertEqual((before['level'],before['currentLevelXp'],before['nextLevelXp']),(level,cost-1,cost))
            total+=cost
            self.assertEqual(growth(total)['level'],level+1)
        self.assertTrue(all(growth(sum(LEVEL_COSTS[:i]))['badge'] is None for i in range(10)))
        self.assertTrue(growth(RANK_UNLOCK_XP)['rankedEligible'])
        self.assertEqual(growth(RANK_UNLOCK_XP)['level'],5)
        self.assertFalse(growth(RANK_UNLOCK_XP - 1)['rankedEligible'])
        self.assertEqual(growth(10**9)['level'],100)
        self.assertEqual(growth(10**9)['totalXp'],10**9)
        self.assertEqual(growth(sum(LEVEL_COSTS[:12]))['level'],13)

    @staticmethod
    def evidence(count, day='2026-10-01', difficulty=3300):
        return [{'key':str(i),'acceptedAt':day+'T01:00:00Z','difficulty':difficulty,
                 'independent':True,'independentKnown':True,'scope':'official'} for i in range(count)]

    def test_historical_seen_and_under_difficulty_never_score(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        values=self.evidence(1,'2026-09-30')+self.evidence(1,'2026-10-01',700)+[dict(self.evidence(1)[0],independent=False)]
        value=ranked(values,values,'2026-10-01T00:00:00Z',now)
        self.assertFalse(value['qualified'])
        self.assertEqual(value['score'],0)
        self.assertEqual(value['legacyPoints']['score'],0)

    def test_daily_decay_and_repeat_maintenance_are_deterministic(self):
        first=self.evidence(100)
        unlock='2026-10-01T00:00:00Z'
        now=dt.datetime(2026,10,4,tzinfo=dt.timezone.utc)
        decayed=ranked(first,first,unlock,now)
        maintained=ranked(first,first+self.evidence(1,'2026-10-02')+self.evidence(1,'2026-10-03'),unlock,now)
        # Preserve the old deterministic replay for historical consumers, but
        # attendance no longer changes a user's demonstrated skill tier.
        self.assertGreater(decayed['legacyPoints']['decayedPoints'],0)
        self.assertEqual(maintained['legacyPoints']['decayedPoints'],0)
        self.assertEqual(maintained['legacyPoints']['earnedPoints'],decayed['legacyPoints']['earnedPoints'])
        self.assertEqual((decayed['tier'],decayed['abilityScore']),(maintained['tier'],maintained['abilityScore']))
        self.assertEqual(decayed,ranked(first,first,unlock,now))
        self.assertEqual(decayed['legacyPoints']['dailyRequired'],1)

    def test_king_stars_continue_and_lower_difficulty_cannot_farm_high_rank(self):
        unlock='2026-10-01T00:00:00Z';now=dt.datetime(2026,10,1,12,tzinfo=dt.timezone.utc)
        first=self.evidence(500)
        value=ranked(first,first,unlock,now)
        self.assertEqual(value['tier'],'王者')
        self.assertIsNone(value['nextAbilityScore'])
        self.assertEqual(value['abilityScore'],3300)
        self.assertGreater(value['legacyPoints']['nextScore'],value['legacyPoints']['score'])
        easy=self.evidence(1000,difficulty=800)
        result=ranked(easy,easy,unlock,now)
        self.assertEqual((result['tier'],result['abilityScore']),('青铜',800))
        self.assertLess(result['legacyPoints']['score'],400)

    def test_history_before_unlock_qualifies_for_skill_without_awarding_legacy_points(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        values=self.evidence(5,'2026-09-30',1800)
        value=ranked(values,values,'2026-10-01T00:00:00Z',now)
        self.assertEqual((value['tier'],value['abilityScore'],value['evidenceCount']),('钻石',1800,5))
        self.assertEqual(value['legacyPoints']['earnedPoints'],0)

    def test_skill_uses_posterior_and_repeated_support_not_best_five_median(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        values=[dict(item,difficulty=difficulty) for item,difficulty in zip(self.evidence(7),[800,1100,1400,1700,2000,1800,3600])]
        value=ranked(values,values,'2026-10-01T00:00:00Z',now)
        self.assertEqual(value['topDifficulties'],[3600,2000,1800,1700,1400])
        self.assertEqual((value['abilityScore'],value['tier'],value['nextAbilityScore']),(1400,'黄金',1600))
        for difficulty,tier in zip(RANK_THRESHOLDS,TIERS):
            with self.subTest(tier=tier):
                sample=self.evidence(5,difficulty=max(1,difficulty))
                result=ranked(sample,sample,'2026-10-01T00:00:00Z',now)
                self.assertLessEqual(result['abilityScore'],max(1,difficulty))
                self.assertEqual(result['tierRequirements'][TIERS.index(tier)]['minAbilityScore'],difficulty)

    def test_king_starts_at_2200_and_existing_evidence_is_reclassified(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        for score, tier, next_score in ((2199, '宗师', 2200), (2200, '王者', None), (3200, '王者', None)):
            with self.subTest(score=score):
                evidence=self.evidence(5, difficulty=score)
                result=ranked(evidence,evidence,'2026-10-01T00:00:00Z',now)
                self.assertEqual((result['tier'],result['abilityScore'],result['nextAbilityScore']), (tier,score//10*10,next_score))

    def test_one_hard_solve_and_unlimited_easy_solves_do_not_grant_high_rank(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        easy=self.evidence(1000,difficulty=800)
        values=easy+[dict(easy[0],key='exceptional',difficulty=3600)]
        value=ranked(values,values,'2026-10-01T00:00:00Z',now)
        self.assertEqual((value['tier'],value['abilityScore']),('青铜',800))
        no_attendance=ranked(values,[],'2026-10-01T00:00:00Z',now+dt.timedelta(days=90))
        self.assertEqual((no_attendance['tier'],no_attendance['abilityScore']),('青铜',800))

    def test_unknown_local_assisted_future_and_invalid_difficulty_cannot_place(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        variants=[{'scope':'local'},{'verdict':'SAMPLE_PASS'},{'independent':False},
                  {'scope':None},{'independentKnown':False},{'independentKnown':None},
                  {'difficulty':None},{'difficulty':True},{'difficulty':10**400},
                  {'difficulty':float('nan')},{'difficulty':float('inf')},{'difficulty':0},
                  {'acceptedAt':'2027-01-01T00:00:00Z'}]
        for variant in variants:
            with self.subTest(variant=variant):
                values=[dict(item,**variant) for item in self.evidence(5)]
                result=ranked(values,values,'2026-10-01T00:00:00Z',now)
                self.assertFalse(result['qualified'])
                self.assertIsNone(result['tier'])
                self.assertIsNone(result['abilityScore'])
                self.assertEqual(result['evidenceCount'],0)

    def test_url_aliases_and_repeat_ac_never_inflate_skill_evidence(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        item=self.evidence(1)[0]
        values=[dict(item,key='https://codeforces.com/contest/123/problem/A'),
                dict(item,key='https://codeforces.com/problemset/problem/123/A'),
                dict(item,key='assisted',independent=False),
                dict(item,key='assisted',acceptedAt='2026-10-01T02:00:00Z')]
        value=ranked(values*20,values,'2026-10-01T00:00:00Z',now)
        self.assertFalse(value['qualified'])
        self.assertEqual(value['evidenceCount'],1)


class RankIntegrationTests(unittest.TestCase):
    import test_training as fixtures
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def test_unlock_stays_durable_while_xp_level_keeps_its_actual_value(self):
        with patch.object(self.service,'_first_acceptance_xp',return_value=RANK_UNLOCK_XP):
            growth_value=self.service.insights()['growth']
        self.assertEqual(growth_value['level'],5)
        self.assertTrue(growth_value['rankedEligible'])
        self.assertFalse(growth_value['ranked']['qualified'])
        original=tuple(self.service.connection.execute('SELECT * FROM tb_rank_profile').fetchone())
        with patch.object(self.service,'_first_acceptance_xp',return_value=100):
            downgraded=self.service.insights()['growth']
        self.assertEqual(downgraded['level'],1)
        self.assertTrue(downgraded['rankedEligible'])
        self.assertEqual(tuple(self.service.connection.execute('SELECT * FROM tb_rank_profile').fetchone()),original)
        with patch.object(self.service,'_first_acceptance_xp',return_value=sum(LEVEL_COSTS[:14])):
            self.assertEqual(self.service.insights()['growth']['level'],15)

    def test_real_official_evidence_places_without_changing_claims_or_code(self):
        self.service.connection.execute("INSERT INTO tb_rank_profile VALUES(1,'2026-10-09T00:00:00Z')")
        for row in self.library.rows[:5]:
            row.update(difficulty=1800, platform='Codeforces', difficultySource='Codeforces 官方 rating', difficultyEstimated=False)
            self.accept(row['id'],code='// Preserve this exact official code')
        result=self.service.insights()
        rank=result['growth']['ranked']
        self.assertEqual((rank['abilityScore'],rank['tier'],rank['evidenceCount']),(1800,'钻石',5))
        self.assertEqual(result['growth']['badge'],'tier-5')
        claims=[tuple(item) for item in self.service.connection.execute('SELECT * FROM achievement_xp_claims ORDER BY achievement_id')]
        awards=[tuple(item) for item in self.service.connection.execute('SELECT * FROM official_first_xp_awards ORDER BY problem_key')]
        records=[tuple(item) for item in self.service.connection.execute('SELECT * FROM submissions ORDER BY id')]
        for _ in range(2):
            self.assertEqual(self.service.insights()['growth']['totalXp'],result['growth']['totalXp'])
        self.assertEqual([tuple(item) for item in self.service.connection.execute('SELECT * FROM achievement_xp_claims ORDER BY achievement_id')],claims)
        self.assertEqual([tuple(item) for item in self.service.connection.execute('SELECT * FROM official_first_xp_awards ORDER BY problem_key')],awards)
        self.assertEqual([tuple(item) for item in self.service.connection.execute('SELECT * FROM submissions ORDER BY id')],records)
        self.assertTrue(all(item['code']=='// Preserve this exact official code' for item in self.service.connection.execute('SELECT code FROM submissions')))
        summary=public_progress(result)
        self.assertEqual((summary['rankTier'],summary['rankScore']),('钻石',1800))
        self.assertEqual(set(summary),{'level','tier','rankTier','rankScore','titles'})


if __name__=='__main__':unittest.main()
