"""Reviewed cross-site counting identity; navigation and old user rows survive."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from catalog_identity import unique_catalog_rows
from catalog_payload import project_row
from insights import canonical_url
from progression import official_reward_evidence
from question_identity import PAIR_IDS, PAIR_KEY, PAIR_KEYS, PAIR_HASHES, question_key
from test_training import Clock, Library, Assets
from training import TrainingService, UTC

URLS = ('https://www.luogu.com.cn/problem/P10865',
        'https://codeforces.com/gym/105139/problem/H')


def rows():
    result = Library().rows[:4]
    for index in range(2):
        result[index].update(id=PAIR_IDS[index], url=URLS[index], difficulty=1800,
                             source='luogu-training' if index == 0 else 'remote')
    result[2].update(url='https://codeforces.com/gym/105139/problem/I')
    result[3].update(url='https://www.luogu.com.cn/problem/P10866')
    return result


def receipt(identity, number, stamp, **extra):
    return dict(id=number, problem_id=identity, mode='submit', scope='official',
                verdict='AC', submitted_at=stamp, finished_at=stamp,
                solution_seen=0, code='fixture source', **extra)


class QuestionIdentityTests(unittest.TestCase):
    def test_only_reviewed_pair_is_same_question_and_native_urls_stay_distinct(self):
        variants = [*URLS, *PAIR_KEYS, *PAIR_IDS, *PAIR_HASHES,
                    URLS[0].replace('www.', '') + '?lang=zh', URLS[1] + '/']
        self.assertEqual({question_key(value) for value in variants}, {PAIR_KEY})
        self.assertEqual([canonical_url(value) for value in URLS], list(PAIR_KEYS))
        self.assertNotEqual(question_key(URLS[0].replace('P10865', 'P10866')), PAIR_KEY)
        self.assertNotEqual(question_key(URLS[1].replace('/H', '/I')), PAIR_KEY)
        self.assertIsNone(question_key('not a valid URL'))

    def test_catalogue_exposes_counting_aliases_without_changing_native_rows(self):
        before = rows()
        source = copy.deepcopy(before)
        result = unique_catalog_rows(before)
        self.assertEqual(len(result), 4)
        self.assertEqual({r['id'] for r in result[:2]}, set(PAIR_IDS))
        for row in result[:2]:
            self.assertEqual(row['questionKey'], PAIR_KEY)
            self.assertEqual(row['questionAliasKeys'], list(PAIR_KEYS))
            self.assertEqual(row['questionAliasIds'], list(PAIR_IDS))
            self.assertEqual(project_row(row)['questionKey'], PAIR_KEY)
            self.assertEqual(row['url'], source[PAIR_IDS.index(row['id'])]['url'])
        self.assertEqual(before, source, 'No caller/source metadata is rewritten')
        same_title = [dict(row, title='Same title') for row in source[2:]]
        self.assertEqual(len(unique_catalog_rows(same_title)), 2)

    def test_two_receipts_and_old_public_url_keys_are_one_true_first_ac(self):
        records = [receipt(PAIR_IDS[1], 'h', '2026-11-09T04:00:00Z'),
                   receipt(PAIR_IDS[0], 'lg', '2026-10-01T04:00:00Z')]
        result = official_reward_evidence(rows(), records)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['key'], PAIR_KEY)
        self.assertEqual(result[0]['problemId'], PAIR_IDS[0])
        self.assertEqual(result[0]['day'], '2026-10-01')
        self.assertEqual(official_reward_evidence(rows(), list(reversed(records))), result)
        hub = {'accounts': [{'platform': 'Luogu', 'solved': [
            {'url': PAIR_KEYS[0], 'acceptedAt': '2026-09-01T04:00:00Z'},
            {'url': PAIR_KEYS[1], 'acceptedAt': '2026-11-01T04:00:00Z'}]}]}
        snapshot = copy.deepcopy(hub)
        result = official_reward_evidence(rows(), records[:1], hub)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['day'], '2026-09-01')
        self.assertFalse(result[0]['independentKnown'])
        self.assertEqual(hub, snapshot)
        local = [dict(records[0], scope='local')]
        self.assertEqual(official_reward_evidence(rows(), local), [])

    def test_milestones_and_ability_do_not_gain_a_second_question(self):
        from progression import ac_achievements
        from ability_assessment import from_records, from_successes
        rewards = ac_achievements({PAIR_KEYS[0]: '2026-10-01T04:00:00Z',
                                  PAIR_KEYS[1]: '2026-11-01T04:00:00Z'})
        self.assertTrue(all(item['progress'] <= 1 for item in rewards))
        records = [receipt(PAIR_IDS[0], 'lg', '2026-10-01T04:00:00Z'),
                   receipt(PAIR_IDS[1], 'h', '2026-11-01T04:00:00Z')]
        learning = from_records(rows(), records, dt.datetime(2026, 11, 9, tzinfo=UTC))
        self.assertEqual(len(learning), 1)
        self.assertEqual(learning[0]['id'], PAIR_KEY)
        facts = [dict(key=key, acceptedAt='2026-10-01T04:00:00Z', scope='official',
                      independent=True, independentKnown=True, difficulty=1800) for key in PAIR_KEYS]
        self.assertEqual(len(from_successes(facts, dt.datetime(2026, 11, 9, tzinfo=UTC))), 1)

    def test_recommendations_cannot_offer_the_other_solved_native_entry(self):
        from insights import recommend_problems
        library = {row['id']: row for row in rows()[:2]}
        for solved in PAIR_IDS:
            with self.subTest(solved=solved):
                recommendations, _level, _basis = recommend_problems(
                    library, {}, {solved: (1800,)}, set(), {solved}, {}, ability=1800)
                self.assertEqual(recommendations, [])


class QuestionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-question-identity-')
        self.root = Path(self.temp.name)
        self.library, self.clock = Library(), Clock()
        self.library.rows = rows()
        self.clock.value = dt.datetime(2026, 11, 9, 4, tzinfo=UTC)
        self.no_queue = patch('leaderboard.LeaderboardClient.queue_sync')
        self.no_queue.start()
        self.service = TrainingService(self.library, self.root / 'personal.sqlite3',
                                       Assets(self.library), clock=self.clock,
                                       backup_dir=self.root / 'backups')

    def tearDown(self):
        self.service.close()
        self.no_queue.stop()
        self.temp.cleanup()

    def accept(self, identity, name, stamp='2026-11-09T04:00:00Z'):
        self.service.connection.execute(
            "INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope,solution_seen) VALUES(?,?,'submit','saved source',?,?,'AC','official',0)",
            (name, identity, stamp, stamp))

    def records(self):
        return [dict(row) for row in self.service.connection.execute('SELECT * FROM submissions')]

    def award_rows(self):
        return [tuple(row) for row in self.service.connection.execute('SELECT * FROM official_first_xp_awards ORDER BY problem_key')]

    def test_new_award_once_in_either_acceptance_order_and_history_unchanged(self):
        for identity, name in zip(PAIR_IDS, ['lg', 'h']):
            self.accept(identity, name)
        self.service.save_draft(PAIR_IDS[0], 'old LG source')
        self.service.save_draft(PAIR_IDS[1], 'old CF source')
        before = self.records()
        drafts = list(map(tuple, self.service.connection.execute('SELECT * FROM drafts')))
        first = self.service._first_acceptance_xp(self.library.rows, self.records())
        self.assertEqual(first, 200)
        self.assertEqual(len(self.award_rows()), 1)
        self.assertEqual(self.award_rows()[0][0], PAIR_KEY)
        self.assertEqual(self.service._first_acceptance_xp(self.library.rows, self.records()), first)
        self.assertEqual(self.records(), before)
        self.assertEqual(list(map(tuple, self.service.connection.execute('SELECT * FROM drafts'))), drafts)

    def test_existing_either_alias_award_is_not_issued_again_or_topped_up(self):
        self.accept(PAIR_IDS[1], 'new-h')
        for key in PAIR_KEYS:
            with self.subTest(old_key=key):
                self.service.connection.execute('DELETE FROM official_first_xp_awards')
                self.service.connection.execute('INSERT INTO official_first_xp_awards VALUES(?,?,?)',
                                                (key, '2026-01-01T00:00:00Z', 50))
                before = self.award_rows()
                self.assertEqual(self.service._first_acceptance_xp(self.library.rows, self.records()), 50)
                self.assertEqual(self.award_rows(), before)

    def test_two_already_paid_legacy_aliases_keep_both_amounts_without_new_reward(self):
        self.accept(PAIR_IDS[0], 'lg')
        self.accept(PAIR_IDS[1], 'h')
        self.service.connection.executemany('INSERT INTO official_first_xp_awards VALUES(?,?,?)',
            [(PAIR_KEYS[0], '2026-01-01T00:00:00Z', 150),
             (PAIR_KEYS[1], '2026-01-02T00:00:00Z', 200)])
        before = self.award_rows()
        self.assertEqual(self.service._first_acceptance_xp(self.library.rows, self.records()), 350)
        self.assertEqual(self.award_rows(), before)
        # A subsequent receipt keeps the same historical total, with no third row.
        self.accept(PAIR_IDS[1], 'h-again')
        self.assertEqual(self.service._first_acceptance_xp(self.library.rows, self.records()), 350)
        self.assertEqual(self.award_rows(), before)

    def test_both_unrated_legacy_rows_fill_only_one_award(self):
        self.accept(PAIR_IDS[1], 'h')
        self.service.connection.executemany('INSERT INTO official_first_xp_awards VALUES(?,?,0)',
            [(key, '2026-01-01T00:00:00Z') for key in PAIR_KEYS])
        self.assertEqual(self.service._first_acceptance_xp(self.library.rows, self.records()), 200)
        self.assertEqual([row[2] for row in self.award_rows()], [0, 200])

    def test_solved_exclusion_and_random_pool_deduplicate_questions_both_directions(self):
        plan = self.service.preview_contest({'count': 3, 'min': 0, 'max': 4000})['plan']
        self.assertEqual(len({question_key(next(r for r in self.library.rows if r['id'] == s['id']).get('url')) for s in plan['slots']}), 3)
        self.accept(PAIR_IDS[0], 'lg')
        solved = self.service._solved_problem_keys(self.library.rows)
        options = {'excludeSolved': True, 'platform': '', 'tags': [], 'reviewedOnly': False}
        for row in self.library.rows[:2]:
            self.assertFalse(self.service._eligible_contest_row(row, options, 0, 4000, solved))
        self.service.connection.execute('DELETE FROM submissions')
        self.accept(PAIR_IDS[1], 'h')
        solved = self.service._solved_problem_keys(self.library.rows)
        self.assertFalse(self.service._eligible_contest_row(self.library.rows[0], options, 0, 4000, solved))

    def test_old_ranking_receipt_for_either_alias_prevents_resend(self):
        self.accept(PAIR_IDS[1], 'h')
        endpoint = 'https://fixture.example'
        user = self.service._ranking_profile()['user_id']
        self.assertEqual(len(self.service._ranking_events(endpoint)), 1)
        for key in PAIR_KEYS:
            with self.subTest(key=key):
                self.service.connection.execute('DELETE FROM ranking_receipts')
                event = hashlib.sha256(('official-v1\0' + user + '\0' + hashlib.sha256(key.encode()).hexdigest()).encode()).hexdigest()
                self.service.connection.execute('INSERT INTO ranking_receipts VALUES(?,?,?)',
                                                (endpoint, event, '2026-01-01T00:00:00Z'))
                before = list(map(tuple, self.service.connection.execute('SELECT * FROM ranking_receipts')))
                self.assertEqual(self.service._ranking_events(endpoint), [])
                self.assertEqual(list(map(tuple, self.service.connection.execute('SELECT * FROM ranking_receipts'))), before)

    def test_global_first_date_is_old_but_today_repeat_remains_practice(self):
        self.accept(PAIR_IDS[0], 'lg', '2026-10-01T04:00:00Z')
        self.accept(PAIR_IDS[1], 'h')
        evidence = self.service._evidence(self.clock().date().isoformat())
        self.assertEqual(len(evidence), 1)
        self.assertFalse(evidence[0]['newProblem'])
        self.assertEqual(evidence[0]['day'], '2026-11-09')
        self.assertEqual(len(self.service._evidence()), 1)

    def test_goal_progress_and_new_list_entries_use_question_identity(self):
        from goals import Goals
        from custom_training_lists import save_list, add_problems
        planner = Goals(self.service)
        planner.save({'title': 'Question identity', 'deadline': '2026-11-10', 'totalProblems': 2})
        self.clock.advance(seconds=1)
        self.accept(PAIR_IDS[0], 'lg', self.clock().isoformat())
        self.accept(PAIR_IDS[1], 'h', self.clock().isoformat())
        goal = planner.list()['goals'][0]
        self.assertEqual(goal['progress'], 1)
        self.assertFalse(set(PAIR_IDS) & {item['id'] for item in goal['dailyTask']['problems']})
        saved = save_list(self.service, {'title': 'Question identity', 'problemIds': list(PAIR_IDS)})['list']
        self.assertEqual(len(saved['problems']), 1)
        self.assertEqual(saved['problems'][0]['problemId'], PAIR_IDS[0])
        result = add_problems(self.service, {'listIds': [saved['id']], 'problemIds': [PAIR_IDS[1]]})
        self.assertEqual(result['added'][saved['id']], 0)


if __name__ == '__main__':
    unittest.main()
