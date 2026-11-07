import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from translation import DeepSeekProvider,TranslationService,protect,restore_math_spelling,english_prose,validate_translation
from scripts.repair_statement_declarations import repair


class SemanticTranslationTests(unittest.TestCase):
    def test_old_shared_translation_is_corrected_without_retranslating_or_editing_original(self):
        source='You are given an array $a$ of length $2n$. Print the maximum possible score.'
        problem={'id':'p','url':'https://codeforces.com/contest/2248/problem/C','markdown':source,'statementAvailable':True}
        wrong='给定一个长度为 $a$ 的数组 $2n$。输出可能获得的最大得分。'
        assets=SimpleNamespace(lock=threading.RLock(),_cached=lambda _:problem)
        with tempfile.TemporaryDirectory() as folder:
            shared=SimpleNamespace(get=lambda *_:wrong)
            service=TranslationService(assets,Path(folder),provider=lambda _:self.fail('A verified role fix needs no translation API'),shared=shared)
            self.assertIn('长度为 $2n$ 的数组 $a$',service.translate('p')['markdown'])
            self.assertEqual(problem['markdown'],source)
            service.close()

    def test_literal_backticks_inside_tex_do_not_hide_english_sentences(self):
        first=r"$s_i=\text{`1'}$";second=r"$s_i=\text{`2'}$"
        source=first+' indicates that this person belongs to the first group, and '+second
        self.assertIn(first,protect(source)[1].values());self.assertIn(second,protect(source)[1].values())
        self.assertIn('indicates that this person',english_prose(source))
        code='`$n$`';self.assertIn(code,protect(code+' then $m$')[1].values())
        original='これは日本語の文章です。漢字と仮名を含む文章を最後まで翻訳してください。\nPoison AND OR Affection by Register int'
        translated='这是一段日文。请完整翻译这段含有汉字与假名的文字。\nPoison AND OR Affection by Register int'
        validate_translation(original,translated)

    def test_readable_math_restores_delimiters_without_accepting_changed_symbols(self):
        source='Given $$$a_i + n$$$ and $$$\\text{YES NO}$$$.'
        self.assertEqual(restore_math_spelling(source,'给定 $a_i+n$ 和 $\\text{YES NO}$。'),'给定 $$$a_i + n$$$ 和 $$$\\text{YES NO}$$$。')
        self.assertEqual(restore_math_spelling(source,'给定 $a_i+2n$ 和 $\\text{YESNO}$。'),'给定 $a_i+2n$ 和 $\\text{YESNO}$。')
        display='$$$$$$ \\begin{array}{l}a_i \\leftarrow a_j\\end{array} $$$$$$'
        self.assertIn(display,protect(display)[1].values())
        self.assertEqual(list(protect('$$$a$$$$$$b$$$')[1].values()),['$$$a$$$','$$$b$$$'])
        self.assertEqual(restore_math_spelling('$$$a_{i} \\leq n$$$','给定 $a_i≤n$。'),'给定 $$$a_{i} \\leq n$$$。')

    def test_readable_retry_keeps_formulas_and_code_when_opaque_tokens_are_dropped(self):
        source='You are given an array $a$ of length $2n$. Print the maximum possible score.\n\n```text\n1 2 3\n```\n'
        class Provider:
            def __call__(self,text):return '给定数组，输出可能获得的最大得分。'
            def translate_readable(self,text):
                return '给定一个长度为 $2n$ 的数组 $a$。输出可能获得的最大得分。'
        with tempfile.TemporaryDirectory() as folder:
            service=TranslationService(None,Path(folder),provider=Provider())
            translated=service._translate_chunk(source)
            self.assertIn('长度为 $2n$ 的数组 $a$',translated)
            self.assertTrue(translated.endswith('\n\n```text\n1 2 3\n```\n'))

    def test_provider_sees_formula_roles_and_can_reorder_intact_inline_tokens(self):
        source='You are given an array $a$ of length $2n$. Print the maximum possible score.'
        protected,tokens=protect(source);name,length=list(tokens)
        def transport(payload,key):
            instruction=payload['messages'][0]['content']
            self.assertIn('"'+name+'": "$a$"',instruction)
            self.assertIn('"'+length+'": "$2n$"',instruction)
            self.assertIn('MAY change order',instruction)
            self.assertEqual(payload['messages'][1]['content'],protected)
            return {'choices':[{'message':{'content':f'给定一个长度为 {length} 的数组 {name}。输出可能获得的最大得分。'},'finish_reason':'stop'}]}
        provider=DeepSeekProvider(transport=transport)
        # A local test provider has no live credentials or network transport.
        class Settings:
            def credentials(self):return None,'https://fixture.invalid','fixture-model','fixture'
        provider.settings=Settings()
        with tempfile.TemporaryDirectory() as folder:
            service=TranslationService(None,Path(folder),provider=provider)
            self.assertEqual(service._translate_chunk(source),'给定一个长度为 $2n$ 的数组 $a$。输出可能获得的最大得分。')

    def test_only_source_proven_reversed_declarations_are_repaired(self):
        source='You are given an array $a$ of length $2n$. Given a string $s$ of length $m$.'
        wrong='给定一个长度为 $a$ 的数组 $2n$，以及长度为 $s$ 的字符串 $m$。'
        fixed,changes=repair(source,wrong)
        self.assertEqual(fixed,'给定一个长度为 $2n$ 的数组 $a$，以及长度为 $m$ 的字符串 $s$。')
        self.assertEqual(len(changes),2)
        self.assertEqual(repair(source,fixed),(fixed,[]))
        self.assertEqual(repair('A different problem without a declaration.',wrong),(wrong,[]))
        self.assertEqual(repair(source+' An array $2n$ of length $a$.',wrong)[1],[changes[1]])

if __name__=='__main__':unittest.main()
