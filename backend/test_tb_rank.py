import datetime as dt
import unittest
from tb_rank import LEVEL_COSTS, RANK_UNLOCK_XP, growth, ranked


class TBRankTests(unittest.TestCase):
    def test_level_boundaries_and_increasing_costs(self):
        total=0
        for level,cost in enumerate(LEVEL_COSTS,1):
            before=growth(total+cost-1)
            self.assertEqual((before['level'],before['currentLevelXp'],before['nextLevelXp']),(level,cost-1,cost))
            total+=cost
            self.assertEqual(growth(total)['level'],level+1)
        self.assertEqual(len({growth(sum(LEVEL_COSTS[:i]))['badge'] for i in range(10)}),10)
        self.assertTrue(growth(RANK_UNLOCK_XP)['rankedEligible'])
        self.assertEqual(growth(10**9)['level'],10)

    @staticmethod
    def evidence(count, day='2026-10-01', difficulty=3300):
        return [{'key':str(i),'acceptedAt':day+'T01:00:00Z','difficulty':difficulty,'independent':True} for i in range(count)]

    def test_historical_seen_and_under_difficulty_never_score(self):
        now=dt.datetime(2026,10,2,tzinfo=dt.timezone.utc)
        values=self.evidence(1,'2026-09-30')+self.evidence(1,'2026-10-01',700)+[dict(self.evidence(1)[0],independent=False)]
        self.assertEqual(ranked(values,values,'2026-10-01T00:00:00Z',now)['score'],0)

    def test_daily_decay_and_repeat_maintenance_are_deterministic(self):
        first=self.evidence(100)
        unlock='2026-10-01T00:00:00Z'
        now=dt.datetime(2026,10,4,tzinfo=dt.timezone.utc)
        decayed=ranked(first,first,unlock,now)
        maintained=ranked(first,first+self.evidence(1,'2026-10-02')+self.evidence(1,'2026-10-03'),unlock,now)
        self.assertGreater(decayed['decayedPoints'],0)
        self.assertEqual(maintained['decayedPoints'],0)
        self.assertEqual(maintained['earnedPoints'],decayed['earnedPoints'])
        self.assertEqual(decayed,ranked(first,first,unlock,now))
        self.assertEqual(decayed['dailyRequired'],1)

    def test_king_stars_continue_and_lower_difficulty_cannot_farm_high_rank(self):
        unlock='2026-10-01T00:00:00Z';now=dt.datetime(2026,10,1,12,tzinfo=dt.timezone.utc)
        first=self.evidence(500)
        value=ranked(first,first,unlock,now)
        self.assertEqual(value['tier'],'王者')
        self.assertGreater(value['nextScore'],value['score'])
        easy=self.evidence(1000,difficulty=800)
        self.assertLess(ranked(easy,easy,unlock,now)['score'],400)


if __name__=='__main__':unittest.main()
