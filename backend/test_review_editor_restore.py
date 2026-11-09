"""Accepted rewrite restoration uses only disposable native receipt fixtures."""
import unittest

import test_training as fixtures
from reviews import reward_totals
from training import TrainingService, iso


class ReviewEditorRestoreTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    completed = fixtures.ServiceTests.completed

    def official(self, code, language='cpp17', review=None, verdict='AC', remote=None,
                 submitted=None, external=False):
        return self.service.record_official({
            'id': 'fixture::A', 'url': self.assets.problem('fixture::A')['url'],
            'code': code, 'language': language, 'reviewId': review, 'external': external,
        }, {'status': 'finished', 'verdict': verdict,
            'submissionId': str(remote or fixtures._next_official_id()),
            'acceptedAt': submitted or iso(self.clock())})

    def first_round(self):
        self.service.save_draft('fixture::A', 'int main() {}')
        self.official('old wrong answer', verdict='WA')
        self.clock.advance(seconds=1)
        self.official('old accepted code')
        self.clock.advance(days=1)
        return self.open_round()

    def open_round(self):
        task = next(t for t in self.service.review_plan()['tasks'] if t['problemId'] == 'fixture::A')
        fresh = self.service.problem('fixture::A', review_id=task['id'])
        self.assertEqual((fresh['draft'], fresh['draftSavedAt']), ('', None))
        return task['id']

    def restart(self):
        self.service.close()
        self.service = TrainingService(self.library, self.db, self.assets, self.judge,
                                       self.clock, self.root / 'backups')

    def assert_editor(self, code, language, receipt=None):
        result = self.service.problem('fixture::A')
        self.assertEqual((result['draft'], result['draftLanguage']), (code, language))
        if receipt:
            self.assertEqual(result['draftSource'], 'official-review')
            self.assertEqual(result['draftSubmissionId'], receipt['id'])
        return result

    def test_two_rewrites_two_languages_restart_and_out_of_order_receipts(self):
        first = self.first_round()
        cpp = 'int main() { return 42; } // accepted rewrite one'
        self.service.save_draft('fixture::A', cpp, review_id=first)
        one = self.official(cpp, review=first, remote=90000)
        self.assert_editor(cpp, 'cpp17', one)
        self.assertEqual(self.service.connection.execute(
            "SELECT code FROM drafts WHERE problem_id='fixture::A' AND context=''"
        ).fetchone()[0], 'int main() {}', 'The earlier ordinary draft remains recoverable')
        self.restart()
        self.assert_editor(cpp, 'cpp17', one)
        self.assertEqual(self.service.problem('fixture::A', review_id=first)['draft'], cpp)

        self.clock.advance(days=10)
        second = self.open_round()
        self.assertNotEqual(first, second)
        python = 'print(42)  # accepted rewrite two\n'
        self.service.save_draft('fixture::A', python, language='python3', review_id=second)
        two = self.official(python, language='python3', review=second, remote=90002)
        self.assertEqual(two['language'], 'python3', 'Language is committed with the receipt')
        self.assert_editor(python, 'python3', two)
        rewards_before = reward_totals(self.service)
        # A distinct older receipt finishes late; even equal-second accepts
        # use the site's submission sequence rather than SQLite arrival rowid.
        self.clock.advance(minutes=5)
        self.official('older same-second C++', review=second, remote=90001,
                      submitted=two['submittedAt'])
        self.official(cpp, review=first, remote=89999, submitted=one['submittedAt'])
        self.official(python, language='python3', review=second, remote=90002,
                      submitted=two['submittedAt'])
        self.assert_editor(python, 'python3', two)
        self.assertEqual(reward_totals(self.service), rewards_before)
        self.restart()
        self.assert_editor(python, 'python3', two)
        self.assertEqual(self.service.problem('fixture::A', review_id=first)['draft'], cpp)
        self.assertEqual(self.service.problem('fixture::A', review_id=second)['draft'], python)

    def test_newer_ordinary_edits_and_deliberate_blank_remain_current(self):
        review = self.first_round()
        self.service.save_draft('fixture::A', 'accepted rewrite', review_id=review)
        self.official('accepted rewrite', review=review)
        # Exact-timestamp edits are also protected conservatively.
        self.service.save_draft('fixture::A', 'my new experiment', language='python3')
        result = self.assert_editor('my new experiment', 'python3')
        self.assertNotIn('draftSource', result)
        self.clock.advance(seconds=1)
        self.service.save_draft('fixture::A', '', language='python3')
        self.restart()
        result = self.assert_editor('', 'python3')
        self.assertIsNotNone(result['draftSavedAt'])
        self.assertEqual(self.service.problem('fixture::A', review_id=review)['draft'], 'accepted rewrite')

    def test_local_samples_and_pending_official_result_do_not_restore_code(self):
        review = self.first_round()
        result = self.completed(code='local test pass', language='python3', review_id=review)
        self.assertEqual(result['submission']['verdict'], 'SAMPLE_PASS')
        self.assert_editor('int main() {}', 'cpp17')
        pending = self.service.record_official({
            'id': 'fixture::A', 'url': self.assets.problem('fixture::A')['url'],
            'code': 'not accepted', 'language': 'python3', 'reviewId': review,
        }, {'status': 'judging', 'submissionId': '91000', 'verdict': 'AC'})
        self.assertIsNone(pending)
        self.assert_editor('int main() {}', 'cpp17')
        self.assertTrue(any(t['id'] == review for t in self.service.review_plan()['tasks']))

    def test_source_less_receipt_then_real_source_enrichment_is_atomic(self):
        review = self.first_round()
        submitted = iso(self.clock())
        empty = self.official('', language='python3', review=review, remote=92000, external=True)
        self.assert_editor('int main() {}', 'cpp17')
        self.restart()
        source = 'print("restored official source")\n'
        enriched = self.official(source, language='python3', review=review,
                                 remote=92000, submitted=submitted)
        self.assertEqual(enriched['id'], empty['id'])
        self.assertEqual(enriched['language'], 'python3')
        self.assert_editor(source, 'python3', enriched)

    def test_legacy_language_enrichment_requires_the_same_immutable_source(self):
        review = self.first_round()
        source = 'print("legacy source with no language fact")\n'
        accepted = self.official(source, review=review, remote=92500)
        enriched = self.official(source, language='python3', review=review, remote=92500,
                                 submitted=accepted['submittedAt'])
        self.assertEqual(enriched['language'], 'python3')
        self.official('conflicting old source', language='cpp17', review=review,
                      remote=92500, submitted=accepted['submittedAt'])
        self.assert_editor(source, 'python3', accepted)
        # An uncertain old draft timestamp is preserved, never a load error.
        with self.service._write() as db:
            db.execute("UPDATE drafts SET saved_at='legacy-unknown' WHERE context='' AND problem_id='fixture::A'")
        self.assert_editor('int main() {}', 'cpp17')

    def test_problem_reads_preserve_all_physical_drafts_and_reject_forged_local_ac(self):
        review = self.first_round()
        self.service.save_draft('fixture::A', 'real review source', review_id=review)
        accepted = self.official('real review source', review=review)
        with self.service._write() as db:
            db.execute('INSERT INTO drafts VALUES(?,?,?,?)',
                       ('fixture::A', 'other-private-context', 'keep other context', iso(self.clock())))
            db.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope,message) VALUES(?,?,'submit',?,?,?,'AC','official',?)",
                       ('local-looking-accept', 'fixture::A', 'must not be restored',
                        '2099-01-01T00:00:00Z', '2099-01-01T00:00:01Z', 'local result'))
            db.execute('INSERT INTO account_preferences VALUES(?,?,?)',
                       ('review-receipt:local-looking-accept', '"' + review + '"', iso(self.clock())))
        before = [tuple(r) for r in self.service.connection.execute('SELECT * FROM drafts ORDER BY context')]
        for _ in range(3):
            self.assert_editor('real review source', 'cpp17', accepted)
        self.assertEqual([tuple(r) for r in self.service.connection.execute(
            'SELECT * FROM drafts ORDER BY context')], before)


if __name__ == '__main__':
    unittest.main()
