"""Official AC milestones and immutable, transaction-owned XP claims."""
import copy
from contextlib import contextmanager
import datetime as dt
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from achievement_rewards import award_achievement_xp
from progression import ACHIEVEMENT_DEFINITIONS, ac_achievements, extra_achievements, earned_titles, public_progress


class AchievementRewardsTests(unittest.TestCase):
    now = dt.datetime(2026, 10, 15, 15, tzinfo=dt.timezone.utc)

    @contextmanager
    def database(self, path=':memory:'):
        connection = sqlite3.connect(path)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def evidence(self, count):
        return {f'problem-{index}': (self.now + dt.timedelta(seconds=index)).isoformat() for index in range(count)}

    def test_complete_ac_ladder_preserves_ids_and_names(self):
        achievements = ac_achievements(self.evidence(51))
        expected = [1, 10, 25, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000]
        self.assertEqual([item['target'] for item in achievements], expected)
        for item in achievements:
            target = item['target']
            self.assertEqual(item['id'], f'official-{target}')
            self.assertEqual(item['name'], f'AC {target}题')
            self.assertEqual(item['unlocked'], target <= 51)
            self.assertEqual(item['progress'], min(target, 51))
            if target < 500:
                self.assertGreater(item['rewardXp'], 0)
                self.assertIsNone(item['rewardTitle'])
            else:
                self.assertEqual(item['rewardXp'], 0)
                self.assertEqual(item['rewardTitle']['target'], target)

    def test_official_evidence_dedupes_url_aliases_and_keeps_unknown_date(self):
        achievements = ac_achievements([
            {'key': 'https://codeforces.com/problemset/problem/123/A', 'acceptedAt': self.now.isoformat(), 'scope': 'official'},
            {'key': 'https://codeforces.com/contest/123/problem/A', 'acceptedAt': (self.now - dt.timedelta(days=1)).isoformat(), 'scope': 'official'},
            {'key': 'different', 'acceptedAt': None, 'scope': 'official'},
            {'key': 'not-official', 'acceptedAt': self.now.isoformat(), 'scope': 'local'},
            {'key': 'not-ac', 'acceptedAt': self.now.isoformat(), 'scope': 'official', 'verdict': 'SAMPLE_PASS'},
            {'id': 'official-10000', 'unlocked': True, 'progress': 10000},
        ])
        self.assertEqual(achievements[1]['progress'], 2)
        self.assertEqual(achievements[0]['unlockedAt'], (self.now - dt.timedelta(days=1)).isoformat())
        self.assertIsNone(ac_achievements({'dated-unknown': None})[0]['unlockedAt'])
        self.assertTrue(ac_achievements({'dated-unknown': None})[0]['unlocked'])

    def test_date_list_and_empty_progress(self):
        self.assertEqual(ac_achievements([self.now.isoformat()] * 10)[1]['progress'], 10)
        self.assertTrue(all(not item['unlocked'] and item['progress'] == 0 for item in ac_achievements([])))

    def test_backfill_and_repeated_refresh_never_duplicate_xp_or_writes(self):
        with self.database() as connection:
            items = ac_achievements(self.evidence(100))
            first = award_achievement_xp(connection, items, now=self.now)
            expected = sum(item['rewardXp'] for item in items if item['unlocked'])
            self.assertEqual(first['xp'], expected)
            self.assertEqual(first['newXp'], expected)
            self.assertEqual(len(first['claims']), 5)
            changes = connection.total_changes
            second = award_achievement_xp(connection, ac_achievements(self.evidence(100)), now=self.now + dt.timedelta(days=1))
            self.assertEqual(second['xp'], expected)
            self.assertEqual(second['newXp'], 0)
            self.assertEqual(connection.total_changes, changes)
            self.assertEqual(first['claims'], second['claims'])

    def test_known_target_and_reward_are_not_overridden_by_input(self):
        with self.database() as connection:
            first = ac_achievements(self.evidence(1))[0]
            first['rewardXp'] = 10**12
            unknown = {**first, 'id': 'forged', 'rewardXp': 10**12}
            false_flag = {**first, 'id': 'official-10000', 'target': 10000, 'progress': 0, 'unlocked': True}
            nan_progress = {**first, 'id': 'official-10', 'target': 10, 'progress': float('nan'), 'unlocked': True}
            result = award_achievement_xp(connection, [first, unknown, false_flag, nan_progress], now=self.now)
            self.assertEqual(result['xp'], 25)
            self.assertEqual(set(result['claims']), {'official-1'})
            self.assertEqual(first['rewardXp'], 25)
            self.assertEqual(unknown['rewardXp'], 0)

    def test_earned_amount_survives_definition_change_and_missing_evidence(self):
        with self.database() as connection:
            original = award_achievement_xp(connection, ac_achievements(self.evidence(1)), now=self.now)
            with patch.dict(ACHIEVEMENT_DEFINITIONS, {'official-1': {'target': 1, 'rewardXp': 10000}}):
                items = ac_achievements(self.evidence(1))
                changed = award_achievement_xp(connection, items, now=self.now)
                self.assertEqual(changed, {**original, 'newXp': 0})
                self.assertEqual(items[0]['rewardXp'], 25)
            self.assertEqual(award_achievement_xp(connection, [], now=self.now)['xp'], original['xp'])
            empty = ac_achievements([])
            self.assertEqual(award_achievement_xp(connection, empty, now=self.now)['newXp'], 0)
            self.assertTrue(empty[0]['unlocked'])
            self.assertEqual(empty[0]['unlockedAt'], self.now.isoformat())

    def test_claims_survive_restart_and_follow_callers_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'personal.sqlite3'
            with self.database(path) as connection:
                award_achievement_xp(connection, [], now=self.now)
            with self.database(path) as connection:
                connection.execute('BEGIN')
                award_achievement_xp(connection, ac_achievements(self.evidence(10)), now=self.now)
                connection.rollback()
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0], 0)
                award_achievement_xp(connection, ac_achievements(self.evidence(10)), now=self.now)
            with self.database(path) as connection:
                restored = award_achievement_xp(connection, ac_achievements(self.evidence(10)), now=self.now)
                self.assertEqual(restored['xp'], 65)
                self.assertEqual(restored['newXp'], 0)

    def test_all_legacy_achievements_have_fixed_rewards(self):
        items = extra_achievements([], [], [], 0)
        items.append({'id': 'contest-1', 'target': 1, 'progress': 0, 'unlocked': False})
        with self.database() as connection:
            self.assertEqual(award_achievement_xp(connection, items, now=self.now)['xp'], 0)
        for item in items:
            self.assertIn(item['id'], ACHIEVEMENT_DEFINITIONS)
            self.assertTrue(item['rewardXp'] > 0 or item['rewardTitle'])

    def test_new_titles_award_no_xp_and_equip_highest_of_each_category(self):
        items = ac_achievements(self.evidence(1500)) + extra_achievements([], [], [], 180)
        with self.database() as connection:
            first = award_achievement_xp(connection, items, now=self.now)
            expected_xp = sum(definition['rewardXp'] for identity, definition in ACHIEVEMENT_DEFINITIONS.items()
                              if identity in first['claims'])
            self.assertEqual(first['xp'], expected_xp)
            for identity in ('official-500', 'official-750', 'official-1000', 'official-1500', 'streak-30', 'streak-90', 'streak-180'):
                self.assertEqual(first['claims'][identity]['awardedXp'], 0)
            titles, equipped = earned_titles(first['claims'])
            self.assertEqual(len(titles), 7)
            self.assertEqual([title['id'] for title in equipped], ['ac-1500', 'streak-180'])
            repeated = award_achievement_xp(connection, ac_achievements([]) + extra_achievements([], [], [], 0), now=self.now)
            self.assertEqual(earned_titles(repeated['claims']), (titles, equipped))
            self.assertEqual(repeated['newXp'], 0)
            self.assertEqual(repeated['xp'], first['xp'])
            self.assertEqual(earned_titles({})[1], [])

    def test_removed_and_converted_rewards_keep_every_earned_xp_without_regrant(self):
        with self.database() as connection:
            award_achievement_xp(connection, [], now=self.now)
            old = {'official-500': 250, 'official-3000': 750, 'official-5000': 1000,
                   'official-10000': 1500, 'independent-3000': 600, 'independent-10000': 1000,
                   'streak-30': 100, 'streak-1000': 700}
            connection.executemany('INSERT INTO achievement_xp_claims VALUES(?,?,?,?)',
                                   [(identity, self.now.isoformat(), amount, self.now.isoformat()) for identity, amount in old.items()])
            before = connection.total_changes
            items = ac_achievements([]) + extra_achievements([], [], [], 0)
            result = award_achievement_xp(connection, items, now=self.now)
            self.assertEqual(result['xp'], sum(old.values()))
            self.assertEqual(result['newXp'], 0)
            self.assertEqual(connection.total_changes, before)
            by_id = {item['id']: item for item in items}
            self.assertTrue(set(old) - {'official-500', 'streak-30', 'streak-1000'} <= set(old) - set(by_id))
            self.assertNotIn('streak-1000', by_id)
            self.assertTrue(by_id['streak-730']['unlocked'])
            self.assertEqual(by_id['streak-730']['name'], '连续训练 2 年')
            self.assertEqual(by_id['streak-730']['rewardXp'], 0)
            self.assertEqual(by_id['streak-730']['legacyAwardedXp'], 700)
            self.assertEqual(by_id['official-500']['legacyAwardedXp'], 250)
            titles, equipped = earned_titles(result['claims'])
            self.assertEqual([title['id'] for title in equipped], ['ac-500', 'streak-730'])
            self.assertEqual(len(titles), 3)

    def test_two_year_streak_uses_seven_hundred_thirty_consecutive_dates(self):
        records = [{'mode': 'submit', 'submitted_at': (self.now + dt.timedelta(days=index)).isoformat()} for index in range(730)]
        result = next(item for item in extra_achievements([], records, [], 730) if item['id'] == 'streak-730')
        self.assertTrue(result['unlocked'])
        self.assertEqual(result['unlockedAt'], records[-1]['submitted_at'])
        self.assertEqual(result['rewardXp'], 0)
        self.assertEqual(result['rewardTitle']['id'], 'streak-730')

    def test_public_progress_has_only_bounded_public_display_fields(self):
        _, equipped = earned_titles({'official-500': {'unlockedAt': self.now.isoformat()}, 'streak-30': {'unlockedAt': None}})
        unlocked = public_progress({'growth': {'level': 10, 'tier': '王者', 'ranked': {'tier': '白银', 'score': 720}, 'equippedTitles': equipped},
                                    'profile': {'loginId': 'private', 'auth_token': 'secret'}})
        self.assertEqual(unlocked['rankScore'], 720)
        self.assertEqual(unlocked['rankTier'], '白银')
        self.assertEqual(len(unlocked['titles']), 2)
        self.assertEqual(set(unlocked), {'level', 'tier', 'rankTier', 'rankScore', 'titles'})
        self.assertEqual(set(unlocked['titles'][0]), {'id', 'name', 'category', 'target'})
        pending = public_progress({'growth': {'level': 7, 'tier': '钻石'}})
        self.assertIsNone(pending['rankScore'])
        self.assertIsNone(pending['rankTier'])
        placing = public_progress({'growth': {'level': 6, 'ranked': {'qualified': False, 'score': 0, 'tier': None}}})
        self.assertIsNone(placing['rankScore'])
        self.assertIsNone(placing['rankTier'])
        high_level = public_progress({'growth': {'level': 150, 'ranked': {'qualified': True, 'score': 2300, 'tier': '钻石'}}})
        self.assertEqual(high_level['level'],100)
        self.assertEqual((high_level['rankTier'],high_level['rankScore']),('钻石',2300))

    def test_extra_rewards_backfill_once_alongside_ac_ladder(self):
        evidence = [{'key': f'problem-{index}', 'acceptedAt': self.now.isoformat(),
                     'platform': 'Codeforces' if index % 2 else 'AtCoder', 'independent': True, 'difficulty': 2100}
                    for index in range(25)]
        items = ac_achievements(evidence) + extra_achievements(evidence, [], [], 0)
        with self.database() as connection:
            first = award_achievement_xp(connection, items, now=self.now)
            self.assertTrue({'independent-5', 'independent-25', 'difficulty-1500', 'difficulty-1800', 'difficulty-2100', 'platforms-2'}.issubset(first['claims']))
            self.assertEqual(award_achievement_xp(connection, copy.deepcopy(items), now=self.now)['newXp'], 0)


class TrainingTitleTests(unittest.TestCase):
    import test_training as fixtures
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    accept = fixtures.ServiceTests.accept

    def test_titles_are_present_in_growth_and_cache_invalidates_on_real_writes(self):
        with self.service._write() as connection:
            connection.execute("INSERT INTO achievement_xp_claims VALUES('official-500',?,250,?)", (self.clock().isoformat(), self.clock().isoformat()))
        value = self.service.insights()
        self.assertEqual(value['growth']['achievementXp'], 250)
        self.assertEqual(value['titles'][0]['id'], 'ac-500')
        self.assertEqual(value['equippedTitles'], value['growth']['equippedTitles'])
        with patch.object(self.service, 'insights', wraps=self.service.insights) as insights:
            public = self.service.public_progress()
            public['titles'][0]['name'] = 'modified outside'
            self.assertNotEqual(self.service.public_progress()['titles'][0]['name'], 'modified outside')
            insights.assert_not_called()
            self.accept()
            self.service.public_progress()
            self.assertEqual(insights.call_count, 1)
            self.clock.advance(days=1)
            self.service.public_progress()
            self.assertEqual(insights.call_count, 2)

    def test_public_accounts_share_ac_titles_with_interface(self):
        from types import SimpleNamespace
        hub = {'accounts': [{'platform': 'codeforces', 'solved': [
            {'url': f'https://codeforces.com/contest/1000/problem/A{index}', 'acceptedAt': None} for index in range(500)]}]}
        self.library.extensions = SimpleNamespace(snapshot=lambda: copy.deepcopy(hub), rows=lambda: [])
        summary = self.service.public_progress()
        self.assertEqual([item['id'] for item in summary['titles']], ['ac-500'])
        self.assertEqual(self.service.connection.execute("SELECT awarded_xp FROM achievement_xp_claims WHERE achievement_id='official-500'").fetchone()[0], 0)
        self.assertEqual(self.service.insights(hub)['growth']['achievementXp'], 685)


if __name__ == '__main__':
    unittest.main()
