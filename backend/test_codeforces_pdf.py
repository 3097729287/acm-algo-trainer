"""Chinese native PDFs, exact pages/samples and retained offline statement data."""
import base64
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from assets import AssetLibrary
from codeforces_pdf import candidates, localized, needs_localized_pdf, selected_pages
from library import LibraryDatabase
from public_platforms import statement as public_statement
from statement_asset_store import references
from statement_format import needs_statement_refresh
from test_library import record
from test_recycle_policy import retained_fixture

URL = 'https://codeforces.com/gym/123456/problem/A'
PDF = 'https://codeforces.com/gym/123456/attachments/download/99/statement-zh.pdf'
FIXTURE = Path(__file__).with_name('fixtures') / 'gym-chinese-booklet.pdf'
ROSTER = ''.join('<tr><td><a href="/gym/123456/problem/'+label+'">'+label+'</a></td>'
    '<td><a href="/gym/123456/problem/'+label+'">'+title+'</a></td><td>1 s, 256 MB</td></tr>'
    for label, title in [('A', 'Addition'), ('B', 'Multiplication')])
LINK = '<a href="'+PDF+'">Statements (zh)</a>'
HTML = ('<div class="problem-statement"><div class="title">A. Addition</div>'
    '<p>Given two integers, print their sum.</p><div class="sample-test">'
    '<div class="input"><pre>1 2</pre></div><div class="output"><pre>3</pre></div></div></div>'+LINK)


def client():
    value = Mock()
    value.text.side_effect = lambda url: {URL: HTML, 'https://codeforces.com/gym/123456': ROSTER}[url]
    value.bytes.side_effect = lambda url: FIXTURE.read_bytes() if url == PDF else (_ for _ in ()).throw(AssertionError(url))
    return value


def cached():
    return {'id': 'fixture::A', 'title': 'Addition', 'url': URL,
        'markdown': '# Addition\n\nGiven two integers, print their sum.',
        'statementVersion': 3, 'statementAvailable': True,
        'samples': [{'name': '样例 1', 'input': '1 2', 'output': '3'}],
        'limits': {'timeMs': 1000, 'memoryMb': 256}}


class CodeforcesPdfTests(unittest.TestCase):
    def test_english_html_also_discovers_original_chinese_booklet(self):
        value = public_statement(client(), 'fixture::A', 'Addition', URL)
        self.assertEqual(value['sitePdfStatus'], 'verified')
        self.assertIn('Given two integers', value['markdown'])
        self.assertEqual(value['samples'], cached()['samples'])
        zh = value['translation']
        self.assertEqual(zh['kind'], 'site')
        self.assertEqual(zh['sourcePageNumbers'], [3, 4])
        self.assertEqual(zh['statementPdf']['widthPoints'], 440)
        self.assertEqual(zh['sourceBinding'], {'kind': 'official-bilingual-roster', 'problem': 'A',
            'pdfTitle': '加法', 'rosterTitle': 'Addition', 'samplePairsVerified': 1})
        self.assertIn('不能遗漏本页', zh['sourceText'])
        self.assertNotIn('Problem B', zh['sourceText'])
        from pypdf import PdfReader
        self.assertEqual(len(PdfReader(io.BytesIO(base64.b64decode(zh['statementPdf']['data'].split(',')[1]))).pages), 2)
        self.assertEqual(base64.b64decode(value['attachments'][PDF]['data'].split(',')[1]), FIXTURE.read_bytes())
        self.assertEqual(value['integrity']['status'], 'complete')

    def test_no_html_falls_back_to_the_same_verified_native_chinese_pages(self):
        c = client()
        c.text.side_effect = lambda url: {URL: LINK, 'https://codeforces.com/gym/123456': ROSTER}[url]
        value = public_statement(c, 'fixture::A', 'Addition', URL)
        self.assertEqual(value['statementLanguage'], 'zh-CN')
        self.assertEqual(value['sourcePageNumbers'], [3, 4])
        self.assertEqual(value['samples'], cached()['samples'])
        self.assertEqual(value['integrity']['status'], 'complete')

    def test_wrong_samples_and_incomplete_bilingual_inventory_keep_the_english_cache(self):
        old = cached()
        old['samples'][0]['output'] = 'not the same example'
        after = localized(client(), old)
        self.assertEqual(after['sitePdfStatus'], 'unavailable')
        self.assertNotIn('translation', after)
        self.assertEqual(after['markdown'], old['markdown'])
        self.assertEqual(after['samples'], old['samples'])
        self.assertNotIn('sitePdfStatus', old, 'the caller snapshot is immutable')
        c = client()
        c.text.side_effect = lambda url: {URL: HTML, 'https://codeforces.com/gym/123456': ROSTER.split('</tr>', 1)[0]+'</tr>'}[url]
        self.assertEqual(localized(c, cached())['sitePdfStatus'], 'unavailable')

    def test_other_contests_tutorials_foreign_hosts_and_unexpected_ports_are_not_downloaded(self):
        for href, text in [(PDF.replace('123456', '654321'), 'Statements (zh)'),
                           (PDF.replace('codeforces.com', 'example.org'), 'Statements (zh)'),
                           (PDF.replace('.com/', '.com:444/'), 'Statements (zh)'),
                           (PDF, 'Tutorial (zh)'), (PDF+'?elsewhere=1', 'Statements (zh)')]:
            c = client()
            value = localized(c, cached(), '<a href="'+href+'">'+text+'</a>')
            self.assertEqual(value['sitePdfStatus'], 'not-provided')
            c.bytes.assert_not_called()
            c.text.assert_not_called()
        self.assertEqual(candidates('<a href="'+PDF+'">Statements (en)</a>', URL, chinese_only=True), [])

    def test_repeated_headers_continue_but_ambiguous_labels_or_cover_titles_do_not_bind(self):
        reader = Mock()
        reader.pages = [None] * 5
        tasks = {'A': {'title': 'Addition'}, 'B': {'title': 'Multiplication'}}
        texts = ['A 加法\nB 乘法', 'Problem A. 加法\n正文', 'Problem A. 加法\n续页', '续页', 'Problem B. 乘法']
        self.assertEqual(selected_pages(reader, 'A', 'Addition', texts=texts, tasks=tasks, bilingual=True)[0], [1, 2, 3])
        for bad in [texts[:3]+['Problem B. 乘法', 'Problem A. 加法'],
                    ['A 错误题名\nB 乘法']+texts[1:], ['A 加法']+texts[1:]]:
            with self.assertRaises(ValueError):
                selected_pages(reader, 'A', 'Addition', texts=bad, tasks=tasks, bilingual=True)
        with self.assertRaises(ValueError):
            selected_pages(reader, 'A', 'Addition', texts=texts)

    def test_bare_letter_headings_chinese_samples_cross_pages_and_real_input_integers(self):
        from qoj import pdf_statement
        from pypdf import PdfReader
        data=FIXTURE.with_name('gym-chinese-numbered.pdf').read_bytes()
        value=pdf_statement(data,'fixture',render_pages=False)
        self.assertEqual(value['sampleExtraction'],'pdf-code-geometry-v1')
        self.assertEqual(value['samples'],[
            {'name':'样例 1','input':'3\n1 2 3','output':'6'},
            {'name':'样例 2','input':'1 3\n2 1 2 3','output':'1 12'}])
        indices,_=selected_pages(PdfReader(io.BytesIO(data)),'A','求和')
        self.assertEqual(indices,[1,2])

    def test_a_problem_url_returning_pdf_keeps_the_original_and_its_chinese_variant(self):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        writer=PdfWriter();page=writer.add_blank_page(width=440,height=600)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
        stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 30 560 Td (Addition) Tj ET\nBT /F1 12 Tf 30 520 Td (Given two integers, print their sum.) Tj ET')
        page[NameObject('/Contents')]=writer._add_object(stream)
        output=io.BytesIO();writer.write(output);data=output.getvalue()
        c=client();c.text.side_effect=lambda url: data.decode('utf-8','replace') if url==URL else ROSTER+LINK
        c.bytes.side_effect=lambda url: data if url==URL else FIXTURE.read_bytes()
        value=public_statement(c,'fixture::A','Addition',URL)
        self.assertIn('Given two integers',value['sourceText'])
        self.assertEqual(value['sourceBinding']['kind'],'native-problem-pdf-title')
        self.assertEqual(base64.b64decode(value['attachments'][URL]['data'].split(',')[1]),data)
        self.assertEqual(value['translation']['sourcePageNumbers'],[3,4])

    def test_prepared_chinese_is_never_replaced_and_old_cache_is_enriched_once(self):
        old = cached()
        self.assertTrue(needs_statement_refresh(old))
        old['translation'] = {'kind': 'site', 'markdown': '保留已经交付的中文。'}
        c = client()
        self.assertEqual(localized(c, old), old)
        self.assertFalse(needs_localized_pdf(old))
        c.text.assert_not_called()
        checked = localized(client(), cached(), '<p>No Chinese attachment.</p>')
        self.assertFalse(needs_statement_refresh(checked))

    def test_background_enrichment_keeps_audit_original_and_personal_data_and_roundtrips_offline(self):
        root = Path(retained_fixture('gym-pdf').name)
        library = LibraryDatabase(root/'library.sqlite3')
        raw, encoded, solution, _ = record()
        encoded['url'] = URL
        old = cached()
        old['integrity'] = {'sourceVerified': True, 'status': 'incomplete', 'checkedAt': 'old-audit',
                            'issues': ['retained original audit']}
        library.import_records([(raw, encoded, solution, old)], {}, {})
        with library.connection() as db:
            db.execute('CREATE TABLE private_draft(code TEXT)')
            db.execute('INSERT INTO private_draft VALUES (?)', ('personal code stays',))
        store = Mock(library=library)
        assets = AssetLibrary(store, root/'assets')
        assets._public_client = client()
        before = library.statement('fixture::A')
        try:
            # API-only draft/response fields must not enter the public statement.
            assets._fetch_statement('fixture::A', dict(before, draft='not part of statement'))
        finally:
            assets.close()
        saved = library.statement('fixture::A')
        self.assertNotIn('draft', saved)
        for field in ('markdown', 'samples', 'limits', 'integrity'):
            self.assertEqual(saved[field], before[field])
        self.assertEqual(saved['sitePdfStatus'], 'verified')
        with library.connection() as db:
            raw_statement = json.loads(db.execute('SELECT content FROM statements').fetchone()[0])
            self.assertTrue(raw_statement['translation']['statementPdf']['data'].startswith('tb-asset:'))
            self.assertEqual(len(references(raw_statement)), 2)
            self.assertEqual(db.execute('SELECT count(*) FROM statement_assets').fetchone()[0], 2)
            self.assertEqual(db.execute('SELECT code FROM private_draft').fetchone()[0], 'personal code stays')
        rebuilt = LibraryDatabase.from_source(library.export_source(root/'source'), root/'rebuilt.sqlite3')
        self.assertEqual(rebuilt.statement('fixture::A')['translation'], saved['translation'])


if __name__ == '__main__':
    unittest.main()
