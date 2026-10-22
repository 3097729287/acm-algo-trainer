"""All presentation categories retain canonical library names and techniques."""
import unittest
from knowledge import category_path,dictionary
from store import Store


class KnowledgeTaxonomyTests(unittest.TestCase):
    def test_every_canonical_technique_is_reachable_from_the_public_tree(self):
        def leaves(nodes):
            return {tag for node in nodes for tag in node['tags']}
        self.assertEqual(leaves(Store.__new__(Store).categories()),set(dictionary()['names']))

    def test_search_strategy_and_data_structures_have_consistent_homes(self):
        self.assertEqual(category_path('枚举'),'思维与策略')
        self.assertEqual(category_path('折半枚举'),'思维与策略')
        self.assertEqual(category_path('DFS'),'搜索')
        self.assertEqual(category_path('BFS'),'搜索')
        self.assertEqual(category_path('记忆化搜索'),'动态规划')
        self.assertEqual(category_path('哈希'),'数据结构')
        self.assertEqual(category_path('字典树'),'字符串')
        self.assertIn('图论',category_path('DFS 序'))
