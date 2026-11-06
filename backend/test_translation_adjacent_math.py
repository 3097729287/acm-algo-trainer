from collections import Counter
import unittest
from translation import protect, restore, validate_translation, TranslationIncomplete


class AdjacentFormulaTests(unittest.TestCase):
    def test_touching_cf_formulas_do_not_hide_following_english(self):
        original=('An array $$$b$$$ is disgusting if $$$1 < gcd(b_i,b_j) < min(b_i,b_j)$$$$$$^{*}$$$.\n\n'
                  'You are given an array $$$a$$$ of length $$$n$$$, consisting of positive integers.\n\n'
                  'You can perform at most $$$n+10$$$ operations. Print any valid array.\n')
        shielded,tokens=protect(original)
        self.assertIn('You are given an array',shielded)
        self.assertIn('consisting of positive integers',shielded)
        self.assertIn('You can perform at most',shielded)
        self.assertIn('Print any valid array.',shielded)
        self.assertIn('$$$1 < gcd(b_i,b_j) < min(b_i,b_j)$$$',tokens.values())
        self.assertIn('$$$^{*}$$$',tokens.values())
        self.assertFalse(any('You are given' in value for value in tokens.values()))
        partial=original.replace('An array','一个数组').replace('is disgusting if','在以下情况下是恶心的')
        with self.assertRaises(TranslationIncomplete):validate_translation(original,partial)
        translated=shielded.replace('An array','一个数组').replace('is disgusting if','在以下情况下是恶心的').replace('You are given an array','给定数组').replace('of length','长度为').replace('consisting of positive integers.','，由正整数组成。').replace('You can perform at most','最多可以执行').replace('operations. Print any valid array.','次操作。输出任意合法的数组。')
        result=restore(translated,tokens)
        validate_translation(original,result)
        self.assertEqual(Counter(protect(result)[1].values()),Counter(tokens.values()))

    def test_mixed_adjacent_math_and_dollar_literals_in_code_stay_separate(self):
        text='Use `$price` here. Given $$a$$$$b$$ and $$$c$$$$$$d$$$, print $n$ integers.\n\n```cpp\ncout << "$name";\n```'
        shielded,tokens=protect(text)
        self.assertIn('Given',shielded)
        self.assertIn('integers.',shielded)
        for formula in ['$$a$$','$$b$$','$$$c$$$','$$$d$$$','$n$','`$price`']:
            self.assertIn(formula,tokens.values())


if __name__=='__main__':unittest.main()
