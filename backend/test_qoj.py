"""QOJ HTML/Chinese examples and genuine PDF table geometry, offline."""
import io
import unittest
from unittest.mock import Mock
from qoj import statement,pdf_statement,problem_id

class QojTests(unittest.TestCase):
    def test_contest_language_and_base_links_share_exact_original_identity(self):
        from insights import canonical_url
        from integrations import canonical
        for url in ('https://qoj.ac/problem/18307','https://qoj.ac/contest/3767/problem/18307/statement/zh_cn'):
            self.assertEqual(canonical_url(url),'qoj.ac/problem/18307')
            self.assertEqual(canonical(url),'https://qoj.ac/problem/18307')
    def page(self,article):return '<span>Time Limit: 4.0 s Memory Limit: 1024 MB Total points: 100</span><h1 class="page-header">#18307. 华容道</h1>'+article

    def test_html_preserves_formula_limits_and_samples_not_ui_or_points(self):
        article='<article class="uoj-article"><p>满足 $a_i \\le n$。</p><h3>输入格式</h3><p>输入数据。</p><h3>样例</h3><h4>输入样例 1</h4><pre>2\n1 2</pre><h4>输出样例 1</h4><pre>3</pre></article><form><pre>private draft must not appear</pre></form>'
        client=Mock();client.text.return_value=self.page(article)
        value=statement(client,'qoj::18307','old','https://qoj.ac/contest/3767/problem/18307/statement/zh_cn')
        self.assertIn('$a_i \\le n$',value['markdown']);self.assertNotIn('private draft',value['markdown'])
        self.assertEqual(value['samples'],[{'name':'样例 1','input':'2\n1 2','output':'3'}])
        self.assertEqual(value['limits'],{'timeMs':4000,'memoryMb':1024});self.assertNotIn('difficulty',value)
        self.assertEqual(value['statementLanguage'],'zh-CN')

    def test_login_mismatched_identity_and_cross_host_pdf_are_rejected(self):
        client=Mock();client.text.return_value='<h1>Login</h1>'
        with self.assertRaises(ValueError):statement(client,'qoj::18307','','https://qoj.ac/problem/18307')
        client.text.return_value=self.page('<iframe id="statements-pdf" src="https://example.org/download.php?type=statement&id=18307"></iframe>')
        with self.assertRaises(ValueError):statement(client,'qoj::18307','','https://qoj.ac/problem/18307')
        client.bytes.assert_not_called()
        for url in ('https://qoj.ac.evil/problem/1','http://qoj.ac/problem/1','https://qoj.ac/problem/no','https://user@qoj.ac/problem/1'):
            with self.assertRaises(ValueError):problem_id(url)

    def test_numbered_chinese_format_headings_are_actual_site_samples(self):
        client=Mock();client.text.return_value=self.page('<article class="uoj-article"><h3>输入格式</h3><p>输入测试用例。</p><h3>样例</h3><h4>输入格式 1</h4><pre>1\n2</pre><h4>输出格式 1</h4><pre>3</pre></article>')
        value=statement(client,'qoj::18307','','https://qoj.ac/problem/18307/statement/zh_cn')
        self.assertEqual([(x['input'],x['output']) for x in value['samples']],[('1\n2','3')])

    def pdf(self,split_borders=False):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        writer=PdfWriter();page=writer.add_blank_page(width=220,height=220)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
        commands=b'10 100 200 80 re S 105 100 m 105 180 l S 10 160 m 210 160 l S 10 130 m 210 130 l S\nBT /F1 8 Tf 20 170 Td (standard input) Tj ET\nBT /F1 8 Tf 115 170 Td (standard output) Tj ET\nBT /F1 8 Tf 20 145 Td (1 2) Tj ET\nBT /F1 8 Tf 115 145 Td (3) Tj ET\nBT /F1 8 Tf 20 115 Td (2 3) Tj ET\nBT /F1 8 Tf 115 115 Td (5) Tj ET'
        if split_borders:
            # Actual QOJ PDFs draw the header and body borders separately;
            # their endpoints differ by about 0.4pt, with no full-height line.
            commands=commands.replace(b'10 100 200 80 re S 105 100 m 105 180 l S',
                b'10 180 m 210 180 l S 10 100 m 210 100 l S '
                b'10 160.2 m 10 180 l S 10 100 m 10 159.8 l S '
                b'105 160.2 m 105 180 l S 105 100 m 105 159.8 l S '
                b'210 160.2 m 210 180 l S 210 100 m 210 159.8 l S')
        stream=DecodedStreamObject();stream.set_data(commands);page[NameObject('/Contents')]=writer._add_object(stream)
        buffer=io.BytesIO();writer.write(buffer)
        return buffer.getvalue()

    def test_pdf_page_images_and_two_separate_table_samples(self):
        value=pdf_statement(self.pdf(),'1')
        self.assertEqual(value['pageCount'],1);self.assertEqual(value['statementFormat'],'pdf-pages-v1')
        self.assertEqual([(sample['input'],sample['output']) for sample in value['samples']],[('1 2','3'),('2 3','5')])
        self.assertTrue(next(iter(value['images'].values())).startswith('data:image/png;base64,'))

    def test_pdf_split_header_and_body_borders_keep_all_sample_rows(self):
        value=pdf_statement(self.pdf(split_borders=True),'1')
        self.assertEqual([(s['input'],s['output']) for s in value['samples']],[('1 2','3'),('2 3','5')])

if __name__=='__main__':unittest.main()
