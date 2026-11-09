"""Pure event-text cache bounds without caching row/account policy decisions."""
import unittest
from unittest.mock import patch

import contest_scope


class EventTextMemoTests(unittest.TestCase):
    def setUp(self):contest_scope._cached_excluded_event_text.cache_clear()
    def tearDown(self):contest_scope._cached_excluded_event_text.cache_clear()

    def test_retirement_wiki_and_removal_are_never_cached_by_event(self):
        row={'id':'probe','url':'https://codeforces.com/contest/1/problem/A','contest':'ICPC China Regional','platform':'Codeforces'}
        with patch.object(contest_scope,'removals',return_value=(set(),set())):
            self.assertFalse(contest_scope.excluded(row))
            self.assertTrue(contest_scope.excluded({**row,'platform':'HDU'}))
            with patch.object(contest_scope,'removals',return_value=({'probe'},set())):
                self.assertTrue(contest_scope.excluded(row))
            final={**row,'contest':'ICPC World Finals'}
            self.assertTrue(contest_scope.excluded(final))
            with patch.object(contest_scope,'requested_wiki_examples',return_value={'probe':row['url']}):
                self.assertFalse(contest_scope.excluded({**final,'wikiExample':True}))
                self.assertTrue(contest_scope.excluded({**final,'wikiExample':True,'platform':'HDU'}))

    def test_long_custom_labels_do_not_enter_global_cache(self):
        text='ICPC '+('x'*4097)+' World Finals'
        expected=contest_scope._uncached_excluded_event_text(text)
        self.assertEqual(contest_scope._excluded_event_text(text),expected)
        self.assertEqual(contest_scope._cached_excluded_event_text.cache_info().currsize,0)
        with patch.object(contest_scope,'_uncached_excluded_event_text',wraps=contest_scope._uncached_excluded_event_text) as original:
            self.assertTrue(contest_scope._excluded_event_text('ICPC World Finals'))
            self.assertTrue(contest_scope._excluded_event_text('ICPC World Finals'))
            self.assertEqual(original.call_count,1)

    def test_process_cache_has_a_hard_entry_limit(self):
        for index in range(4097):contest_scope._excluded_event_text('Ordinary regional '+str(index))
        self.assertEqual(contest_scope._cached_excluded_event_text.cache_info().currsize,4096)
        self.assertEqual(contest_scope._cached_excluded_event_text.cache_info().maxsize,4096)


if __name__=='__main__':unittest.main()
