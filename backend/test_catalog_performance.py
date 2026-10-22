"""Fresh request views remove redundant work without freezing public metadata."""
import threading
from contextlib import closing
import json
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import knowledge
import test_training as fixtures


class CatalogViewTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def test_insights_reads_one_catalog_and_the_next_request_is_fresh(self):
        with patch.object(self.library, 'data', wraps=self.library.data) as read:
            self.service.insights()
            self.assertEqual(read.call_count, 1)
            self.library.rows[0]['title'] = 'Updated public title'
            self.service.insights()
            self.assertEqual(read.call_count, 2)
            self.assertEqual(self.service._row('fixture::A')['title'], 'Updated public title')

    def test_snapshot_is_released_on_error_and_does_not_cross_threads(self):
        other = []
        with patch.object(self.library, 'data', wraps=self.library.data) as read:
            with self.assertRaisesRegex(RuntimeError, 'fixture'):
                with self.service._library_view():
                    self.service._library().clear()
                    self.assertEqual(len(self.service._library()), 8)
                    self.library.rows[0]['title'] = 'Concurrent update'
                    worker = threading.Thread(target=lambda: other.append(self.service._library()[0]['title']))
                    worker.start()
                    worker.join(2)
                    self.assertFalse(worker.is_alive())
                    self.assertEqual(other, ['Concurrent update'])
                    self.assertNotEqual(self.service._library()[0]['title'], other[0])
                    raise RuntimeError('fixture')
            self.assertEqual(self.service._library()[0]['title'], 'Concurrent update')
            self.assertEqual(read.call_count, 3)


class DictionaryIndexTests(unittest.TestCase):
    def test_changed_names_aliases_and_parent_chain_take_effect_immediately(self):
        table = {'names': ['First'], 'aliases': {'alias': 'First'}, 'groups': {'Old': ['First']}}
        with patch.object(knowledge, 'dictionary', return_value=table):
            self.assertEqual(knowledge.canonical_tag(' FIRST '), 'First')
            self.assertEqual(knowledge.category_path('First'), 'Old')
            table['names'].append('Second')
            table['aliases']['alias'] = 'Second'
            table['groups'] = {'New': ['Second']}
            self.assertEqual(knowledge.canonical_tag('second'), 'Second')
            self.assertEqual(knowledge.canonical_tag('alias'), 'Second')
            self.assertEqual(knowledge.category_path('Second'), 'New')


class PersonalReadCacheTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def enable_cache(self):
        self.library.library = SimpleNamespace(content_signature=lambda: json.dumps(self.library.rows, sort_keys=True))

    def test_unchanged_reads_skip_catalog_and_results_remain_independent(self):
        self.enable_cache()
        self.service.start_training('fixture::A')
        first = self.service.workspace()
        self.service.insights()
        self.service.workspace()  # Analytics may persist newly assigned daily tasks.
        with patch.object(self.library, 'data', side_effect=AssertionError('unchanged catalog decoded')):
            second = self.service.workspace()
            second['training'][0]['title'] = 'Consumer edit'
            self.assertEqual(self.service.workspace()['training'][0]['title'],first['training'][0]['title'])
            insights = self.service.insights()
            self.assertEqual(insights['growth']['newAchievementXp'],0)

    def test_writes_external_commits_catalog_and_date_invalidate(self):
        self.enable_cache()
        self.service.start_training('fixture::A')
        self.service.workspace()
        with patch.object(self.library,'data',wraps=self.library.data) as read:
            self.service.save_draft('fixture::A','new draft')
            self.service.workspace()
            self.assertGreater(read.call_count,0)
            read.reset_mock()
            with closing(sqlite3.connect(self.db)) as writer:
                writer.execute("UPDATE training SET active=0 WHERE id='fixture::A'")
                writer.commit()
            self.assertEqual(self.service.workspace()['summary']['total'],0)
            self.assertGreater(read.call_count,0)
            read.reset_mock()
            self.library.rows[0]['title']='New public title'
            self.service.workspace()
            self.assertGreater(read.call_count,0)
            read.reset_mock()
            self.clock.advance(days=1)
            self.service.workspace()
            self.assertGreater(read.call_count,0)


if __name__ == '__main__':
    unittest.main()
