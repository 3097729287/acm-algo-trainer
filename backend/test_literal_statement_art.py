import copy
import json
from pathlib import Path
import re
import unittest

from statement_cleanup import clean_statement
from statement_format import html_markdown,needs_statement_refresh,nowcoder_statement

FIXTURES=Path(__file__).parent/'fixtures/statements'
DIAMOND='  *\n ***\n*****\n ***\n  *'


class LiteralStatementArtTests(unittest.TestCase):
    def test_official_nowcoder_html_retains_diamond_indentation(self):
        source=(FIXTURES/'nowcoder-214218.html').read_text(encoding='utf8')
        body=nowcoder_statement(source,'https://ac.nowcoder.com/acm/problem/214218')
        self.assertIn('```text\n'+DIAMOND+'\n```',body)
        self.assertIn('1 <= n<= 49',body)
        self.assertIn('每行行末不要有空格',body)
        self.assertNotIn('复制',body)

    def test_old_cached_statement_is_corrected_offline_without_changing_samples(self):
        source=json.loads((FIXTURES/'nowcoder-214218-legacy.json').read_text(encoding='utf8'))
        before=copy.deepcopy(source);value=clean_statement(source)
        self.assertIn('```text\n'+DIAMOND+'\n```',value['markdown'])
        self.assertEqual(value['samples'],source['samples'])
        self.assertEqual(source,before)
        self.assertFalse(needs_statement_refresh(value))
        altered=dict(source,markdown=source['markdown']+'\n新题面')
        self.assertIn('新题面',clean_statement(altered)['markdown'])
        self.assertTrue(needs_statement_refresh(source))

    def test_symbols_are_literal_while_normal_lists_and_preformatted_code_survive(self):
        source='<p>画出图形：</p><p>&nbsp;#</p><p>###</p><p>&nbsp;#</p><ul><li>第一条</li><li>第二条</li></ul><pre>  a\n\n    b\n</pre>'
        value=html_markdown(source,prose_pre=True)
        self.assertIn('```text\n #\n###\n #\n```',value)
        self.assertIn('- 第一条',value)
        self.assertIn('- 第二条',value)

    def test_fenced_stars_do_not_cause_background_refetch(self):
        self.assertFalse(needs_statement_refresh({'url':'https://ac.nowcoder.com/acm/problem/1','statementVersion':7,'markdown':'例子\n\n```text\n*\n***\n*\n```'}))
