"""Prebuilt public text remains offline, current and safe across upgrades."""
import hashlib
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest

from assets import AssetLibrary
from library import LibraryDatabase
from translation import (TRANSLATION_FORMAT, TranslationService,
                         bundled_translation, english_prose, protect, validate_translation)

SOURCE=('##################################################\n# A. Train Car\n'
        '# 来源：https://atcoder.jp/contests/fixture/tasks/fixture_a\n'
        '##################################################\n\n'
        'Given a positive integer $N$, print twice its value.\n\n'
        '## Input\n\n```text\n3\n```\n')
CHINESE=SOURCE.replace('Train Car','火车车厢').replace(
    'Given a positive integer $N$, print twice its value.',
    '给定一个正整数 $N$，输出它的两倍。').replace('Input','输入')

def translation(source=SOURCE,markdown=CHINESE):
    return {'kind':'bundled','markdown':markdown,'provider':'预置中文译文',
            'sourceLanguage':'en','targetLanguage':'zh-CN',
            'sourceHash':hashlib.sha256(source.encode()).hexdigest(),'format':TRANSLATION_FORMAT}

def statement(source=SOURCE):
    return {'id':'fixture','title':'Train Car','url':'https://atcoder.jp/contests/fixture/tasks/fixture_a',
            'markdown':source,'samples':[{'input':'3\n','output':'6\n'}],
            'statementAvailable':True,'limits':{'timeMs':2000,'memoryMb':256}}

class BundledTranslationTests(unittest.TestCase):
    def test_default_chinese_survives_validation_and_seed_merge(self):
        prepared=dict(translation(),defaultLanguage='zh-CN')
        self.assertEqual(bundled_translation(dict(statement(),translation=prepared))['defaultLanguage'],'zh-CN')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);seed=LibraryDatabase(root/'seed.sqlite3');live=LibraryDatabase(root/'live.sqlite3')
            seed.save_statement('fixture',dict(statement(),translation=prepared))
            live.save_statement('fixture',dict(statement(),fetchedAt='local-cache'))
            live.merge_seed(seed.path)
            self.assertEqual(live.statement('fixture')['translation']['defaultLanguage'],'zh-CN')
            self.assertEqual(live.statement('fixture')['fetchedAt'],'local-cache')
            site={'kind':'site','markdown':CHINESE,'sourceUrl':statement()['url']}
            live.save_statement('fixture',dict(statement(),translation=site,fetchedAt='site-cache'))
            seed.save_statement('fixture',dict(statement(),translation=dict(site,defaultLanguage='zh-CN')))
            live.merge_seed(seed.path,fingerprint='site-default')
            self.assertEqual(live.statement('fixture')['translation']['defaultLanguage'],'zh-CN')
            self.assertEqual(live.statement('fixture')['fetchedAt'],'site-cache')
            edited=dict(site,markdown=CHINESE+' local edit')
            live.save_statement('fixture',dict(statement(),translation=edited))
            live.merge_seed(seed.path,fingerprint='keep-local-site-edit')
            self.assertNotIn('defaultLanguage',live.statement('fixture')['translation'])

    def test_spaced_inline_math_never_masks_english_between_normal_inline_variables(self):
        formula='$ $(0,0) \\xrightarrow{\\texttt{long}} (2,0) \\xrightarrow{\\texttt{long}} (4,0)$ $'
        source='A valid sequence is: '+formula+'.\nGiven $N$ $M$, print the result using the following positive integer values.\n'
        values=protect(source)[1].values()
        self.assertIn(formula,values)
        self.assertIn('print the result',english_prose(source))
        with self.assertRaises(Exception):validate_translation(source,source)

    def test_literal_lists_and_unformatted_math_are_not_untranslated_sentences(self):
        source='Given a list of strings, compute the number of different values.\n\nFor example: aaaa, aaabb, aaa, aaab, bb, aaab, ab, b, bb.\n\ndis(u,v)+dis(v,w)+dis(w,u)\n'
        translated=source.replace('Given a list of strings, compute the number of different values.','给定一个字符串列表，计算不同取值的数量。').replace('For example:','例如：')
        validate_translation(source,translated)
        with self.assertRaises(Exception):validate_translation(source,source)

    def test_prose_spacing_cannot_change_a_numeric_value(self):
        source='Given a positive integer, compute lowbit 6 in this example.'
        translated='给定一个正整数，在这个例子中计算 lowbit6。'
        self.assertIsNotNone(bundled_translation({'markdown':source,'translation':translation(source,translated)}))
        self.assertIsNone(bundled_translation({'markdown':source,'translation':translation(source,translated.replace('6','16'))}))

    def test_accented_phonetic_notation_is_not_a_sentence(self):
        source='Gather sand to form a tower is a Chinese idiom, whose Pinyin is jgrave{u} shbar{a} chacute{e}ng tcheck{a}. It means to pile sand into a pagoda, referring that a little makes a lot.'
        translated='聚沙成塔是一个汉语成语，拼音是jgrave{u} shbar{a} chacute{e}ng tcheck{a}。意思是将沙子堆积成宝塔，比喻积少成多。'
        validate_translation(source,translated)
        with self.assertRaises(Exception):validate_translation(source,source)

    def test_unfenced_python_and_cpp_functions_remain_code(self):
        code='def sample(a: list[int]) -> list[int]:\n    return [a[i] for i in range(len(a))]\n'
        cpp='int main()\n{\n  const char* s="}"; // braces are text\n  if (s[0]) { return 6; }\n  return 6;\n}'
        source='Given an array of positive integers, compute the result.\n\n'+code+'\n'+cpp+'\n'
        values=protect(source)[1].values()
        self.assertIn(code,values);self.assertIn(cpp,values)
        translated=source.replace('Given an array of positive integers, compute the result.','给定一个正整数数组，计算结果。')
        self.assertIsNotNone(bundled_translation({'markdown':source,'translation':translation(source,translated)}))
        self.assertIsNone(bundled_translation({'markdown':source,'translation':translation(source,translated.replace('return 6','return 7'))}))

    def test_raw_sample_tokens_and_pseudocode_are_not_english_prose(self):
        source=('Given an array of positive integers, compute the following result.\n\n'
                'function f(a):\nv := 0\nfor i from 1 to length(a):\nv := v + a[i]\nreturn v\n\n'
                '$ $\\sum_{1 \\le i,j \\le n} f(i,j).$ $\n\n'
                '示例1\n\n输入\n\n复制\n\nHello World\n\n输出\n\n复制\n\nYES\n')
        translated=source.replace('Given an array of positive integers, compute the following result.','给定一个正整数数组，计算以下结果。')
        self.assertNotIn('Hello World',english_prose(source))
        self.assertNotIn('length',english_prose(source))
        self.assertNotIn('sum',english_prose(source))
        self.assertIsNotNone(bundled_translation({'markdown':source,'translation':translation(source,translated)}))
        self.assertIsNone(bundled_translation({'markdown':source,'translation':translation(source,translated.replace('YES','是'))}))

    def test_archive_samples_and_spaced_display_formulas_remain_immutable(self):
        source='Given an integer, print the following value. $ $ \\sum_{i=1}^{n} i \\cdot x_i $ $\n\n--- 样例 1 输入 ---\nABC\nxyz\n--- 样例 1 输出 ---\nYES\n'
        translated=source.replace('Given an integer, print the following value.','给定一个整数，输出以下数值。')
        self.assertIn('$ $ \\sum_{i=1}^{n} i \\cdot x_i $ $',protect(source)[1].values())
        self.assertNotIn('ABC',english_prose(source))
        validate_translation(source,translated)
        self.assertIsNotNone(bundled_translation({'markdown':source,'translation':translation(source,translated)}))
        self.assertIsNone(bundled_translation({'markdown':source,'translation':translation(source,translated.replace('YES','是'))}))

    def test_archive_title_does_not_swallow_prose_or_block_manual_translation(self):
        self.assertIn('Given a positive integer',english_prose(SOURCE))
        class Provider:
            name='fixture'
            def __call__(self,text):
                return text.replace('Train Car','火车车厢').replace('Given a positive integer','给定一个正整数').replace(', print twice its value.','，输出它的两倍。').replace('Input','输入')
        assets=SimpleNamespace(lock=threading.RLock(),_cached=lambda _:statement())
        with tempfile.TemporaryDirectory() as folder:
            result=TranslationService(assets,Path(folder),provider=Provider()).translate('fixture')
            self.assertEqual(result['markdown'],CHINESE)

    def test_only_complete_unchanged_protected_spans_and_current_original_are_accepted(self):
        value={'markdown':SOURCE,'translation':translation()}
        self.assertEqual(bundled_translation(value)['markdown'],CHINESE)
        for original,translated in [(SOURCE+'changed',CHINESE),(SOURCE,CHINESE.replace('$N$','$M$')),
                                    (SOURCE,CHINESE.replace('\n3\n','\n4\n')),(SOURCE,SOURCE)]:
            with self.subTest(original=original,translated=translated):
                self.assertIsNone(bundled_translation({'markdown':original,'translation':translation(markdown=translated)}))

    def test_problem_serves_prebuilt_text_offline_and_discards_stale_text(self):
        value=dict(statement(),translation=translation())
        store=SimpleNamespace(library=SimpleNamespace(statement=lambda _:value),
                              row=lambda _:{'知识点':[]})
        assets=AssetLibrary(store)
        self.assertTrue(assets.problem('fixture',fetch=False)['translation']['cached'])
        self.assertEqual(assets.localized_statement('fixture')['markdown'],CHINESE)
        value['markdown']+=' changed original'
        assets._cached.cache_clear()
        self.assertNotIn('translation',assets.problem('fixture',fetch=False))
        self.assertIsNone(assets.localized_statement('fixture'))

    def test_seed_adds_translation_without_overwriting_fetched_original_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);seed=LibraryDatabase(root/'seed.sqlite3');live=LibraryDatabase(root/'live.sqlite3')
            seed.save_statement('fixture',dict(statement(),translation=translation()))
            live.save_statement('fixture',dict(statement(),fetchedAt='personal-cache-metadata'))
            live.merge_seed(seed.path)
            result=live.statement('fixture')
            self.assertEqual(result['fetchedAt'],'personal-cache-metadata')
            self.assertEqual(result['markdown'],SOURCE)
            self.assertEqual(result['translation']['markdown'],CHINESE)
            live.save_statement('fixture',dict(statement(),fetchedAt='refreshed'))
            self.assertEqual(live.statement('fixture')['translation']['markdown'],CHINESE)
            # A user-edited statement must never gain an unrelated translation.
            live.save_statement('fixture',dict(statement(SOURCE+' edited'),fetchedAt='keep'))
            live.merge_seed(seed.path,fingerprint='new-fixture-seed')
            self.assertNotIn('translation',live.statement('fixture'))
            self.assertEqual(live.statement('fixture')['fetchedAt'],'keep')

if __name__=='__main__':unittest.main()
