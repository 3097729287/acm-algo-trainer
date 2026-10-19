"""Exports, receipt-only task notifications and bounded background statistics."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from data_export import export_data
from preferences import save_preferences, read_preferences
from statement_format import html_markdown, nowcoder_statement
import test_training as fixtures


class JournalTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    accept = fixtures.ServiceTests.accept

    def test_export_is_read_only_json_and_retains_learning_not_credentials(self):
        self.service.start_training('fixture::A')
        self.service.save_draft('fixture::A', '// 中文草稿\nint main(){}')
        self.accept()
        with self.service._write() as connection:
            connection.execute("UPDATE ranking_profile SET auth_token='PRIVATE_TOKEN'")
            connection.execute("INSERT INTO account_preferences VALUES('translation-secret','{\"apiKey\":\"PRIVATE_API_KEY\"}','2026-10-08')")
        changes=self.service.connection.total_changes
        result=json.loads(json.dumps(export_data(self.service),ensure_ascii=False))
        self.assertEqual(self.service.connection.total_changes,changes)
        self.assertEqual((result['format'],result['formatVersion']),('tb-learning-export',1))
        self.assertEqual(result['tables']['drafts'][0]['code'],'// 中文草稿\nint main(){}')
        self.assertEqual(result['tables']['submissions'][0]['verdict'],'AC')
        self.assertIn('goal_daily_assignments',result['tables'])
        self.assertNotIn('PRIVATE_TOKEN',json.dumps(result))
        self.assertNotIn('PRIVATE_API_KEY',json.dumps(result))

    def test_claim_finishes_without_computing_insights_or_assigning_goals(self):
        self.accept()
        with patch.object(self.service,'insights',side_effect=AssertionError('heavy read on claim')), \
             patch('goals.Goals.list',side_effect=AssertionError('goal assignment on claim')):
            value=self.service.claim_daily_task('solve-1')
        self.assertEqual(value['awardedXp'],25)
        self.assertEqual(value['dailyTasks']['claimable'],0)
        self.assertTrue(value['dailyTasks']['tasks'][0]['claimed'])
        self.assertEqual(self.service.insights()['growth']['missionXp'],25)

    def test_insights_cache_invalidates_on_writes_library_changes_and_day(self):
        import insights
        signature=[1]
        self.library.library=SimpleNamespace(content_signature=lambda:signature[0])
        with patch('insights.build_insights',wraps=insights.build_insights) as build:
            first=self.service.insights()
            first['summary']['totalSolved']=9999
            self.assertNotEqual(self.service.insights()['summary']['totalSolved'],9999)
            self.assertEqual(build.call_count,1)
            self.service.save_draft('fixture::A','int main(){}')
            self.service.insights();self.assertEqual(build.call_count,2)
            signature[0]+=1
            self.service.insights();self.assertEqual(build.call_count,3)
            self.clock.advance(days=1)
            self.service.insights();self.assertEqual(build.call_count,4)

    def test_new_preferences_are_validated_and_tutorial_completion_is_monotonic(self):
        save_preferences(self.service,{'preferences':{'showPlatforms':False,'onboardingCompleted':True}})
        save_preferences(self.service,{'preferences':{'showPlatforms':True,'onboardingCompleted':False}})
        self.assertTrue(read_preferences(self.service)['preferences']['onboardingCompleted'])
        with self.assertRaises(fixtures.ServiceError):
            save_preferences(self.service,{'preferences':{'showPlatforms':'no'}})
        from account_sync import merge_states
        def state(done,stamp):
            return {'tables':{'account_preferences':[{'key':'ui','value':json.dumps({'onboardingCompleted':done}),'updated_at':stamp}]},'publicAccounts':{}}
        merged=merge_states(state(True,'2026-10-08'),state(False,'2026-10-09'))
        self.assertTrue(json.loads(merged['tables']['account_preferences'][0]['value'])['onboardingCompleted'])


class StatementTests(unittest.TestCase):
    def test_lists_code_tables_formula_and_images_survive(self):
        value=html_markdown('<h2>Description</h2><p>Let <var>a_i &lt; n</var>.</p><ul><li>one</li><li>two</li></ul><pre>2 3\n1 2 3\n</pre><table><tr><th>n</th><th>v</th></tr><tr><td>1</td><td>2</td></tr></table><img src="/image.png">','https://example.com/task')
        for expected in ('## Description','$a_i < n$','- one','- two','```text\n2 3\n1 2 3\n```','| --- | --- |','https://example.com/image.png'):
            self.assertIn(expected,value)

    def test_nowcoder_preserves_latex_and_omits_copy_widgets_and_flat_samples(self):
        value=nowcoder_statement('<h2 class="subject-item-title">题目描述</h2><div class="subject-describe">数组<img src="https://www.nowcoder.com/equation?tex=a_1%2Ca_2%2C%5Cdots%2Ca_n"><h2>输入描述:</h2><pre>第一行<br>第二行</pre></div><div class="question-oi">示例1 输入 复制 5 3 1 2 3 4 5</div>','https://ac.nowcoder.com/acm/contest/1/A')
        self.assertIn('$a_1,a_2,\\dots,a_n$',value)
        self.assertIn('第一行\n第二行',value)
        self.assertNotIn('复制',value)
        self.assertNotIn('示例1',value)


if __name__=='__main__':unittest.main()
