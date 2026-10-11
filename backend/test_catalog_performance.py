"""Fresh request views remove redundant work without freezing public metadata."""
import threading
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


if __name__ == '__main__':
    unittest.main()
