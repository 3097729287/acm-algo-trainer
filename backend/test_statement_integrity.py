"""Disposable statement, resource, task-type and upgrade checks; no live OJ POSTs."""
import base64
from contextlib import closing
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from assets import AssetLibrary
from contest_policy import content_ready, apply_visibility
from library import LibraryDatabase
from statement_format import html_markdown
from statement_integrity import annotate_type, ordinary_samples, statement_type
from statement_resources import archive_resources, inspect_resource, resource_references
from test_library import record


class StatementIntegrityTests(unittest.TestCase):
    def test_background_fetch_cannot_undo_audit_retirement_or_replace_chinese(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            library=LibraryDatabase(Path(directory)/'library.sqlite3')
            raw,encoded,solution,statement=record()
            library.import_records([(raw,encoded,solution,statement)],{}, {})
            old={'id':encoded['id'],'markdown':'Original audited statement.','samples':[{'input':'1','output':'2'}],
                 'translation':{'kind':'site','markdown':'保留已经交付的中文。'},
                 'integrity':{'status':'incomplete','sourceVerified':True,'checkedAt':'original-audit','issues':['unrenderable-source-math:original']}}
            library.save_statement(encoded['id'],old)
            with library.connection() as db:
                data=json.loads(db.execute('SELECT encoded FROM problems WHERE id=?',(encoded['id'],)).fetchone()[0])
                data.update(statementRetired=True,statementRetirementPolicy='public-statement-audit-v1',
                            statementPriorVisibility={'catalogHidden':True},catalogHidden=True)
                db.execute('UPDATE problems SET encoded=? WHERE id=?',(json.dumps(data),encoded['id']))
            before=library.statement(encoded['id'])
            incoming=dict(old,markdown='Fresh original body, not yet reviewed.',translation=None,
                          integrity={'status':'complete','sourceVerified':True,'checkedAt':'new-get'})
            with self.assertRaises(ValueError):library.save_statement(encoded['id'],incoming)
            self.assertEqual(library.statement(encoded['id']),before)
            self.assertTrue(library.find(encoded['id'])['encoded']['statementRetired'])
            reviewed=dict(old,currentSourceMarkdown=incoming['markdown'],integrity=dict(incoming['integrity'],
                corpusAuditVerifiedSha256=hashlib.sha256(incoming['markdown'].encode()).hexdigest()))
            library.save_statement(encoded['id'],reviewed)
            self.assertNotIn('statementRetired',library.find(encoded['id'])['encoded'])
            self.assertTrue(library.find(encoded['id'])['encoded']['catalogHidden'],'unrelated earlier policy stays hidden')
            self.assertEqual(library.statement(encoded['id'])['translation'],old['translation'])

    def test_verified_pdf_can_use_native_adapter_without_entering_local_judge(self):
        from statement_integrity import native_submission_supported
        assets=AssetLibrary.__new__(AssetLibrary)
        pdf={'markdown':'Original complete PDF.', 'samples':[], 'localJudgeSupported':False,
             'integrity':{'status':'complete','sourceVerified':True,'sampleCount':0,'pdfPageCountVerified':True}}
        assets._cached=lambda identity:dict(pdf)
        rows=[{'id':'pdf','url':'https://qoj.ac/problem/18307'},
              {'id':'communication','url':'https://qoj.ac/problem/18308','problemType':'communication','catalogReplayReady':True},
              {'id':'foreign','url':'https://example.test/problem/1','catalogReplayReady':True}]
        self.assertEqual([r['id'] for r in assets.candidates(rows,official=True)],['pdf'])
        self.assertFalse(ordinary_samples(pdf))
        self.assertFalse(native_submission_supported('https://qoj.ac.evil.test/problem/18307'))
        self.assertFalse(native_submission_supported('https://qoj.ac/problem/18307?contest_id=1'))

    def test_verified_source_alias_keeps_one_identity_after_seed_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);seed=LibraryDatabase(root/'seed.sqlite3')
            raw,encoded,solution,statement=record()
            encoded['verifiedSourceAliases']=[{'platform':'QOJ','url':'https://qoj.ac/problem/14684'}]
            seed.import_records([(raw,encoded,solution,statement)],{}, {})
            self.assertEqual(seed.find(url='https://qoj.ac/problem/14684')['id'],encoded['id'])
            rebuilt=LibraryDatabase.from_source(seed.export_source(root/'source'),root/'rebuilt.sqlite3')
            self.assertEqual(rebuilt.find(url='https://qoj.ac/problem/14684')['id'],encoded['id'])
            self.assertEqual(len(rebuilt.rows()),1)

    def test_zero_samples_requires_source_evidence_and_does_not_hide_special_types(self):
        value = {'markdown': 'This is an interactive problem. Ask the judge for a vertex.', 'samples': []}
        self.assertFalse(content_ready(value))
        value['integrity'] = {'sourceVerified': True, 'sampleCount': 0}
        self.assertTrue(content_ready(value))
        self.assertFalse(ordinary_samples(value))
        value['samples'] = [{'input': '1', 'output': '2'}]
        self.assertFalse(ordinary_samples(value), 'a transcript is not a normal executable sample')
        self.assertEqual(statement_type({'markdown': 'This is not an interactive problem.'}), 'standard')
        self.assertEqual(statement_type({'markdown': '本题为提交答案题。'}), 'output-only')
        self.assertEqual(statement_type({'communication': True}), 'communication')
        self.assertFalse(content_ready({'markdown': '# Input\n\n# Output', 'samples': [{'input':'','output':''}]}))

    def test_sql_and_python_reject_a_malformed_sample_and_keep_special_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            db = LibraryDatabase(Path(directory) / 'library.sqlite3')
            db.import_records([record()], {}, {})
            for samples in [[{'input': '1', 'output': '2'}, {'input': 'missing output'}], [None]]:
                db.save_statement('fixture::A', {'markdown': 'Read two integers and print their sum.', 'samples': samples})
                self.assertFalse(db.find('fixture::A')['content_ready'])
                self.assertFalse(content_ready(db.statement('fixture::A')))
            value = {'markdown': 'This is an interactive problem. Ask queries.', 'samples':[{'input':'1','output':'2'}]}
            db.save_statement('fixture::A', value)
            self.assertFalse(db.find('fixture::A')['content_ready'])
            self.assertTrue(db.statement('fixture::A')['statementAvailable'])

    def test_explicit_retirement_overrides_training_membership_without_deleting_id(self):
        row = {'id':'same-id', 'trainingListMember': True, 'statementRetired': True}
        self.assertTrue(apply_visibility(row)['catalogHidden'])
        self.assertEqual(apply_visibility(row)['id'], 'same-id')

    def test_gif_original_bytes_frames_and_reference_image_survive(self):
        from PIL import Image
        output = io.BytesIO()
        Image.new('RGB', (3, 3), 'red').save(output, format='GIF', save_all=True,
            append_images=[Image.new('RGB', (3,3), 'blue')], duration=[50, 150], loop=0)
        data = output.getvalue(); url = 'https://img.atcoder.jp/fixture/animation.gif'
        client = Mock(); client.bytes.return_value = data
        value = archive_resources({'url':'https://atcoder.jp/contests/fixture/tasks/fixture_a',
            'markdown':'An animation: ![steps][figure]\n\n[figure]: '+url, 'samples': []}, client)
        self.assertEqual(value['resourceManifest'][url]['frameCount'], 2)
        self.assertEqual(base64.b64decode(value['images'][url].split(',',1)[1]), data)
        self.assertEqual(value['resourceIssues'], [])
        with self.assertRaises(ValueError): inspect_resource(b'<html>Login</html>', url, 'image')

    def test_all_pdf_pages_and_the_original_download_are_preserved(self):
        from pypdf import PdfWriter
        output = io.BytesIO(); writer = PdfWriter()
        for _ in range(3): writer.add_blank_page(100, 150)
        writer.write(output); data = output.getvalue(); url = 'https://qoj.ac/fixture.pdf'
        client = Mock(); client.bytes.return_value = data
        value = archive_resources({'url':'https://qoj.ac/problem/1','markdown':'[PDF]('+url+')','samples':[]},client)
        self.assertEqual(value['attachments'][url]['pageCount'],3)
        self.assertEqual(base64.b64decode(value['attachments'][url]['data'].split(',',1)[1]),data)

    def test_interaction_table_keeps_lines_inside_their_cells(self):
        value = html_markdown('<table><tr><th>Input</th><th>Output</th></tr><tr><td><pre>2\n1 2\n3 4</pre></td><td>query<br>reply</td></tr></table>')
        self.assertIn('`2`<br />`1 2`<br />`3 4`',value)
        self.assertIn('query<br />reply',value)
        self.assertEqual(len(value.splitlines()),3)

    def test_qoj_normal_missing_statement_entry_uses_the_existing_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Mock(); store.library = LibraryDatabase(Path(directory)/'library.sqlite3')
            assets = AssetLibrary(store,Path(directory)/'assets')
            result = {'id':'fixture-qoj','title':'Original','url':'https://qoj.ac/problem/18307',
                'markdown':'Read the integer and print its square.', 'samples':[{'input':'2','output':'4'}]}
            with patch('public_platforms.statement',return_value=result) as adapter:
                self.assertEqual(assets._fetch_missing('fixture-qoj',result)['id'],'fixture-qoj')
                adapter.assert_called_once()
                self.assertEqual(store.library.statement('fixture-qoj')['markdown'],result['markdown'])
            assets.close()

    def test_online_backup_and_seed_merge_preserve_wal_edits_imports_and_chinese(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); seed=LibraryDatabase(root/'seed.sqlite3');seed.import_records([record()],{}, {})
            live=LibraryDatabase(root/'live.sqlite3'); live.merge_seed(seed.path)
            statement={'markdown':'Read numbers.', 'samples':[{'input':'','output':'1'}],
                'translation':{'kind':'site','markdown':'读取数字。'}}
            live.save_statement('fixture::A',statement)
            import sqlite3
            with closing(sqlite3.connect(live.path)) as db:
                db.execute('PRAGMA journal_mode=WAL')
                db.execute('CREATE TABLE private_draft(code TEXT)')
                db.execute('INSERT INTO private_draft VALUES (?)',('my unsent code',))
                db.commit()
                self.assertTrue(Path(str(live.path)+'-wal').exists())
                backup=root/'online.sqlite3'
                with live.connection() as source, closing(sqlite3.connect(backup)) as destination:
                    source.backup(destination)
            with LibraryDatabase(backup,readonly=True).connection() as db:
                self.assertEqual(db.execute('SELECT code FROM private_draft').fetchone()[0],'my unsent code')
            seed.save_statement('fixture::A',dict(statement,images={'offline':'unchanged bytes'}))
            live.merge_seed(seed.path, fingerprint='second')
            self.assertEqual(live.statement('fixture::A')['translation']['markdown'],'读取数字。')
            with live.connection() as db:
                self.assertEqual(db.execute('SELECT code FROM private_draft').fetchone()[0],'my unsent code')


if __name__ == '__main__': unittest.main()
