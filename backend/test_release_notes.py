"""Update histories survive upgrades, repeated launches and amended notes."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from release_notes import archive_current


class ReleaseNoteTests(unittest.TestCase):
    def test_history_is_preserved_and_launches_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);app=root/'app';history=root/'Desktop'/'ToBe更新记录'
            (app/'resources/update-notes').mkdir(parents=True)
            def release(version,text):
                (app/'VERSION').write_text(version)
                (app/'resources/update-notes'/(version+'.md')).write_text(text,encoding='utf8')
                return archive_current(app,desktop=history)
            first=release('1.5.5','# 已安装版本\n背景保持未拆。\n')
            original=first.read_bytes()
            second=release('1.5.6','# 新版本\n修复全屏返回桌面。\n')
            self.assertEqual(archive_current(app,desktop=history),second)
            self.assertEqual(len(list(history.glob('*.md'))),2)
            amended=release('1.5.6','# 新版本\n修复全屏返回桌面。\n补充验证结果。\n')
            self.assertNotEqual(amended,second)
            self.assertEqual(first.read_bytes(),original)
            self.assertIn('修复全屏',second.read_text(encoding='utf8'))
            self.assertEqual(len(list(history.glob('*.md'))),3)
