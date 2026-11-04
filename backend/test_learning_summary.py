"""Behavioral checks using disposable accounts, real SQLite and official fixtures."""
import datetime as dt
import json
import unittest
import test_training as fixtures
from learning_summary import LearningSummary, record_effective, effective_seconds, read, write, KEY
from training import ServiceError


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.ServiceTests(); self.case.setUp()
        self.t = self.case.service
        self.case.clock.value = dt.datetime(2026, 11, 5, 4, tzinfo=dt.timezone.utc)
        for index, row in enumerate(self.case.library.rows):
            row.update(url=f'https://codeforces.com/contest/999/problem/{chr(65+index)}', tags=['输入输出'],
                       catalogStatementReady=True, difficultySource='Codeforces 官方 rating')
        self.s = LearningSummary(self.t)

    def tearDown(self): self.case.tearDown()

    def configure(self, tracks=None, **config):
        v = self.s.refresh()
        return self.s.update({'action': 'configure', 'revision': v['revision'], 'tracks': tracks or ['io-basics'],
                              'config': {'weekdayMinutes': 60, 'weekendMinutes': 120, **config}})

    def accept(self, value):
        return self.s.update({'action': 'accept', 'revision': value['revision'], 'proposalId': value['proposal']['id']})

    def test_no_time_is_guessed_and_default_goal_is_bronze(self):
        value = self.s.refresh()
        self.assertIsNone(value['plan']); self.assertIsNone(value['proposal'])
        self.assertIsNone(value['config']['weekdayMinutes']); self.assertEqual(value['config']['goal']['title'], '区域赛铜牌')
        self.assertIn('填写', next(p['text'] for p in value['article'] if p['id'] == 'week'))

    def test_proposal_has_no_effect_until_adopted_and_budget_is_shared(self):
        value = self.configure(['io-basics', 'basic-control'])
        self.assertIsNone(value['plan'])
        value = self.accept(value)
        self.assertEqual(value['plan']['tracks'], ['io-basics', 'basic-control'])
        for day in value['plan']['days']: self.assertLessEqual(day['used'], day['minutes'])
        self.assertEqual(len({t['key'] for t in value['plan']['tasks']}), len(value['plan']['tasks']))

    def test_bad_or_stale_adoption_cannot_replace_accepted_plan(self):
        value = self.configure()
        with self.assertRaises(ServiceError): self.s.update({'action': 'accept', 'revision': 'stale', 'proposalId': value['proposal']['id']})
        self.assertIsNone(self.s.snapshot()['plan'])

    def test_reading_and_clock_never_imply_independent_mastery(self):
        value = self.accept(self.configure())
        task = next(t for t in value['plan']['tasks'] if t['kind'] == 'lecture')
        value = self.s.update({'action': 'complete', 'revision': value['revision'], 'key': task['key']})
        self.assertEqual(next(t for t in value['topics'] if t['id'] == 'io-basics')['level'], 1)
        now = self.case.clock.value.timestamp()
        record_effective(self.t, {'intervals': [[now-299, now]]})
        value = self.s.refresh()
        self.assertEqual(next(t for t in value['topics'] if t['id'] == 'io-basics')['independent'], 0)

    def test_wrong_quiz_fails_and_correct_quiz_only_proves_concept(self):
        value = self.configure()
        with self.assertRaises(ServiceError): self.s.update({'action': 'quiz', 'revision': value['revision'], 'topicId': 'io-basics', 'answer': 1})
        value = self.s.update({'action': 'quiz', 'revision': value['revision'], 'topicId': 'io-basics', 'answer': 0})
        self.assertEqual(next(t for t in value['topics'] if t['id'] == 'io-basics')['level'], 2)

    def test_official_acceptance_and_twenty_four_hour_retention_are_distinct(self):
        self.case.accept('fixture::A')
        value = self.s.refresh(); topic = next(t for t in value['topics'] if t['id'] == 'io-basics')
        self.assertEqual((topic['level'], topic['independent'], topic['retained']), (5, 1, 0))
        self.case.clock.advance(hours=23); self.case.accept('fixture::A')
        self.assertEqual(next(t for t in self.s.refresh()['topics'] if t['id'] == 'io-basics')['retained'], 0)
        self.case.clock.advance(hours=2); self.case.accept('fixture::A')
        self.assertEqual(next(t for t in self.s.refresh()['topics'] if t['id'] == 'io-basics')['retained'], 1)

    def test_assisted_acceptance_is_not_an_independent_solve(self):
        self.t.start_training('fixture::A', assisted=True)
        self.case.accept('fixture::A')
        topic = next(t for t in self.s.refresh()['topics'] if t['id'] == 'io-basics')
        self.assertEqual(topic['independent'], 0); self.assertEqual(topic['publicAccepted'], 1)

    def test_aliases_do_not_make_multiple_learning_events(self):
        self.case.library.rows[1]['url'] = 'https://codeforces.com/problemset/problem/999/A'
        self.case.accept('fixture::A'); self.case.accept('fixture::B')
        topic = next(t for t in self.s.refresh()['topics'] if t['id'] == 'io-basics')
        self.assertEqual(topic['independent'], 1)

    def test_delayed_history_survives_a_long_absence(self):
        self.case.accept('fixture::A'); self.case.clock.advance(days=140)
        self.assertEqual(next(t for t in self.s.refresh()['topics'] if t['id'] == 'io-basics')['independent'], 1)

    def test_effective_intervals_are_idempotent_and_union_overlapping_tabs(self):
        now = self.case.clock.value.timestamp()
        record_effective(self.t, {'intervals': [[now-120, now-60], [now-90, now]]})
        record_effective(self.t, {'intervals': [[now-120, now-60]]})
        self.assertEqual(effective_seconds(self.t), 120)
        with self.assertRaises(ServiceError): record_effective(self.t, {'intervals': [[now-300, now]]})

    def test_effective_intervals_split_at_beijing_midnight(self):
        self.case.clock.value = dt.datetime(2026, 11, 5, 16, 1, tzinfo=dt.timezone.utc)
        now = self.case.clock.value.timestamp()
        record_effective(self.t, {'intervals': [[now-120, now]]})
        self.assertEqual(self.t.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'effective-learning-day:%'").fetchone()[0], 2)

    def test_paragraph_acknowledgement_tracks_its_exact_version(self):
        value = self.s.refresh(); p = value['article'][0]
        value = self.s.update({'action': 'seen', 'revision': value['revision'], 'paragraphs': {p['id']: p['hash']}})
        self.assertEqual(value['seen'][p['id']], p['hash'])
        value = self.s.update({'action': 'seen', 'revision': value['revision'], 'paragraphs': {p['id']: 'wrong'}})
        self.assertEqual(value['seen'][p['id']], p['hash'])

    def test_cross_week_preserves_history_and_same_stage_continues(self):
        value = self.accept(self.configure()); old_stage = value['plan']['stage']
        self.case.clock.advance(days=7); value = self.s.refresh()
        self.assertEqual(value['plan']['stage'], old_stage); self.assertTrue(value['history'])
        old = self.s.history(value['history'][0]['id']); self.assertNotEqual(old['plan']['week'], value['plan']['week'])

    def test_history_deletion_preserves_submissions_and_drafts(self):
        value = self.accept(self.configure()); self.case.accept('fixture::A')
        self.t.save_draft('fixture::A', 'personal code')
        self.case.clock.advance(days=7); value = self.s.refresh()
        before = [tuple(r) for r in self.t.connection.execute('SELECT * FROM drafts')]
        count = self.t.connection.execute('SELECT COUNT(*) FROM submissions').fetchone()[0]
        self.s.update({'action': 'delete-history', 'revision': value['revision'], 'id': value['history'][0]['id']})
        self.assertEqual(before, [tuple(r) for r in self.t.connection.execute('SELECT * FROM drafts')])
        self.assertEqual(count, self.t.connection.execute('SELECT COUNT(*) FROM submissions').fetchone()[0])

    def test_difficulty_does_not_silently_replace_tasks(self):
        value = self.accept(self.configure()); identity = value['plan']['id']
        original = json.loads(json.dumps(value['plan']))
        value = self.s.update({'action': 'difficulty', 'revision': value['revision'], 'reason': 'hard'})
        self.assertEqual(value['plan'], original)
        self.assertEqual(value['proposal']['pace'], 'foundation')
        self.assertTrue(any(task['kind'] == 'lecture' for task in value['proposal']['tasks']))
        value = self.accept(value)
        self.assertNotEqual(value['plan']['id'], identity)
        self.assertEqual(value['plan']['pace'], 'foundation')

    def test_too_easy_offers_practice_and_keeps_existing_facts(self):
        value = self.accept(self.configure()); before = json.loads(json.dumps(value['topics']))
        identity = value['plan']['id']
        value = self.s.update({'action': 'difficulty', 'revision': value['revision'], 'reason': 'easy'})
        self.assertEqual(value['plan']['id'], identity)
        self.assertEqual(value['topics'], before)
        self.assertEqual(value['proposal']['pace'], 'practice')
        self.assertFalse(any(task['kind'] in ('lecture', 'course', 'quiz', 'template-problem') for task in value['proposal']['tasks'] if task['status'] != 'done'))
        self.assertTrue(any(task['kind'] == 'problem' for task in value['proposal']['tasks']))

    def test_established_ability_recommends_algorithms_without_inventing_basic_mastery(self):
        value = self.s.refresh(); before = json.loads(json.dumps(value['topics']))
        tracks = self.s._default_tracks(value['topics'], {'qualified': True, 'abilityScore': 1100})
        self.assertEqual(tracks, ['prefix-difference'])
        self.assertEqual(value['topics'], before)
        self.assertTrue(all(topic['level'] == 0 for topic in value['topics']))

    def test_demonstrated_advanced_topic_does_not_restart_at_missing_io_tags(self):
        value = self.s.refresh()
        advanced = next(topic for topic in value['topics'] if topic['id'] == 'sorting-basics')
        advanced['level'] = 5
        tracks = self.s._default_tracks(value['topics'])
        self.assertNotIn(tracks[0], ['io-basics', 'basic-control', 'arrays', 'functions'])

    def test_unknown_manual_completion_cannot_fake_official_ac(self):
        value = self.accept(self.configure()); task = next(t for t in value['plan']['tasks'] if t['kind'] == 'problem')
        with self.assertRaises(ServiceError): self.s.update({'action': 'complete', 'revision': value['revision'], 'key': task['key']})

    def test_active_contest_preserves_previous_article_and_blocks_replanning(self):
        value = self.accept(self.configure()); before = value['article']
        self.case.contest(count=2, duration=30)
        value = self.s.refresh(); self.assertEqual(value['article'], before)
        with self.assertRaises(ServiceError): self.s.update({'action': 'propose', 'revision': value['revision'], 'tracks': ['arrays']})

    def test_all_rest_days_do_not_create_impossible_tasks(self):
        value = self.configure(restDays=list(range(7)))
        self.assertFalse(value['proposal']['tasks']); self.assertTrue(value['proposal']['waiting'])

    def test_mixed_check_starts_explicitly_and_requires_post_contest_reflection(self):
        value = self.accept(self.configure())
        task = next(t for t in value['plan']['tasks'] if t['kind'] == 'mixed')
        result = self.s.start({'planId': value['plan']['id'], 'key': task['key']})
        self.assertEqual(self.t.active_contest()['id'], result['contest']['id'])
        self.t.finish_contest(result['contest']['id'])
        value = self.s.refresh()
        self.assertNotEqual(next(t for t in value['plan']['tasks'] if t['key'] == task['key'])['status'], 'done')
        value = self.s.update({'action': 'reflect', 'revision': value['revision'], 'key': task['key'], 'note': '本次练习要继续检查边界条件'})
        self.assertEqual(next(t for t in value['plan']['tasks'] if t['key'] == task['key'])['status'], 'done')

    def test_replace_keeps_date_and_budget_and_uses_an_actual_different_original(self):
        value = self.accept(self.configure()); task = next(t for t in value['plan']['tasks'] if t['kind'] == 'problem')
        before = dict(task)
        value = self.s.update({'action': 'replace', 'revision': value['revision'], 'key': task['key']})
        replacement = next(t for t in value['plan']['tasks'] if t['order'] == before['order'])
        self.assertNotEqual(replacement['original'], before['original'])
        self.assertEqual((replacement['date'], replacement['minutes']), (before['date'], before['minutes']))

    def test_summary_retention_opens_a_separate_blank_draft(self):
        self.case.accept('fixture::A'); self.t.save_draft('fixture::A', 'old personal code')
        value = self.accept(self.configure()); task = next(t for t in value['plan']['tasks'] if t['kind'] == 'review')
        self.case.clock.advance(hours=25)
        opened = self.t.start_training(task['id'], restore_review_id=task['reviewId'], defer_workspace=True)
        self.assertTrue(opened['reviewTask']['openedAt'])
        code = self.t.problem(task['id'], review_id=task['reviewId'])['draft']
        self.assertNotIn('old personal code', str(code))
        self.assertEqual(self.t.connection.execute("SELECT COUNT(*) FROM drafts WHERE code='old personal code'").fetchone()[0], 1)

if __name__ == '__main__': unittest.main()
