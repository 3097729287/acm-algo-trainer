"""URL-indexed official reward facts preserve local alias and receipt priority."""
import unittest
from unittest.mock import patch

import insights
from progression import official_reward_evidence


class RewardEvidenceTests(unittest.TestCase):
    url = 'https://codeforces.com/contest/123/problem/A'

    def hub(self, *records):
        return {'accounts': [{'platform': 'Codeforces', 'solved': list(records)}]}

    def test_hub_prefers_curated_alias_over_remote_and_retains_first_curated(self):
        rows = [
            {'id': 'remote', 'url': self.url, 'source': 'remote', 'difficulty': 2500},
            {'id': 'curated', 'url': self.url.replace('/contest/123/problem/A', '/problemset/problem/123/A'), 'source': 'archive', 'difficulty': 1700},
            {'id': 'second-curated', 'url': self.url, 'source': 'archive', 'difficulty': 1800},
        ]
        result = official_reward_evidence(rows, [], self.hub({'url': self.url, 'acceptedAt': '2026-10-15T00:00:00Z'}))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['difficulty'], 1700)
        rows[1]['difficulty'] = None
        self.assertIsNone(official_reward_evidence(rows, [], self.hub({'url': self.url, 'acceptedAt': '2026-10-15T00:00:00Z'}))[0]['difficulty'])

    def test_native_official_receipt_keeps_its_evidence_over_public_history(self):
        rows = [{'id': 'local', 'url': self.url, 'source': 'archive', 'difficulty': 1700}]
        submission = {'id': 'official-1', 'problem_id': 'local', 'mode': 'submit', 'scope': 'official',
                      'verdict': 'AC', 'submitted_at': '2026-10-15T00:00:00Z', 'finished_at': '2026-10-15T00:00:01Z', 'solution_seen': False}
        result = official_reward_evidence(rows, [submission], self.hub({'url': self.url, 'acceptedAt': '2026-01-01T00:00:00Z'}))
        self.assertEqual(result[0]['source'], 'submission')
        self.assertEqual(result[0]['difficulty'], 1700)
        self.assertTrue(result[0]['independent'])
        self.assertEqual(result[0]['acceptedAt'], '2026-10-15T00:00:00.000000Z')

    def test_undated_hub_fact_can_gain_timestamp_without_type_error(self):
        result = official_reward_evidence([], [], self.hub(
            {'url': self.url}, {'url': self.url, 'acceptedAt': '2026-10-15T00:00:00Z'},
            {'url': self.url, 'acceptedAt': '2026-10-16T00:00:00Z'}))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['acceptedAt'], '2026-10-15T00:00:00.000000Z')

    def test_url_lookup_is_linear_in_library_plus_public_evidence(self):
        rows = [{'id': str(index), 'url': f'https://codeforces.com/contest/123/problem/A{index}', 'difficulty': 1700}
                for index in range(200)]
        solved = [{'url': row['url'], 'acceptedAt': '2026-10-15T00:00:00Z'} for row in rows]
        with patch.object(insights, 'canonical_url', wraps=insights.canonical_url) as normalize:
            result = official_reward_evidence(rows, [], self.hub(*solved))
        self.assertEqual(len(result), 200)
        self.assertLessEqual(normalize.call_count, len(rows) + len(solved))


if __name__ == '__main__':
    unittest.main()
