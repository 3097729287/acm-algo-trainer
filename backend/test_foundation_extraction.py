"""Reviewed editorial extraction preserves prose, illustrations and relationships."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('extract_foundations', ROOT / 'scripts/extract_foundations.py')
extraction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extraction)


class FoundationExtractionTests(unittest.TestCase):
    def test_reviewed_public_foundations_are_collected_and_exactly_linked(self):
        source = ROOT / 'data/library'
        manifest = extraction.load(ROOT / 'data/foundation_extractions.json')
        additions, links = extraction.extract(source, manifest)
        self.assertEqual((additions, links), ([], []), 'Run the reviewed extraction before shipping')
        editorials = {row['problem_id']: row for row in extraction.load(source / 'detailed_solutions.json')}
        lessons = [row['content'] for row in extraction.load(source / 'lectures.json') if row['content'].get('conceptSource') == 'reviewed-editorial-extraction']
        self.assertEqual(len(lessons), len(manifest['lessons']))
        relationships = extraction.load(source / 'links.json')
        for lesson in lessons:
            problem = lesson['sourceProblemIds'][0]
            editorial = editorials[problem]
            self.assertIn(lesson['sourceMarkdown'], editorial['markdown'])
            body = lesson['sourceMarkdown'].split('\n', 1)[1].strip()
            self.assertIn(body, lesson['markdown'])
            self.assertEqual(hashlib.sha256(lesson['sourceMarkdown'].encode()).hexdigest(), lesson['sourceHash'])
            self.assertEqual(lesson['images'], editorial['images'])
            own = [row for row in relationships if row['lecture_id'] == lesson['id']]
            self.assertEqual([(row['problem_id'], row['kind']) for row in own], [(problem, 'own')])

    def test_append_is_idempotent_and_preserves_existing_content_and_links(self):
        public = ROOT / 'data/library'
        manifest = extraction.load(ROOT / 'data/foundation_extractions.json')
        manifest['lessons'] = manifest['lessons'][:1]
        problem_id = manifest['lessons'][0]['problemId']
        with tempfile.TemporaryDirectory(prefix='tb-foundations-') as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            old = {'id': 'lecture:local', 'content': {'id': 'lecture:local', 'markdown': 'Keep this imported lesson.'}}
            relationship = {'problem_id': problem_id, 'lecture_id': old['id'], 'kind': 'explicit', 'position': 0}
            for name in ('problems', 'detailed_solutions'):
                rows = [row for row in extraction.load(public / (name + '.json')) if row.get('id', row.get('problem_id')) == problem_id]
                (source / (name + '.json')).write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
            for name, rows in (('lectures', [old]), ('links', [relationship]), ('meta', {'schema': '4', 'revision': 'fixture'})):
                (source / (name + '.json')).write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
            source_bytes = {name: (source / (name + '.json')).read_bytes() for name in ('problems', 'detailed_solutions')}
            with patch.object(extraction, 'ROOT', root):
                result = extraction.apply(source, manifest)
                self.assertEqual((result['added'], result['linksAdded']), (1, 1))
                self.assertIn(old, extraction.load(source / 'lectures.json'))
                self.assertIn(relationship, extraction.load(source / 'links.json'))
                after = {path.name: path.read_bytes() for path in source.iterdir()}
                self.assertEqual(extraction.apply(source, manifest)['added'], 0)
                self.assertEqual(after, {path.name: path.read_bytes() for path in source.iterdir()})
                for name, content in source_bytes.items():
                    self.assertEqual((source / (name + '.json')).read_bytes(), content)
                for name in ('lectures', 'links', 'meta'):
                    self.assertEqual(len(list((root / '.backups').glob('*/' + name + '.json'))), 1)

    def test_unknown_or_high_difficulty_cannot_be_added_as_new_work(self):
        public = ROOT / 'data/library'
        manifest = extraction.load(ROOT / 'data/foundation_extractions.json')
        manifest['lessons'] = manifest['lessons'][:1]
        original = extraction.load
        for difficulty in (None, 2201, 3000, True):
            def load(path):
                rows = original(path)
                if Path(path).name == 'problems.json':
                    rows = copy.deepcopy(rows)
                    for row in rows:
                        if row['id'] == manifest['lessons'][0]['problemId']:
                            row['encoded']['difficulty'] = difficulty
                return rows
            with self.subTest(difficulty=difficulty), patch.object(extraction, 'load', side_effect=load):
                with self.assertRaisesRegex(ValueError, 'difficulty'):
                    extraction.extract(public, manifest)


if __name__ == '__main__':
    unittest.main()
