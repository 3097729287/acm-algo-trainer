"""Evidence, rank compatibility and private metrics in disposable state."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import unittest
import test_training as fixtures
from admin import controls
from knowledge import analyze_problem,category_path,dictionary,normalize_tags
from tb_rank import TIERS,RANK_THRESHOLDS,rank_index
from training import ServiceError
from usage import record,snapshot

class PrivateMetricsTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept
    session='11111111-1111-4111-8111-111111111111'
    def tick(self,sequence,seconds=30):return record(self.service,{'sessionId':self.session,'sequence':sequence,'seconds':seconds})
    def test_usage_is_idempotent_and_overlapping_windows_do_not_double_count(self):
        self.tick(1);self.tick(1)
        self.assertEqual(snapshot(self.service)['totalSeconds'],30)
        self.clock.advance(seconds=10);self.tick(2)
        self.assertEqual(snapshot(self.service)['totalSeconds'],40)
        self.session='22222222-2222-4222-8222-222222222222';self.tick(1)
        self.assertEqual(snapshot(self.service)['totalSeconds'],40)
        for seconds in (-1,0,61,float('nan'),True):
            with self.assertRaises(ServiceError):self.tick(3,seconds)
    def test_usage_splits_beijing_midnight_and_is_read_only_on_query(self):
        self.clock.value=dt.datetime(2026,10,23,16,0,10,tzinfo=dt.timezone.utc)
        self.tick(1,30)
        self.assertEqual(snapshot(self.service)['days'],[{'date':'2026-10-23','seconds':20},{'date':'2026-10-24','seconds':10}])
        before=self.service.connection.total_changes;snapshot(self.service)
        self.assertEqual(self.service.connection.total_changes,before)
        self.clock.advance(seconds=70);self.tick(2,30)
        self.assertEqual(snapshot(self.service)['totalSeconds'],60)
    def test_metrics_use_real_official_ac_and_deduplicate_repeat_ac_same_day(self):
        self.accept();self.accept();self.accept('fixture::B')
        self.clock.advance(days=1);self.accept('fixture::C')
        value=self.service.insights()['personalStatistics']
        self.assertEqual(value['maxDailyAc'],2)
        self.assertEqual(value['longestAcStreak'],2)
        self.assertEqual(value['hardestSolved']['id'],'fixture::C')
    def test_broad_subject_counts_and_filters_keep_unknown_children_unknown(self):
        row=self.library.rows[0];row.update(tags=[],knowledgeCategories=['动态规划'])
        self.accept()
        entries={item['name']:item for item in self.service.insights()['knowledge']}
        self.assertEqual(entries['动态规划']['available'],1)
        self.assertEqual(entries['动态规划']['officialAccepted'],1)
        options={'platform':'','tags':['动态规划'],'excludeSolved':False,'reviewedOnly':False}
        self.assertTrue(self.service._eligible_contest_row(row,options,0,10000,set()))
        self.assertFalse(self.service._eligible_contest_row(row,{**options,'tags':['线性 DP']},0,10000,set()))
    def test_old_admin_rank_indexes_read_without_rewriting_and_new_save_is_stable(self):
        self.service.admin_mode=True
        with self.service._write() as connection:
            connection.execute("INSERT INTO account_preferences VALUES('admin-controls',?,?)",(json.dumps({'level':10,'tier':9,'allAchievements':False}),'2026-10-01'))
        before=self.service.connection.total_changes
        self.assertEqual(controls(self.service)['tier'],8)
        self.assertEqual(self.service.connection.total_changes,before)
        controls(self.service,{'level':10,'tier':4,'allAchievements':False})
        self.assertEqual(controls(self.service)['tier'],4)

class ReviewedKnowledgeTests(unittest.TestCase):
    def test_interactive_is_a_real_leaf_and_generic_title_is_not_algorithmic_evidence(self):
        self.assertEqual(normalize_tags(['interactive'],official=True)['tags'],['交互题'])
        self.assertNotIn('交互题',analyze_problem({'title':'交互题'},'给定数组，输出所有元素的 MEX。')['tags'])
        self.assertIn('交互题',analyze_problem({},'This is an interactive problem. Print a query and flush your output.')['tags'])
    def test_geometry_topics_have_the_same_parent_in_every_filter_tree(self):
        for name in ('平面向量','点积与叉积','线段相交','圆与切线','凸包','旋转卡壳','几何重心','半平面交','三维几何'):
            self.assertIn(name,dictionary()['names'])
            self.assertTrue(category_path(name).startswith('计算几何'),(name,category_path(name)))
    def test_every_targeted_annotation_binds_to_the_exact_public_solution(self):
        root=Path(__file__).resolve().parents[1]
        review=json.loads((root/'backend/resources/knowledge_topic_review.json').read_text(encoding='utf-8'))
        solutions={p['problem_id']:p['markdown'] for p in json.loads((root/'data/library/solutions.json').read_text(encoding='utf-8'))}
        for rule in review['problems'].values():
            for source in rule['sources']:
                identity=source['reference'].split('#')[-1]
                self.assertEqual(hashlib.sha256(solutions[identity].encode()).hexdigest(),source['sha256'],identity)
    def test_current_rank_ladder_has_nine_names_and_preserves_threshold_meanings(self):
        self.assertEqual(TIERS,('黑铁','青铜','白银','黄金','翡翠','钻石','大师','宗师','王者'))
        for index,boundary in enumerate(RANK_THRESHOLDS):self.assertEqual(rank_index(boundary),index)
