import unittest

from statement_format import codeforces_samples, html_markdown


class SavedStatements(unittest.TestCase):
    def test_katex_keeps_source_once(self):
        html = '<p>区间 <span class="katex"><span class="katex-mathml"><math><semantics><mrow>重复</mrow><annotation encoding="application/x-tex">[L,R]</annotation></semantics></math></span><span class="katex-html">重复</span></span></p>'
        self.assertEqual(html_markdown(html), '区间 $[L,R]$')

    def test_mathjax_keeps_source_once(self):
        html = '<p><span class="MathJax_Preview">n</span><span class="MathJax">n</span><script type="math/tex">n^2</script> 个</p><script>alert(1)</script>'
        self.assertEqual(html_markdown(html), '$n^2$ 个')

    def test_saved_samples_keep_lines_and_empty_input(self):
        html = '<div class="problem-statement"><div class="sample-test"><div class="input"><div class="title">InputCopy</div><pre id="saved"><div class="test-example-line">3</div><div class="test-example-line">1 2 3</div></pre></div><div class="output"><pre id="saved2">6<br>7<br></pre></div><div class="input"><pre></pre></div><div class="output"><pre>Hi</pre></div></div></div>'
        samples = codeforces_samples(html)
        self.assertEqual([(s['input'], s['output']) for s in samples], [('3\n1 2 3', '6\n7'), ('', 'Hi')])

    def test_parentheses_in_link_destination(self):
        self.assertEqual(html_markdown('<a href="https://example.org/Tree_(graph_theory)">tree</a>'),
                         '[tree](https://example.org/Tree_%28graph_theory%29)')

    def test_incomplete_pair_rejected(self):
        with self.assertRaises(ValueError):
            codeforces_samples('<div class="problem-statement"><div class="input"><pre>1</pre></div></div>')

    def test_atcoder_sample_output_keeps_explanation_formula_and_figure(self):
        html='<div class="part"><section><h3>Sample Input 1</h3><pre>5 3\n1 3 1 5 1</pre></section></div><div class="part"><section><h3>Sample Output 1</h3><pre>3</pre><p>As shown below, count <var>(2,3)</var> once.</p><img src="//img.atcoder.jp/abc481/figure.png"/></section></div>'
        text=html_markdown(html,'https://atcoder.jp/contests/abc481/tasks/abc481_b')
        self.assertIn('Sample Input 1',text)
        self.assertIn('5 3\n1 3 1 5 1',text)
        self.assertIn('count $(2,3)$ once.',text)
        self.assertIn('![](https://img.atcoder.jp/abc481/figure.png)',text)

    def test_lazy_picture_source_and_old_atcoder_cache_migration(self):
        from statement_format import needs_statement_refresh
        self.assertIn('https://img.atcoder.jp/a.png',html_markdown('<img data-src="https://img.atcoder.jp/a.png"/>'))
        self.assertTrue(needs_statement_refresh({'url':'https://atcoder.jp/contests/abc481/tasks/abc481_b','statementVersion':4}))
        self.assertFalse(needs_statement_refresh({'url':'https://atcoder.jp/contests/abc481/tasks/abc481_b','statementVersion':5}))


if __name__ == '__main__':
    unittest.main()
