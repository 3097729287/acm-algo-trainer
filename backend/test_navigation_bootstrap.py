"""The entry level uses actual account ledgers without the full knowledge scan."""
import json
import unittest
from unittest.mock import patch

import test_training as fixtures
import test_experience_challenge as challenge


class NavigationBootstrapTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    accept = fixtures.ServiceTests.accept

    def equivalent(self):
        entry = self.service.navigation()
        full = self.service.insights()['growth']
        for key in ('level', 'totalXp', 'currentLevelXp', 'nextLevelXp', 'experienceChallenge', 'confirmed'):
            self.assertEqual(entry[key], full[key], key)
        self.assertEqual(entry['authority']['owner'], full['authority']['owner'])
        return entry

    def test_fresh_entry_does_not_wait_for_knowledge_tasks_or_claims(self):
        with patch('insights.build_insights', side_effect=AssertionError('full scan')), patch.object(self.service, 'daily_tasks', side_effect=AssertionError('task calculation')):
            entry = self.service.navigation()
        self.assertEqual((entry['level'], entry['totalXp']), (1, 0))
        self.assertTrue(entry['experienceChallenge']['eligible'])
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0], 0)
        self.assertNotIn('ranked', entry)
        self.assertNotIn('achievements', entry)

    def test_first_official_award_and_repeat_reads_match_full_growth(self):
        self.accept('fixture::A')
        entry = self.equivalent()
        self.assertEqual(entry['totalXp'], 100)
        for _ in range(3):
            self.assertEqual(self.service.navigation()['totalXp'], 100)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM official_first_xp_awards').fetchone()[0], 1)
        self.accept('fixture::A')
        self.assertEqual(self.equivalent()['totalXp'], 100)

    def test_claimed_rewards_and_current_ranking_owner_are_preserved(self):
        self.accept('fixture::A')
        profile = self.service._ranking_profile()
        self.service._ranking_rewards(profile, {'userId': profile['user_id'], 'totalXp': 33, 'awards': []})
        at = self.clock().isoformat()
        with self.service._write() as db:
            db.execute('INSERT INTO achievement_xp_claims VALUES(?,?,?,?)', ('official-10', at, 77, at))
            db.execute('INSERT INTO account_preferences VALUES(?,?,?)', ('review-reward:fixture', json.dumps({'version': 1, 'xp': 20, 'receiptId': 'verified-fixture'}), at))
            db.execute('INSERT INTO ranking_reward_totals VALUES(?,?,?,?,?)', (profile['endpoint'], 'another-owner', 900, '[]', at))
        self.assertEqual(self.equivalent()['totalXp'], 230)

    def test_beginner_curve_and_administrator_selection_match_full_growth(self):
        from experience_challenge import update
        update(self.service, {'action': 'choose', 'choice': 'beginner'})
        self.accept('fixture::A')
        self.assertEqual(self.equivalent()['level'], 1)
        self.service.admin_mode = True
        from admin import controls
        controls(self.service, {'level': 3, 'tier': 1, 'allAchievements': False})
        self.assertEqual(self.equivalent()['level'], 3)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0], 0)

    def test_aliases_and_unknown_difficulties_keep_original_award_rules(self):
        self.library.rows[0].update(url='https://codeforces.com/contest/100/problem/A', difficulty=None)
        self.library.rows[1].update(url='https://codeforces.com/contest/100/problem/A', difficulty=None)
        self.accept('fixture::A')
        self.accept('fixture::B')
        self.assertEqual(self.equivalent()['totalXp'], 0)
        self.library.rows[0]['difficulty'] = 1800
        self.library.rows[1]['difficulty'] = 1800
        self.assertEqual(self.equivalent()['totalXp'], 200)


class ChallengeEntryTests(unittest.TestCase):
    setUp = challenge.ChallengeTests.setUp
    tearDown = challenge.ChallengeTests.tearDown
    completed = fixtures.ServiceTests.completed
    judge_drill = staticmethod(challenge.ChallengeTests.judge_drill)
    choose = challenge.ChallengeTests.choose

    def test_completed_full_template_grants_once_before_full_insights(self):
        self.choose()
        self.completed(challenge.PROBLEMS[0], code='correct')
        for _ in range(3):
            value = self.service.navigation()
            self.assertEqual((value['level'], value['totalXp']), (6, 1500))
        self.assertEqual(self.service.insights()['growth']['totalXp'], 1500)
        # The old fixed receipt remains intact; the level-six top-up is separate.
        self.assertEqual(challenge.read(self.service)['awardedXp'], 500)


if __name__ == '__main__':
    unittest.main()
