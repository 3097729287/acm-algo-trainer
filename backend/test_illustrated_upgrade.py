"""Reviewed lessons and portable figures survive import and bundled upgrades."""
import base64
from pathlib import Path
import tempfile
import unittest

from educational_images import collect_images
import lecture_curation as C
from library import LibraryDatabase
from test_library import record


class IllustratedUpgradeTests(unittest.TestCase):
    def test_reviewed_lesson_keeps_derivation_once_and_collects_application_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            svg = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"/>'
            for name in ('concept.svg', 'application.svg'):
                (root / name).write_text(svg, encoding='utf-8')
            entry = dict(id='lesson', title='从零讲：枚举', tags=['枚举'],
                         sourceContest='fixture', sourceProblem='A', sourceTitle='示例',
                         editorialVersion='2026-10-11')
            source = '### 从零讲：枚举\n\n独有的推导段落。\n\n![概念](concept.svg)\n\n```cpp\nint answer = 1;\n```\n'
            problem = '## A. 示例\n\n### 题意\n\n实际题目条件。\n\n### 思路\n\n实际应用步骤。\n\n![应用](application.svg)\n'
            result = C.curate(entry, source, problem)
            self.assertEqual(result['markdown'].count('独有的推导段落'), 1)
            self.assertEqual(result['markdown'].count('实际题目条件'), 1)
            self.assertEqual(result['markdown'].count('实际应用步骤'), 1)
            self.assertNotIn('## 本题完整推导与原有例子', result['markdown'])
            self.assertFalse(result['quality']['supplemented'])
            self.assertEqual(result['topic'], '枚举')
            self.assertEqual(result['conceptSource'], 'reviewed-heading')
            self.assertEqual(C.code_hashes(result['markdown']), C.code_hashes(source))
            images = collect_images(result['markdown'], root / 'lesson.md', root)
            self.assertEqual(set(images), {'concept.svg', 'application.svg'})
            database = LibraryDatabase(root / 'library.sqlite3')
            result['images'] = images
            database.import_records([record()], {'lesson': result}, {'fixture::A': [('lesson', 'explicit')]})
            (root / 'concept.svg').unlink()
            (root / 'application.svg').unlink()
            saved = database.lecture_entries()['lesson']
            self.assertEqual(saved['images'], images)
            for data in saved['images'].values():
                self.assertEqual(base64.b64decode(data.split(',')[1]).decode(), svg)

    def test_standalone_reviewed_tutorial_is_not_wrapped_with_duplicate_application(self):
        entry = dict(id='lesson', title='从零讲：枚举', tags=['枚举'], sourceContest='fixture',
                     sourceProblem='A', sourceTitle='示例', editorialVersion='2026-10-11', standalone=True)
        source = '# 枚举教程\n\n## 游戏规则\n\n完整教程。\n\n## 推导\n\n证明。\n'
        result = C.curate(entry, source, '## A. 示例\n\n### 题意\n\n重复条件。\n\n### 思路\n\n重复应用。\n')
        self.assertIn('完整教程。', result['markdown'])
        self.assertNotIn('重复条件', result['markdown'])
        self.assertNotIn('重复应用', result['markdown'])

    def test_upgrade_removes_only_unedited_unreferenced_retired_bundled_lessons(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = LibraryDatabase(root / 'old.sqlite3')
            old.import_records([record()], {name: {'id': name, 'markdown': name} for name in ('retired', 'edited', 'linked')},
                               {'fixture::A': [(name, 'explicit') for name in ('retired', 'edited', 'linked')]})
            live = LibraryDatabase(root / 'live.sqlite3')
            live.merge_seed(old.path)
            live.import_records([record('custom::A')], {'edited': {'id': 'edited', 'markdown': 'Personal lesson edit.'}},
                                {'custom::A': [('linked', 'explicit')]})
            new = LibraryDatabase(root / 'new.sqlite3')
            new.import_records([record()], {'new': {'id': 'new', 'markdown': 'Reviewed lesson.'}},
                               {'fixture::A': [('new', 'explicit')]})
            live.merge_seed(new.path)
            lessons = live.lecture_entries()
            self.assertEqual(set(lessons), {'new', 'edited', 'linked'})
            self.assertEqual(lessons['edited']['markdown'], 'Personal lesson edit.')
            self.assertEqual(live.references('custom::A'), [('linked', 'explicit')])
            self.assertEqual(live.references('fixture::A'), [('new', 'explicit')])
            live.check()


if __name__ == '__main__':
    unittest.main()
